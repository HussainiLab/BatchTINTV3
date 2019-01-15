from PyQt5 import QtGui, QtCore, QtWidgets
import os
import sys

project_name = 'BatchTINTV3'


def center(self):
    """centers the window on the screen"""
    frameGm = self.frameGeometry()
    screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
    centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
    frameGm.moveCenter(centerPoint)
    self.move(frameGm.topLeft())


def background(self):  # defines the background for each window
    """providing the background info for each window"""

    project_dir = os.path.dirname(os.path.abspath("__file__"))

    if os.path.basename(project_dir) != project_name:
        project_dir = os.path.dirname(sys.argv[0])

    # defining the directory filepaths
    self.PROJECT_DIR = project_dir  # project directory

    self.IMG_DIR = os.path.join(self.PROJECT_DIR, 'img')  # image directory
    # self.CORE_DIR = os.path.join(self.PROJECT_DIR, 'core')  # core directory
    self.SETTINGS_DIR = os.path.join(self.PROJECT_DIR, 'settings')  # settings directory
    if not os.path.exists(self.SETTINGS_DIR):
        os.mkdir(self.SETTINGS_DIR)

    # Acquiring information about geometry
    self.setWindowIcon(QtGui.QIcon(os.path.join(self.IMG_DIR, 'cumc-crown.png')))  # declaring the icon image
    self.deskW, self.deskH = QtWidgets.QDesktopWidget().availableGeometry().getRect()[2:]  # gets the window resolution
    # self.setWindowState(QtCore.Qt.WindowMaximized) # will maximize the GUI
    self.setGeometry(0, 0, self.deskW/2, self.deskH/2)  # Sets the window size, 800x460 is the size of our window
    # --- Reading in saved directory information ------

    # defining the filename that stores the directory information
    self.directory_settings = os.path.join(self.SETTINGS_DIR, 'directory.json')
    self.settings_fname = os.path.join(self.SETTINGS_DIR, 'settings.json')

    QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('GTK+'))


class Worker(QtCore.QObject):
    def __init__(self, function, *args, **kwargs):
        super(Worker, self).__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start.connect(self.run)

    start = QtCore.pyqtSignal(str)

    @QtCore.pyqtSlot()
    def run(self):
        self.function(*self.args, **self.kwargs)


def find_consec(data):
    """finds the consecutive numbers and outputs as a list"""
    consecutive_values = []  # a list for the output
    current_consecutive = [data[0]]

    if len(data) == 1:
        return [[data[0]]]

    for index in range(1, len(data)):

        if data[index] == data[index - 1] + 1:
            current_consecutive.append(data[index])

            if index == len(data) - 1:
                consecutive_values.append(current_consecutive)

        else:
            consecutive_values.append(current_consecutive)
            current_consecutive = [data[index]]

            if index == len(data) - 1:
                consecutive_values.append(current_consecutive)
    return consecutive_values


def print_msg(self, msg):

    if self is None:
        print(msg)
    else:
        self.LogAppend.myGUI_signal_str.emit(msg)
