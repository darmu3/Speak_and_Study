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

        self.last_name_label = QLabel("Фамилия:")
        self.first_name_label = QLabel("Имя:")
        self.patronymic_label = QLabel("Отчество:")
        self.phone_number_label = QLabel("Телефон:")
        self.age_label = QLabel("Возраст:")
        self.courses_label = QLabel("Курсы:")
        self.last_name_edit = QLineEdit()
        self.first_name_edit = QLineEdit()
        self.patronymic_edit = QLineEdit()
        self.phone_number_edit = QLineEdit()
        self.age_edit = QLineEdit()
        self.courses_participating_text_browser = QTextBrowser()

        name_validator = QRegExpValidator(QRegExp("[А-Яа-яЁё]+"))
        age_validator = QRegExpValidator(QRegExp("[0-9]+"))
        self.last_name_edit.setValidator(name_validator)
        self.first_name_edit.setValidator(name_validator)
        self.patronymic_edit.setValidator(name_validator)
        self.age_edit.setValidator(age_validator)
        self.age_edit.setMaxLength(3)

        self.last_name_edit.setReadOnly(True)
        self.first_name_edit.setReadOnly(True)
        self.patronymic_edit.setReadOnly(True)
        self.phone_number_edit.setReadOnly(True)
        self.age_edit.setReadOnly(True)

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
        details_layout.addWidget(self.courses_label)
        details_layout.addWidget(self.courses_participating_text_browser)

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

        layout.addWidget(listeners_area)
        layout.addWidget(details_area)
        layout.addWidget(buttons_area)

        self.setLayout(layout)

        self.edit_listener_button.clicked.connect(self.toggle_edit_mode)
        delete_listener_button.clicked.connect(self.delete_listener)

        self.installEventFilter(self)

    def update_listeners(self):
        self.load_listeners()

    def showEvent(self, event):
        # Вызывается при каждом показе страницы
        self.update_listeners()

    def eventFilter(self, obj, event):
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
        self.listeners_list.clearSelection()

        self.clear_info()

        if self.edit_listener_button.text() == "Сохранить\nизменения":
            self.edit_listener_button.setText("Редактировать\nинформацию\nо слушателе")

        self.edit_read_true()

    def show_warning_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Внимание!")
        msg_box.setText(message)
        msg_box.exec_()

    def clear_info(self):
        self.last_name_edit.clear()
        self.first_name_edit.clear()
        self.patronymic_edit.clear()
        self.phone_number_edit.clear()
        self.age_edit.clear()
        self.courses_participating_text_browser.clear()

    def toggle_edit_mode(self):
        if not self.listeners_list.selectedItems():
            self.show_warning_message("Выберите слушателя для редактирования.")
            return

        if self.edit_listener_button.text() == "Редактировать\nинформацию\nо слушателе":
            self.edit_read_false()
            self.edit_listener_button.setText("Сохранить\nизменения")
        else:
            self.edit_read_true()
            self.edit_listener_button.setText("Редактировать\nинформацию\nо слушателе")

            self.save_listener_changes()

    def save_listener_changes(self):
        try:
            if not self.listeners_list.selectedItems():
                self.show_warning_message("Выберите слушателя для редактирования.")
                return

            selected_item = self.listeners_list.selectedItems()[0]
            listener_id = selected_item.data(1)

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

            new_last_name = self.last_name_edit.text()
            new_first_name = self.first_name_edit.text()
            new_patronymic = self.patronymic_edit.text()
            new_phone_number = self.phone_number_edit.text()
            new_age = self.age_edit.text()

            print(
                f"Current Data: {current_last_name}, {current_first_name}, {current_patronymic}, "
                f"{current_phone_number}, {current_age}")
            print(f"New Data: {new_last_name}, {new_first_name}, {new_patronymic}, {new_phone_number}, {new_age}")

            if (current_last_name, current_first_name, current_patronymic, current_phone_number, int(current_age)) == (
                    new_last_name, new_first_name, new_patronymic, new_phone_number, int(new_age)
            ):
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

            self.load_listeners()

            self.clear_info()

        except Exception as e:
            error_message = f"Произошла ошибка при сохранении изменений: {e}\n\n" \
                            "Формат номера телефона должен быть 8(XXX)XXX-XX-XX."
            self.show_warning_message(error_message)

    def delete_listener(self):
        try:
            if not self.listeners_list.selectedItems():
                self.show_warning_message("Выберите слушателя для удаления.")
                return

            selected_item = self.listeners_list.selectedItems()[0]
            listener_id = selected_item.data(1)

            confirm_message = "Вы уверены, что хотите удалить этого слушателя?"
            confirm_result = QMessageBox.question(self, 'Подтверждение удаления', confirm_message,
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if confirm_result == QMessageBox.No:
                return

            connection = connect()
            cursor = connection.cursor()
            cursor.execute('DELETE FROM "Users" WHERE "user_id" = %s', (listener_id,))
            connection.commit()
            close_db_connect(connection, cursor)

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

        cursor.execute('SELECT "Courses".course_id, "Courses".name_course FROM "Courses" '
                       'JOIN "usercourses" ON "Courses".course_id = "usercourses".course_id '
                       'WHERE "usercourses".user_id = %s', (listener_id,))
        courses_participating = cursor.fetchall()
        close_db_connect(connection, cursor)

        if listener_details:
            user_id, last_name, first_name, patronymic, phone_number, age = listener_details

            self.last_name_edit.setText(last_name)
            self.first_name_edit.setText(first_name)
            self.patronymic_edit.setText(patronymic)
            self.phone_number_edit.setText(phone_number)
            self.age_edit.setText(str(age))

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

        sorted_listeners = sorted(listeners, key=lambda x: x[0])

        for user_id, second_name, first_name, patronymic, phone_number, age in sorted_listeners:
            item_text = f"{second_name} {first_name}"
            item = QListWidgetItem(item_text)
            item.setData(1, user_id)
            self.listeners_list.addItem(item)

        for i in range(self.listeners_list.count()):
            item = self.listeners_list.item(i)
            if item.data(1) == current_user_id:
                self.listeners_list.setCurrentItem(item)
                break
