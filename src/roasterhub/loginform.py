import sys
import os
import platform
from pathlib import Path
from json import load as jload
import json

from PyQt5.QtWidgets import (QApplication, QPushButton, QLabel, QLineEdit, QGridLayout, QMessageBox, QDialog)
from artisanlib.dialogs import ArtisanResizeablDialog

if platform.system() == 'Linux':
    home = os.environ['HOME']
    usercrjson = Path(home + "/.rhub/usercr.json")
elif platform.system() == 'Windows':
    home = os.environ['HOMEPATH']
    usercrjson = Path(home + "/.rhub/usercr.json")

class LoginForm(ArtisanResizeablDialog):

    def __init__(self, parent=None, aw=None):
        super().__init__(parent, aw)
        self.setModal(True)
        self.setWindowTitle(QApplication.translate("Form Caption", "Roasterhub Config", None))
        self.resize(500, 220)

        layout = QGridLayout()

        label_name = QLabel('<font size="3"> Email </font>')
        self.lineEdit_username = QLineEdit()

        data = self.usercrjson_data()
        if data:
            self.lineEdit_username.setText(data['user'])

        self.lineEdit_username.setPlaceholderText('Enter Roasterhub email Account')
        layout.addWidget(label_name, 0, 0)
        layout.addWidget(self.lineEdit_username, 0, 1)

        label_password = QLabel('<font size="3"> Key </font>')
        self.lineEdit_password = QLineEdit()

        data = self.usercrjson_data()
        if data:
            self.lineEdit_password.setText(data['password'])

        self.lineEdit_password.setPlaceholderText('Enter Roasterhub Key')
        layout.addWidget(label_password, 1, 0)
        layout.addWidget(self.lineEdit_password, 1, 1)

        label_machineid = QLabel('<font size="3"> Machine id </font>')
        self.lineEdit_machineid = QLineEdit()

        data = self.usercrjson_data()
        if data:
            self.lineEdit_machineid.setText(data['data'])

        self.lineEdit_machineid.setPlaceholderText('Please enter your machine id')
        layout.addWidget(label_machineid, 2, 0)
        layout.addWidget(self.lineEdit_machineid, 2, 1)

        button_login = QPushButton('Save')
        button_login.clicked.connect(self.save_to_disk)
        layout.addWidget(button_login, 3, 0, 1, 2)
        layout.setRowMinimumHeight(2, 75)

        self.setLayout(layout)

        # data to proced
        self.exitdialognapp = False

    def check_password(self):
        msg = QMessageBox()

        if self.lineEdit_username.text() is not None and self.lineEdit_password.text() is not None:
            msg.setText('Success')
            msg.exec_()
            self.close()
        else:
            msg.setText('Incorrect Password')
            msg.exec_()

    def usercrjson_data(self):
        if usercrjson.is_file():
            with open(usercrjson) as f:
                return jload(f)
        return None

    def save_to_disk(self):
        msg = QMessageBox()
        data = self.usercrjson_data()
        if self.lineEdit_username.text() is not None and self.lineEdit_password.text() is not None:

            data_to_save = {
                'user': self.lineEdit_username.text().replace(" ", ""),
                'password': self.lineEdit_password.text().replace(" ", ""),
                'data': self.lineEdit_machineid.text().replace(" ", ""),
            }

            json_data_to_save = json.dumps(data_to_save)
            f = open(usercrjson, "w")
            f.write(json_data_to_save)
            f.close()

            msg.setText('Roasterhub Will close this app, after that please launch manually!')
            msg.exec_()
            self.close()
            self.exitdialognapp = True
        else:
            msg.setText('Empty Form')
            msg.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    form = LoginForm()
    form.show()

    sys.exit(app.exec_())