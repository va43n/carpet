import json
import os
import shutil

from PyQt5.QtWidgets import (QScrollArea, QWidget, QHBoxLayout,
                             QMainWindow, QStackedWidget,
                             QVBoxLayout, QPushButton, QLabel,
                             QSizePolicy, QGridLayout, QLineEdit)
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap
from PyQt5.QtCore import Qt

from task_window import TaskWindow
from user_info import UserInfo
from download import Download


class MainWindow(QMainWindow):
    '''Класс, предоставляющий интерфейс основного приложения и организующий
    связь между пользовательским вводом и основными составляющими приложения:
    основным меню, меню настроек и меню выбора задания. Для вызова выбранного
    задания используется класс TaskWindow из модуля task_window.py.'''

    def __init__(self, w, h):
        '''Инициализатор класса, запускает окно с интерфейсом и задает
        основные параметры.'''
        super().__init__()

        # Объект класса с информацией пользователя
        self.user = UserInfo()

        # Объект класса для скачивания новых заданий
        self.download = Download()

        # Установка названия приложения
        self.setWindowTitle('Коврик')

        # Установка размеров окна
        self.w = w
        self.h = h

        # Задание пользовательского шрифта RubicMonoOne-Regular
        font_id = QFontDatabase.addApplicationFont('fonts/RubikMonoOne-'
                                                   + 'Regular.ttf')
        if font_id == -1:
            print('Не удалось загрузить шрифт. '
                  + 'Возможно, папка fonts отсутствует.')
            return
        self.font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        font_size = 75
        font = QFont(self.font_family, font_size)

        # Опредление стиля основных виджетов интерфейса
        self.setStyleSheet('''
            QWidget {
                background-color: #000000;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit {
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
            ''')

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Приложение имеет три страницы: меню, выбор задания, настройки
        self.page_menu = QWidget()
        self.page_choose = QWidget()
        self.page_options = QWidget()

        # ====================================================================
        # Настройка меню
        menu_label_title = QLabel('Коврик с заданиями', self)
        menu_label_title.setAlignment(Qt.AlignCenter)
        menu_label_title.setFont(font)

        menu_button_choose = QPushButton('Начать', self)
        menu_button_choose.setSizePolicy(QSizePolicy.Expanding,
                                              QSizePolicy.Expanding)
        menu_button_choose.clicked.connect(self.go_to_choose)
        menu_button_choose.setFont(font)

        menu_button_options = QPushButton('Настройки', self)
        menu_button_options.setSizePolicy(QSizePolicy.Expanding,
                                               QSizePolicy.Expanding)
        menu_button_options.clicked.connect(self.go_to_options)
        menu_button_options.setFont(font)

        menu_button_exit = QPushButton('Выйти', self)
        menu_button_exit.setSizePolicy(QSizePolicy.Expanding,
                                            QSizePolicy.Expanding)
        menu_button_exit.clicked.connect(self.close)
        menu_button_exit.setFont(font)

        menu_layout = QGridLayout()
        menu_layout.setRowStretch(0, 100)
        menu_layout.setRowStretch(1, 133)
        menu_layout.setRowStretch(2, 133)
        menu_layout.setRowStretch(3, 133)
        menu_layout.setColumnStretch(0, 1)
        menu_layout.setColumnStretch(1, 1)
        menu_layout.setColumnStretch(2, 1)

        menu_layout.addWidget(menu_label_title, 0, 0, 1, 3)
        menu_layout.addWidget(menu_button_choose, 1, 1)
        menu_layout.addWidget(menu_button_options, 2, 1)
        menu_layout.addWidget(menu_button_exit, 3, 1)
        self.page_menu.setLayout(menu_layout)
        # ====================================================================

        # ====================================================================
        # Настройка страницы с выбором задания
        choose_label_title = QLabel('Выберите задание', self)
        choose_label_title.setAlignment(Qt.AlignCenter)
        choose_label_title.setFont(font)

        hbox_layout = QHBoxLayout()
        choose_button_refresh = QPushButton('Обновить', self)
        choose_button_refresh.setSizePolicy(QSizePolicy.Expanding,
                                                 QSizePolicy.Expanding)
        choose_button_refresh.clicked.connect(self.refresh_tasks_info)
        choose_button_refresh.setFont(font)
        hbox_layout.addWidget(choose_button_refresh)

        choose_button_back = QPushButton('Назад в меню', self)
        choose_button_back.setSizePolicy(QSizePolicy.Expanding,
                                              QSizePolicy.Expanding)
        choose_button_back.clicked.connect(self.go_to_menu)
        choose_button_back.setFont(font)
        hbox_layout.addWidget(choose_button_back)

        self.choose_scroll_area = QScrollArea()
        self.choose_scroll_area.setWidgetResizable(True)

        # Массив виджетов с заданиями
        self.grid_items = []
        self.refresh_tasks_info()

        choose_layout = QVBoxLayout()

        choose_layout.addWidget(choose_label_title)
        choose_layout.addWidget(self.choose_scroll_area)
        choose_layout.addLayout(hbox_layout)

        choose_layout.setStretch(0, 20)
        choose_layout.setStretch(1, 70)
        choose_layout.setStretch(2, 10)

        self.page_choose.setLayout(choose_layout)
        # ====================================================================

        # ====================================================================
        # Настройка страницы с настройками
        options_label_title = QLabel('Настройки', self)
        options_label_title.setAlignment(Qt.AlignCenter)
        options_label_title.setFont(font)

        options_label_username = QLabel('Введите логин', self)
        options_label_username.setFont(font)

        options_label_password = QLabel('Введите пароль', self)
        options_label_password.setFont(font)

        options_label_result = QLabel('', self)
        options_label_result.setAlignment(Qt.AlignCenter)
        options_label_result.setFont(font)

        options_edit_username = QLineEdit()
        options_edit_username.setText(self.user.get_username())
        options_edit_username.setFont(font)

        options_edit_password = QLineEdit()
        options_edit_password.setText(self.user.get_password())
        options_edit_password.setFont(font)

        options_button_set = QPushButton('Сохранить', self)
        options_button_set.setFont(font)
        options_button_set.clicked.connect(lambda click:
                                   self.user.set_data(
                                        options_edit_username.text(),
                                        options_edit_password.text(),
                                        options_label_result.setText)
                                   )

        options_button_back = QPushButton('Назад в меню', self)
        options_button_back.setFont(font)
        options_button_back.clicked.connect(self.go_to_menu)

        options_layout = QVBoxLayout()
        options_layout.addWidget(options_label_title)

        options_layout.addWidget(options_label_username)
        options_layout.addWidget(options_edit_username)

        options_layout.addWidget(options_label_password)
        options_layout.addWidget(options_edit_password)

        options_layout.addWidget(options_button_set)
        options_layout.addWidget(options_label_result)

        options_layout.addWidget(options_button_back)
        self.page_options.setLayout(options_layout)
        # ====================================================================

        # Добавление страниц в stacked_widget
        self.stacked_widget.addWidget(self.page_menu)
        self.stacked_widget.addWidget(self.page_choose)
        self.stacked_widget.addWidget(self.page_options)

        self.stacked_widget.setCurrentWidget(self.page_menu)

    def get_grid_items(self):
        '''Функция, считывающая все задания из файла db/all_tasks.json и
        вставляющая их в список QScrollArea'''
        font = QFont(self.font_family, 50)
        title_max_lentgh = 25

        # Получение списка всех папок в папке pwd/db
        folders = [f for f in os.listdir('db') if os.path.isdir('db/' + f)]
        for name in folders:
            # Каждый элемент списка - виджет. Создание виджета
            item = QWidget()
            layout = QGridLayout(item)

            # Открытие файла задания и считывание необходимых параметров
            with open(f'db/{name}/task.json', 'r') as task_file:
                task_data = json.load(task_file)
                if task_data['username'] != self.user.get_username():
                    continue

                task_id = task_data['task_id']
                title = task_data['title']
                is_completed = 'Да' if task_data['is_complete'] else 'Нет'
                difficulty = task_data['difficulty']

            if len(title) > title_max_lentgh:
                title = title[:title_max_lentgh - 3] + '...'

            label_title = QLabel(title, self)
            label_title.setFont(font)
            label_title.setAlignment(Qt.AlignCenter)

            label_difficulty = QLabel(f'Сложность: {difficulty}/10', self)
            label_difficulty.setFont(font)
            label_difficulty.setAlignment(Qt.AlignCenter)

            label_is_complete = QLabel(f'Пройдено: {is_completed}', self)
            label_is_complete.setFont(font)
            label_is_complete.setAlignment(Qt.AlignCenter)

            # Каждая кнопка Начать в списке запускает свое задание,
            # определеняемое путем
            button_start = QPushButton('Начать', self)
            button_start.setFont(font)
            button_start.setSizePolicy(QSizePolicy.Expanding,
                                 QSizePolicy.Expanding)

            button_start.clicked.connect(lambda click, path=name:
                                   self.go_to_chosen_task(path, self.w,
                                                          self.h, path))

            # Каждая кнопка Удалить в списке удаляет свое задание,
            # определеняемое путем
            button_delete = QPushButton('Удалить', self)
            button_delete.setFont(font)
            button_delete.setSizePolicy(QSizePolicy.Expanding,
                                        QSizePolicy.Expanding)

            button_delete.clicked.connect(lambda click, path=name:
                                   self.delete_chosen_task(path))

            label_image = QLabel(self)
            pixmap = QPixmap(f'db/{name}/preview.png')
            label_image.setPixmap(pixmap)
            label_image.setMaximumWidth(640)
            label_image.setMaximumHeight(480)
            label_image.setScaledContents(True)

            layout.addWidget(label_title, 0, 0, 1, 3)
            layout.addWidget(label_difficulty, 1, 0, 1, 2)
            layout.addWidget(label_is_complete, 2, 0, 1, 2)
            layout.addWidget(button_start, 3, 0)
            layout.addWidget(button_delete, 3, 1)
            layout.addWidget(label_image, 1, 2, 3, 1)

            layout.setRowStretch(0, 1)
            layout.setRowStretch(1, 1)
            layout.setRowStretch(2, 1)
            layout.setRowStretch(3, 1)

            self.grid_items.append(item)

    def go_to_chosen_task(self, path: str, w: int, h: int, task_id: str):
        '''Функция, запускающая выбранное задание. Для этого запускается
        объект класса TaskWindow с параметром пути'''
        print('start task with task id', task_id)
        new_window = TaskWindow(path, w, h, self.font_family, task_id, self)
        new_window.exec_()

    def delete_chosen_task(self, path: str):
        '''Функция, удаляющая выбранное задание из локальной базы данных
        миникомпьютера'''
        shutil.rmtree(f'db/{path}')
        self.refresh_tasks_info()

    def go_to_menu(self):
        '''Функция для перехода на страницу меню'''
        self.stacked_widget.setCurrentWidget(self.page_menu)

    def go_to_choose(self):
        '''Функция для перехода на страницу выбора задания'''
        self.stacked_widget.setCurrentWidget(self.page_choose)

    def go_to_options(self):
        '''Функция для перехода на страницу настроек'''
        self.stacked_widget.setCurrentWidget(self.page_options)

    def refresh_tasks_info(self):
        '''Функция для обновления виджетов заданий в окне
        выбора заданий'''
        print('Refresh!')

        self.grid_items = []
        self.download.download_patient_files()
        self.get_grid_items()

        choose_v_cont = QWidget()
        choose_v = QVBoxLayout(choose_v_cont)
        for i, item in enumerate(self.grid_items):
            choose_v.addWidget(item)
        self.choose_scroll_area.setWidget(choose_v_cont)

    def closeEvent(self, event):
        '''Функция, вызываемая при закрытии основного окна'''
        with open('info/calibration_info.json', 'w'):
            pass
