
# -*- coding: utf-8 -*-
"""
Base GUI to be used in Python programs
(2016)
"""

# Built-In Modules
import sys
import os

# Third-Party Modules
from PyQt5 import QtCore, QtGui


class DicomGUI(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.createMainFrame()
        self.createMenu()
        self.createStatusBar()
        self.applyStyling()

    def onConnect(self):
        pass

    def onInit(self):
        pass

    def onStart(self):
        pass

    def onStop(self):
        pass

    def onSettings(self):
        pass

    def onAbout(self):
        pass

    def createMainFrame(self):
        # Define the main window / interface
        # self.viewWidget = EMViewWidget()
        # self.viewWidget
        # self.setCentralWidget(self.viewWidget)
        pass

    def createStatusBar(self):
        self.statusBar()

    def createMenu(self):
        self.toolbar = QtGui.QToolBar()
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)

        connect_action = self.mkAction('&Connect',
                                       shortcut='Ctrl+C',
                                       slot=self.onConnect,
                                       tip='Connect')
        init_action = self.mkAction('&Initialize',
                                    slot=self.onInit,
                                    tip='Initialize')
        start_action = self.mkAction('&Start',
                                     shortcut='Ctrl+M',
                                     slot=self.onStart,
                                     tip='Start')
        # stop_action = self.mkAction('&Stop',
        #                             shortcut='Ctrl+T',
        #                             slot=self.onStop,
        #                             tip='Stop')
        exit_action = self.mkAction('E&xit',
                                    slot=self.close,
                                    shortcut='Ctrl+X',
                                    tip='Exit')
        # for action in [start_action,
                       # stop_action,
                       # init_action]:
            # action.setEnabled(False)

        """ SETTINGS ACTIONS """
        settings_action = self.mkAction('User Settings',
                                        slot=self.onSettings,
                                        tip='Configure')

        """ HELP ACTIONS """
        about_action = self.mkAction("&About",
                                     shortcut='F1',
                                     slot=self.onAbout,
                                     tip='About')

        """ ADD TO MENUBAR """
        file_menu = self.file_menu = self.menuBar().addMenu("File")
        # view_menu = self.view_menu = self.menuBar().addMenu("View")
        settings_menu = self.settings_menu = self.menuBar().addMenu("Settings")
        help_menu = self.help_menu = self.menuBar().addMenu("Help")

        add_actions(file_menu,
                    (connect_action,
                     init_action,
                     None,
                     start_action,
                     # stop_action,
                     None,
                     exit_action))
        add_actions(settings_menu,
                    (settings_action,))
        add_actions(help_menu,

                    (about_action,))

        """ ADD TO TOOLBAR """
        add_actions(self.toolbar,
                    (start_action,
                     # stop_action,
                     None))

        self.connect_action = connect_action
        self.init_action = init_action
        self.start_action = start_action
        # self.stop_action = stop_action
        self.settings_action = settings_action
        self.about_action = about_action
        self.exit_action = exit_action

    @QtCore.pyqtSlot()
    def stbar(self, message, dur):
        # for catching signals to update msgbar
        self.statusBar().showMessage(message, dur)

    def mkAction(self, text, slot=None, shortcut=None,
                 icon=None, tip=None, checkable=False,
                 signal="triggered()"):

        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon(icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def applyStyling(self):
        pass

    def closeEvent(self, event):
        print("Closing the app")
        self.deleteLater()


def add_actions(target, actions, isCheckable=False):
    for action in actions:
        if action is None:
            target.addSeparator()
        else:
            target.addAction(action)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    form = DicomGUI()
    app.setActiveWindow(form)
    form.show()
    sys.exit(app.exec_())
