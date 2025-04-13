from PyQt5.QtWidgets import (QScrollArea, QWidget, QHBoxLayout,
                             QMainWindow, QStackedWidget,
                             QVBoxLayout, QPushButton, QLabel,
                             QSizePolicy, QGridLayout, QLineEdit)
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap
from PyQt5.QtCore import Qt
from task_window import TaskWindow
from user_info import UserInfo
from download import Download
import json
import os


class MainWindow(QMainWindow):
    '''Класс, предоставляющий интерфейс основного приложения и организующий
    связь между пользовательским вводом и основными составляющими приложения:
    основным меню, меню настроек и меню выбора задания. Для вызова выбранного
    задания используется класс TaskWindow из модуля task_window.py.'''

    def __init__(self, w, h):
        '''Инициализатор класса, запускает окно с интерфейсом и задает
        основные параметры.'''
        super().__init__()

        # Класс с настройками пользователя
        self.user = UserInfo()

        # Класс для скачивания новых заданий
        self.download = Download()
        self.download.dowload_patient_files()

        # Настройка основного окна
        self.setWindowTitle('Главное меню')

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

        # Опредление стиля основных виджетов интерфейса
        self.setStyleSheet("""
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
            """)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Приложение имеет три страницы: меню, выбор задания, настройки
        self.page_menu = QWidget()
        self.page_choose = QWidget()
        self.page_options = QWidget()

        # ====================================================================
        # Настройка главной страницы
        self.menu_label_title = QLabel('Задания', self)
        self.menu_label_title.setAlignment(Qt.AlignCenter)

        self.menu_button_choose = QPushButton('Начать', self)
        self.menu_button_choose.setSizePolicy(QSizePolicy.Expanding,
                                              QSizePolicy.Expanding)
        self.menu_button_choose.clicked.connect(self.go_to_choose)

        self.menu_button_options = QPushButton('Настройки', self)
        self.menu_button_options.setSizePolicy(QSizePolicy.Expanding,
                                               QSizePolicy.Expanding)
        self.menu_button_options.clicked.connect(self.go_to_options)

        self.menu_button_exit = QPushButton('Выйти', self)
        self.menu_button_exit.setSizePolicy(QSizePolicy.Expanding,
                                            QSizePolicy.Expanding)
        self.menu_button_exit.clicked.connect(self.close)

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
        # ====================================================================

        # ====================================================================
        # Настройка страницы с выбором задания

        self.choose_label_title = QLabel('Выберите задание', self)
        self.choose_label_title.setAlignment(Qt.AlignCenter)

        hbox_layout = QHBoxLayout()
        self.choose_button_refresh = QPushButton('Обновить', self)
        self.choose_button_refresh.setSizePolicy(QSizePolicy.Expanding,
                                                 QSizePolicy.Expanding)
        self.choose_button_refresh.clicked.connect(self.refresh_completion_info)
        hbox_layout.addWidget(self.choose_button_refresh)

        self.choose_button_back = QPushButton('Назад в меню', self)
        self.choose_button_back.setSizePolicy(QSizePolicy.Expanding,
                                              QSizePolicy.Expanding)
        self.choose_button_back.clicked.connect(self.go_to_menu)
        hbox_layout.addWidget(self.choose_button_back)

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
        choose_layout.addLayout(hbox_layout)

        choose_layout.setStretch(0, 20)
        choose_layout.setStretch(1, 70)
        choose_layout.setStretch(2, 10)

        self.page_choose.setLayout(choose_layout)
        # ====================================================================

        # ====================================================================
        # Настройка страницы с настройками
        self.options_label_title = QLabel('Настройки', self)
        self.options_label_username = QLabel('Введите логин', self)

        self.options_edit_username = QLineEdit()
        self.options_edit_username.setText(self.user.get_username())
        self.options_edit_username.textChanged.connect(self.user.set_username)

        self.options_button_back = QPushButton('Назад в меню', self)
        self.options_button_back.clicked.connect(self.go_to_menu)

        options_layout = QVBoxLayout()
        options_layout.addWidget(self.options_label_title)
        options_layout.addWidget(self.options_label_username)
        options_layout.addWidget(self.options_edit_username)
        options_layout.addWidget(self.options_button_back)
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

            button = QPushButton('Начать', self)
            button.setFont(font)
            button.setSizePolicy(QSizePolicy.Expanding,
                                 QSizePolicy.Expanding)

            # Каждая кнопка в списке запускает свое задание,
            # определеняемое путем
            button.clicked.connect(lambda click, path=name:
                                   self.go_to_chosen_task(path, self.w,
                                                          self.h, task_id))

            label_image = QLabel(self)
            pixmap = QPixmap(f'db/{name}/preview.png')
            label_image.setPixmap(pixmap)
            label_image.setMaximumWidth(640)
            label_image.setMaximumHeight(480)
            label_image.setScaledContents(True)

            layout.addWidget(label_title, 0, 0, 1, 2)
            layout.addWidget(label_difficulty, 1, 0)
            layout.addWidget(label_is_complete, 2, 0)
            layout.addWidget(button, 3, 0)
            layout.addWidget(label_image, 1, 1, 3, 1)

            layout.setRowStretch(0, 1)
            layout.setRowStretch(1, 1)
            layout.setRowStretch(2, 1)
            layout.setRowStretch(3, 1)

            self.grid_items.append(item)

    def go_to_chosen_task(self, path: str, w: int, h: int, task_id: str):
        '''Функция, запускающая выбранное задание. Для этого запускается класс
        TaskWindow с параметром пути'''
        new_window = TaskWindow(path, w, h, self.font_family, task_id, self)
        new_window.exec_()

    def go_to_menu(self):
        '''Функция для перехода на страницу меню'''
        self.stacked_widget.setCurrentWidget(self.page_menu)

    def go_to_choose(self):
        '''Функция для перехода на страницу выбора задания'''
        self.stacked_widget.setCurrentWidget(self.page_choose)

    def go_to_options(self):
        '''Функция для перехода на страницу настроек'''
        self.stacked_widget.setCurrentWidget(self.page_options)

    def refresh_completion_info(self):
        print('Refresh!')

        self.grid_items = []
        self.download.dowload_patient_files()
        self.get_grid_items()

        choose_v_cont = QWidget()
        choose_v = QVBoxLayout(choose_v_cont)
        for i, item in enumerate(self.grid_items):
            choose_v.addWidget(item)
        self.choose_scroll_area.setWidget(choose_v_cont)

    def resizeEvent(self, event):
        '''Функция, вызываемая при изменении интерфейса приложения,
        изменяющая шрифт во всем приложении'''
        font_size = min(100, max(10, self.width() // 25))

        font = QFont(self.font_family, font_size)

        self.menu_label_title.setFont(font)
        self.menu_button_choose.setFont(font)
        self.menu_button_options.setFont(font)
        self.menu_button_exit.setFont(font)

        self.choose_label_title.setFont(font)
        self.choose_button_refresh.setFont(font)
        self.choose_button_back.setFont(font)

        self.options_label_title.setFont(font)
        self.options_label_username.setFont(font)
        self.options_edit_username.setFont(font)
        self.options_button_back.setFont(font)

        super().resizeEvent(event)

    def closeEvent(self, event):
        '''Функция, вызываемая при закрытии основного окна'''
        with open('calibration_info.json', 'w'):
            pass
