from PyQt5.QtCore import QEvent, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QVBoxLayout, \
    QListWidget, QListWidgetItem, QMessageBox, QDialog

from conn_db import connect, close_db_connect


class TeachersPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.editing_mode = False  # Флаг для отслеживания режима редактирования
        self.initUI()
        self.load_teachers()

    def initUI(self):
        layout = QHBoxLayout()

        details_area = QWidget()
        details_layout = QFormLayout()

        label = QLabel("Подробная информация о\nпреподавателе:")
        details_layout.addRow(label)
        label.setFixedHeight(30)

        self.last_name_label = QLabel("Фамилия:")
        self.first_name_label = QLabel("Имя:")
        self.patronymic_label = QLabel("Отчество:")
        self.education_label = QLabel("Образование:")
        self.speciality_label = QLabel("Специальность:")
        self.seniority_label = QLabel("Стаж работы:")
        self.last_name_edit = QLineEdit()
        self.first_name_edit = QLineEdit()
        self.patronymic_edit = QLineEdit()
        self.education_edit = QLineEdit()
        self.speciality_edit = QLineEdit()
        self.seniority_edit = QLineEdit()

        self.last_name_edit.setReadOnly(True)
        self.first_name_edit.setReadOnly(True)
        self.patronymic_edit.setReadOnly(True)
        self.education_edit.setReadOnly(True)
        self.speciality_edit.setReadOnly(True)
        self.seniority_edit.setReadOnly(True)

        details_layout.addWidget(self.last_name_label)
        details_layout.addWidget(self.last_name_edit)
        details_layout.addWidget(self.first_name_label)
        details_layout.addWidget(self.first_name_edit)
        details_layout.addWidget(self.patronymic_label)
        details_layout.addWidget(self.patronymic_edit)
        details_layout.addWidget(self.education_label)
        details_layout.addWidget(self.education_edit)
        details_layout.addWidget(self.speciality_label)
        details_layout.addWidget(self.speciality_edit)
        details_layout.addWidget(self.seniority_label)
        details_layout.addWidget(self.seniority_edit)

        buttons_area = QWidget()
        buttons_layout = QVBoxLayout()
        self.edit_teacher_button = QPushButton("Редактировать\nинформацию\nо преподавателе")
        delete_teacher_button = QPushButton("Удалить\nпреподавателя")
        add_teacher_button = QPushButton("Добавить\nпреподавателя")
        buttons_layout.addWidget(add_teacher_button)
        buttons_layout.addWidget(self.edit_teacher_button)
        buttons_layout.addWidget(delete_teacher_button)
        buttons_area.setLayout(buttons_layout)

        self.edit_teacher_button.setFixedHeight(60)
        delete_teacher_button.setFixedHeight(60)

        details_area.setLayout(details_layout)

        teachers_area = QWidget()
        teachers_layout = QVBoxLayout()
        label = QLabel("Преподаватели:")
        self.teachers_list = QListWidget()
        self.teachers_list.itemClicked.connect(self.show_teacher_details)
        teachers_layout.addWidget(label)
        teachers_layout.addWidget(self.teachers_list)
        teachers_area.setLayout(teachers_layout)

        layout.addWidget(teachers_area)
        layout.addWidget(details_area)
        layout.addWidget(buttons_area)

        self.setLayout(layout)

        self.edit_teacher_button.clicked.connect(self.toggle_edit_mode)
        delete_teacher_button.clicked.connect(self.delete_teacher)
        add_teacher_button.clicked.connect(self.add_teacher)

        self.installEventFilter(self)

    def update_teachers(self):
        self.load_teachers()

    def showEvent(self, event):
        # Вызывается при каждом показе страницы
        self.update_teachers()

    def set_add_validators(self, last_name_edit, first_name_edit, patronymic_edit, seniority_edit):
        name_validator = QRegExpValidator(QRegExp("[А-Яа-яЁё]+"))
        seniority_validator = QRegExpValidator(QRegExp("[0-9]+"))
        last_name_edit.setValidator(name_validator)
        first_name_edit.setValidator(name_validator)
        patronymic_edit.setValidator(name_validator)
        seniority_edit.setValidator(seniority_validator)
        seniority_edit.setMaxLength(3)

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.MouseButtonRelease:
            self.clear_teacher_selection()
        return super().eventFilter(obj, event)

    def edit_read_true(self):
        self.last_name_edit.setReadOnly(True)
        self.first_name_edit.setReadOnly(True)
        self.patronymic_edit.setReadOnly(True)
        self.education_edit.setReadOnly(True)
        self.speciality_edit.setReadOnly(True)
        self.seniority_edit.setReadOnly(True)

    def edit_read_false(self):
        self.last_name_edit.setReadOnly(False)
        self.first_name_edit.setReadOnly(False)
        self.patronymic_edit.setReadOnly(False)
        self.education_edit.setReadOnly(False)
        self.speciality_edit.setReadOnly(False)
        self.seniority_edit.setReadOnly(False)

    def clear_teacher_selection(self):
        self.teachers_list.clearSelection()

        self.clear_info()

        if self.edit_teacher_button.text() == "Сохранить\nизменения":
            self.edit_teacher_button.setText("Редактировать\nинформацию\nо преподавателе")

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
        self.education_edit.clear()
        self.speciality_edit.clear()
        self.seniority_edit.clear()

    def toggle_edit_mode(self):
        if not self.teachers_list.selectedItems():
            self.show_warning_message("Выберите преподавателя для редактирования.")
            return

        if self.edit_teacher_button.text() == "Редактировать\nинформацию\nо преподавателе":
            self.edit_read_false()
            self.edit_teacher_button.setText("Сохранить\nизменения")
            self.editing_mode = True
        else:
            self.edit_read_true()
            self.edit_teacher_button.setText("Редактировать\nинформацию\nо преподавателе")
            self.editing_mode = False
            self.save_teacher_changes()
            self.clear_teacher_selection()

    def add_teacher(self):
        try:
            if self.edit_teacher_button.text() == "Сохранить\nизменения":
                self.show_warning_message("Закончите редактирование перед добавлением нового преподавателя.")
                return

            add_teacher_dialog = QDialog(self)
            add_teacher_dialog.setWindowTitle("Добавить преподавателя")

            add_teacher_layout = QFormLayout()

            new_last_name_edit = QLineEdit()
            new_first_name_edit = QLineEdit()
            new_patronymic_edit = QLineEdit()
            new_education_edit = QLineEdit()
            new_speciality_edit = QLineEdit()
            new_seniority_edit = QLineEdit()

            self.set_add_validators(new_last_name_edit, new_first_name_edit, new_patronymic_edit, new_seniority_edit)

            add_teacher_layout.addRow("Фамилия:", new_last_name_edit)
            add_teacher_layout.addRow("Имя:", new_first_name_edit)
            add_teacher_layout.addRow("Отчество:", new_patronymic_edit)
            add_teacher_layout.addRow("Образование:", new_education_edit)
            add_teacher_layout.addRow("Специальность:", new_speciality_edit)
            add_teacher_layout.addRow("Стаж работы:", new_seniority_edit)

            add_button = QPushButton("Добавить")
            cancel_button = QPushButton("Отмена")

            add_button.clicked.connect(lambda: self.save_new_teacher(add_teacher_dialog,
                                                                     new_last_name_edit.text(),
                                                                     new_first_name_edit.text(),
                                                                     new_patronymic_edit.text(),
                                                                     new_education_edit.text(),
                                                                     new_speciality_edit.text(),
                                                                     new_seniority_edit.text()))

            cancel_button.clicked.connect(add_teacher_dialog.close)

            add_teacher_layout.addRow(add_button, cancel_button)

            add_teacher_dialog.setLayout(add_teacher_layout)
            print("Before showing the dialog")
            add_teacher_dialog.exec_()
            print("After showing the dialog")

        except Exception as e:
            print(f"Error in add_teacher: {e}")
            self.show_warning_message(f"Произошла ошибка при открытии диалогового окна: {e}")

    def save_new_teacher(self, dialog, last_name, first_name, patronymic, education, speciality, seniority):
        try:
            if not last_name or not first_name or not patronymic or not education or not speciality or not seniority:
                self.show_warning_message("Заполните все поля.")
                return

            connection = connect()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO "Teachers" ("second_name", "first_name", "patronymic", "education", "speciality", '
                '"seniority")'
                'VALUES (%s, %s, %s, %s, %s, %s) RETURNING teacher_id',
                (last_name, first_name, patronymic, education, speciality, seniority)
            )

            connection.commit()

            connection.commit()
            close_db_connect(connection, cursor)

            self.load_teachers()

            dialog.accept()

        except Exception as e:
            print(f"Error in save_new_teacher: {e}")
            self.show_warning_message(f"Произошла ошибка при добавлении преподавателя: {e}")

    def save_teacher_changes(self):
        try:
            print("Saving teacher changes...")

            if not self.teachers_list.selectedItems():
                self.show_warning_message("Выберите преподавателя для редактирования.")
                return

            selected_item = self.teachers_list.selectedItems()[0]
            teacher_id = selected_item.data(1)

            connection = connect()
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM "Teachers" WHERE "teacher_id" = %s', (teacher_id,))
            current_data = cursor.fetchone()
            close_db_connect(connection, cursor)

            if not current_data:
                self.show_warning_message("Не удалось получить текущие данные преподавателя.")
                return

            teacher_id, current_last_name, current_first_name, current_patronymic, current_education, \
                current_speciality, current_seniority = current_data

            new_last_name = self.last_name_edit.text()
            new_first_name = self.first_name_edit.text()
            new_patronymic = self.patronymic_edit.text()
            new_education = self.education_edit.text()
            new_speciality = self.speciality_edit.text()
            new_seniority = self.seniority_edit.text()

            print(
                f"Current Data: {current_last_name}, {current_first_name}, {current_patronymic}, {current_education}, "
                f"{current_speciality}, {current_seniority}")
            print(
                f"New Data: {new_last_name}, {new_first_name}, {new_patronymic}, {new_education}, {new_speciality}, "
                f"{new_seniority}")

            if (current_last_name, current_first_name, current_patronymic, current_education, current_speciality,
                int(current_seniority)) == (new_last_name, new_first_name, new_patronymic, new_education,
                                            new_speciality, int(new_seniority)):
                print("No changes detected.")
                return

            else:
                connection = connect()
                cursor = connection.cursor()
                cursor.execute(
                    'UPDATE "Teachers" SET "second_name" = %s, "first_name" = %s, "patronymic" = %s, "education" = %s, '
                    '"speciality" = %s, "seniority" = %s WHERE "teacher_id" = %s',
                    (new_last_name, new_first_name, new_patronymic, new_education, new_speciality, new_seniority,
                     teacher_id)
                )

                connection.commit()
                close_db_connect(connection, cursor)

                # Update the list of teachers
                self.load_teachers()

                self.clear_info()

        except Exception as e:
            error_message = f"Произошла ошибка при сохранении изменений: {e}\n\n" \
                            "Формат записи стажа работы — XXX."
            self.show_warning_message(error_message)

    def delete_teacher(self):
        if self.edit_teacher_button.text() == "Сохранить\nизменения":
            self.show_warning_message("Закончите редактирование перед удалением преподавателя.")
            return
        try:
            if not self.teachers_list.selectedItems():
                self.show_warning_message("Выберите преподавателя для удаления.")
                return

            selected_item = self.teachers_list.selectedItems()[0]
            teacher_id = selected_item.data(1)

            confirm_message = "Вы уверены, что хотите удалить этого преподавателя?"
            confirm_result = QMessageBox.question(self, 'Подтверждение удаления', confirm_message,
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if confirm_result == QMessageBox.No:
                return

            connection = connect()
            cursor = connection.cursor()
            cursor.execute('DELETE FROM "Teachers" WHERE "teacher_id" = %s', (teacher_id,))
            connection.commit()
            close_db_connect(connection, cursor)

            self.load_teachers()

            self.clear_info()

        except Exception as e:
            print("Произошла ошибка при удалении преподавателя:", e)

    def show_teacher_details(self, item):
        teacher_id = item.data(1)

        connection = connect()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM \"Teachers\" WHERE teacher_id = %s", (teacher_id,))
        teacher_details = cursor.fetchone()
        close_db_connect(connection, cursor)

        if teacher_details:
            teacher_id, last_name, first_name, patronymic, education, speciality, seniority = teacher_details

            self.last_name_edit.setText(last_name)
            self.first_name_edit.setText(first_name)
            self.patronymic_edit.setText(patronymic)
            self.education_edit.setText(education)
            self.speciality_edit.setText(speciality)
            self.seniority_edit.setText(str(seniority))

    def load_teachers(self):
        connection = connect()

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "Teachers"')
        teachers = cursor.fetchall()

        close_db_connect(connection, cursor)

        current_item = self.teachers_list.currentItem()
        current_teacher_id = current_item.data(1) if current_item else None

        self.teachers_list.clear()

        sorted_teachers = sorted(teachers, key=lambda x: x[0])

        for teacher_id, last_name, first_name, patronymic, education, speciality, seniority in sorted_teachers:
            item_text = f"{last_name} {first_name}"
            item = QListWidgetItem(item_text)
            item.setData(1, teacher_id)
            self.teachers_list.addItem(item)

        for i in range(self.teachers_list.count()):
            item = self.teachers_list.item(i)
            if item.data(1) == current_teacher_id:
                self.teachers_list.setCurrentItem(item)
                break
