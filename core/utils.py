from PyQt4 import QtGui, QtCore
import os


def center(self):
    """centers the window on the screen"""
    frameGm = self.frameGeometry()
    screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
    centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
    frameGm.moveCenter(centerPoint)
    self.move(frameGm.topLeft())


def background(self):  # defines the background for each window
    """providing the background info for each window"""

    # defining the directory filepaths
    self.PROJECT_DIR = os.path.dirname(os.path.abspath("__file__"))  # project directory
    self.IMG_DIR = os.path.join(self.PROJECT_DIR, 'img')  # image directory
    self.CORE_DIR = os.path.join(self.PROJECT_DIR, 'core')  # core directory
    self.SETTINGS_DIR = os.path.join(self.PROJECT_DIR, 'settings')  # settings directory
    if not os.path.exists(self.SETTINGS_DIR):
        os.mkdir(self.SETTINGS_DIR)

    # Acquiring information about geometry
    self.setWindowIcon(QtGui.QIcon(os.path.join(self.IMG_DIR, 'cumc-crown.png')))  # declaring the icon image
    self.deskW, self.deskH = QtGui.QDesktopWidget().availableGeometry().getRect()[2:]  # gets the window resolution
    # self.setWindowState(QtCore.Qt.WindowMaximized) # will maximize the GUI
    self.setGeometry(0, 0, self.deskW/2, self.deskH/2)  # Sets the window size, 800x460 is the size of our window
    # --- Reading in saved directory information ------

    # defining the filename that stores the directory information
    self.directory_settings = os.path.join(self.SETTINGS_DIR, 'directory.json')
    self.settings_fname = os.path.join(self.SETTINGS_DIR, 'settings.json')

    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('GTK+'))


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