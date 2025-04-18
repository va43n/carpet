import numpy as np
from numpy.linalg import norm
import cv2
from picamera2 import Picamera2
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from math import atan, pi, radians, sin, cos
import copy
import json
import os


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
            {'size': (self.w, self.h), 'format': 'RGB888'}))
        self.cam.start()

        # Получение первого кадра
        self.prev_frame = self.cam.capture_array()
        self.prev_frame = cv2.cvtColor(self.prev_frame, cv2.COLOR_BGR2GRAY)

        # Каждый кадр с камеры будет записываться в переменную self.frame
        self.frame = -1

        # True - если камера прямо сейчас калибруется, иначе - False
        self.is_calibrating = False

        # True - если камера уже откалибрована, иначе - False
        self.is_calibrated = False

        # Количество кадров, которые не обрабатываются сразу после калибровки
        # или после выполнения задачи
        self.skip_frames_number = 5

        # Текущее количество пропускаемых кадров:
        # Изначально -1 - кадры пока не пропускаются - камера еще не
        # откалибрована либо задача еще не выполнена;
        # После калибровки или после выполнения задачи значение находится
        # в пределе от 0 до self.skip_frames_number.
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
        # self.backSub = cv2.bgsegm.createBackgroundSubtractorMOG()

        # True - если поток активен, иначе False
        self._is_running = True

        self.check_calibration_info_file()

    def run(self):
        '''Функция, запускаемая в отдельном потоке. Обрабатывает каждый
        кадр с камеры'''
        while self._is_running:
            # True -  если задача выполнена;
            # False - если задача не выполнена.
            # Позволяет понимать, когда нужно завершить выполнение всех циклов
            is_completed = False

            # Если прямо сейчас происходит калибровка, значит нет
            # необходимости считывать новый кадр с камеры
            if self.is_calibrating:
                continue

            # Считывание кадра с камеры
            self.frame = self.cam.capture_array()
            frame_gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            # Если камера еще не калибровалась, нет необходимости
            # искать движущиеся объекты в кадре
            if not self.is_calibrated:
                self.prev_frame = copy.deepcopy(frame_gray)
                continue

            # Если только что была выполнена задача и прямо сейчас
            # устанавливается новая задача, нет необходимости
            # искать движущиеся объекты
            if self.is_changing_ex:
                self.prev_frame = copy.deepcopy(frame_gray)
                continue

            # Получение маски
            diff = cv2.absdiff(frame_gray, self.prev_frame)
            blur = cv2.GaussianBlur(diff, (5, 5), 0)
            _, mask = cv2.threshold(blur, 30, 255, cv2.THRESH_BINARY)
            self.prev_frame = copy.deepcopy(frame_gray)

            mask_for_ct = mask

            # Нахождение контуров
            contours, hierarchy = cv2.findContours(mask_for_ct,
                                                   cv2.RETR_EXTERNAL,
                                                   cv2.CHAIN_APPROX_SIMPLE)

            # Фильтрация контуров, количество пикселей в которых меньше 100
            min_contour_area = 100
            large_contours = [ct for ct in contours if
                              cv2.contourArea(ct) > min_contour_area]

            # Если необходимо пропустить несколько кадров после калибровки
            # или после выполнения задания:
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
                    for key in self.new_figures.keys():
                        fig = self.new_figures[key]
                        cx, cy = fig[0]
                        a, b = fig[1]
                        theta = radians(fig[2])

                        dx = self.w - pt[0] - cx
                        dy = self.h - pt[1] - cy

                        rot_x = dx * cos(theta) + dy * sin(theta)
                        rot_y = dx * (-sin(theta)) + dy * cos(theta)

                        eq = (rot_x ** 2) / (a ** 2) + (rot_y ** 2) / (b ** 2)
                        if eq <= 1:
                            self.is_changing_ex = True
                            print(f'Ex {self.curr_ex + 1} completed')
                            print(f'stand on figures[{key}] ({cx}, {cy}; '
                                  f'{a}, {b}; {theta}) by {pt=} in {points=}')
                            self.ex_completed()

                            is_completed = True
                            break
                    if is_completed:
                        break
                if is_completed:
                    break

        # Остановка и закрытие камеры после завершения цикла
        self.cam.stop()
        self.cam.close()

    def stop(self):
        '''Функция остановки потока, останавливает и закрывает камеру'''
        self.cam.stop()
        self.cam.close()
        self._is_running = False

    def check_calibration_info_file(self):
        if os.path.getsize('info/calibration_info.json') == 0:
            return

        with open('info/calibration_info.json', 'r') as file:
            data = json.load(file)
            print('data =', data)
            self.rect_ct[0] = np.array(data['1'])
            self.rect_ct[1] = np.array(data['2'])
            self.rect_ct[2] = np.array(data['3'])
            self.rect_ct[3] = np.array(data['4'])
            print(f'{self.rect_ct=}')

            self.do_calibration()

    def set_figures(self):
        '''Функция, устанавливающая фигуры'''
        self.figures = {}
        if self.curr_ex >= self.all_exes_count:
            self.send_ex_complited_announce.emit('end')
        for key in self.all_exes[self.curr_ex][1]:
            self.figures[key[0]] = key[1]
        print(f'{self.figures=}')

    @pyqtSlot(int)
    def start_calibration(self, input):
        '''Функция, начинающая калибровку.'''
        if isinstance(self.frame, int):
            return

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
            self.sort_calibration_points()
            self.do_calibration()

    def sort_calibration_points(self):
        '''Функция, сортирующая массив точек калибровки для последующей
        калибровки'''

        # Правильное расположение точек калибровки:
        # 1 2
        # 4 3
        # В общем случае точки могут быть введены в другом порядке, в таком
        # случае нужно поменять порядок:
        rect_copy = copy.deepcopy(self.rect_ct)

        # Сначала отбираются точки с минимальной и максимальной нормой,
        # соответственно, точки 1 и 3
        ind_min = 0
        ind_max = 0
        biggest = norm(rect_copy[0])
        lowest = norm(rect_copy[0])
        for i in range(1, 3):
            temp = norm(rect_copy[i])
            if lowest > temp:
                lowest = temp
                ind_min = i
            elif biggest < temp:
                biggest = temp
                ind_max = i

        self.rect_ct[0] = rect_copy[ind_min]
        self.rect_ct[2] = rect_copy[ind_max]

        if ind_min < ind_max:
            rect_copy.pop(ind_max)
            rect_copy.pop(ind_min)
        else:
            rect_copy.pop(ind_min)
            rect_copy.pop(ind_max)

        # Далее, чтоб отличить 2-ю от 4-й точки можно сравнить их x-координаты:
        # у 2-й точки x всегда больше, чем у 4-й точки
        if rect_copy[0][0] < rect_copy[1][0]:
            self.rect_ct[1] = rect_copy[1]
            self.rect_ct[3] = rect_copy[0]
        else:
            self.rect_ct[1] = rect_copy[0]
            self.rect_ct[3] = rect_copy[1]

        del rect_copy

        data = {
            '1': self.rect_ct[0].tolist(),
            '2': self.rect_ct[1].tolist(),
            '3': self.rect_ct[2].tolist(),
            '4': self.rect_ct[3].tolist()
        }

        with open('info/calibration_info.json', 'w') as file:
            json.dump(data, file, indent=4)

        print(f'{data=}')

    def do_calibration(self):
        '''Функция, выполняющая саму калибровку, изменяющая координаты
        фигур, их размеры ии углы наклона на новые, соответствующие новому
        окну'''

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

        self.is_calibrating = False

        self.curr_skip = 0

    def ex_completed(self):
        '''Функция, вызывающаяся, когда задача выполнена, и посылающая с
        помощью сигнала send_ex_complited_announce одну из двух строк в
        класс TaskWindow:
        Если строка - changed, значит задача была выполнена и нужно
        показать на экране следующую задачу;
        Если строка - end, значит последняя задача была выполнена,
        нужно закончить выполнение упражнения.'''

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

        self.curr_skip = 0
