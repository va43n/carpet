import sys

from PyQt5.QtWidgets import QApplication

from main_window import MainWindow


if __name__ == '__main__':
    # Очистка файла с точками калибровки при запуске
    with open('info/calibration_info.json', 'w'):
        pass

    # Создание QT приложения
    app = QApplication(sys.argv)

    # Cоздание главного окна и его вывод на весь экран
    window = MainWindow(1920, 1080)
    window.showFullScreen()

    # Запуск event loop, выход из программы в случае
    # завершения работы приложения
    sys.exit(app.exec_())
