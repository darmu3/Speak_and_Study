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
        self.load_contracts()

    def showEvent(self, event):
        # Вызывается при каждом показе страницы
        self.update_contracts()

    def load_contracts(self):
        connection = connect()

        cursor = connection.cursor()

        cursor.execute('SELECT contract_id, contract_date, user_id, signed FROM "Contracts" ORDER BY contract_id ASC')
        contracts = cursor.fetchall()

        self.contracts_list.clear()

        for contract in contracts:
            contract_id, contract_date, user_id, signed = contract
            item = QListWidgetItem(f"№ Договора: {contract_id}, Дата подписания: {contract_date}, User ID: {user_id}")
            item.setData(1, contract_id)
            self.contracts_list.addItem(item)

            if signed and not user_id:
                self.remove_contract_and_request(contract_id)

        close_db_connect(connection, cursor)

    def show_contract_details(self, item):
        contract_id = item.data(1)

        connection = connect()

        cursor = connection.cursor()
        cursor.execute('SELECT contract_file FROM "Contracts" WHERE contract_id = %s', (contract_id,))
        contract_file = cursor.fetchone()[0]

        close_db_connect(connection, cursor)

        if contract_file:
            temp_file_path = "C:/Users/Александр/PycharmProjects/Course_app/основные файлы/temp_contract.docx"
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(contract_file)

            doc = Document(temp_file_path)

            details_text = ""
            for paragraph in doc.paragraphs:
                details_text += paragraph.text + "\n"

            self.contract_details_text.setPlainText(details_text)

            os.remove(temp_file_path)
        else:
            self.contract_details_text.clear()

    def remove_contract_and_request(self, contract_id):
        connection = connect()

        cursor = connection.cursor()
        cursor.execute('DELETE FROM "Contracts" WHERE contract_id = %s', (contract_id,))
        connection.commit()

        close_db_connect(connection, cursor)
