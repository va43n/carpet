import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


if __name__ == '__main__':
    print('Приложение запущено')

    app = QApplication(sys.argv)

    screen = app.primaryScreen()
    screen_size = screen.size()
    window = MainWindow(screen_size.width(), screen_size.height())

    window.showFullScreen()
    sys.exit(app.exec_())

    print('Приложение закрыто')
