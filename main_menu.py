from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QStackedWidget, QLabel, QHBoxLayout, QTextBrowser, \
    QListWidget, QListWidgetItem
from conn_db import connect, close_db_connect
from listeners_page import ListenersPage
from teachers_page import  TeachersPage


class MainMenuWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()
        self.load_requests()

    def initUI(self):
        self.is_request_selected = False  # Флаг для отслеживания выбора заявки

        # Область с кнопками
        self.taskbar_layout = QVBoxLayout()

        self.pages = QStackedWidget()

        # Создаем кнопки для страниц
        page_names = ["Главное меню", "Слушатели", "Курсы", "Преподаватели", "Договоры", "Отчеты"]
        for i, page_name in enumerate(page_names):
            button = QPushButton(page_name)
            button.clicked.connect(self.show_page(i))
            self.taskbar_layout.addWidget(button)

        # Создаем виджеты страниц
        self.create_main_menu_page()
        self.create_listeners_page()
        self.pages.addWidget(self.create_page("Курсы"))
        self.create_teachers_page()
        self.pages.addWidget(self.create_page("Договоры"))
        self.pages.addWidget(self.create_page("Отчеты"))

        # Обработчик для выбора заявки в списке
        self.requests_list.itemClicked.connect(self.show_request_details)

        # Размещаем виджеты с кнопками и страницами в основном макете
        main_layout = QHBoxLayout(self)
        main_layout.addLayout(self.taskbar_layout)
        main_layout.addWidget(self.pages)

        self.setLayout(main_layout)

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        # Если произошло событие MouseButtonRelease на self, очистите выделение в listeners_list
        if obj == self and event.type() == QEvent.MouseButtonRelease:
            self.clear_listener_selection()
        return super().eventFilter(obj, event)

    def clear_listener_selection(self):
        # Очистите выделение в списке слушателей
        self.requests_list.clearSelection()
        self.details_text.clear()


    def resizeEvent(self, event):
        # При изменении размера окна будем изменять размер шрифта
        new_font_size = int(self.width() / 60)  # Пример расчета нового размера шрифта
        font = self.details_text.font()
        font.setPointSize(new_font_size)
        self.details_text.setFont(font)

        # Вызываем родительский метод для обработки стандартных событий изменения размера окна
        super().resizeEvent(event)

    def create_main_menu_page(self):
        page = QWidget()
        layout = QHBoxLayout()

        # Область с заявками
        requests_area = QWidget()
        requests_layout = QVBoxLayout()
        label = QLabel("Заявки:")
        self.requests_list = QListWidget()
        requests_layout.addWidget(label)
        requests_layout.addWidget(self.requests_list)
        requests_area.setLayout(requests_layout)

        # Область с подробной информацией
        details_area = QWidget()
        details_layout = QVBoxLayout()
        label = QLabel("Подробная информация:")
        self.details_text = QTextBrowser()
        details_layout.addWidget(label)
        details_layout.addWidget(self.details_text)
        details_area.setLayout(details_layout)

        # Кнопки "Составить договор" и "Отказать"
        buttons_area = QWidget()
        buttons_layout = QVBoxLayout()
        compose_contract_button = QPushButton("Составить договор")
        reject_button = QPushButton("Отказать")
        buttons_layout.addWidget(compose_contract_button)
        buttons_layout.addWidget(reject_button)
        buttons_area.setLayout(buttons_layout)

        layout.addWidget(requests_area)
        layout.addWidget(details_area)
        layout.addWidget(buttons_area)

        page.setLayout(layout)

        self.pages.addWidget(page)

    def create_page(self, page_name):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(f"Это страница {page_name}")
        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def show_page(self, page_index):
        def handler():
            self.pages.setCurrentIndex(page_index)

        return handler

    def load_requests(self):
        # Соединение с базой данных
        connection = connect()

        # Создание курсора для выполнения SQL-запросов
        cursor = connection.cursor()

        # Выборка не просмотренных заявок из базы данных
        cursor.execute('SELECT * FROM "Requests" WHERE status = FALSE')
        requests = cursor.fetchall()

        close_db_connect(connection, cursor)

        # Очистка списка заявок
        self.requests_list.clear()

        # Добавление заявок в список
        for request in requests:
            request_id, first_name, second_name, age, status = request
            item_text = f"Заявка № {request_id}"
            item = QListWidgetItem(item_text)
            item.setData(1, request_id)  # Дополнительные данные для хранения идентификатора заявки
            self.requests_list.addItem(item)

    def show_request_details(self, item):
        # Получение идентификатора заявки из дополнительных данных
        request_id = item.data(1)

        # Получение подробной информации о заявке из базы данных
        connection = connect()

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM \"Requests\" WHERE request_id = %s", (request_id,))
        request_details = cursor.fetchone()

        close_db_connect(connection, cursor)

        # Отображение подробной информации
        if request_details:
            request_id, first_name, second_name, age, status = request_details
            details_text = f"Имя: {first_name}\nФамилия: {second_name}\nВозраст: {age}\n"
            self.details_text.setPlainText(details_text)

    def create_listeners_page(self):
        listeners_page = ListenersPage(self)  # Создаем объект ListenersPage
        self.pages.addWidget(listeners_page)  # Добавляем его в QStackedWidget

    def create_teachers_page(self):
        teachers_page = TeachersPage(self)
        self.pages.addWidget(teachers_page)