# -*- coding: utf-8 -*-
"""
DicomModule

User Settings Dialog and associated IO functions
"""

# BUILT-IN MODULES
import sys
# import os
import json
# import queue
# THIRD-PARTY MODULES
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# LOCAL OR CUSTOM MODULES
# from EMNav_GUI import *
# from EMNav_Processor import *


class JSONSettingsInterface(QDialog):
    """ Basic settings dialog for JSON-based settings

    This class has:
        - Dialog Window
        - [Accept], [Restore Default], [Cancel] pushbuttons
        - Tab frame for organizing different settings

    This class does:
        - Populates tabs and form-rows
        - Converts specific item logic to dictionary
        - Converts dictionary to specific item logic
        - Converts JSON config file to dictionary
        - Converts dictionary to JSON config file

    """

    def __init__(self, userSettings=None, parent=None):
        """ create core functional widgets (save, cancel, etc) """
        super().__init__(parent=parent)

        if not bool(userSettings):
            userSettings = self.InitializeSettings()

        self.rootFile = r'./config.json'

        layout = QVBoxLayout()  # master layout
        bttnLayout = QHBoxLayout()
        okbttn = QPushButton("Accept Settings")
        okbttn.clicked.connect(self.acceptSettings)
        defbttn = QPushButton("Restore Defaults")
        defbttn.clicked.connect(self.restoreDefaults)
        clsbttn = QPushButton("Cancel")
        clsbttn.clicked.connect(self.close)
        bttnLayout.addStretch()
        bttnLayout.addWidget(okbttn)
        bttnLayout.addWidget(defbttn)
        bttnLayout.addWidget(clsbttn)

        # ADD TABS HERE
        self.TabFrame = QTabWidget()
        self.CreateSettingsTab(self.TabFrame)

        self.dict2field(userSettings=userSettings)

        layout.addWidget(self.TabFrame)
        layout.addLayout(bttnLayout)
        self.setLayout(layout)

        self.setWindowTitle("Settings")
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumSize(300, 300)
        self.resize(500, 550)

    def CreateSettingsTab(self, tabWidget):
        # Tab Maker
        self.createUserSettings(tabWidget)

    def createUserSettings(self, tab):
        userSettingsForm = QWidget()
        tab.addTab(userSettingsForm, "User Settings")
        layout = QFormLayout()
        layout.setVerticalSpacing(10)

        # Create widgets / setting interfaces here:
        self.com_port = QLineEdit("COM0")

        # Add rows to Layout for each settings widget:
        layout.addRow("COMPORT:", self.com_port)

        userSettingsForm.setLayout(layout)

    def acceptSettings(self):
        # if user decides to save changes to fields
        userSettings = self.field2dict()
        # re-place config file
        self.dict2json(userSettings, self.rootFile)
        self.close()

    def restoreDefaults(self):
        # pulls data from hard-coded settings
        userSettings = self.InitializeSettings()
        print("Settings: Default")
        self.dict2field(userSettings)

    def dict2field(self, userSettings={}):
        # Populate Fields with Dict Entries
        self.com_port.setText(str(userSettings['COM_PORT']))

    def field2dict(self):
        # Populate Dict from Field Entries
        userSettings = {}
        userSettings['COM_PORT'] = self.com_port.text()
        return userSettings

# ----- FUNCTIONAL METHODS ----------------------

    @staticmethod
    def json2dict(file='./config.json'):
        # method parses json file, writes dict and returns as UserSettings
        with open(file) as data_file:
            userSettings = json.load(data_file)
            data_file.close()
        print('Reading config.json')
        return userSettings

    @staticmethod
    def dict2json(userSettings={}, file='./config.json'):
        # method takes in dict of UserSettings and re-writes json config
        with open(file, 'w') as data_file:
            json.dump(userSettings, data_file,
                      sort_keys=True, indent=4)
            data_file.close()
        print('Writing config.json')

    @staticmethod
    def InitializeSettings():
        # if no files found initializes default settings and creates a
        # config.json file

        userSettings = {'COM_PORT': 0}      # Rate of Processor Refresh
        # write/ over-write (if user accepts defaults) config.json file
        # conFigdict2json(userSettings)

        return userSettings


if __name__ == "__main__":

    app = QApplication(sys.argv)
    try:
        US = JSONSettingsInterface.json2dict(r'./config.json')
    except:
        US = JSONSettingsInterface.InitializeSettings()
    form = JSONSettingsInterface(userSettings=US)
    form.show()
    sys.exit(app.exec_())
