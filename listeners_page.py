from PyQt5.QtCore import QEvent, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QVBoxLayout, \
    QListWidget, QListWidgetItem, QMessageBox, QTextBrowser
from conn_db import connect, close_db_connect


class ListenersPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()
        self.load_listeners()

    def initUI(self):
        layout = QHBoxLayout()

        # Область с подробной информацией о слушателе
        details_area = QWidget()
        details_layout = QFormLayout()

        label = QLabel("Подробная информация о\nслушателе:")
        details_layout.addRow(label)
        label.setFixedHeight(30)

        # Используем QLineEdit вместо QTextEdit
        self.last_name_edit = QLineEdit()
        self.first_name_edit = QLineEdit()
        self.patronymic_edit = QLineEdit()
        self.phone_number_edit = QLineEdit()
        self.age_edit = QLineEdit()

        # Добавляем валидаторы для фамилии, имени и отчества
        name_validator = QRegExpValidator(QRegExp("[А-Яа-яЁё]+"))  # Разрешены только буквы русского алфавита
        age_validator = QRegExpValidator(QRegExp("[0-9]+"))
        self.last_name_edit.setValidator(name_validator)
        self.first_name_edit.setValidator(name_validator)
        self.patronymic_edit.setValidator(name_validator)
        self.age_edit.setValidator(age_validator)
        self.age_edit.setMaxLength(3)

        # Используем QLabel для текста перед каждым QLineEdit
        self.last_name_label = QLabel("Фамилия:")
        self.first_name_label = QLabel("Имя:")
        self.patronymic_label = QLabel("Отчество:")
        self.phone_number_label = QLabel("Телефон:")
        self.age_label = QLabel("Возраст:")

        # Устанавливаем белый цвет текста
        white_text_style = "color: black;"
        self.last_name_edit.setStyleSheet(white_text_style)
        self.first_name_edit.setStyleSheet(white_text_style)
        self.patronymic_edit.setStyleSheet(white_text_style)
        self.phone_number_edit.setStyleSheet(white_text_style)
        self.age_edit.setStyleSheet(white_text_style)

        self.last_name_edit.setReadOnly(True)
        self.first_name_edit.setReadOnly(True)
        self.patronymic_edit.setReadOnly(True)
        self.phone_number_edit.setReadOnly(True)
        self.age_edit.setReadOnly(True)

        # Добавляем QLabel и QLineEdit в QVBoxLayout
        details_layout.addWidget(self.last_name_label)
        details_layout.addWidget(self.last_name_edit)
        details_layout.addWidget(self.first_name_label)
        details_layout.addWidget(self.first_name_edit)
        details_layout.addWidget(self.patronymic_label)
        details_layout.addWidget(self.patronymic_edit)
        details_layout.addWidget(self.phone_number_label)
        details_layout.addWidget(self.phone_number_edit)
        details_layout.addWidget(self.age_label)
        details_layout.addWidget(self.age_edit)

        # Вставьте следующий код в метод initUI после создания self.age_edit
        self.courses_label = QLabel("Курсы:")
        self.courses_participating_text_browser = QTextBrowser()
        details_layout.addWidget(self.courses_label)
        details_layout.addWidget(self.courses_participating_text_browser)

        # Кнопки "Редактировать информацию о слушателе" и "Удалить слушателя"
        buttons_area = QWidget()
        buttons_layout = QVBoxLayout()
        self.edit_listener_button = QPushButton("Редактировать\nинформацию\nо слушателе")
        delete_listener_button = QPushButton("Удалить слушателя")
        buttons_layout.addWidget(self.edit_listener_button)
        buttons_layout.addWidget(delete_listener_button)
        buttons_area.setLayout(buttons_layout)

        self.edit_listener_button.setFixedHeight(60)
        delete_listener_button.setFixedHeight(60)

        details_area.setLayout(details_layout)

        # Область со слушателями
        listeners_area = QWidget()
        listeners_layout = QVBoxLayout()
        label = QLabel("Слушатели:")
        self.listeners_list = QListWidget()
        self.listeners_list.itemClicked.connect(self.show_listener_details)
        listeners_layout.addWidget(label)
        listeners_layout.addWidget(self.listeners_list)
        listeners_area.setLayout(listeners_layout)

        listeners_area.setMinimumWidth(300)

        layout.addWidget(listeners_area)
        layout.addWidget(details_area)
        layout.addWidget(buttons_area)

        self.setLayout(layout)

        # Connect the "Редактировать информацию о слушателе" button to the toggle_edit_mode method
        self.edit_listener_button.clicked.connect(self.toggle_edit_mode)
        # Connect the "Удалить слушателя" button to the delete_listener method
        delete_listener_button.clicked.connect(self.delete_listener)

        # Подключите метод clear_listener_selection к событию MouseButtonRelease на self
        self.installEventFilter(self)

    def update_listeners(self):
        # Обновление списка договоров
        self.load_listeners()

    def showEvent(self, event):
        # Вызывается при каждом показе страницы
        self.update_listeners()

    def eventFilter(self, obj, event):
        # Если произошло событие MouseButtonRelease на self, очистите выделение в listeners_list
        if obj == self and event.type() == QEvent.MouseButtonRelease:
            self.clear_listener_selection()
        return super().eventFilter(obj, event)

    def edit_read_true(self):
        self.last_name_edit.setReadOnly(True)
        self.first_name_edit.setReadOnly(True)
        self.patronymic_edit.setReadOnly(True)
        self.phone_number_edit.setReadOnly(True)
        self.age_edit.setReadOnly(True)

    def edit_read_false(self):
        self.last_name_edit.setReadOnly(False)
        self.first_name_edit.setReadOnly(False)
        self.patronymic_edit.setReadOnly(False)
        self.phone_number_edit.setReadOnly(False)
        self.age_edit.setReadOnly(False)

    def clear_listener_selection(self):
        # Очистите выделение в списке слушателей
        self.listeners_list.clearSelection()

        self.clear_info()

        # Установите кнопку обратно в режим "Редактировать информацию о слушателе" только тогда, если она в режиме
        # сохранения изменений
        if self.edit_listener_button.text() == "Сохранить\nизменения":
            self.edit_listener_button.setText("Редактировать\nинформацию\nо слушателе")

        self.edit_read_true()

    def toggle_edit_mode(self):
        # Check if a listener is selected
        if not self.listeners_list.selectedItems():
            self.show_warning_message("Выберите слушателя для редактирования.")
            return

        if self.edit_listener_button.text() == "Редактировать\nинформацию\nо слушателе":
            self.edit_read_false()
            self.edit_listener_button.setText("Сохранить\nизменения")
        else:
            self.edit_read_true()
            self.edit_listener_button.setText("Редактировать\nинформацию\nо слушателе")

            # Сохраняем изменения в БД
            self.save_listener_changes()

    def show_warning_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Внимание!")
        msg_box.setText(message)
        msg_box.exec_()

    def clear_info(self):
        # Сбросить текст в QLineEdit
        self.last_name_edit.clear()
        self.first_name_edit.clear()
        self.patronymic_edit.clear()
        self.phone_number_edit.clear()
        self.age_edit.clear()
        self.courses_participating_text_browser.clear()

    def save_listener_changes(self):
        try:
            # Check if a listener is selected
            if not self.listeners_list.selectedItems():
                self.show_warning_message("Выберите слушателя для редактирования.")
                return

            # Получаем идентификатор слушателя из списка слушателей
            selected_item = self.listeners_list.selectedItems()[0]
            listener_id = selected_item.data(1)

            # Получаем текущие данные из БД
            connection = connect()
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM "Users" WHERE "user_id" = %s', (listener_id,))
            current_data = cursor.fetchone()
            close_db_connect(connection, cursor)

            if not current_data:
                self.show_warning_message("Не удалось получить текущие данные слушателя.")
                return

            user_id, current_last_name, current_first_name, current_patronymic, current_phone_number, current_age = \
                current_data

            # Получаем новые данные из QLineEdit
            new_last_name = self.last_name_edit.text()
            new_first_name = self.first_name_edit.text()
            new_patronymic = self.patronymic_edit.text()
            new_phone_number = self.phone_number_edit.text()
            new_age = self.age_edit.text()

            print(
                f"Current Data: {current_last_name}, {current_first_name}, {current_patronymic}, {current_phone_number}, {current_age}")
            print(f"New Data: {new_last_name}, {new_first_name}, {new_patronymic}, {new_phone_number}, {new_age}")

            # Проверяем, изменились ли данные
            if (current_last_name, current_first_name, current_patronymic, current_phone_number, int(current_age)) == (
                    new_last_name, new_first_name, new_patronymic, new_phone_number, int(new_age)
            ):
                # Если данные не изменились, выходим без сохранения
                print("No changes detected.")
                self.clear_info()
                self.listeners_list.clearSelection()
                return

            if 12 <= int(new_age) <= 120:
                connection = connect()
                cursor = connection.cursor()
                cursor.execute('UPDATE "Users" SET "second_name" = %s, "first_name" = %s, "patronymic" = %s, '
                               '"phone_number" = %s, "age" = %s WHERE "user_id" = %s',
                               (new_last_name, new_first_name, new_patronymic, new_phone_number, new_age, listener_id))
                connection.commit()
                close_db_connect(connection, cursor)
            else:
                age_message = f"Возраст должен быть от 12 до 120 лет"
                self.show_warning_message(age_message)

            # Обновляем список слушателей
            self.load_listeners()

            self.clear_info()

        except Exception as e:
            # При возникновении ошибки выведите сообщение с информацией о формате номера телефона
            error_message = f"Произошла ошибка при сохранении изменений: {e}\n\n" \
                            "Формат номера телефона должен быть 8(XXX)XXX-XX-XX."
            self.show_warning_message(error_message)

    def delete_listener(self):
        try:
            # Check if a listener is selected
            if not self.listeners_list.selectedItems():
                self.show_warning_message("Выберите слушателя для удаления.")
                return

            # Получаем идентификатор слушателя из списка слушателей
            selected_item = self.listeners_list.selectedItems()[0]
            listener_id = selected_item.data(1)

            # Запрос на подтверждение удаления
            confirm_message = "Вы уверены, что хотите удалить этого слушателя?"
            confirm_result = QMessageBox.question(self, 'Подтверждение удаления', confirm_message,
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if confirm_result == QMessageBox.No:
                return

            # Удаляем слушателя из БД (замените это соответствующим кодом для вашей БД)
            connection = connect()
            cursor = connection.cursor()
            cursor.execute('DELETE FROM "Users" WHERE "user_id" = %s', (listener_id,))
            connection.commit()
            close_db_connect(connection, cursor)

            # Обновляем список слушателей
            self.load_listeners()

            self.clear_info()

        except Exception as e:
            print("Произошла ошибка при удалении слушателя:", e)

    def show_listener_details(self, item):
        listener_id = item.data(1)

        connection = connect()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "Users" WHERE user_id = %s', (listener_id,))
        listener_details = cursor.fetchone()

        # Получаем информацию о курсах, на которых участвует слушатель
        cursor.execute('SELECT "Courses".course_id, "Courses".name_course FROM "Courses" '
                       'JOIN "usercourses" ON "Courses".course_id = "usercourses".course_id '
                       'WHERE "usercourses".user_id = %s', (listener_id,))
        courses_participating = cursor.fetchall()
        close_db_connect(connection, cursor)

        if listener_details:
            user_id, last_name, first_name, patronymic, phone_number, age = listener_details

            # Отображение подробной информации о слушателе
            self.last_name_edit.setText(last_name)
            self.first_name_edit.setText(first_name)
            self.patronymic_edit.setText(patronymic)
            self.phone_number_edit.setText(phone_number)
            self.age_edit.setText(str(age))

            # Отображение информации о курсах
            courses_info = "\n".join(
                [f"{course_id}: {course_name}" for course_id, course_name in courses_participating])
            self.courses_participating_text_browser.setPlainText(f"{courses_info}\n")

    def load_listeners(self):
        connection = connect()

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "Users"')
        listeners = cursor.fetchall()

        close_db_connect(connection, cursor)

        current_item = self.listeners_list.currentItem()
        current_user_id = current_item.data(1) if current_item else None

        self.listeners_list.clear()

        # Сортируем слушателей по user_id
        sorted_listeners = sorted(listeners, key=lambda x: x[0])

        for user_id, second_name, first_name, patronymic, phone_number, age in sorted_listeners:
            item_text = f"{second_name} {first_name}"
            item = QListWidgetItem(item_text)
            item.setData(1, user_id)
            self.listeners_list.addItem(item)

        # Устанавливаем текущий элемент после обновления списка
        for i in range(self.listeners_list.count()):
            item = self.listeners_list.item(i)
            if item.data(1) == current_user_id:
                self.listeners_list.setCurrentItem(item)
                break
