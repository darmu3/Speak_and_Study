from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QPlainTextEdit, QListWidget, QWidget, QSizePolicy, QHBoxLayout, \
    QLabel

from conn_db import connect, close_db_connect


class ReportsPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout()

        reports_list_layout = QVBoxLayout()
        self.reports_list = QListWidget()
        self.reports_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        reports_list_layout.addWidget(self.reports_list)

        report_description_layout = QVBoxLayout()
        report_description_label = QLabel("Подробная информация об отчете")
        self.report_description = QPlainTextEdit()
        self.report_description.setReadOnly(True)
        self.report_description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        report_description_layout.addWidget(report_description_label)
        report_description_layout.addWidget(self.report_description)

        generate_report_button_layout = QVBoxLayout()
        generate_report_button = QPushButton("Составить отчет")
        generate_report_button.clicked.connect(self.generate_report)
        generate_report_button_layout.addWidget(generate_report_button)

        self.layout.addLayout(reports_list_layout)
        self.layout.addLayout(report_description_layout)
        self.layout.addLayout(generate_report_button_layout)

        self.setLayout(self.layout)

        self.load_reports_list()

    def generate_report(self):
        selected_report = self.reports_list.currentItem()

        if selected_report:
            if selected_report.text() == "Отчет о количестве заявок на курсы":
                report_data = self.get_report_data_courses()
            elif selected_report.text() == "Отчет о преподавателях и курсах, которые они ведут":
                report_data = self.get_report_data_teachers()
            elif selected_report.text() == "Отчет о возрастных группах заявителей на курсы":
                report_data = self.get_report_data_age_groups()
            elif selected_report.text() == "Отчет о рейтинге преподавателей":
                report_data = self.generate_teacher_rating_report()
            elif selected_report.text() == "Отчет о заполненности курсов":
                report_data = self.get_report_data_course_occupancy()
        else:
            report_data = "Выберите отчет для его составления."

        self.report_description.setPlainText(report_data)

    def load_reports_list(self):
        reports = ["Отчет о количестве заявок на курсы", "Отчет о преподавателях и курсах, которые они ведут",
                   "Отчет о возрастных группах заявителей на курсы", "Отчет о рейтинге преподавателей",
                   "Отчет о заполненности курсов"]
        self.reports_list.addItems(reports)

    def get_report_data_courses(self):
        connection = connect()
        cursor = connection.cursor()

        sql_query = """
        SELECT "Courses".course_id, "Courses".name_course, COUNT("Requests".request_id) AS num_requests
        FROM "Courses"
        LEFT JOIN "Requests" ON "Courses".course_id = "Requests".course_id
        GROUP BY "Courses".course_id, "Courses".name_course
        ORDER BY "Courses".course_id;
        """
        cursor.execute(sql_query)

        result = cursor.fetchall()

        close_db_connect(connection, cursor)

        report_text = f"Отчет о заявках на участие в курсах:\n\n"
        for row in result:
            course_id = row[0]
            course_name = row[1]
            num_requests = row[2]

            report_text += f"Курс: {course_id} - {course_name}, Количество заявок: {num_requests}\n\n"

        return report_text

    def get_report_data_teachers(self):
        connection = connect()
        cursor = connection.cursor()

        sql_query = '''
        SELECT "Teachers".teacher_id, "Teachers".first_name, "Teachers".second_name,
               STRING_AGG("Courses".name_course, ', ') AS courses_taught
        FROM "Teachers"
        LEFT JOIN "Courses" ON "Teachers".teacher_id = "Courses".teacher_id
        GROUP BY "Teachers".teacher_id, "Teachers".first_name, "Teachers".second_name;
        '''
        cursor.execute(sql_query)

        result = cursor.fetchall()

        close_db_connect(connection, cursor)

        report_text = f"Отчет о преподавателях и курсах, которые они ведут:\n\n"
        for row in result:
            teacher_id = row[0]
            teacher_first_name = row[1]
            teacher_second_name = row[2]
            course_name = row[3]

            report_text += f"Преподаватель: {teacher_id} - {teacher_first_name} {teacher_second_name}, Ведет курс: " \
                           f"{course_name}\n\n"

        return report_text

    def get_report_data_age_groups(self):
        connection = connect()
        cursor = connection.cursor()

        sql_query = """
        SELECT
            CASE
                WHEN "Requests".age <= 18 THEN 'До 18 лет'
                WHEN "Requests".age BETWEEN 19 AND 30 THEN '19-30 лет'
                WHEN "Requests".age BETWEEN 31 AND 40 THEN '31-40 лет'
                WHEN "Requests".age BETWEEN 41 AND 50 THEN '41-50 лет'
                ELSE 'Старше 50 лет'
            END AS age_group,
            COUNT("Requests".request_id) AS num_requests
        FROM
            "Requests"
        GROUP BY
            age_group
        ORDER BY
            age_group;
        """
        cursor.execute(sql_query)

        result = cursor.fetchall()

        close_db_connect(connection, cursor)

        report_text = f"Отчет о возрастных группах заявителей на курсы:\n\n"
        for row in result:
            age_group = row[0]
            num_requests = row[1]

            report_text += f"Возрастная группа: {age_group}, Количество заявок: {num_requests}\n\n"

        return report_text

    def generate_teacher_rating_report(self):
        connection = connect()
        cursor = connection.cursor()

        sql_query = '''
        SELECT "Courses".teacher_id, "Teachers".first_name, "Teachers".second_name,
               COUNT(DISTINCT "Courses".course_id) AS num_courses,
               COUNT(DISTINCT "Requests".request_id) AS num_requests
        FROM "Courses"
        LEFT JOIN "Teachers" ON "Courses".teacher_id = "Teachers".teacher_id
        LEFT JOIN "Requests" ON "Courses".course_id = "Requests".course_id
        WHERE "Courses".teacher_id IS NOT NULL
        GROUP BY "Courses".teacher_id, "Teachers".first_name, "Teachers".second_name
        ORDER BY num_courses DESC, num_requests DESC;
        '''
        cursor.execute(sql_query)

        result = cursor.fetchall()

        close_db_connect(connection, cursor)

        report_text = "Отчет о рейтинге преподавателей по количеству проводимых курсов и общему количеству " \
                      "заявок на курсы преподавателя:\n\n"
        for row in result:
            teacher_id = row[0]
            teacher_first_name = row[1]
            teacher_second_name = row[2]
            num_courses = row[3]
            num_requests = row[4]

            report_text += f"Учитель {teacher_id}: {teacher_first_name} {teacher_second_name}\n"
            report_text += f"Количество проведенных курсов: {num_courses}\n"
            report_text += f"Общее количество заявок на курсы преподавателя: {num_requests}\n\n"

        return report_text

    def get_report_data_course_occupancy(self):
        connection = connect()
        cursor = connection.cursor()

        sql_query = """
        SELECT "Courses".course_id, "Courses".name_course, COUNT("usercourses".user_id) AS num_students,
               "Courses".available_places
        FROM "Courses"
        LEFT JOIN "usercourses" ON "Courses".course_id = "usercourses".course_id
        GROUP BY "Courses".course_id, "Courses".name_course, "Courses".available_places
        ORDER BY "Courses".course_id;
        """
        cursor.execute(sql_query)

        result = cursor.fetchall()

        close_db_connect(connection, cursor)

        report_text = f"Отчет о заполненности курсов:\n\n"
        for row in result:
            course_id = row[0]
            course_name = row[1]
            num_students = row[2]
            available_places = row[3]

            occupancy_percentage = (num_students / available_places) * 100 if available_places > 0 else 0

            report_text += f"Курс: {course_id} - {course_name}\n"
            report_text += f"Количество студентов: {num_students}, Доступные места: {available_places}\n"
            report_text += f"Заполненность курса: {occupancy_percentage:.2f}%\n\n"

        return report_text
