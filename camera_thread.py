import numpy as np
import cv2
from picamera2 import Picamera2
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from math import atan, pi, radians, sin, cos
import copy


class CameraThread(QThread):
    '''Класс, запускаемый в отдельном потоке и работающий параллельно
    классу TaskWindow. Считывает каждый кадр с камеры, находит движущиеся
    объекты, определяет, выполнена ли текущая задача.'''

    # Сигнал, связывающий этот класс с классом TaskWindow, вызывающийся
    # всякий раз когда нужно послать кадр с камеры в класс TaskWindow,
    # вызывающий функцию в классе TaskWindow и передающий картинку в виде
    # np массива.
    send_frame_to_window = pyqtSignal(np.ndarray)

    # Сигнал, связывающий этот класс с классом TaskWindow, вызывающийся
    # всякий раз когда выполняется задача, вызывающий функцию в классе
    # TaskWindow и передающий одну из двух строк:
    # Если строка - changed, значит задача была выполнена и нужно
    # показать на экране следующую задачу;
    # Если строка - end, значит последняя задача была выполнена,
    # нужно закончить выполнение упражнения.
    send_ex_complited_announce = pyqtSignal(str)

    def __init__(self, w: int, h: int, all_exes):
        '''Инициализатор класса, включающий камеру и задающий
        основные параметры'''
        super().__init__()

        self.w = w
        self.h = h

        # Запуск камеры
        self.cam = Picamera2()
        self.cam.configure(self.cam.create_preview_configuration(
            main={'size': (self.w, self.h)}))
        self.cam.start()

        # True - если камера прямо сейчас калибруется, иначе - False
        self.is_calibrating = False

        # True - если камера уже откалибрована, иначе - False
        self.is_calibrated = False

        # Количество кадров, которые не обрабатываются сразу после калибровки
        self.skip_frames_number = 5

        # Текущее количество пропускаемых кадров:
        # Изначально -1 - кадры пока не пропускаются - камера еще не
        # откалибрована;
        # После калибровки значение находится в пределе от 0 до
        # self.skip_frames_number.
        self.curr_skip = -1

        # True - если только что была выполнена одна из задач, иначе - False
        self.is_changing_ex = False

        # Индекс текущей точки калибровки - от 0 до 3
        self.curr_point = 0

        # Вершины прямоугольника для калибровки камеры
        self.rect_ct = [0, 0, 0, 0]

        # Переменные, связанные с номерами задач
        self.all_exes = all_exes
        self.all_exes_count = len(self.all_exes)
        self.curr_ex = 0

        # Определение фигур во всех задачах задания
        self.figures = {}
        self.new_figures = {}
        self.set_figures()

        # Определение переменной для нахождения маски переднего плана
        self.backSub = cv2.createBackgroundSubtractorMOG2()

        # True - если поток активен, иначе False
        self._is_running = True

    def run(self):
        '''Функция, запускаемая в отдельном потоке. Обрабатывает каждый
        кадр с камеры'''
        while self._is_running:
            # Если прямо сейчас происходит калибровка, значит нет
            # необходимости считывать новый кадр с камеры
            if self.is_calibrating:
                continue

            # Считывание кадра с камеры
            self.frame = self.cam.capture_array()
            self.frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)

            # Если камера еще не калибровалась, нет необходимости
            # искать движущиеся объекты в кадре
            if not self.is_calibrated:
                continue

            # Если только что была выполнена задача и прямо сейчас
            # устанавливается новая задача, нет необходимости
            # искать движущиеся объекты
            if self.is_changing_ex:
                continue

            # Получение маски переднего плана
            fg_mask = self.backSub.apply(self.frame)

            # Отсечение на маске пикселей, насыщенность которых меньше 220
            retval, mask_thr = cv2.threshold(fg_mask, 220, 255,
                                             cv2.THRESH_BINARY)

            # Фильтрация очень маленьких объектов
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask_eroded = cv2.morphologyEx(mask_thr, cv2.MORPH_OPEN, kernel)

            mask_for_ct = mask_eroded

            # Нахождение контуров
            contours, hierarchy = cv2.findContours(mask_for_ct,
                                                   cv2.RETR_EXTERNAL,
                                                   cv2.CHAIN_APPROX_SIMPLE)

            # Фильтрация контуров, количество пикселей в которых меньше 100
            min_contour_area = 100
            large_contours = [ct for ct in contours if
                              cv2.contourArea(ct) > min_contour_area]

            # Если необходимо пропустить несколько кадров после калибровки:
            if self.curr_skip >= 0 and self.curr_skip <= self.skip_frames_number:
                self.curr_skip += 1
                continue

            for ct in large_contours:
                # Каждый контур превращается в прямоугольник с известными
                # координатами начала, а также высотой и шириной. Далее
                # проверяется, касается ли хотя бы один из контуров фигуры
                # из задания (эллипса), если да, то задание выполнено.
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

        # Остановка и закрытие камеры после завершения цикла
        self.cam.stop()
        self.cam.close()

    def stop(self):
        '''Функция остановки потока, останавливает и закрывает камеру'''
        self.cam.stop()
        self.cam.close()
        self._is_running = False

    def set_figures(self):
        '''Функция, устанавливающая фигуры'''
        self.figures = {}
        if self.curr_ex >= self.all_exes_count:
            self.send_ex_complited_announce.emit('end')
        for key in self.all_exes[self.curr_ex][1]:
            self.figures[key[0]] = key[1]
        print(self.figures)

    @pyqtSlot(int)
    def start_calibration(self, input):
        '''Функция, начинающая калибровку.'''
        if input == 0:
            self.is_calibrating = True
            self.curr_point = 0
            rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            self.send_frame_to_window.emit(rgb_frame)

    @pyqtSlot(np.ndarray)
    def set_calibration_point(self, point):
        '''Функция, вызываемая при срабатывании сигнала set_point_signal из
        класса TaskWindow, принимающая на вход точку калибровки'''
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

        # Если пользователь ввел 4 точки, необходимо выполнить саму
        # камеры
        if self.curr_point == 4:
            self.do_calibration()

    def do_calibration(self):
        '''Функция, выполняющая саму калибровку, изменяющая координаты
        фигур, их размеры ии углы наклона на новые, соответствующие новому
        окну'''
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
        '''Функция, вызывающаяся, когда задача выполнена, и посылающая с
        помощью сигнала send_ex_complited_announce одну из двух строк в
        класс TaskWindow:
        Если строка - changed, значит задача была выполнена и нужно
        показать на экране следующую задачу;
        Если строка - end, значит последняя задача была выполнена,
        нужно закончить выполнение упражнения.'''
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
