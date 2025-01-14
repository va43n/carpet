from PyQt5.QtWidgets import (QApplication, QScrollArea, QWidget,
                             QMainWindow, QStackedWidget,
                             QVBoxLayout, QPushButton, QLabel,
                             QSizePolicy, QGridLayout)
from PyQt5.QtGui import QFont, QFontDatabase, QPixmap
from PyQt5.QtCore import Qt
from task_window import TaskWindow


class MainWindow(QMainWindow):
    '''Класс, предоставляющий интерфейс основного приложения и организующий
    связь между пользовательским вводом и основными составляющими приложения:
    основным меню, меню настроек и меню выбора задания. Для вызова выбранного
    задания используется класс TaskWindow из модуля task_window.py.'''

    def __init__(self, w, h):
        '''Инициализатор класса, запускает окно с интерфейсом и задает
        основные параметры.'''
        super().__init__()

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
        self.menu_label_title = QLabel('Приложение', self)
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
        # ====================================================================

        # ====================================================================
        # Настройка страницы с выбором задания
        self.choose_label_title = QLabel('Выберите задание', self)
        self.choose_label_title.setAlignment(Qt.AlignCenter)

        self.choose_button_back = QPushButton('Назад в меню', self)
        self.choose_button_back.setSizePolicy(QSizePolicy.Expanding,
                                              QSizePolicy.Expanding)
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
        # ====================================================================

        # ====================================================================
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
        # ====================================================================

        # Добавление страниц в stacked_widget
        self.stacked_widget.addWidget(self.page_menu)
        self.stacked_widget.addWidget(self.page_choose)
        self.stacked_widget.addWidget(self.page_options)

        self.stacked_widget.setCurrentWidget(self.page_menu)

    def get_grid_items(self):
        '''Функция, считывающая все задания из файла db/all_tasks.txt и
        вставляющая их в список QScrollArea'''
        font = QFont(self.font_family, 50)
        with open('db/all_tasks.txt') as f:
            for line in f:
                # Разбиение каждой строки файла на массив элементов
                l = list(map(lambda item: item.replace('\n', ''), line.split(' ')))

                # Каждый элемент списка - виджет. Создание виджета
                item = QWidget()
                layout = QGridLayout(item)

                label_difficulty = QLabel(f'Сложность: {l[1]}/5', self)
                label_difficulty.setFont(font)
                label_difficulty.setAlignment(Qt.AlignCenter)

                is_completed = 'Да' if l[2] == '1' else 'Нет'
                label_is_complete = QLabel(f'Пройдено: {is_completed}', self)
                label_is_complete.setFont(font)
                label_is_complete.setAlignment(Qt.AlignCenter)

                button = QPushButton('Начать', self)
                button.setFont(font)
                button.setSizePolicy(QSizePolicy.Expanding,
                                     QSizePolicy.Expanding)

                # Каждая кнопка в списке запускает свое задание,
                # определеняемое путем
                button.clicked.connect(lambda click, path=l[0]:
                                       self.go_to_chosen_task(path, self.w,
                                                              self.h))

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
        '''Функция, запускающая выбранное задание. Для этого запускается класс
        TaskWindow с параметром пути'''
        new_window = TaskWindow(path, w, h)
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
        self.choose_button_back.setFont(font)

        self.options_label_title.setFont(font)
        self.options_label_option1.setFont(font)
        self.options_label_option2.setFont(font)
        self.options_button_back.setFont(font)

        super().resizeEvent(event)
