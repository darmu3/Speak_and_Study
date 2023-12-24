from PyQt5.QtCore import QEvent, QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QVBoxLayout, \
    QListWidget, QListWidgetItem, QMessageBox, QDialog, QComboBox
from conn_db import connect, close_db_connect


class CoursesPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.editing_mode = False
        self.initUI()
        self.load_courses()

    def initUI(self):
        layout = QHBoxLayout()

        # Details area for course information
        details_area = QWidget()
        details_layout = QFormLayout()

        label = QLabel("Подробная информация о курсе:")
        details_layout.addRow(label)
        label.setFixedHeight(30)

        self.course_name_edit = QLineEdit()
        self.course_description_edit = QLineEdit()
        self.available_places_edit = QLineEdit()

        self.course_name_label = QLabel("Название курса:")
        self.course_description_label = QLabel("Описание курса:")
        self.available_places_label = QLabel("Доступные места:")

        white_text_style = "color: black;"
        self.course_name_edit.setStyleSheet(white_text_style)
        self.course_description_edit.setStyleSheet(white_text_style)
        self.available_places_edit.setStyleSheet(white_text_style)

        self.course_name_edit.setReadOnly(True)
        self.course_description_edit.setReadOnly(True)
        self.available_places_edit.setReadOnly(True)

        details_layout.addWidget(self.course_name_label)
        details_layout.addWidget(self.course_name_edit)
        details_layout.addWidget(self.course_description_label)
        details_layout.addWidget(self.course_description_edit)
        details_layout.addWidget(self.available_places_label)
        details_layout.addWidget(self.available_places_edit)

        # Buttons for editing course information and deleting course
        buttons_area = QWidget()
        buttons_layout = QVBoxLayout()
        self.edit_course_button = QPushButton("Редактировать\nинформацию\nо курсе")
        delete_course_button = QPushButton("Удалить\nкурс")
        add_course_button = QPushButton("Добавить\nкурс")
        buttons_layout.addWidget(add_course_button)
        buttons_layout.addWidget(self.edit_course_button)
        buttons_layout.addWidget(delete_course_button)
        buttons_area.setLayout(buttons_layout)

        self.edit_course_button.setFixedHeight(60)
        delete_course_button.setFixedHeight(60)

        details_area.setLayout(details_layout)

        # Area for courses
        courses_area = QWidget()
        courses_layout = QVBoxLayout()
        label = QLabel("Курсы:")
        self.courses_list = QListWidget()
        self.courses_list.itemClicked.connect(self.show_course_details)
        courses_layout.addWidget(label)
        courses_layout.addWidget(self.courses_list)
        courses_area.setLayout(courses_layout)

        # Добавление QComboBox для выбора преподавателя
        self.teacher_combo_box = QComboBox()
        self.teacher_combo_box.hide()
        self.load_teachers()
        details_layout.addWidget(QLabel("Преподаватель:"))
        details_layout.addWidget(self.teacher_combo_box)

        courses_area.setMinimumWidth(300)

        layout.addWidget(courses_area)
        layout.addWidget(details_area)
        layout.addWidget(buttons_area)

        self.setLayout(layout)

        self.set_add_validators(self.course_name_edit, self.course_description_edit, self.available_places_edit)

        self.edit_course_button.clicked.connect(self.toggle_edit_mode)
        delete_course_button.clicked.connect(self.delete_course)
        add_course_button.clicked.connect(self.add_course)
        self.installEventFilter(self)

    def update_courses(self):
        # Обновление списка договоров
        self.load_courses()

    def showEvent(self, event):
        # Вызывается при каждом показе страницы
        self.update_courses()

    def add_course(self):
        # Функция добавления курса

        # Открываем QDialog для ввода информации о курсе
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление курса")
        dialog_layout = QFormLayout(dialog)

        course_name_edit = QLineEdit()
        course_description_edit = QLineEdit()
        available_places_edit = QLineEdit()

        self.set_add_validators(course_name_edit, course_description_edit, available_places_edit)

        dialog_layout.addRow("Название курса:", course_name_edit)
        dialog_layout.addRow("Описание курса:", course_description_edit)
        dialog_layout.addRow("Доступные места:", available_places_edit)

        # Кнопка для перехода к выбору преподавателя
        next_button = QPushButton("Далее")
        dialog_layout.addWidget(next_button)

        def save_course_info():
            # Функция сохранения информации о курсе и перехода к выбору преподавателя

            name = course_name_edit.text()
            description = course_description_edit.text()
            available_places = available_places_edit.text()

            if not name or not description or not available_places:
                self.show_warning_message("Пожалуйста, заполните все поля.")
                return

            # Сохраняем информацию о курсе в базе данных
            connection = connect()
            cursor = connection.cursor()
            cursor.execute(
                'INSERT INTO "Courses" ("name_course", "course_description", "available_places") '
                'VALUES (%s, %s, %s) RETURNING "course_id"',
                (name, description, available_places)
            )
            course_id = cursor.fetchone()[0]

            # Фиксируем изменения в базе данных
            connection.commit()

            close_db_connect(connection, cursor)

            # Закрываем текущий QDialog
            dialog.close()

            # Переходим к выбору преподавателя
            self.choose_teacher_for_course(course_id)

        next_button.clicked.connect(save_course_info)

        # Отображаем QDialog
        dialog.exec_()

    def choose_teacher_for_course(self, course_id):
        # Открываем новый QDialog для выбора преподавателя
        teacher_dialog = QDialog(self)
        teacher_dialog.setWindowTitle("Выбор преподавателя")
        teacher_dialog_layout = QVBoxLayout(teacher_dialog)

        label = QLabel("Выберите преподавателя:")
        teacher_dialog_layout.addWidget(label)

        # Создаем новый QComboBox
        teacher_combo_box_dialog = QComboBox()
        self.load_teachers(teacher_combo_box_dialog)
        teacher_dialog_layout.addWidget(teacher_combo_box_dialog)

        # Кнопка для сохранения информации о преподавателе и курсе
        save_button = QPushButton("Добавить")
        teacher_dialog_layout.addWidget(save_button)

        def save_teacher_course_info():
            # Функция сохранения информации о преподавателе и курсе

            teacher_id = teacher_combo_box_dialog.currentData()
            if teacher_id is None:
                self.show_warning_message("Выберите преподавателя.")
                return

            # Сохраняем информацию о преподавателе и курсе в базе данных (в таблице Courses)
            connection = connect()
            cursor = connection.cursor()
            try:
                cursor.execute(
                    'UPDATE "Courses" SET "teacher_id" = %s WHERE "course_id" = %s',
                    (teacher_id, course_id)
                )
                connection.commit()

                # Обновляем список курсов и очищаем информацию о курсе
                self.load_courses()
                self.clear_course_info()

            except Exception as e:
                print("Произошла ошибка при сохранении информации о преподавателе и курсе:", e)
                self.show_warning_message("Произошла ошибка при сохранении информации. Пожалуйста, попробуйте еще раз.")

            finally:
                close_db_connect(connection, cursor)

            # Закрываем текущий QDialog
            teacher_dialog.close()

        save_button.clicked.connect(save_teacher_course_info)

        # Отображаем QDialog
        teacher_dialog.exec_()

    def load_teachers(self, combo_box=None):
        # Функция загрузки преподавателей в QComboBox

        connection = connect()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "Teachers"')
        teachers = cursor.fetchall()
        close_db_connect(connection, cursor)

        if combo_box is None:
            # Если combo_box не передан, используем self.teacher_combo_box
            combo_box = self.teacher_combo_box

        combo_box.clear()

        # Add an empty item at the beginning
        combo_box.addItem("")

        for teacher_id, second_name, first_name, patronymic, education, speciality, seniority in teachers:
            full_name = f"{second_name} {first_name} {patronymic}"
            combo_box.addItem(full_name, teacher_id)

    def set_add_validators(self, course_name_edit, course_description_edit, available_places_edit):
        name_validator = QRegExpValidator(QRegExp("[А-Яа-яЁё ]+"))
        available_places_validator = QRegExpValidator(QRegExp("[0-9]+"))

        course_name_edit.setValidator(name_validator)
        course_description_edit.setValidator(name_validator)
        available_places_edit.setValidator(available_places_validator)
        available_places_edit.setMaxLength(3)

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.MouseButtonRelease:
            self.clear_course_selection()
        return super().eventFilter(obj, event)

    def edit_read_true(self):
        self.course_name_edit.setReadOnly(True)
        self.course_description_edit.setReadOnly(True)
        self.available_places_edit.setReadOnly(True)

    def edit_read_false(self):
        self.course_name_edit.setReadOnly(False)
        self.course_description_edit.setReadOnly(False)
        self.available_places_edit.setReadOnly(False)

    def clear_course_selection(self):
        self.courses_list.clearSelection()
        self.clear_course_info()

        if self.edit_course_button.text() == "Сохранить\nизменения":
            self.edit_course_button.setText("Редактировать\nинформацию\nо курсе")

        self.edit_read_true()

    def toggle_edit_mode(self):
        if not self.courses_list.selectedItems():
            self.show_warning_message("Выберите курс для редактирования.")
            return

        if self.edit_course_button.text() == "Редактировать\nинформацию\nо курсе":
            self.edit_read_false()
            self.edit_course_button.setText("Сохранить\nизменения")
            self.teacher_combo_box.show()
            self.editing_mode = True
        else:
            self.edit_read_true()
            self.edit_course_button.setText("Редактировать\nинформацию\nо курсе")
            self.editing_mode = False
            self.teacher_combo_box.hide()
            self.save_course_changes()
            self.clear_course_selection()

    def show_warning_message(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Внимание!")
        msg_box.setText(message)
        msg_box.exec_()

    def clear_course_info(self):
        self.course_name_edit.clear()
        self.course_description_edit.clear()
        self.available_places_edit.clear()
        self.teacher_combo_box.hide()

    def save_course_changes(self):
        try:
            if not self.courses_list.selectedItems():
                self.show_warning_message("Выберите курс для редактирования.")
                return

            selected_item = self.courses_list.selectedItems()[0]
            course_id = selected_item.data(1)

            connection = connect()
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM "Courses" WHERE "course_id" = %s', (course_id,))
            current_data = cursor.fetchone()
            close_db_connect(connection, cursor)

            if not current_data:
                self.show_warning_message("Не удалось получить текущие данные курса.")
                return

            # Распаковываем данные
            course_id, current_name, current_description, current_available_places, current_teacher_id = current_data

            new_name = self.course_name_edit.text()
            new_description = self.course_description_edit.text()
            new_available_places = self.available_places_edit.text()

            # Получаем teacher_id из QComboBox
            teacher_id = self.teacher_combo_box.currentData()

            if (current_name, current_description, current_available_places, current_teacher_id) == (
                    new_name, new_description, new_available_places, teacher_id):
                print("No changes detected.")

                connection = connect()
                cursor = connection.cursor()
                cursor.execute(
                    'UPDATE "Courses" SET "name_course" = %s, "course_description" = %s, "available_places" = %s, '
                    '"teacher_id" = %s '
                    'WHERE "course_id" = %s',
                    (new_name, new_description, new_available_places, teacher_id, course_id)
                )

                connection.commit()
                close_db_connect(connection, cursor)

                self.load_courses()
                self.clear_course_info()

                return

            else:
                connection = connect()
                cursor = connection.cursor()
                cursor.execute(
                    'UPDATE "Courses" SET "name_course" = %s, "course_description" = %s, "available_places" = %s, '
                    '"teacher_id" = %s '
                    'WHERE "course_id" = %s',
                    (new_name, new_description, new_available_places, teacher_id, course_id)
                )

                connection.commit()
                close_db_connect(connection, cursor)

                self.load_courses()
                self.clear_course_info()

        except Exception as e:
            error_message = f"Произошла ошибка при сохранении изменений: {e}\n\n"
            self.show_warning_message(error_message)

    def delete_course(self):
        if self.edit_course_button.text() == "Сохранить\nизменения":
            self.show_warning_message("Закончите редактирование перед удалением курса.")
            return
        try:
            if not self.courses_list.selectedItems():
                self.show_warning_message("Выберите курс для удаления.")
                return

            selected_item = self.courses_list.selectedItems()[0]
            course_id = selected_item.data(1)

            confirm_message = "Вы уверены, что хотите удалить этот курс?"
            confirm_result = QMessageBox.question(self, 'Подтверждение удаления', confirm_message,
                                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if confirm_result == QMessageBox.No:
                return

            connection = connect()
            cursor = connection.cursor()
            cursor.execute('DELETE FROM "Courses" WHERE "course_id" = %s', (course_id,))
            connection.commit()
            close_db_connect(connection, cursor)

            self.load_courses()
            self.clear_course_info()

        except Exception as e:
            print("Произошла ошибка при удалении курса:", e)

    def show_course_details(self, item):
        self.teacher_combo_box.show()

        course_id = item.data(1)

        connection = connect()
        cursor = connection.cursor()

        # Получаем информацию о курсе
        cursor.execute("SELECT * FROM \"Courses\" WHERE course_id = %s", (course_id,))
        course_details = cursor.fetchone()

        close_db_connect(connection, cursor)

        if course_details:
            course_id, name, description, available_places, teacher_id = course_details

            # Отображаем информацию о курсе
            self.course_name_edit.setText(name)
            self.course_description_edit.setText(description)
            self.available_places_edit.setText(str(available_places))

            # Отображаем информацию о преподавателе в комбобоксе
            if teacher_id:
                index = self.teacher_combo_box.findData(teacher_id)
                self.teacher_combo_box.setCurrentIndex(index)
            else:
                self.teacher_combo_box.setCurrentIndex(0)

    # Измените цикл в методе load_courses
    def load_courses(self):
        connection = connect()

        cursor = connection.cursor()
        cursor.execute('SELECT * FROM "Courses"')
        courses = cursor.fetchall()

        close_db_connect(connection, cursor)

        current_item = self.courses_list.currentItem()
        current_course_id = current_item.data(1) if current_item else None

        self.courses_list.clear()

        sorted_courses = sorted(courses, key=lambda x: x[0])

        for course_info in sorted_courses:
            item_text = f"{course_info[1]}"  # Изменение в этой строке, чтобы использовать правильные индексы
            item = QListWidgetItem(item_text)
            item.setData(1, course_info[0])
            self.courses_list.addItem(item)

        for i in range(self.courses_list.count()):
            item = self.courses_list.item(i)
            if item.data(1) == current_course_id:
                self.courses_list.setCurrentItem(item)
                break
