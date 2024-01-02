import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
from qt_material import apply_stylesheet

from main_menu import MainMenuWidget


class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Speak_and_Study_Admin')
        self.setGeometry(100, 100, 800, 600)

        # Задаем минимальный размер окна
        self.setMinimumSize(1050, 600)

        self.central_widget = MainMenuWidget(self)
        self.setCentralWidget(self.central_widget)

        self.center()

    def center(self):
        # Получаем размер экрана
        screen = QDesktopWidget().screenGeometry()

        # Получаем размеры окна
        size = self.geometry()

        # Вычисляем центральные координаты окна
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2

        # Устанавливаем окно по центру
        self.move(x, y)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    apply_stylesheet(app, theme='light_blue.xml')

    window = MyApp()
    window.show()
    sys.exit(app.exec_())
