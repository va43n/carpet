import numpy as np
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal
from PIL import Image
from camera_thread import CameraThread
import json


class TaskWindow(QDialog):
    '''Класс, предоставляющий интерфейс дополнительного окна, вызываемого
    при запуске одного из заданий. Во время работы класс в отдельном потоке
    инициализирует класс CameraThread из модуля camera_thread.py для работы
    с камерой.'''

    # Сигнал, связывающий этот класс с классом потока, вызывающийся
    # при запуске калибровки, вызывающий функцию в классе потока и
    # передающий 0, если произведен запуск калибровки
    calibration_start_signal = pyqtSignal(int)

    # Сигнал, связывающий этот класс с классом потока, вызывающийся
    # при установке каждой точки калибровки, вызывающий функцию в классе
    # потока и передающий координаты нажатой точки
    set_point_signal = pyqtSignal(np.ndarray)

    def __init__(self, path: str, w: int, h: int, font_family, main_window):
        '''Инициализатор класса, запускает окно с интерфейсом.'''
        super().__init__()

        self.font_family = font_family
        self.main_window = main_window

        self.w = w
        self.h = h

        # Установка пути в заданию
        self.path = f'db/{path}'

        # ====================================================================
        # Задание параметров окна и определение виджетов

        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)

        self.setWindowTitle(f'Задание {path}')
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowState(Qt.WindowFullScreen)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.calibration_label = QLabel('Нажмите ЛКМ, чтобы откалибровать '
                                        'камеру. Нажмите ПКМ, чтобы прервать '
                                        'выполнение задания.', self)

        font = QFont(self.font_family, 30)
        self.calibration_label.setFont(font)
        self.calibration_label.setWordWrap(True)
        self.calibration_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)

        layout.addWidget(self.calibration_label, 1)

        self.img = QLabel(self)
        self.img.setScaledContents(True)

        layout.addWidget(self.img, 7)
        self.setLayout(layout)

        # ====================================================================

        # Массив всех задач задания
        self.all_exes = []

        # Обработка файла, описывающего все задание: task.json
        with open(f'{self.path}/task.json') as f:
            data = json.load(f)
            for ex in data['all_exes']:
                self.all_exes.append([ex['img'], []])
                for fig in ex['ex_figs']:
                    self.all_exes[-1][1].append([fig['name'],
                                                 [fig['center'],
                                                  fig['radius'],
                                                  fig['angle']]])

        # Количество задач задания
        self.all_exes_count = len(self.all_exes)

        # Текущий индекс задачи: от 0 до self.all_exes_count - 1
        self.curr_ex = 0

        # Статус калибровки: 0 - начало калибровки;
        # 1, 2, 3, 4 - 1-я, 2-я, 3-я, 4-я точки
        self.calibrate_state = 0

        self.show_ex(self.curr_ex)

        # Инициализация класса CameraThread
        self.thread = CameraThread(self.w, self.h, self.all_exes)

        # Бинд сигналов к функциям класса CameraThread
        self.calibration_start_signal.connect(self.thread.start_calibration)
        self.set_point_signal.connect(self.thread.set_calibration_point)

        # Бинд сигналов класса CameraThread к функциям данного класса
        self.thread.send_frame_to_window.connect(self.set_image)
        self.thread.send_ex_complited_announce.connect(self.ex_changed)

        # Запуск потока
        self.thread.start()

    def turn_array_into_qpixmap(self, arr: np.ndarray):
        '''Преобразование np массива в QPixmap для последующего отображения
        картинки на экране'''
        img = Image.fromarray(arr)
        qimg = QImage(img.tobytes(), img.width, img.height,
                      QImage.Format.Format_RGB888)
        return QPixmap.fromImage(qimg)

    def show_ex(self, i):
        '''Функция, отображающая i-ю задачу на коврике'''
        img_path = f'{self.path}/{self.all_exes[i][0]}'

        pixmap = QPixmap(img_path)
        self.img.setPixmap(pixmap)

    def set_image(self, arr):
        '''Функция, вызываемая через сигнал из класса CameraThread,
        принимающая на вход изображение в виде np массива и размещающая
        изображение на коврике.'''
        pixmap = self.turn_array_into_qpixmap(arr)
        self.img.setPixmap(pixmap)

    def ex_changed(self, input):
        '''Функция, вызываемая через сигнал из класса CameraThread,
        принимающее на вход одну из двух строк.
        Если строка - changed, значит задача была выполнена и нужно
        показать на экране следующую задачу;
        Если строка - end, значит последняя задача была выполнена,
        нужно закончить выполнение упражнения, поставить 1 в файл is_complete
        и вызвать функцию в главном окне, обновляющую информацию в меню
        выбора'''
        if input == 'changed':
            self.curr_ex += 1
            self.show_ex(self.curr_ex)
        elif input == 'end':
            with open(f'{self.path}/task.json', 'r') as f:
                data = json.load(f)
            data['is_complete'] = True
            with open(f'{self.path}/task.json', 'w') as f:
                json.dump(data, f, indent=4)

            self.main_window.refresh_completion_info()

            self.accept()

    def mousePressEvent(self, event):
        '''Функция, орабатывающая пользовательский ввод с мыши.
        Если пользователь нажал ЛКМ, значит он калибрует камеру;
        Если пользователь нажал ПКМ, значит нужно завершить выполнение
        задания.'''
        if event.button() == Qt.LeftButton:
            if self.calibrate_state == 0:
                self.calibration_label.setText('Для калибровки нажмите левой '
                                               'кнопкой мыши на каждую '
                                               'вершину зеленой рамки.')

                self.calibration_start_signal.emit(self.calibrate_state)
            else:
                point = np.array([event.x(), event.y()])
                self.set_point_signal.emit(point)

            self.calibrate_state = (self.calibrate_state + 1) % 5
            if self.calibrate_state == 0:
                self.calibration_label.setText('Калибровка завершена, можно '
                                               'начать выполнять задание! '
                                               'Нажмите ПКМ, чтобы прервать '
                                               'выполнение задания.')
                self.show_ex(self.curr_ex)

        elif event.button() == Qt.RightButton:
            self.accept()

    def closeEvent(self, event):
        '''Функция, вызываемая при закрытии окна, завершает
        выполнение потока CameraThread'''
        self.thread.stop()
        self.thread.wait()
        event.accept()
