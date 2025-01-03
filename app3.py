import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QDialog, QScrollArea, QWidget, QMainWindow, QStackedWidget, QVBoxLayout, QGridLayout, QPushButton, QLineEdit, QLabel, QSizePolicy
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QMutex, QMutexLocker
import cv2
from picamera2 import Picamera2
from PIL import Image
import copy
from math import atan, pi, radians, sin, cos


class CameraThread(QThread):
    send_frame_to_window = pyqtSignal(np.ndarray)
    send_ex_complited_announce = pyqtSignal(str)

    def __init__(self, w: int, h: int, all_exes):
        super().__init__()

        self.w = w
        self.h = h

        self.cam = Picamera2()
        self.cam.configure(self.cam.create_preview_configuration(
            main={'size': (self.w, self.h)}))
        self.cam.start()
        self.is_calibrating = False
        self.is_calibrated = False
        self.skip_frames_number = 5
        self.curr_skip = -1
        self.is_changing_ex = False
        self.curr_point = 0
        self.rect_ct = [0, 0, 0, 0]

        self.all_exes = all_exes
        self.all_exes_count = len(self.all_exes)
        self.curr_ex = 0
        self.figures = {}
        self.new_figures = {}
        self.set_figures()
        self.backSub = cv2.createBackgroundSubtractorMOG2()

        self._is_running = True

    def run(self):
        while self._is_running:
            if self.is_calibrating:
                continue
            self.frame = self.cam.capture_array()
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)

            if not self.is_calibrated:
                continue

            if self.is_changing_ex:
                continue

            fg_mask = self.backSub.apply(self.frame)

            retval, mask_thr = cv2.threshold(fg_mask, 220, 255,
                                             cv2.THRESH_BINARY)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask_eroded = cv2.morphologyEx(mask_thr, cv2.MORPH_OPEN, kernel)

            mask_for_ct = mask_eroded

            contours, hierarchy = cv2.findContours(mask_for_ct,
                                                   cv2.RETR_EXTERNAL,
                                                   cv2.CHAIN_APPROX_SIMPLE)

            min_contour_area = 100
            large_contours = [ct for ct in contours if
                              cv2.contourArea(ct) > min_contour_area]

            if self.curr_skip >= 0 and self.curr_skip <= self.skip_frames_number:
                self.curr_skip += 1
                continue

            frame_with_rect = self.frame.copy()
            for ct in large_contours:
                x, y, w, h = cv2.boundingRect(ct)
                points = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                for pt in points:
                    for key in self.figures.keys():
                        fig = self.new_figures[key]
                        cx, cy = fig[0]
                        a, b = fig[1]
                        theta = radians(fig[2])

                        dx = pt[0] - cx
                        dy = pt[1] - cy

                        rot_x = dx * cos(theta) + dy * sin(theta)
                        rot_y = dx * (-sin(theta)) + dy * cos(theta)

                        eq = (rot_x ** 2) / (a ** 2) + (rot_y ** 2) / (b ** 2)
                        if eq <= 1:
                            self.is_changing_ex = True
                            print(f'Ex {self.curr_ex + 1} completed')
                            self.ex_completed()
                            continue

                frame_with_rect = cv2.rectangle(self.frame, (x, y), (x + w, y + h),
                                                (0, 0, 150), 2)

            frame_with_rect = cv2.line(self.frame, self.rect_ct[0], self.rect_ct[1],
                                       (0, 100, 0), 2)
            frame_with_rect = cv2.line(self.frame, self.rect_ct[1], self.rect_ct[2],
                                       (0, 100, 0), 2)
            frame_with_rect = cv2.line(self.frame, self.rect_ct[2], self.rect_ct[3],
                                       (0, 100, 0), 2)
            frame_with_rect = cv2.line(self.frame, self.rect_ct[0], self.rect_ct[3],
                                       (0, 100, 0), 2)
            for key in self.figures.keys():
                fig = self.new_figures[key]
                frame_with_rect = cv2.ellipse(self.frame, fig[0], fig[1], fig[2], 0,
                                              360, (255, 0, 0), 2)

            frame_with_rect = cv2.cvtColor(frame_with_rect, cv2.COLOR_BGR2RGB)
        self.cam.stop()
        self.cam.close()

    def stop(self):
        self.cam.stop()
        self.cam.close()
        self._is_running = False

    def set_figures(self):
        self.figures = {}
        if self.curr_ex >= self.all_exes_count:
            self.send_ex_complited_announce.emit('end')
        for key in self.all_exes[self.curr_ex][1]:
            self.figures[key[0]] = key[1]
        print(self.figures)

    @pyqtSlot(int)
    def start_calibration(self, input):
        if input == 0:
            self.is_calibrating = True
            self.curr_point = 0
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            self.send_frame_to_window.emit(rgb_frame)

    @pyqtSlot(np.ndarray)
    def set_calibration_point(self, point):
        self.rect_ct[self.curr_point] = point
        self.curr_point += 1
        self.frame = cv2.ellipse(self.frame, point, (0, 0), 0, 0,
                                 360, (0, 255, 0), 10)
        if self.curr_point >= 2:
            self.frame = cv2.line(self.frame,
                                  self.rect_ct[self.curr_point - 1],
                                  self.rect_ct[self.curr_point - 2],
                                  (0, 100, 0), 2)
        rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        self.send_frame_to_window.emit(rgb_frame)

        if self.curr_point == 4:
            self.do_calibration()

    def do_calibration(self):
        self.is_calibrating = False
        self.is_calibrated = True

        self.new_figures = copy.deepcopy(self.figures)

        angle = (atan((self.rect_ct[3][1] - self.rect_ct[2][1])
                      / (self.rect_ct[3][0] - self.rect_ct[2][0])) * 180 / pi)
        scale1 = self.w / np.linalg.norm(self.rect_ct[0] - self.rect_ct[1])
        scale2 = self.h / np.linalg.norm(self.rect_ct[1] - self.rect_ct[2])

        for key in self.new_figures.keys():
            n_fig = self.new_figures[key]

            n_fig[2] = angle

            n_fig[0][0] = n_fig[0][0] / scale1 + self.rect_ct[0][0]
            n_fig[0][1] = n_fig[0][1] / scale2 + self.rect_ct[0][1]
            n_fig[1][0] = round(n_fig[1][0] / scale1)
            n_fig[1][1] = round(n_fig[1][1] / scale2)

            n_fig[0][0] = round(n_fig[0][0])
            n_fig[0][1] = round(n_fig[0][1])

    def ex_completed(self):
        self.curr_skip = 0

        self.curr_ex += 1
        if self.curr_ex >= self.all_exes_count:
            self.cam.stop()
            self.cam.close()
            self.send_ex_complited_announce.emit('end')
        else:
            self.set_figures()
            self.do_calibration()
            self.send_ex_complited_announce.emit('changed')
            self.is_changing_ex = False


class TaskWindow(QDialog):
    calibration_start_signal = pyqtSignal(int)
    set_point_signal = pyqtSignal(np.ndarray)

    def __init__(self, path: str, w: int, h: int):
        super().__init__()

        self.path = f'db/{path}'

        self.setWindowTitle(f'Задание {path}')
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowState(Qt.WindowFullScreen)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.img = QLabel(self)
        self.img.setScaledContents(True)

        layout.addWidget(self.img)
        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                color: #FFFFFF;
            }
            """)

        self.all_exes = []

        with open(f'{self.path}/task.txt') as f:
            ex = ''
            for line in f:
                line = line.replace('\n', '')
                if line[-4:] == '.png':
                    ex = line
                    self.all_exes.append([ex, []])
                elif line == 'end':
                    ex = ''
                else:
                    parts = line.split(': ')
                    values = parts[1].split('; ')
                    point = list(map(int, values[0].split(', ')))
                    radius = list(map(int, values[1].split(', ')))
                    angle = int(values[2])
                    self.all_exes[-1][1].append([parts[0], [point, radius, angle]])

        self.all_exes_count = len(self.all_exes)
        self.curr_ex = 0
        # 0 - start calibration; 1, 2, 3, 4 - 1st, 2nd, 3rd, 4th points
        self.calibrate_state = 0

        self.show_ex(self.curr_ex)

        self.thread = CameraThread(1920, 1080, self.all_exes)
        self.calibration_start_signal.connect(self.thread.start_calibration)
        self.set_point_signal.connect(self.thread.set_calibration_point)
        self.thread.send_frame_to_window.connect(self.set_image)
        self.thread.send_ex_complited_announce.connect(self.ex_changed)
        self.thread.start()

    def turn_array_into_qpixmap(self, arr: np.ndarray):
        img = Image.fromarray(arr)
        qimg = QImage(img.tobytes(), img.width, img.height,
                      QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def show_ex(self, i):
        img_path = f'{self.path}/{self.all_exes[i][0]}'

        pixmap = QPixmap(img_path)
        self.img.setPixmap(pixmap)

    def set_image(self, arr):
        pixmap = self.turn_array_into_qpixmap(arr)
        self.img.setPixmap(pixmap)

    def ex_changed(self, input):
        if input == 'changed':
            self.curr_ex += 1
            self.show_ex(self.curr_ex)
        elif input == 'end':
            self.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.calibrate_state == 0:
                self.calibration_start_signal.emit(self.calibrate_state)
            else:
                point = np.array([event.x(), event.y()])
                self.set_point_signal.emit(point)
            self.calibrate_state = (self.calibrate_state + 1) % 5
            if self.calibrate_state == 0:
                self.show_ex(self.curr_ex)

        elif event.button() == Qt.RightButton:
            self.accept()

    def closeEvent(self, event):
        self.thread.stop()
        self.thread.wait()
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self, w, h):
        super().__init__()

        # Настройка основного окна
        self.setWindowTitle('Главное меню')

        self.w = w
        self.h = h

        font_id = QFontDatabase.addApplicationFont('fonts/RubikMonoOne-Regular.ttf')
        if font_id == -1:
            print('Не удалось загрузить шрифт. Возможно, папка fonts отсутствует.')
            return
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #101010;
                border-radius: 30px;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background-color: #202020;
            }
            QPushButton:pressed {
                background-color: #050505;
            }
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                background-color: #202020;
                width: 26px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
            }
            """)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.page_menu = QWidget()
        self.page_choose = QWidget()
        self.page_options = QWidget()

        # Настройка главной страницы
        self.menu_label_title = QLabel('Приложение', self)
        self.menu_label_title.setAlignment(Qt.AlignCenter)

        self.menu_button_choose = QPushButton('Начать', self)
        self.menu_button_choose.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.menu_button_choose.clicked.connect(self.go_to_choose)

        self.menu_button_options = QPushButton('Настройки', self)
        self.menu_button_options.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.menu_button_options.clicked.connect(self.go_to_options)

        self.menu_button_exit = QPushButton('Выйти', self)
        self.menu_button_exit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.menu_button_exit.clicked.connect(QApplication.quit)

        menu_layout = QGridLayout()
        menu_layout.setRowStretch(0, 100)
        menu_layout.setRowStretch(1, 133)
        menu_layout.setRowStretch(2, 133)
        menu_layout.setRowStretch(3, 133)
        menu_layout.setColumnStretch(0, 1)
        menu_layout.setColumnStretch(1, 1)
        menu_layout.setColumnStretch(2, 1)

        menu_layout.addWidget(self.menu_label_title, 0, 0, 1, 3)
        menu_layout.addWidget(self.menu_button_choose, 1, 1)
        menu_layout.addWidget(self.menu_button_options, 2, 1)
        menu_layout.addWidget(self.menu_button_exit, 3, 1)
        self.page_menu.setLayout(menu_layout)

        # Настройка страницы с выбором задания
        self.choose_label_title = QLabel('Выберите задание', self)
        self.choose_label_title.setAlignment(Qt.AlignCenter)

        self.choose_button_back = QPushButton('Назад в меню', self)
        self.choose_button_back.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.choose_button_back.clicked.connect(self.go_to_menu)

        self.choose_scroll_area = QScrollArea()
        self.choose_scroll_area.setWidgetResizable(True)

        self.grid_items = []
        self.get_grid_items()
        choose_v_cont = QWidget()
        choose_v = QVBoxLayout(choose_v_cont)
        for i, item in enumerate(self.grid_items):
            choose_v.addWidget(item)
        self.choose_scroll_area.setWidget(choose_v_cont)

        choose_layout = QVBoxLayout()

        choose_layout.addWidget(self.choose_label_title)
        choose_layout.addWidget(self.choose_scroll_area)
        choose_layout.addWidget(self.choose_button_back)

        choose_layout.setStretch(0, 20)
        choose_layout.setStretch(1, 70)
        choose_layout.setStretch(2, 10)

        self.page_choose.setLayout(choose_layout)

        # Настройка страницы с настройками
        self.options_label_title = QLabel('Настройки', self)
        self.options_label_option1 = QLabel('Какая-то настройка 1', self)
        self.options_label_option2 = QLabel('Какая-то настройка 2', self)

        self.options_button_back = QPushButton('Назад в меню', self)
        self.options_button_back.clicked.connect(self.go_to_menu)

        options_layout = QVBoxLayout()
        options_layout.addWidget(self.options_label_title)
        options_layout.addWidget(self.options_label_option1)
        options_layout.addWidget(self.options_label_option2)
        options_layout.addWidget(self.options_button_back)
        self.page_options.setLayout(options_layout)

        # Добавление страниц в stacked_widget
        self.stacked_widget.addWidget(self.page_menu)
        self.stacked_widget.addWidget(self.page_choose)
        self.stacked_widget.addWidget(self.page_options)

        self.stacked_widget.setCurrentWidget(self.page_menu)

    def get_grid_items(self):
        font = QFont(self.font_family, 50)
        with open('db/all_tasks.txt') as f:
            for line in f:
                l = list(map(lambda item: item.replace('\n', ''), line.split(' ')))
                item = QWidget()
                layout = QGridLayout(item)

                label_difficulty = QLabel(f'Сложность: {l[1]}/5', self)
                label_difficulty.setFont(font)
                label_difficulty.setAlignment(Qt.AlignCenter)

                label_is_complete = QLabel(f"Пройдено: {'Да' if l[2] == 1 else 'Нет'}", self)
                label_is_complete.setFont(font)
                label_is_complete.setAlignment(Qt.AlignCenter)

                button = QPushButton('Начать', self)
                button.setFont(font)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                button.clicked.connect(lambda click, path=l[0]: 
                    self.go_to_chosen_task(path, self.w, self.h))

                label_image = QLabel(self)
                pixmap = QPixmap(f'db/{l[0]}/preview.png')
                label_image.setPixmap(pixmap)
                label_image.setMaximumWidth(640)
                label_image.setMaximumHeight(480)
                label_image.setScaledContents(True)

                layout.addWidget(label_difficulty, 0, 0)
                layout.addWidget(label_is_complete, 1, 0)
                layout.addWidget(button, 2, 0)
                layout.addWidget(label_image, 0, 1, 3, 1)

                layout.setRowStretch(0, 1)
                layout.setRowStretch(1, 1)
                layout.setRowStretch(2, 1)

                self.grid_items.append(item)

    def go_to_chosen_task(self, path: str, w: int, h: int):
        new_window = TaskWindow(path, w, h)
        new_window.exec_()

    def go_to_menu(self):
        self.stacked_widget.setCurrentWidget(self.page_menu)

    def go_to_choose(self):
        self.stacked_widget.setCurrentWidget(self.page_choose)

    def go_to_options(self):
        self.stacked_widget.setCurrentWidget(self.page_options)

    def resizeEvent(self, event):
        font_size = min(100, max(10, self.width() // 25))

        font = QFont(self.font_family, font_size)

        self.menu_label_title.setFont(font)
        self.menu_button_choose.setFont(font)
        self.menu_button_options.setFont(font)
        self.menu_button_exit.setFont(font)

        self.choose_label_title.setFont(font)
        self.choose_button_back.setFont(font)

        self.options_label_title.setFont(font)
        self.options_label_option1.setFont(font)
        self.options_label_option2.setFont(font)
        self.options_button_back.setFont(font)

        super().resizeEvent(event)


if __name__ == '__main__':
    print('start')

    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    screen_size = screen.size()
    window = MainWindow(screen_size.width(), screen_size.height())
    window.showFullScreen()
    sys.exit(app.exec_())

    print('end')
