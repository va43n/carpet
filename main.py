import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


if __name__ == '__main__':
    print('Приложение запущено')

    with open('info/calibration_info.json', 'w'):
        pass

    app = QApplication(sys.argv)

    screen = app.primaryScreen()
    screen_size = screen.size()
    window = MainWindow(1920, 1080)

    window.showFullScreen()

    print('Приложение закрыто')
    sys.exit(app.exec_())
