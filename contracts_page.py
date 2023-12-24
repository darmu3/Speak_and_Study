import os

from PyQt5.QtWidgets import QWidget, QListWidget, QTextBrowser, QListWidgetItem, QHBoxLayout, QLabel, QVBoxLayout
from conn_db import connect, close_db_connect
from docx import Document


class ContractsPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.initUI()
        self.load_contracts()

    def initUI(self):
        layout = QHBoxLayout()

        # Область со списком договоров
        contracts_list_layout = QVBoxLayout()
        self.contracts_list = QListWidget()
        self.contracts_list.itemClicked.connect(self.show_contract_details)
        contracts_list_layout.addWidget(self.contracts_list)

        # Область с подробной информацией о договоре
        contract_description_layout = QVBoxLayout()
        contract_details_label = QLabel("Подробная информация о договоре")
        self.contract_details_text = QTextBrowser()
        contract_description_layout.addWidget(contract_details_label)
        contract_description_layout.addWidget(self.contract_details_text)

        layout.addLayout(contracts_list_layout)
        layout.addLayout(contract_description_layout)

        self.setLayout(layout)

    def update_contracts(self):
        # Обновление списка договоров
        self.load_contracts()

    def showEvent(self, event):
        # Вызывается при каждом показе страницы
        self.update_contracts()

    def load_contracts(self):
        # Соединение с базой данных
        connection = connect()

        # Создание курсора для выполнения SQL-запросов
        cursor = connection.cursor()

        # Выборка договоров из базы данных с сортировкой по возрастанию
        cursor.execute('SELECT contract_id, contract_date, user_id, signed FROM "Contracts" ORDER BY contract_id ASC')
        contracts = cursor.fetchall()

        # Очистка списка договоров
        self.contracts_list.clear()

        # Добавление договоров в список
        for contract in contracts:
            contract_id, contract_date, user_id, signed = contract
            item = QListWidgetItem(f"№ Договора: {contract_id}, Дата подписания: {contract_date}, User ID: {user_id}")
            item.setData(1, contract_id)  # Сохраняем идентификатор договора как дополнительные данные
            item.setData(2, user_id)  # Сохраняем идентификатор пользователя как дополнительные данные
            self.contracts_list.addItem(item)

            # Check if the contract is signed but has no user_id, then delete it
            if signed and not user_id:
                self.remove_contract_and_request(contract_id)

        close_db_connect(connection, cursor)

    def show_contract_details(self, item):
        # Получение идентификатора договора и пользователя из дополнительных данных
        contract_id = item.data(1)
        user_id = item.data(2)

        # Получение подробной информации о договоре из базы данных
        connection = connect()

        cursor = connection.cursor()
        cursor.execute('SELECT contract_file FROM "Contracts" WHERE contract_id = %s', (contract_id,))
        contract_file = cursor.fetchone()[0]

        close_db_connect(connection, cursor)

        if contract_file:
            # Создание временного файла для сохранения бинарных данных
            temp_file_path = "C:/Users/Александр/PycharmProjects/Course_app/основные файлы/temp_contract.docx"
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(contract_file)

            # Загрузка документа из временного файла
            doc = Document(temp_file_path)

            # Отображение подробной информации
            details_text = ""
            for paragraph in doc.paragraphs:
                details_text += paragraph.text + "\n"

            self.contract_details_text.setPlainText(details_text)

            # Удаление временного файла после использования
            os.remove(temp_file_path)
        else:
            self.contract_details_text.clear()

    def remove_contract_and_request(self, contract_id):
        # Удаление договора и связанной заявки по contract_id
        connection = connect()

        cursor = connection.cursor()
        cursor.execute('DELETE FROM "Contracts" WHERE contract_id = %s', (contract_id,))
        connection.commit()

        close_db_connect(connection, cursor)
