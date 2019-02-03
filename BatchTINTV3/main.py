import sys, json, datetime, os, time
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from core.utils import center, background, Worker, find_consec
from core.settings import Settings_Window
from core.smtpSettings import SmtpSettings, AddExpter, add_Expter
from core.KlustaFunctions import klusta, check_klusta_ready, folder_ready, find_tetrodes, session_analyzable
from core.ChooseDirectory import chooseDirectory

_author_ = "Geoffrey Barrett"  # defines myself as the author

Large_Font = ("Verdana", 12)  # defines two fonts for different purposes (might not be used
Small_Font = ("Verdana", 8)


class Window(QtWidgets.QWidget):  # defines the window class (main window)

    def __init__(self):  # initializes the main window
        super(Window, self).__init__()
        # self.setGeometry(50, 50, 500, 300)
        background(self)  # acquires some features from the background function we defined earlier
        self.setWindowTitle("BatchTINT - Main Window")  # sets the title of the window

        self.numCores = str(os.cpu_count())  # initializing the number of cores the users CPU has

        self.RepeatAddSessionsThread = QtCore.QThread(self)
        self.BatchTintThread = QtCore.QThread()
        self.reset_add_thread = False
        self.repeat_thread_active = False

        self.current_session = ''
        self.current_subdirectory = ''
        self.LogAppend = Communicate()
        self.LogAppend.myGUI_signal_str.connect(self.AppendLog)

        self.LogError = Communicate()
        self.LogError.myGUI_signal_str.connect(self.raiseError)

        self.RemoveQueueItem = Communicate()
        self.RemoveQueueItem.myGUI_signal_str.connect(self.takeTopLevel)

        self.RemoveSessionItem = Communicate()
        self.RemoveSessionItem.myGUI_signal_str.connect(self.takeChild)

        self.RemoveSessionData = Communicate()
        self.RemoveSessionData.myGUI_signal_str.connect(self.takeChildData)

        self.RemoveChildItem = Communicate()
        self.RemoveChildItem.myGUI_signal_QTreeWidgetItem.connect(self.removeChild)

        self.adding_session = True
        self.reordering_queue = False

        self.choice = ''
        self.home()  # runs the home function

    def home(self):  # defines the home function (the main window)

        try:  # attempts to open previous directory catches error if file not found
            # No saved directory's need to create file
            with open(self.directory_settings, 'r+') as filename:  # opens the defined file
                directory_data = json.load(filename)  # loads the directory data from file
                if os.path.exists(directory_data['directory']):
                    current_directory_name = directory_data['directory']  # defines the data
                else:
                    current_directory_name = 'No Directory Currently Chosen!'  # states that no directory was chosen

        except FileNotFoundError:  # runs if file not found
            with open(self.directory_settings, 'w') as filename:  # opens a file
                current_directory_name = 'No Directory Currently Chosen!'  # states that no directory was chosen
                directory_data = {'directory': current_directory_name}  # creates a dictionary
                json.dump(directory_data, filename)  # writes the dictionary to the file

        # ---------------logo --------------------------------

        cumc_logo = QtWidgets.QLabel(self)  # defining the logo image
        logo_fname = os.path.join(self.IMG_DIR, "BatchKlustaLogo.png")  # defining logo pathname
        im2 = Image.open(logo_fname)  # opening the logo with PIL
        logowidth, logoheight = im2.size  # acquiring the logo width/height
        logo_pix = QtGui.QPixmap(logo_fname)  # getting the pixmap
        cumc_logo.setPixmap(logo_pix)  # setting the pixmap
        cumc_logo.setGeometry(0, 0, logowidth, logoheight)  # setting the geometry

        # ------buttons ------------------------------------------
        quitbtn = QtWidgets.QPushButton('Quit', self)  # making a quit button
        quitbtn.clicked.connect(self.close_app)  # defining the quit button functionality (once pressed)
        quitbtn.setShortcut("Ctrl+Q")  # creates shortcut for the quit button
        quitbtn.setToolTip('Click to quit Batch-Tint!')

        self.setbtn = QtWidgets.QPushButton('Klusta Settings')  # Creates the settings pushbutton
        self.setbtn.setToolTip('Define the settings that KlustaKwik will use.')

        self.klustabtn = QtWidgets.QPushButton('Run', self)  # creates the batch-klusta pushbutton
        self.klustabtn.setToolTip('Click to perform batch analysis via Tint and KlustaKwik!')

        self.smtpbtn = QtWidgets.QPushButton('SMTP Settings', self)
        self.smtpbtn.setToolTip("Click to change the SMTP settings for e-mail notifications.")

        self.choose_dir = QtWidgets.QPushButton('Choose Directory', self)  # creates the choose directory pushbutton

        self.current_directory = QtWidgets.QLineEdit()  # creates a line edit to display the chosen directory (current)
        self.current_directory.textChanged.connect(self.change_directory)
        self.current_directory.setText(current_directory_name)  # sets the text to the current directory
        self.current_directory.setAlignment(QtCore.Qt.AlignHCenter)  # centers the text
        self.current_directory.setToolTip('The current directory that Batch-Tint will analyze.')

        # defines an attribute to exchange info between classes/modules
        self.current_directory_name = current_directory_name

        # defines the button functionality once pressed
        self.klustabtn.clicked.connect(lambda: self.run(self.current_directory_name))

        # ------------------------------------ check box  ------------------------------------------------
        self.nonbatch_check = QtWidgets.QCheckBox('Non-Batch?')
        self.nonbatch_check.setToolTip("Check this if you don't want to run batch. This means you will choose\n"
                                       "the folder that directly contains all the session files (.set, .pos, .N, etc.).")
        self.nonbatch = 0

        self.silent_cb = QtWidgets.QCheckBox('Run Silently')
        self.silent_cb.setToolTip("Check if you want Tint to run in the background.")

        # ---------------- queue widgets --------------------------------------------------
        self.directory_queue = QtWidgets.QTreeWidget()
        self.directory_queue.headerItem().setText(0, "Axona Sessions:")
        self.directory_queue.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        directory_queue_label = QtWidgets.QLabel('Queue: ')

        self.up_btn = QtWidgets.QPushButton("Move Up", self)
        self.up_btn.setToolTip("Clcik this button to move selected directories up on the queue!")
        self.up_btn.clicked.connect(lambda: self.moveQueue('up'))

        self.down_btn = QtWidgets.QPushButton("Move Down", self)
        self.down_btn.setToolTip("Clcik this button to move selected directories down on the queue!")
        self.down_btn.clicked.connect(lambda: self.moveQueue('down'))

        queue_btn_layout = QtWidgets.QVBoxLayout()
        queue_btn_layout.addWidget(self.up_btn)
        queue_btn_layout.addWidget(self.down_btn)

        queue_layout = QtWidgets.QVBoxLayout()
        queue_layout.addWidget(directory_queue_label)
        queue_layout.addWidget(self.directory_queue)

        queue_and_btn_layout = QtWidgets.QHBoxLayout()
        queue_and_btn_layout.addLayout(queue_layout)
        queue_and_btn_layout.addLayout(queue_btn_layout)

        # ------------------------ multithreading widgets -------------------------------------

        Multithread_l = QtWidgets.QLabel('Simultaneous Tetrodes (#):')
        Multithread_l.setToolTip('Input the number of tetrodes you want to analyze simultaneously')

        self.numThreads = QtWidgets.QLineEdit()

        Multi_layout = QtWidgets.QHBoxLayout()

        # for order in [self.multithread_cb, core_num_l, self.core_num, Multithread_l, self.numThreads]:
        for order in [Multithread_l, self.numThreads]:
            if 'Layout' in order.__str__():
                Multi_layout.addLayout(order)
            else:
                Multi_layout.addWidget(order, 0, QtCore.Qt.AlignCenter)

        checkbox_layout = QtWidgets.QHBoxLayout()
        checkbox_layout.addStretch(1)
        checkbox_layout.addWidget(self.nonbatch_check)
        checkbox_layout.addStretch(1)
        checkbox_layout.addWidget(self.silent_cb)
        checkbox_layout.addStretch(1)
        checkbox_layout.addLayout(Multi_layout)
        checkbox_layout.addStretch(1)

        try:
            with open(self.settings_fname, 'r+') as filename:
                settings = json.load(filename)
                self.numThreads.setText(str(settings['NumThreads']))
                if settings['Silent'] == 1:
                    self.silent_cb.toggle()
                if settings['nonbatch'] == 1:
                    self.nonbatch_check.toggle

        except FileNotFoundError:
            self.silent_cb.toggle()
            self.numThreads.setText('1')

        # ------------- Log Box -------------------------
        self.Log = QtWidgets.QTextEdit()
        log_label = QtWidgets.QLabel('Log: ')

        log_lay = QtWidgets.QVBoxLayout()
        log_lay.addWidget(log_label, 0, QtCore.Qt.AlignTop)
        log_lay.addWidget(self.Log)

        # ------------------------------------ version information -------------------------------------------------
        # finds the modification date of the program
        try:
            mod_date = time.ctime(os.path.getmtime(__file__))
        except:
            mod_date = time.ctime(os.path.getmtime(os.path.join(self.PROJECT_DIR, "BatchSort.exe")))

        # creates a label with that information
        vers_label = QtWidgets.QLabel("BatchTINT V3.0 - Last Updated: " + mod_date)

        # ------------------- page layout ----------------------------------------
        layout = QtWidgets.QVBoxLayout()  # setting the layout

        layout1 = QtWidgets.QHBoxLayout()  # setting layout for the directory options
        layout1.addWidget(self.choose_dir)  # adding widgets to the first tab
        layout1.addWidget(self.current_directory)

        btn_order = [self.klustabtn, self.setbtn, self.smtpbtn, quitbtn]  # defining button order (left to right)
        btn_layout = QtWidgets.QHBoxLayout()  # creating a widget to align the buttons
        for butn in btn_order:  # adds the buttons in the proper order
            btn_layout.addWidget(butn)

        layout_order = [cumc_logo, layout1, checkbox_layout, queue_and_btn_layout, log_lay, btn_layout]

        layout.addStretch(1)  # adds the widgets/layouts according to the order
        for order in layout_order:
            if 'Layout' in order.__str__():
                layout.addLayout(order)
                layout.addStretch(1)
            else:
                layout.addWidget(order, 0, QtCore.Qt.AlignCenter)
                layout.addStretch(1)

        layout.addStretch(1)  # adds stretch to put the version info at the bottom
        layout.addWidget(vers_label)  # adds the date modification/version number
        self.setLayout(layout)  # sets the widget to the one we defined

        center(self)  # centers the widget on the screen

        self.show()  # shows the widget

        # if self.current_directory_name != 'No Directory Currently Chosen!':
        # starting adding any existing sessions in a different thread
        # self.RepeatAddSessionsThread = QtCore.QThread(self)
        self.RepeatAddSessionsThread.start()
        self.RepeatAddSessionsWorker = Worker(RepeatAddSessions, self)
        self.RepeatAddSessionsWorker.moveToThread(self.RepeatAddSessionsThread)
        self.RepeatAddSessionsWorker.start.emit("start")

    def run(self, directory):  # function that runs klustakwik

        """This method runs when the Batch-TINT button is pressed on the GUI,
        and commences the analysis"""
        self.batch_tint = True
        self.klustabtn.setText('Stop')
        self.klustabtn.setToolTip('Click to stop Batch-Tint.')  # defining the tool tip for the start button
        self.klustabtn.clicked.disconnect()
        self.klustabtn.clicked.connect(self.stopBatch)

        # self.BatchTintThread = QtCore.QThread()
        self.BatchTintThread.start()

        self.BatchTintWorker = Worker(runGUI, self, directory)
        self.BatchTintWorker.moveToThread(self.BatchTintThread)
        self.BatchTintWorker.start.emit("start")

    def close_app(self):
        # pop up window that asks if you really want to exit the app ------------------------------------------------

        choice = QtWidgets.QMessageBox.question(self, "Quitting BatchTINT",
                                                "Do you really want to exit?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()  # tells the app to quit
        else:
            pass

    def raiseError(self, error_val):
        """raises an error window given certain errors from an emitted signal"""

        if 'ManyFet' in error_val:
            self.choice = QtWidgets.QMessageBox.question(self, "No Chosen Directory: BatchTINT",
                                                         "You have chosen more than four features,\n"
                                                         "clustering will take a long time.\n"
                                                         "Do you realy want to continue?",
                                                         QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)

        elif 'NoDir' in error_val:
            self.choice = QtWidgets.QMessageBox.question(self, "No Chosen Directory: BatchTINT",
                                                         "You have not chosen a directory,\n"
                                                         "please choose one to continue!",
                                                         QtWidgets.QMessageBox.Ok)

        elif 'GoogleDir' in error_val:
            self.choice = QtWidgets.QMessageBox.question(self, "Google Drive Directory: BatchTINT",
                                                         "You have not chosen a directory within Google Drive,\n"
                                                         "be aware that during testing we have experienced\n"
                                                         "permissions errors while using Google Drive directories\n"
                                                         "that would result in BatchTINTV3 not being able to move\n"
                                                         "the files to the Processed folder (and stopping the GUI),\n"
                                                         "do you want to continue?",
                                                         QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        elif 'NoSet' in error_val:
            self.choice = QtWidgets.QMessageBox.question(self, "No .Set Files!",
                                                         "You have chosen a directory that has no .Set files!\n"
                                                         "Please choose a different directory!",
                                                         QtWidgets.QMessageBox.Ok)

        elif 'InvDirBatch' in error_val:
            self.choice = QtWidgets.QMessageBox.question(self, "Invalid Directory!",
                                                         "In 'Batch Mode' you need to choose a directory\n"
                                                         "with subdirectories that contain all your Tint\n"
                                                         "files. Press Abort and choose new file, or if you\n"
                                                         "plan on adding folders to the chosen directory press\n"
                                                         "continue.",
                                                         QtWidgets.QMessageBox.Abort | QtWidgets.QMessageBox.Ok)
        elif 'InvDirNonBatch' in error_val:
            self.choice = QtWidgets.QMessageBox.question(self, "Invalid Directory!",
                                                         "In 'Non-Batch Mode' you need to choose a directory\n"
                                                         "that contain all your Tint files.\n",
                                                         QtWidgets.QMessageBox.Ok)

    def AppendLog(self, message):
        """
        A function that will append the Log field of the main window (mainly
        used as a slot for a custom pyqt signal)
        """
        self.Log.append(message)

    def stopBatch(self):
        self.klustabtn.clicked.connect(lambda: self.run(self.current_directory_name))
        self.BatchTintThread.terminate()

        self.LogAppend.myGUI_signal_str.emit(
            '[%s %s]: BatchTint stopped!' % (str(datetime.datetime.now().date()),
                                             str(datetime.datetime.now().time())[
                                             :8]))

        self.batch_tint = False
        self.klustabtn.setText('Run')
        self.klustabtn.setToolTip(
            'Click to perform batch analysis via Tint and KlustaKwik!')  # defining the tool tip for the start button

    def change_directory(self):
        """
        Whenever directory is changed, clear the directory queue
        """
        self.current_directory_name = self.current_directory.text()

        try:
            self.directory_queue.clear()
        except AttributeError:
            pass

        self.restart_add_sessions_thread()

    def restart_add_sessions_thread(self):

        self.reset_add_thread = True

        if not hasattr(self, 'repeat_thread_active'):
            return

        while self.repeat_thread_active:
            time.sleep(0.1)

        # self.reset_add_thread = False
        # self.RepeatAddSessionsThread = QtCore.QThread()
        self.RepeatAddSessionsThread.setTerminationEnabled(True)
        self.RepeatAddSessionsThread.start()

        self.RepeatAddSessionsWorker = Worker(RepeatAddSessions, self)
        self.RepeatAddSessionsWorker.moveToThread(self.RepeatAddSessionsThread)
        self.RepeatAddSessionsWorker.start.emit("start")

    def moveQueue(self, direction):
        """This method is not threaded"""
        # get all the queue items

        while self.adding_session:
            if self.reordering_queue:
                self.reordering_queue = False
            time.sleep(0.1)

        time.sleep(0.1)
        self.reordering_queue = True

        item_count = self.directory_queue.topLevelItemCount()
        queue_items = {}
        for item_index in range(item_count):
            queue_items[item_index] = self.directory_queue.topLevelItem(item_index)

        # get selected options and their locations
        selected_items = self.directory_queue.selectedItems()
        selected_items_copy = []
        [selected_items_copy.append(item.clone()) for item in selected_items]

        add_to_new_queue = list(queue_items.values())

        if not selected_items:
            # skips when there are no items selected
            return

        new_queue_order = {}

        # find if consecutive indices from 0 on are selected as these won't move any further up

        indices = find_keys(queue_items, selected_items)
        consecutive_indices = find_consec(indices)
        # this will spit a list of lists, these nested lists will have consecutive indices within them
        # i.e. if indices 0, 1 and 3 were chosen it would have [[0, 1], [3]]

        if 'up' in direction:
            # first add the selected items to their new spots
            for consecutive in consecutive_indices:
                if 0 in consecutive:
                    # these items can't move up any further
                    for index in consecutive:
                        new_item = queue_items[index].clone()
                        new_queue_order[index] = new_item

                else:
                    for index in consecutive:
                        # move these up the list (decrease in index value since 0 is the top of the list)
                        new_item = queue_items[index].clone()
                        new_queue_order[index - 1] = new_item

            for key, val in new_queue_order.items():
                for index, item in enumerate(add_to_new_queue):
                    if val.data(0, 0) == item.data(0, 0):
                        add_to_new_queue.remove(item)  # remove item from the list
                        break

            _ = list(new_queue_order.keys())  # a list of already moved items

            # place the unplaced items that aren't moving
            for static_index, static_value in queue_items.items():
                # print(static_value.data(0,0))
                # place the unplaced items
                if static_index in _:
                    continue

                for queue_item in new_queue_order.values():
                    not_in_reordered = True
                    if static_value.data(0, 0) == queue_item.data(0, 0):
                        # don't re-add the one that is going to be moved
                        not_in_reordered = False
                        break

                if not_in_reordered:
                    for value in add_to_new_queue:
                        if static_value.data(0, 0) == value.data(0, 0):
                            add_to_new_queue.remove(value)  # remove item from the list
                            break

                    new_queue_order[static_index] = static_value.clone()

        elif 'down' in direction:
            # first add the selected items to their new spots
            for consecutive in consecutive_indices:
                if (item_count - 1) in consecutive:
                    # these items can't move down any further
                    for index in consecutive:
                        new_item = queue_items[index].clone()
                        # new_item.setSelected(True)
                        new_queue_order[index] = new_item
                else:
                    for index in consecutive:
                        # move these down the list (increase in index value since 0 is the top of the list)
                        new_item = queue_items[index].clone()
                        # new_item.setSelected(True)
                        new_queue_order[index + 1] = new_item

            for key, val in new_queue_order.items():
                for index, item in enumerate(add_to_new_queue):
                    if val.data(0, 0) == item.data(0, 0):
                        add_to_new_queue.remove(item)
                        break

            _ = list(new_queue_order.keys())  # a list of already moved items

            # place the unplaced items that aren't moving
            for static_index, static_value in queue_items.items():
                if static_index in _:
                    continue

                for queue_item in new_queue_order.values():
                    not_in_reordered = True
                    if static_value.data(0, 0) == queue_item.data(0, 0):
                        # don't re-add the one that is going to be moved
                        not_in_reordered = False
                        break

                if not_in_reordered:
                    for value in add_to_new_queue:
                        if static_value.data(0, 0) == value.data(0, 0):
                            add_to_new_queue.remove(value)  # remove item from the list
                            break

                    new_queue_order[static_index] = static_value.clone()

        # add the remaining items
        indices_needed = [index for index in range(item_count) if index not in list(new_queue_order.keys())]
        for index, displaced_item in enumerate(add_to_new_queue):
            new_queue_order[indices_needed[index]] = displaced_item.clone()

        self.directory_queue.clear()  # clears the list

        for key, value in sorted(new_queue_order.items()):
            self.directory_queue.addTopLevelItem(value)

        # reselect the items
        iterator = QtWidgets.QTreeWidgetItemIterator(self.directory_queue)
        while iterator.value():
            for selected_item in selected_items_copy:
                item = iterator.value()
                if item.data(0, 0) == selected_item.data(0, 0):
                    item.setSelected(True)
                    break
            iterator += 1
        self.reordering_queue = False

    def takeTopLevel(self, item_count):
        item_count = int(item_count)
        self.directory_queue.takeTopLevelItem(item_count)
        self.top_level_taken = True

    def setChild(self, child_count):
        self.child_session = self.directory_item.child(int(child_count))
        self.child_set = True

    def takeChild(self, child_count):
        self.child_session = self.directory_item.takeChild(int(child_count))
        self.child_taken = True
        # return child_session

    def takeChildData(self, child_count):
        self.child_session = self.directory_item.takeChild(int(child_count)).data(0, 0)
        self.child_data_taken = True

    def removeChild(self, QTreeWidgetItem):
        root = self.directory_queue.invisibleRootItem()
        (QTreeWidgetItem.parent() or root).removeChild(QTreeWidgetItem)
        self.child_removed = True


def find_keys(my_dictionary, value):
    """finds a key for a given value of a dictionary"""
    key = []
    if not isinstance(value, list):
        value = [value]
    [key.append(list(my_dictionary.keys())[list(my_dictionary.values()).index(val)]) for val in value]
    return key


@QtCore.pyqtSlot()
def raise_window(new_window, old_window):
    """ raise the current window"""
    if 'Choose' in str(new_window):
        new_window.raise_()
        new_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        new_window.show()
        time.sleep(0.1)

    elif "Choose" in str(old_window):
        time.sleep(0.1)
        old_window.hide()
        return
    else:
        new_window.raise_()
        new_window.show()
        time.sleep(0.1)
        old_window.hide()


@QtCore.pyqtSlot()
def cancel_window(new_window, old_window):
    """ raise the current window"""
    new_window.raise_()
    new_window.show()
    time.sleep(0.1)
    old_window.hide()

    if 'SmtpSettings' in str(new_window) and 'AddExpter' in str(old_window):  # needs to clear the text files
        old_window.expter_edit.setText('')
        old_window.email_edit.setText('')


def new_directory(self, main):
    """This method will look open a dialog and prompt the user to select a directory,"""
    current_directory_name = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
    self.current_directory_e.setText(current_directory_name)


def addSessions(self):
    while self.reordering_queue:
        # pauses add Sessions when the individual is reordering
        time.sleep(0.1)

    current_directory = os.path.realpath(self.current_directory_name)
    if self.nonbatch == 0:
        # finds the sub directories within the chosen directory
        sub_directories = [d for d in os.listdir(current_directory)
                           if os.path.isdir(os.path.join(current_directory, d)) and
                           d not in ['Processed', 'Converted']]  # finds the subdirectories within each folder

    else:
        # current_directory = os.path.dirname(self.current_directory_name)
        sub_directories = [os.path.basename(current_directory)]
        current_directory = os.path.dirname(current_directory)

    # find items already in the queue
    added_directories = []

    # iterating through queue items
    iterator = QtWidgets.QTreeWidgetItemIterator(self.directory_queue)
    while iterator.value():
        directory_item = iterator.value()

        # check if directory still exists
        if not os.path.exists(os.path.join(current_directory, directory_item.data(0, 0))) and \
                '.set' not in directory_item.data(0, 0):
            # then remove from the list since it doesn't exist anymore
            root = self.directory_queue.invisibleRootItem()
            for child_index in range(root.childCount()):
                if root.child(child_index) == directory_item:
                    self.RemoveChildItem.myGUI_signal_QTreeWidgetItem.emit(directory_item)
                    # root.removeChild(directory_item)
        else:
            added_directories.append(directory_item.data(0, 0))

        iterator += 1

    for directory in sub_directories:

        try:
            set_files = [file for file in os.listdir(os.path.join(current_directory, directory))
                         if '.set' in file and
                         not os.path.isdir(os.path.join(current_directory, directory, file))]
        except FileNotFoundError:
            return

        if set_files:
            if directory in added_directories:
                # add sessions that aren't already added

                # find the treewidget item
                iterator = QtWidgets.QTreeWidgetItemIterator(self.directory_queue)
                while iterator.value():
                    directory_item = iterator.value()
                    if directory_item.data(0, 0) == directory:
                        break
                    iterator += 1

                # find added sessions
                added_sessions = []
                try:
                    iterator = QtWidgets.QTreeWidgetItemIterator(directory_item)
                except UnboundLocalError:
                    # print('hello')
                    return
                except RuntimeError:
                    return

                while iterator.value():
                    session_item = iterator.value()
                    added_sessions.append(session_item.data(0, 0))
                    iterator += 1

                for set_file in set_files:
                    # find all the tetrodes for that set file
                    tetrodes = find_tetrodes(set_file, os.path.join(current_directory,
                                                                    directory))

                    # check if all the tetrodes within that set file have been analyzed
                    analyzable = session_analyzable(os.path.join(current_directory, directory),
                                                    set_file, tetrodes)

                    if analyzable:
                        # add session
                        if set_file not in added_sessions and set_file != self.current_session:
                            session_item = QtWidgets.QTreeWidgetItem()
                            session_item.setText(0, set_file)
                            directory_item.addChild(session_item)
                    else:
                        pass

            else:

                # add all the sessions within this directory
                directory_item = QtWidgets.QTreeWidgetItem()
                directory_item.setText(0, directory)

                if set_files:
                    for set_file in set_files:
                        if set_file == self.current_session:
                            continue

                        tetrodes = find_tetrodes(set_file, os.path.join(current_directory,
                                                                        directory))  # find all the tetrodes for that set file

                        # check if all the tetrodes within that set file have been analyzed
                        analyzable = session_analyzable(os.path.join(current_directory, directory),
                                                        set_file, tetrodes)

                        if analyzable:
                            # add session
                            session_item = QtWidgets.QTreeWidgetItem()
                            session_item.setText(0, set_file)
                            directory_item.addChild(session_item)

                            self.directory_queue.addTopLevelItem(directory_item)
                else:
                    pass


def silent(self, state):
    with open(self.settings_fname, 'r+') as filename:
        settings = json.load(filename)
        if state:
            settings['Silent'] = 1
        else:
            settings['Silent'] = 0
    with open(self.settings_fname, 'w') as filename:
        json.dump(settings, filename)


class Communicate(QtCore.QObject):
    """A custom pyqtsignal so that errors and popups can be called from the threads
    to the main window"""
    myGUI_signal_str = QtCore.pyqtSignal(str)
    myGUI_signal_QTreeWidgetItem = QtCore.pyqtSignal(QtWidgets.QTreeWidgetItem)


def nonbatch(self, state):
    self.directory_queue.clear()
    self.restart_add_sessions_thread()

    with open(self.settings_fname, 'r+') as filename:
        settings = json.load(filename)
        if state:
            settings['nonbatch'] = 1
            self.nonbatch = 1
        else:
            settings['nonbatch'] = 0
            self.nonbatch = 0
    with open(self.settings_fname, 'w') as filename:
        json.dump(settings, filename)


def runGUI(main_window, directory):
    """This method is executed when you press 'Run' in the GUI."""
    # ------- making a function that runs the entire GUI ----------

    with open(main_window.settings_fname, 'r+') as f:  # opens setting file
        settings = json.load(f)  # loads settings

    # checks if the settings are appropriate to run analysis
    klusta_ready = check_klusta_ready(settings, directory, self=main_window,
                                      settings_filename=main_window.settings_fname,
                                      numThreads=main_window.numThreads.text(),
                                      numCores=main_window.numCores)

    if klusta_ready:

        main_window.LogAppend.myGUI_signal_str.emit(
            '[%s %s]: Analyzing the following directory: %s!' % (str(datetime.datetime.now().date()),
                                                                 str(datetime.datetime.now().time())[
                                                                 :8], directory))

        if main_window.nonbatch == 0:
            # message that shows how many files were found
            main_window.LogAppend.myGUI_signal_str.emit(
                '[%s %s]: Found %d sub-directories in the directory!' % (str(datetime.datetime.now().date()),
                                                                         str(datetime.datetime.now().time())[
                                                                         :8],
                                                                         main_window.directory_queue.topLevelItemCount()))

        else:
            directory = os.path.dirname(directory)

        if main_window.directory_queue.topLevelItemCount() == 0:
            if main_window.nonbatch == 1:
                main_window.choice = ''
                main_window.LogError.myGUI_signal_str.emit('InvDirNonBatch')
                while main_window.choice == '':
                    time.sleep(0.2)
                main_window.stopBatch()
                return
            else:
                main_window.choice = ''
                main_window.LogError.myGUI_signal_str.emit('InvDirBatch')
                while main_window.choice == '':
                    time.sleep(0.2)

                if main_window.choice == QtWidgets.QMessageBox.Abort:
                    main_window.stopBatch()
                    return

        # ----------- cycle through each file and find the tetrode files ------------------------------------------
        # for sub_directory in sub_directories:  # finding all the folders within the directory

        while main_window.batch_tint:

            main_window.directory_item = main_window.directory_queue.topLevelItem(0)

            if not main_window.directory_item:
                continue
            else:
                main_window.current_subdirectory = main_window.directory_item.data(0, 0)

                # check if the directory exists, if not, remove it

                if not os.path.exists(os.path.join(directory, main_window.current_subdirectory)):
                    main_window.top_level_taken = False
                    main_window.RemoveQueueItem.myGUI_signal_str.emit(str(0))
                    while not main_window.top_level_taken:
                        time.sleep(0.1)
                    # main_window.directory_queue.takeTopLevelItem(0)
                    continue

            while main_window.directory_item.childCount() != 0:

                main_window.current_session = main_window.directory_item.child(0).data(0, 0)
                main_window.child_data_taken = False
                main_window.RemoveSessionData.myGUI_signal_str.emit(str(0))
                while not main_window.child_data_taken:
                    time.sleep(0.1)

                sub_directory = main_window.directory_item.data(0, 0)

                directory_ready = False

                main_window.LogAppend.myGUI_signal_str.emit(
                    '[%s %s]: Checking if the following directory is ready to analyze: %s!' % (
                        str(datetime.datetime.now().date()),
                        str(datetime.datetime.now().time())[
                        :8], str(sub_directory)))

                while not directory_ready:
                    directory_ready = folder_ready(main_window, os.path.join(directory, sub_directory))

                if main_window.directory_item.childCount() == 0:
                    main_window.top_level_taken = False
                    main_window.RemoveQueueItem.myGUI_signal_str.emit(str(0))
                    while not main_window.top_level_taken:
                        time.sleep(0.1)
                try:

                    # runs the function that will perform the klusta'ing
                    if not os.path.exists(os.path.join(directory, sub_directory)):
                        main_window.top_level_taken = False
                        main_window.RemoveQueueItem.myGUI_signal_str.emit(str(0))
                        while not main_window.top_level_taken:
                            time.sleep(0.1)
                        continue
                    else:

                        klusta(sub_directory, directory, settings, settings_filename=main_window.settings_fname,
                               self=main_window)

                except NotADirectoryError:
                    # if the file is not a directory it prints this message
                    main_window.LogAppend.myGUI_signal_str.emit(
                        '[%s %s]: %s is not a directory!' % (
                            str(datetime.datetime.now().date()),
                            str(datetime.datetime.now().time())[
                            :8], str(sub_directory)))
                    continue


def RepeatAddSessions(main_window):
    main_window.repeat_thread_active = True

    try:
        main_window.adding_session = True
        addSessions(main_window)
        main_window.adding_session = False
    except FileNotFoundError:
        pass
    except RuntimeError:
        pass

    while True:

        if main_window.reset_add_thread:
            main_window.repeat_thread_active = False
            main_window.reset_add_thread = False
            return

        try:
            main_window.adding_session = True
            time.sleep(0.1)
            addSessions(main_window)
            main_window.adding_session = False
            time.sleep(0.1)
        except FileNotFoundError:
            pass
        except RuntimeError:
            pass


def run():
    app = QtWidgets.QApplication(sys.argv)

    main_w = Window()  # calling the main window
    chooseDirectory_w = chooseDirectory()  # calling the Choose Directory Window
    settings_w = Settings_Window()  # calling the settings window
    smtp_setting_w = SmtpSettings()  # calling the smtp settings window
    add_exper = AddExpter()

    add_exper.addbtn.clicked.connect(lambda: add_Expter(add_exper, smtp_setting_w))
    # syncs the current directory on the main window
    chooseDirectory_w.current_directory_name = main_w.current_directory_name

    main_w.raise_()  # making the main window on top

    add_exper.cancelbtn.clicked.connect(lambda: cancel_window(smtp_setting_w, add_exper))
    add_exper.backbtn.clicked.connect(lambda: raise_window(smtp_setting_w, add_exper))

    smtp_setting_w.addbtn.clicked.connect(lambda: raise_window(add_exper, smtp_setting_w))

    main_w.silent_cb.stateChanged.connect(lambda: silent(main_w, main_w.silent_cb.isChecked()))
    main_w.nonbatch_check.stateChanged.connect(lambda: nonbatch(main_w, main_w.nonbatch_check.isChecked()))
    # brings the directory window to the foreground
    main_w.choose_dir.clicked.connect(lambda: raise_window(chooseDirectory_w, main_w))

    # brings the main window to the foreground
    chooseDirectory_w.backbtn.clicked.connect(lambda: raise_window(main_w, chooseDirectory_w))
    chooseDirectory_w.applybtn.clicked.connect(lambda: chooseDirectory_w.apply_dir(main_w))
    # brings the main window to the foreground

    main_w.setbtn.clicked.connect(lambda: raise_window(settings_w, main_w))

    main_w.smtpbtn.clicked.connect(lambda: raise_window(smtp_setting_w, main_w))

    smtp_setting_w.backbtn.clicked.connect(lambda: raise_window(main_w, smtp_setting_w))

    settings_w.backbtn.clicked.connect(lambda: raise_window(main_w, settings_w))

    settings_w.backbtn2.clicked.connect(lambda: raise_window(main_w, settings_w))

    # prompts the user to choose a directory
    chooseDirectory_w.dirbtn.clicked.connect(lambda: new_directory(chooseDirectory_w, main_w))

    sys.exit(app.exec_())  # prevents the window from immediately exiting out


if __name__ == "__main__":
    run()  # the command that calls run()
