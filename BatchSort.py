import functools, sys
from PIL import Image
from PyQt4 import QtCore, QtGui

from core.KlustaFunctions import *

_author_ = "Geoffrey Barrett"  # defines myself as the author

Large_Font = ("Verdana", 12)  # defines two fonts for different purposes (might not be used
Small_Font = ("Verdana", 8)


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


class Window(QtGui.QWidget):  # defines the window class (main window)

    def __init__(self):  # initializes the main window
        super(Window, self).__init__()
        # self.setGeometry(50, 50, 500, 300)
        background(self)  # acquires some features from the background function we defined earlier
        self.setWindowTitle("BatchTINT - Main Window")  # sets the title of the window
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

        cumc_logo = QtGui.QLabel(self)  # defining the logo image
        logo_fname = os.path.join(self.IMG_DIR, "BatchKlustaLogo.png")  # defining logo pathname
        im2 = Image.open(logo_fname)  # opening the logo with PIL
        logowidth, logoheight = im2.size  # acquiring the logo width/height
        logo_pix = QtGui.QPixmap(logo_fname)  # getting the pixmap
        cumc_logo.setPixmap(logo_pix)  # setting the pixmap
        cumc_logo.setGeometry(0, 0, logowidth, logoheight)  # setting the geometry

        # ------buttons ------------------------------------------
        quitbtn = QtGui.QPushButton('Quit', self)  # making a quit button
        quitbtn.clicked.connect(self.close_app)  # defining the quit button functionality (once pressed)
        quitbtn.setShortcut("Ctrl+Q")  # creates shortcut for the quit button
        quitbtn.setToolTip('Click to quit Batch-Tint!')

        self.setbtn = QtGui.QPushButton('Klusta Settings')  # Creates the settings pushbutton
        self.setbtn.setToolTip('Define the settings that KlustaKwik will use.')

        self.klustabtn = QtGui.QPushButton('Run', self)  # creates the batch-klusta pushbutton
        self.klustabtn.setToolTip('Click to perform batch analysis via Tint and KlustaKwik!')

        self.smtpbtn = QtGui.QPushButton('SMTP Settings', self)
        self.smtpbtn.setToolTip("Click to change the SMTP settings for e-mail notifications.")

        self.choose_dir = QtGui.QPushButton('Choose Directory', self)  # creates the choose directory pushbutton

        self.cur_dir = QtGui.QLineEdit()  # creates a line edit to display the chosen directory (current)
        self.cur_dir.setText(current_directory_name)  # sets the text to the current directory
        self.cur_dir.setAlignment(QtCore.Qt.AlignHCenter)  # centers the text
        self.cur_dir.setToolTip('The current directory that Batch-Tint will analyze.')

        # defines an attribute to exchange info between classes/modules
        self.current_directory_name = current_directory_name

        # defines the button functionality once pressed
        self.klustabtn.clicked.connect(lambda: self.run(self.current_directory_name))

        # ------------------------------------ check box  ------------------------------------------------
        self.nonbatch_check = QtGui.QCheckBox('Non-Batch?')
        self.nonbatch_check.setToolTip("Check this if you don't want to run batch. This means you will choose\n"
                                       "the folder that directly contains all the session files (.set, .pos, .N, etc.).")
        self.nonbatch = 0

        self.silent_cb = QtGui.QCheckBox('Run Silently')
        self.silent_cb.setToolTip("Check if you want Tint to run in the background.")

        # ---------------- queue widgets --------------------------------------------------
        self.directory_queue = QtGui.QTreeWidget()
        self.directory_queue.headerItem().setText(0, "Axona Sessions:")
        self.directory_queue.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        directory_queue_label = QtGui.QLabel('Queue: ')

        self.up_btn = QtGui.QPushButton("Move Up", self)
        self.up_btn.setToolTip("Clcik this button to move selected directories up on the queue!")
        self.up_btn.clicked.connect(lambda: self.moveQueue('up'))

        self.down_btn = QtGui.QPushButton("Move Down", self)
        self.down_btn.setToolTip("Clcik this button to move selected directories down on the queue!")
        self.down_btn.clicked.connect(lambda: self.moveQueue('down'))

        queue_btn_layout = QtGui.QVBoxLayout()
        queue_btn_layout.addWidget(self.up_btn)
        queue_btn_layout.addWidget(self.down_btn)

        queue_layout = QtGui.QVBoxLayout()
        queue_layout.addWidget(directory_queue_label)
        queue_layout.addWidget(self.directory_queue)

        queue_and_btn_layout = QtGui.QHBoxLayout()
        queue_and_btn_layout.addLayout(queue_layout)
        queue_and_btn_layout.addLayout(queue_btn_layout)

        # ------------------------ multithreading widgets -------------------------------------

        self.Multithread_cb = QtGui.QCheckBox('Multiprocessing')
        self.Multithread_cb.setToolTip('Check if you want to run multiple tetrodes simultaneously')

        core_num_l = QtGui.QLabel('Cores (#):')
        core_num_l.setToolTip('Generally the number of processes that multiprocessing should use is \n'
                              'equal to the number of cores your computer has.')

        self.core_num = QtGui.QLineEdit()

        Multithread_l = QtGui.QLabel('Simultaneous Tetrodes (#):')
        Multithread_l.setToolTip('Input the number of tetrodes you want to analyze simultaneously')

        self.Multithread = QtGui.QLineEdit()

        Multi_layout = QtGui.QHBoxLayout()

        # for order in [self.Multithread_cb, core_num_l, self.core_num, Multithread_l, self.Multithread]:
        for order in [Multithread_l, self.Multithread]:
            if 'Layout' in order.__str__():
                Multi_layout.addLayout(order)
                # Multi_layout.addStretch(1)
            else:
                Multi_layout.addWidget(order, 0, QtCore.Qt.AlignCenter)
                # Multi_layout.addWidget(order)
                # Multi_layout.addStretch(1)

        checkbox_layout = QtGui.QHBoxLayout()
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
                self.core_num.setText(str(settings['Cores']))
                self.Multithread.setText(str(settings['NumThreads']))
                if settings['Silent'] == 1:
                    self.silent_cb.toggle()
                if settings['Multi'] == 1:
                    self.Multithread_cb.toggle()
                if settings['Multi'] == 0:
                    self.core_num.setDisabled(1)
                if settings['nonbatch'] == 1:
                    self.nonbatch_check.toggle

        except FileNotFoundError:
            self.silent_cb.toggle()
            self.core_num.setDisabled(1)
            self.core_num.setText('4')
            self.Multithread.setText('1')

        # ------------- Log Box -------------------------
        self.Log = QtGui.QTextEdit()
        log_label = QtGui.QLabel('Log: ')

        log_lay = QtGui.QVBoxLayout()
        log_lay.addWidget(log_label, 0, QtCore.Qt.AlignTop)
        log_lay.addWidget(self.Log)

        # ------------------------------------ version information -------------------------------------------------
        # finds the modification date of the program
        try:
            mod_date = time.ctime(os.path.getmtime(__file__))
        except:
            mod_date = time.ctime(os.path.getmtime(os.path.join(self.PROJECT_DIR, "BatchSort.exe")))

        vers_label = QtGui.QLabel("BatchTINT V3.0 - Last Updated: " + mod_date)  # creates a label with that information

        # ------------------- page layout ----------------------------------------
        layout = QtGui.QVBoxLayout()  # setting the layout

        layout1 = QtGui.QHBoxLayout()  # setting layout for the directory options
        layout1.addWidget(self.choose_dir)  # adding widgets to the first tab
        layout1.addWidget(self.cur_dir)

        btn_order = [self.klustabtn, self.setbtn, self.smtpbtn, quitbtn]  # defining button order (left to right)
        btn_layout = QtGui.QHBoxLayout()  # creating a widget to align the buttons
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

        if self.current_directory_name != 'No Directory Currently Chosen!':
            # starting adding any existing sessions in a different thread

            self.RepeatAddSessionsThread = QtCore.QThread()
            self.RepeatAddSessionsThread.start()

            self.RepeatAddSessionsWorker = Worker(RepeatAddSessions, self)
            self.RepeatAddSessionsWorker.moveToThread(self.RepeatAddSessionsThread)
            self.RepeatAddSessionsWorker.start.emit("start")

    def run(self, directory):  # function that runs klustakwik

        """This method runs when the Batch-TINT button is pressed on the GUI,
        and commences the analysis"""
        '''
        self.BatchTintThread = threading.Thread(target=BatchTint(self, directory))
        self.BatchTintThread.daemon = True
        self.BatchTintThread.start()
        '''
        self.batch_tint = True
        self.klustabtn.setText('Stop')
        self.klustabtn.setToolTip('Click to stop Batch-Tint.')  # defining the tool tip for the start button
        self.klustabtn.clicked.disconnect()
        self.klustabtn.clicked.connect(self.stopBatch)

        self.BatchTintThread = QtCore.QThread()
        self.BatchTintThread.start()

        self.BatchTintWorker = Worker(BatchTint, self, directory)
        self.BatchTintWorker.moveToThread(self.BatchTintThread)
        self.BatchTintWorker.start.emit("start")

    def close_app(self):
        # pop up window that asks if you really want to exit the app ------------------------------------------------

        choice = QtGui.QMessageBox.question(self, "Quitting BatchTINT",
                                            "Do you really want to exit?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            sys.exit()  # tells the app to quit
        else:
            pass

    def raiseError(self, error_val):
        '''raises an error window given certain errors from an emitted signal'''

        if 'ManyFet' in error_val:
            self.choice = QtGui.QMessageBox.question(self, "No Chosen Directory: BatchTINT",
                                                     "You have chosen more than four features,\n"
                                                     "clustering will take a long time.\n"
                                                     "Do you realy want to continue?",
                                                 QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        elif 'NoDir' in error_val:
            self.choice = QtGui.QMessageBox.question(self, "No Chosen Directory: BatchTINT",
                                                   "You have not chosen a directory,\n"
                                                   "please choose one to continue!",
                                                     QtGui.QMessageBox.Ok)

        elif 'GoogleDir' in error_val:
            self.choice = QtGui.QMessageBox.question(self, "Google Drive Directory: BatchTINT",
                                                       "You have not chosen a directory within Google Drive,\n"
                                                       "be aware that during testing we have experienced\n"
                                                       "permissions errors while using Google Drive directories\n"
                                                       "that would result in BatchTINTV2 not being able to move\n"
                                                       "the files to the Processed folder (and stopping the GUI),\n"
                                                       "do you want to continue?",
                                                       QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        elif 'NoSet' in error_val:
            self.choice = QtGui.QMessageBox.question(self, "No .Set Files!",
                                                     "You have chosen a directory that has no .Set files!\n"
                                                     "Please choose a different directory!",
                                                     QtGui.QMessageBox.Ok)

        elif 'InvDirBatch':
            self.choice = QtGui.QMessageBox.question(self, "Invalid Directory!",
                                                     "In 'Batch Mode' you need to choose a directory\n"
                                                     "with subdirectories that contain all your Tint\n"
                                                     "files. Press Abort and choose new file, or if you\n"
                                                     "plan on adding folders to the chosen directory press\n"
                                                     "continue.",
                                                     QtGui.QMessageBox.Abort | QtGui.QMessageBox.Ok)
        elif 'InvDirNonBatch':
            self.choice = QtGui.QMessageBox.question(self, "Invalid Directory!",
                                                     "In 'Non-Batch Mode' you need to choose a directory\n"
                                                     "that contain all your Tint files.\n",
                                                     QtGui.QMessageBox.Ok)

    def AppendLog(self, message):
        '''A function that will append the Log field of the main window (mainly
        used as a slot for a custom pyqt signal)'''
        self.Log.append(message)

    def stopBatch(self):
        # self.klustabtn.clicked.disconnect()
        self.klustabtn.clicked.connect(lambda: self.run(self.current_directory_name))
        self.BatchTintThread.quit()
        # self.RepeatAddSessionsThread.quit()
        self.batch_tint = False
        self.klustabtn.setText('Run')
        self.klustabtn.setToolTip(
            'Click to perform batch analysis via Tint and KlustaKwik!')  # defining the tool tip for the start button

    def moveQueue(self, direction):
        '''This method is not threaded'''
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

        #add_to_new_queue = self.directory_queue.items
        #for i in range(len(selected_items)):
        #    selected_items[i] = selected_items[i].clone()

        if not selected_items:
            # skips when there are no items selected
            return

        new_queue_order = {}

        # find if consecutive indices from 0 on are selected as these won't move any further up

        indices = find_keys(queue_items, selected_items)
        # non_selected_indices = sorted([index for index in range(item_count) if index not in indices])
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
                        # new_item.setSelected(True)
                        new_queue_order[index] = new_item

                else:
                    for index in consecutive:
                        # move these up the list (decrease in index value since 0 is the top of the list)
                        new_item = queue_items[index].clone()
                        # new_item.setSelected(True)
                        new_queue_order[index-1] = new_item

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
                    # item = queue_items[non_selected_indices.pop()]
                    for value in add_to_new_queue:
                        if static_value.data(0, 0) == value.data(0, 0):
                            add_to_new_queue.remove(value)  # remove item from the list
                            break

                    new_queue_order[static_index] = static_value.clone()

        elif 'down' in direction:
            # first add the selected items to their new spots
            for consecutive in consecutive_indices:
                if (item_count-1) in consecutive:
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
                    # item = queue_items[non_selected_indices.pop()]
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
            # for item in selected_items:
            #     if item.data(0, 0) == value.data(0, 0):
            #         value.setSelected(True)

            self.directory_queue.addTopLevelItem(value)

        # reselect the items
        iterator = QtGui.QTreeWidgetItemIterator(self.directory_queue)
        while iterator.value():
            for selected_item in selected_items_copy:
                item = iterator.value()
                if item.data(0, 0) == selected_item.data(0, 0):
                    item.setSelected(True)
                    break
            iterator += 1
        # for index in range(item_count):
        #   self.directory_queue.takeTopLevelItem(0)
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


def find_consec(data):
    '''finds the consecutive numbers and outputs as a list'''
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


class Settings_Window(QtGui.QTabWidget):

    def __init__(self):
        super(Settings_Window, self).__init__()
        self.Settings()

    def Settings(self):
        self.set_adv = {}
        self.set_feats = {}
        self.set_chan_inc = {}
        self.position = {}
        self.reporting = {}

        self.default_adv = {'MaxPos': 30, 'nStarts': 1, 'RandomSeed': 1,
                       'DistThresh': 6.907755, 'PenaltyK': 1.0, 'PenaltyKLogN': 0.0,
                       'ChangedThresh': 0.05, 'MaxIter': 500, 'SplitEvery': 40,
                       'FullStepEvery': 20, 'Subset': 1}

        tab1 = QtGui.QWidget()  # creates the basic tab
        tab2 = QtGui.QWidget()  # creates the advanced tab

        background(self)
        # deskW, deskH = background.Background(self)
        self.setWindowTitle("BatchTINT - Settings Window")

        self.addTab(tab1, 'Basic')
        self.addTab(tab2, 'Advanced')
        # -------------------- number of tetrodes ---------------------

        num_tet_l = QtGui.QLabel('Number of Tetrodes')
        self.num_tet = QtGui.QLineEdit()
        self.num_tet.setToolTip('The maximum number of tetrodes in your directory folders.')

        num_tet_lay = QtGui.QHBoxLayout()
        num_tet_lay.addWidget(num_tet_l)
        # num_tet_lay.addStretch('1')
        num_tet_lay.addWidget(self.num_tet)

        # ------------------ clustering features --------------------------------
        clust_l = QtGui.QLabel('Clustering Features:')

        grid_ft = QtGui.QGridLayout()

        self.clust_ft_names = ['PC1', 'PC2', 'PC3', 'PC4',
                               'A', 'Vt', 'P', 'T',
                               'tP', 'tT', 'En', 'Ar']

        for feat in self.clust_ft_names:
            if feat != '':
                self.set_feats[feat] = 0

        self.clust_ft_cbs = {}

        positions = [(i, j) for i in range(4) for j in range(4)]

        for position, clust_ft_name in zip(positions, self.clust_ft_names):

            if clust_ft_name == '':
                continue
            self.position[clust_ft_name] = position
            self.clust_ft_cbs[position] = QtGui.QCheckBox(clust_ft_name)
            grid_ft.addWidget(self.clust_ft_cbs[position], *position)
            self.clust_ft_cbs[position].stateChanged.connect(
                functools.partial(self.channel_feats, clust_ft_name, position))

        # self.clust_ft_cbs.toggle()

        clust_feat_lay = QtGui.QHBoxLayout()
        clust_feat_lay.addWidget(clust_l)
        clust_feat_lay.addLayout(grid_ft)

        # -------------------------- reporting checkboxes ---------------------------------------

        report_l = QtGui.QLabel('Reporting Options:')

        self.report = ['Verbose', 'Screen', 'Log File']

        self.report_cbs = {}

        grid_report = QtGui.QGridLayout()

        positions = [(i, j) for i in range(1) for j in range(4)]

        for position, option in zip(positions, self.report):

            if option == '':
                continue
            self.position[option] = position
            self.report_cbs[position] = QtGui.QCheckBox(option)
            grid_report.addWidget(self.report_cbs[position], *position)
            self.report_cbs[position].stateChanged.connect(
                functools.partial(self.reporting_options, option, position))

        grid_lay = QtGui.QHBoxLayout()
        grid_lay.addWidget(report_l)
        grid_lay.addLayout(grid_report)

        # --------------------------Channels to Include-------------------------------------------

        chan_inc = QtGui.QLabel('Channels to Include:')

        grid_chan = QtGui.QGridLayout()
        self.chan_names = ['1', '2', '3', '4']

        for chan in self.chan_names:
            self.set_chan_inc[chan] = 0

        self.chan_inc_cbs = {}

        positions = [(i, j) for i in range(1) for j in range(4)]

        for position, chan_name in zip(positions, self.chan_names):

            if chan_name == '':
                continue
            self.position[chan_name] = position
            self.chan_inc_cbs[position] = QtGui.QCheckBox(chan_name)
            grid_chan.addWidget(self.chan_inc_cbs[position], *position)
            self.chan_inc_cbs[position].stateChanged.connect(
                functools.partial(self.channel_include, chan_name, position))
            self.chan_inc_cbs[position].setToolTip('Include channel ' + str(chan_name) + ' in the analysis.')

        chan_name_lay = QtGui.QHBoxLayout()
        chan_name_lay.addWidget(chan_inc)
        chan_name_lay.addLayout(grid_chan)

        # --------------------------basic lay doublespinbox------------------------------------------------
        '''
        max_clust_l = QtGui.QLabel('Maximum Clusters: ')
        min_clust_l = QtGui.QLabel('Minimum Clusters: ')
        max_clust = QtGui.QDoubleSpinBox()
        min_clust = QtGui.QDoubleSpinBox()

        clust_maxmin_order = [min_clust_l, min_clust, max_clust_l, max_clust]
        clust_maxmin_lay = QtGui.QHBoxLayout()

        for order in clust_maxmin_order:
            clust_maxmin_lay.addWidget(order, 0, QtCore.Qt.AlignCenter)
            clust_maxmin_lay.addStretch(1)
        '''
        # --------------------------adv lay doublespinbox------------------------------------------------

        row1 = QtGui.QHBoxLayout()
        row2 = QtGui.QHBoxLayout()
        row3 = QtGui.QHBoxLayout()
        row4 = QtGui.QHBoxLayout()
        row5 = QtGui.QHBoxLayout()
        row6 = QtGui.QHBoxLayout()

        maxposclust_l = QtGui.QLabel('MaxPossibleClusters: ')
        self.maxpos = QtGui.QLineEdit()

        chThresh_l = QtGui.QLabel('ChangedThresh: ')
        self.chThresh = QtGui.QLineEdit()

        nStarts_l = QtGui.QLabel('nStarts: ')
        self.nStarts = QtGui.QLineEdit()

        MaxIter_l = QtGui.QLabel('MaxIter: ')
        self.Maxiter = QtGui.QLineEdit()

        RandomSeed_l = QtGui.QLabel('RandomSeed: ')
        self.RandomSeed = QtGui.QLineEdit()

        SplitEvery_l = QtGui.QLabel('SplitEvery: ')
        self.SplitEvery = QtGui.QLineEdit()

        DistThresh_l = QtGui.QLabel('DistThresh: ')
        self.DistThresh = QtGui.QLineEdit()

        FullStepEvery_l  = QtGui.QLabel('FullStepEvery: ')
        self.FullStepEvery = QtGui.QLineEdit()

        PenaltyK_l = QtGui.QLabel('PenaltyK: ')
        self.PenaltyK = QtGui.QLineEdit()

        Subset_l = QtGui.QLabel('Subset: ')
        self.Subset = QtGui.QLineEdit()

        PenaltyKLogN_l = QtGui.QLabel('PenaltyKLogN: ')
        self.PenaltyKLogN = QtGui.QLineEdit()

        row1order = [maxposclust_l, self.maxpos, chThresh_l, self.chThresh]
        for order in row1order:
            row1.addWidget(order)
            # row1.addStretch(1)

        row2order = [nStarts_l, self.nStarts, MaxIter_l, self.Maxiter]
        for order in row2order:
            row2.addWidget(order)
            # row2.addStretch(1)

        row3order = [RandomSeed_l, self.RandomSeed, SplitEvery_l, self.SplitEvery]
        for order in row3order:
            row3.addWidget(order)
            # row3.addStretch(1)

        row4order = [DistThresh_l, self.DistThresh, FullStepEvery_l, self.FullStepEvery]
        for order in row4order:
            row4.addWidget(order)
            # row4.addStretch(1)

        row5order = [PenaltyK_l, self.PenaltyK, Subset_l, self.Subset]
        for order in row5order:
            row5.addWidget(order)
            # row5.addStretch(1)

        row6order = [PenaltyKLogN_l, self.PenaltyKLogN]
        for order in row6order:
            row6.addWidget(order)
            # row6.addStretch(1)

        # ------------------------ buttons ----------------------------------------------------
        self.basicdefaultbtn = QtGui.QPushButton("Default", tab1)
        self.basicdefaultbtn.clicked.connect(self.basic_default)
        self.advanceddefaultbtn = QtGui.QPushButton("Default", tab2)
        self.advanceddefaultbtn.clicked.connect(self.adv_default)

        self.backbtn = QtGui.QPushButton('Back', tab1)

        self.backbtn2 = QtGui.QPushButton('Back', tab2)

        self.apply_tab1btn = QtGui.QPushButton('Apply', tab1)
        self.apply_tab1btn.clicked.connect(self.apply_tab1)

        self.apply_tab2btn = QtGui.QPushButton('Apply',tab2)
        self.apply_tab2btn.clicked.connect(self.apply_tab2)

        basic_butn_order = [self.apply_tab1btn, self.basicdefaultbtn, self.backbtn]
        basic_butn_lay = QtGui.QHBoxLayout()
        for order in basic_butn_order:
            basic_butn_lay.addWidget(order, 0, QtCore.Qt.AlignCenter)
            # basic_butn_lay.addStretch(1)

        adv_butn_order = [self.apply_tab2btn, self.advanceddefaultbtn, self.backbtn2]
        adv_butn_lay = QtGui.QHBoxLayout()
        for order in adv_butn_order:
            adv_butn_lay.addWidget(order, 0, QtCore.Qt.AlignCenter)
            # adv_butn_lay.addStretch(1)

        # -------------------------- layouts ----------------------------------------------------

        # basic_lay_order = [chan_name_lay, clust_feat_lay, clust_maxmin_lay, basic_butn_lay]
        basic_lay_order = [num_tet_lay, chan_name_lay, clust_feat_lay, grid_lay, basic_butn_lay]
        basic_lay = QtGui.QVBoxLayout()

        # basic_lay.addStretch(1)
        for order in basic_lay_order:
            if 'Layout' in order.__str__():
                basic_lay.addLayout(order)
                basic_lay.addStretch(1)
            else:
                basic_lay.addWidget(order, 0, QtCore.Qt.AlignCenter)
                basic_lay.addStretch(1)

        tab1.setLayout(basic_lay)

        adv_lay_order = [row1, row2, row3, row4, row5, row6, adv_butn_lay]
        adv_lay = QtGui.QVBoxLayout()

        # basic_lay.addStretch(1)
        for order in adv_lay_order:
            if 'Layout' in order.__str__():
                adv_lay.addLayout(order)
                adv_lay.addStretch(1)
            else:
                adv_lay.addWidget(order, 0, QtCore.Qt.AlignCenter)
                adv_lay.addStretch(1)

        tab2.setLayout(adv_lay)

        try:
            # No saved directory's need to create file
            with open(self.settings_fname, 'r+') as filename:
                self.settings = json.load(filename)
                self.maxpos.setText(str(self.settings['MaxPos']))
                self.chThresh.setText(str(self.settings['ChangedThresh']))
                self.nStarts.setText(str(self.settings['nStarts']))
                self.RandomSeed.setText(str(self.settings['RandomSeed']))
                self.DistThresh.setText(str(self.settings['DistThresh']))
                self.PenaltyK.setText(str(self.settings['PenaltyK']))
                self.PenaltyKLogN.setText(str(self.settings['PenaltyKLogN']))
                self.Maxiter.setText(str(self.settings['MaxIter']))
                self.SplitEvery.setText(str(self.settings['SplitEvery']))
                self.FullStepEvery.setText(str(self.settings['FullStepEvery']))
                self.Subset.setText(str(self.settings['Subset']))
                self.num_tet.setText(str(self.settings['NumTet']))

                for name in self.chan_names:
                    if int(self.settings[name]) == 1:
                        self.chan_inc_cbs[self.position[name]].toggle()

                for feat in self.clust_ft_names:
                    if feat != '':
                        if int(self.settings[feat]) == 1:
                            self.clust_ft_cbs[self.position[feat]].toggle()

                for option in self.report:
                    if int(self.settings[option]) == 1:
                        self.report_cbs[self.position[option]].toggle()

        except FileNotFoundError:

            with open(self.settings_fname, 'w') as filename:
                self.default_set_feats = self.set_feats
                self.default_set_feats['PC1'] = 1
                self.default_set_feats['PC2'] = 1
                self.default_set_feats['PC3'] = 1

                self.default_set_channels_inc = self.set_chan_inc
                self.default_set_channels_inc['1'] = 1
                self.default_set_channels_inc['2'] = 1
                self.default_set_channels_inc['3'] = 1
                self.default_set_channels_inc['4'] = 1

                self.default_reporting = self.reporting
                self.reporting['Verbose'] = 1
                self.reporting['Screen'] = 1
                self.reporting['Log File'] = 1

                self.settings = {}

                for dictionary in [self.default_adv, self.default_set_feats, self.default_set_channels_inc, self.default_reporting]:
                    self.settings.update(dictionary)

                default_set_feats = []
                default_reporting = []
                default_set_channels_inc = []

                self.settings['NumTet'] = '8'
                self.settings['NumFet'] = 3
                self.settings['Silent'] = 1
                self.settings['Multi'] = 0
                self.settings['UseFeatures'] = '1111111111111'
                self.settings['NumThreads'] = 1
                self.settings['Cores'] = 4

                json.dump(self.settings, filename)  # save the default values to this file

                self.maxpos.setText(str(self.settings['MaxPos']))
                self.chThresh.setText(str(self.settings['ChangedThresh']))
                self.nStarts.setText(str(self.settings['nStarts']))
                self.RandomSeed.setText(str(self.settings['RandomSeed']))
                self.DistThresh.setText(str(self.settings['DistThresh']))
                self.PenaltyK.setText(str(self.settings['PenaltyK']))
                self.PenaltyKLogN.setText(str(self.settings['PenaltyKLogN']))
                self.Maxiter.setText(str(self.settings['MaxIter']))
                self.SplitEvery.setText(str(self.settings['SplitEvery']))
                self.FullStepEvery.setText(str(self.settings['FullStepEvery']))
                self.Subset.setText(str(self.settings['Subset']))
                self.num_tet.setText(str(self.settings['NumTet']))

                for name in self.chan_names:
                    if self.settings[name] == 1:
                        self.chan_inc_cbs[self.position[name]].toggle()

                for feat in self.clust_ft_names:
                    if feat != '':
                        if self.settings[feat] == 1:
                            self.clust_ft_cbs[self.position[feat]].toggle()

                for option in self.report:
                    if int(self.settings[option]) == 1:
                        self.report_cbs[self.position[option]].toggle()
        center(self)
        # self.show()

    def reporting_options(self, option, position):
        if self.report_cbs[position].isChecked():
            self.reporting[option] = 1
        else:
            self.reporting[option] = 0

    def channel_feats(self, clust_ft_name, position):
        if self.clust_ft_cbs[position].isChecked():
            self.set_feats[clust_ft_name] = 1
        else:
            self.set_feats[clust_ft_name] = 0

    def channel_include(self, channel_name, position):
        if self.chan_inc_cbs[position].isChecked():
            self.set_chan_inc[channel_name] = 1
        else:
            self.set_chan_inc[channel_name] = 0

    def adv_default(self):
        """Sets the Advanced Settings to their Default Values"""
        self.maxpos.setText(str(self.default_adv['MaxPos']))
        self.chThresh.setText(str(self.default_adv['ChangedThresh']))
        self.nStarts.setText(str(self.default_adv['nStarts']))
        self.RandomSeed.setText(str(self.default_adv['RandomSeed']))
        self.DistThresh.setText(str(self.default_adv['DistThresh']))
        self.PenaltyK.setText(str(self.default_adv['PenaltyK']))
        self.PenaltyKLogN.setText(str(self.default_adv['PenaltyKLogN']))
        self.Maxiter.setText(str(self.default_adv['MaxIter']))
        self.SplitEvery.setText(str(self.default_adv['SplitEvery']))
        self.FullStepEvery.setText(str(self.default_adv['FullStepEvery']))
        self.Subset.setText(str(self.default_adv['Subset']))

        self.apply_tab2btn.animateClick()

    def basic_default(self):
        """Sets the Basic Settings to their Default Values"""
        default_set_feats = {}
        default_set_feats['PC1'] = 1
        default_set_feats['PC2'] = 1
        default_set_feats['PC3'] = 1

        default_set_channels_inc = {}
        default_set_channels_inc['1'] = 1
        default_set_channels_inc['2'] = 1
        default_set_channels_inc['3'] = 1
        default_set_channels_inc['4'] = 1

        default_reporting = {}
        default_reporting['Verbose'] = 1
        default_reporting['Screen'] = 1
        default_reporting['Log File'] = 1

        for name in self.chan_names:
            default_keys = list(default_set_channels_inc.keys())
            if name in default_keys and self.chan_inc_cbs[self.position[name]].isChecked() == False:
                self.chan_inc_cbs[self.position[name]].toggle()
            elif name not in default_keys and self.chan_inc_cbs[self.position[name]].isChecked() == True:
                self.chan_inc_cbs[self.position[name]].toggle()

        for feat in self.clust_ft_names:
            if feat != '':
                default_keys = list(default_set_feats.keys())
                if feat in default_keys and self.clust_ft_cbs[self.position[feat]].isChecked() == False:
                    self.clust_ft_cbs[self.position[feat]].toggle()
                elif feat not in default_keys and self.clust_ft_cbs[self.position[feat]].isChecked() == True:
                    self.clust_ft_cbs[self.position[feat]].toggle()

        for option in self.report:
            default_keys = list(default_reporting.keys())
            if option in default_keys and self.report_cbs[self.position[option]].isChecked() == False:
                self.report_cbs[self.position[option]].toggle()
            elif option not in default_keys and self.report_cbs[self.position[option]].isChecked() == True:
                self.report_cbs[self.position[option]].toggle()

        self.num_tet.setText('8')

        self.apply_tab1btn.animateClick()

    def apply_tab1(self):

        with open(self.settings_fname, 'r+') as filename:

            for name, position in self.position.items():

                if name in self.chan_names:
                    if self.chan_inc_cbs[position].isChecked():
                        self.settings[name] = 1
                    else:
                        self.settings[name] = 0

                if name in self.clust_ft_names:
                    if self.clust_ft_cbs[position].isChecked():
                        self.settings[name] = 1
                    else:
                        self.settings[name] = 0

                if name in self.report:
                    if self.report_cbs[position].isChecked():
                        self.settings[name] = 1
                    else:
                        self.settings[name] = 0

            chan_inc = [chan for chan in self.chan_names if self.settings[chan] == 1]
            feat_inc = [feat for feat in self.clust_ft_names if self.settings[feat] == 1]

            UseFeat = ''
            # start_feat = 1
            for i in range(len(self.chan_names)):
                for j in range(len(feat_inc)):
                    if str(i+1) in chan_inc:
                        UseFeat += '1'
                    else:
                        UseFeat += '0'
            UseFeat += '1'

            self.settings['NumFet'] = len(feat_inc)
            self.settings['NumTet'] = str(self.num_tet.text())
            self.settings['UseFeatures'] = UseFeat

            self.backbtn.animateClick()

        with open(self.settings_fname, 'w') as filename:
            json.dump(self.settings, filename)  # save the default values to this file

    def apply_tab2(self):
        with open(self.settings_fname, 'r+') as filename:

            self.settings['MaxPos'] = self.maxpos.text()
            self.settings['nStarts'] = self.nStarts.text()
            self.settings['RandomSeed'] = self.RandomSeed.text()
            self.settings['DistThresh'] = self.DistThresh.text()
            self.settings['PenaltyK'] = self.PenaltyK.text()
            self.settings['PenaltyKLogN'] = self.PenaltyKLogN.text()
            self.settings['ChangedThresh'] = self.chThresh.text()
            self.settings['MaxIter'] = self.Maxiter.text()
            self.settings['SplitEvery'] = self.SplitEvery.text()
            self.settings['FullStepEvery'] = self.FullStepEvery.text()
            self.settings['Subset'] = self.Subset.text()

            self.backbtn2.animateClick()
        with open(self.settings_fname, 'w') as filename:
            json.dump(self.settings, filename)  # save the default values to this file


class Choose_Dir(QtGui.QWidget):

    def __init__(self):
        super(Choose_Dir, self).__init__()
        background(self)
        # deskW, deskH = background.Background(self)
        width = self.deskW / 5
        height = self.deskH / 5
        self.setGeometry(0, 0, width, height)

        with open(self.directory_settings, 'r+') as filename:
            directory_data = json.load(filename)
            current_directory_name = directory_data['directory']
            if not os.path.exists(current_directory_name):
                current_directory_name = 'No Directory Currently Chosen!'

        self.setWindowTitle("BatchTINT - Choose Directory")

        # ---------------- defining instructions -----------------
        instr = QtGui.QLabel("For Batch Processing: choose the directory that contains subdirectories where these\n"
                             "subdirectories contain all the session files (.set, .pos, .eeg, .N, etc.). Batch-Tint\n"
                             "will iterate through each sub-directory and each session within those sub-directories.\n\n"
                             "For Non-Batch: choose the directory that directly contains the contain all the session\n"
                             "files (.set, .pos, .eeg, .N, etc.) and Batch-Tint will iterate through each session.\n")

        # ----------------- buttons ----------------------------
        self.dirbtn = QtGui.QPushButton('Choose Directory', self)
        self.dirbtn.setToolTip('Click to choose a directory!')
        # dirbtn.clicked.connect(self.new_dir)

        cur_dir_t = QtGui.QLabel('Current Directory:')  # the label saying Current Directory
        self.cur_dir_e = QtGui.QLineEdit() # the label that states the current directory
        self.cur_dir_e.setText(current_directory_name)
        self.cur_dir_e.setAlignment(QtCore.Qt.AlignHCenter)
        self.current_directory_name = current_directory_name

        self.backbtn = QtGui.QPushButton('Back', self)
        self.applybtn = QtGui.QPushButton('Apply', self)


        # ---------------- save checkbox -----------------------
        self.save_cb = QtGui.QCheckBox('Leave Checked To Save Directory', self)
        self.save_cb.toggle()
        self.save_cb.stateChanged.connect(self.save_dir)

        # ----------------- setting layout -----------------------

        layout_dir = QtGui.QVBoxLayout()

        layout_h1 = QtGui.QHBoxLayout()
        layout_h1.addWidget(cur_dir_t)
        layout_h1.addWidget(self.cur_dir_e)

        layout_h2 = QtGui.QHBoxLayout()
        layout_h2.addWidget(self.save_cb)

        btn_layout = QtGui.QHBoxLayout()
        btn_order = [self.dirbtn, self.applybtn, self.backbtn]

        # btn_layout.addStretch(1)
        for butn in btn_order:
            btn_layout.addWidget(butn)
            # btn_layout.addStretch(1)

        layout_order = [instr, layout_h1, self.save_cb, btn_layout]

        for order in layout_order:
            if 'Layout' in order.__str__():
                layout_dir.addLayout(order)
            else:
                layout_dir.addWidget(order, 0, QtCore.Qt.AlignCenter)

        self.setLayout(layout_dir)

        center(self)
        # self.show()

    def save_dir(self, state):
        self.current_directory_name = str(self.cur_dir_e.text())
        if state == QtCore.Qt.Checked:  # do this if the Check Box is checked
            # print('checked')
            with open(self.directory_settings, 'w') as filename:
                directory_data = {'directory': self.current_directory_name}
                json.dump(directory_data, filename)
        else:
            # print('unchecked')
            pass

    def apply_dir(self, main):
        self.current_directory_name = str(self.cur_dir_e.text())
        self.save_cb.checkState()

        if self.save_cb.isChecked():  # do this if the Check Box is checked
            self.save_dir(self.save_cb.checkState())
        else:
            pass

        main.directory_queue.clear()
        main.cur_dir.setText(self.current_directory_name)
        main.current_directory_name = self.current_directory_name

        self.backbtn.animateClick()


class SmtpSettings(QtGui.QWidget):
    def __init__(self):
        super(SmtpSettings, self).__init__()
        background(self)
        # deskW, deskH = background.Background(self)
        width = self.deskW / 3
        height = self.deskH / 3
        self.setGeometry(0, 0, width, height)

        self.smtpfile = os.path.join(self.SETTINGS_DIR, 'smtp.json')  # defining the directory filename

        try:
            with open(self.smtpfile, 'r+') as filename:
                self.smtp_data = json.load(filename)
        except FileNotFoundError:
            with open(self.smtpfile, 'w') as filename:
                self.smtp_data = {}
                self.smtp_data['ServerName'] = 'smtp.gmail.com'
                self.smtp_data['Port'] = '587'
                self.smtp_data['Username'] = ''
                self.smtp_data['Password'] = ''
                self.smtp_data['Notification'] = 'Off'
                json.dump(self.smtp_data, filename)

        self.setWindowTitle("BatchTINT - SMTP Settings")

        # ----------------- smtp widgets ------------------------
        self.expterList = QtGui.QTreeWidget()
        self.expterList.headerItem().setText(0, "Experimenter")
        self.expterList.headerItem().setText(1, "Emails")
        self.expterList.setUniformRowHeights(True)

        self.expterList.itemDoubleClicked.connect(self.editItems)
        expters = {}
        self.expter_fname = os.path.join(self.SETTINGS_DIR, 'experimenter.json')

        try:
            with open(self.expter_fname, 'r+') as f:
                expters = json.load(f)
        except FileNotFoundError:
            pass

        for key, value in expters.items():
            new_item = QtGui.QTreeWidgetItem()
            new_item.setFlags(new_item.flags() |QtCore.Qt.ItemIsEditable)
            new_item.setText(0, key)
            new_item.setText(1, value)
            self.expterList.addTopLevelItem(new_item)

        self.backbtn = QtGui.QPushButton('Back', self)
        applybtn = QtGui.QPushButton('Apply', self)
        applybtn.clicked.connect(self.ApplyBtn)

        rembtn = QtGui.QPushButton('Delete Selected Experimenters', self)
        rembtn.clicked.connect(self.removeItems)

        self.addbtn = QtGui.QPushButton('Add Experimenter', self)
        # self.addbtn.clicked.connect(self.add_expter)

        server_name_l = QtGui.QLabel('Server Name: ')
        self.server_name_edit = QtGui.QLineEdit()
        self.server_name_edit.setText(self.smtp_data['ServerName'])
        server_lay = QtGui.QHBoxLayout()
        server_lay.addWidget(server_name_l)
        server_lay.addWidget(self.server_name_edit)

        port_l = QtGui.QLabel('Port: ')
        self.port_edit = QtGui.QLineEdit()
        self.port_edit.setText(self.smtp_data['Port'])
        port_lay = QtGui.QHBoxLayout()
        port_lay.addWidget(port_l)
        port_lay.addWidget(self.port_edit)

        pass_l = QtGui.QLabel('Password: ')
        self.pass_edit = QtGui.QLineEdit()
        self.pass_edit.setEchoMode(QtGui.QLineEdit.Password)
        self.pass_edit.setText(self.smtp_data['Password'])
        pass_lay = QtGui.QHBoxLayout()
        pass_lay.addWidget(pass_l)
        pass_lay.addWidget(self.pass_edit)

        username_l = QtGui.QLabel('Username: ')
        self.username_edit = QtGui.QLineEdit()
        self.username_edit.setText(self.smtp_data['Username'])
        username_lay = QtGui.QHBoxLayout()
        username_lay.addWidget(username_l)
        username_lay.addWidget(self.username_edit)

        server_layout = QtGui.QHBoxLayout()
        server_layout.addLayout(server_lay)
        server_layout.addLayout(port_lay)

        user_layout = QtGui.QHBoxLayout()
        user_layout.addLayout(username_lay)
        user_layout.addLayout(pass_lay)

        self.notification_cb = QtGui.QCheckBox('Allow Email Notifications: ')
        self.notification_cb.stateChanged.connect(self.NotificationStatus)

        if self.smtp_data['Notification'] == 'Off':
            self.server_name_edit.setDisabled(1)
            self.port_edit.setDisabled(1)
            self.pass_edit.setDisabled(1)
            self.username_edit.setDisabled(1)
        else:
            self.notification_cb.toggle()
            self.server_name_edit.setEnabled(1)
            self.port_edit.setEnabled(1)
            self.pass_edit.setEnabled(1)
            self.username_edit.setEnabled(1)

        # ------------------------ layout -----------------------
        layout = QtGui.QVBoxLayout()

        btn_layout = QtGui.QHBoxLayout()
        btn_order = [applybtn, self.addbtn, rembtn, self.backbtn]

        # btn_layout.addStretch(1)
        for butn in btn_order:
            btn_layout.addWidget(butn)
            # btn_layout.addStretch(1)

        layout_order = [self.notification_cb, server_layout, user_layout, self.expterList, btn_layout]

        for order in layout_order:
            if 'Layout' in order.__str__():
                layout.addLayout(order)
            else:
                layout.addWidget(order)

        self.setLayout(layout)

        center(self)
        # self.show()

    def removeItems(self):
        root = self.expterList.invisibleRootItem()
        with open(self.expter_fname, 'r+') as f:
            expters = json.load(f)
        for item in self.expterList.selectedItems():
            expters = {key: expters[key] for key in expters if key != item.text(0)}
            (item.parent() or root).removeChild(item)

        with open(self.expter_fname, 'w') as f:
            json.dump(expters, f)

    def editItems(self, item, column):
        self.expterList.editItem(item, column)

    def ApplyBtn(self):
        with open(self.smtpfile, 'r+') as filename:
            self.smtp_data = json.load(filename)

        self.smtp_data['ServerName'] = str(self.server_name_edit.text())
        self.smtp_data['Port'] = str(self.port_edit.text())
        self.smtp_data['Password'] = str(self.pass_edit.text())
        self.smtp_data['Username'] = str(self.username_edit.text())

        with open(self.expter_fname, 'r+') as f:
            expters = json.load(f)
        root = self.expterList.invisibleRootItem()
        child_count = root.childCount()
        for i in range(child_count):
            item = root.child(i)
            expters[item.text(0)] = item.text(1)

        with open(self.expter_fname, 'w') as f:
            json.dump(expters, f)

        with open(self.smtpfile, 'w') as filename:
            json.dump(self.smtp_data, filename)

            self.backbtn.animateClick()

    def NotificationStatus(self):
        # self.smtp_data = {}
        with open(self.smtpfile, 'r+') as filename:
            self.smtp_data = json.load(filename)

        if self.notification_cb.isChecked():
            self.smtp_data['Notification'] = 'On'
            self.server_name_edit.setEnabled(1)
            self.port_edit.setEnabled(1)
            self.pass_edit.setEnabled(1)
            self.username_edit.setEnabled(1)
        else:
            self.smtp_data['Notification'] = 'Off'
            self.server_name_edit.setDisabled(1)
            self.port_edit.setDisabled(1)
            self.pass_edit.setDisabled(1)
            self.username_edit.setDisabled(1)
        with open(self.smtpfile, 'w') as filename:
            json.dump(self.smtp_data, filename)


class AddExpter(QtGui.QWidget):
    def __init__(self):
        super(AddExpter, self).__init__()
        background(self)
        # deskW, deskH = background.Background(self)
        width = self.deskW / 3
        height = self.deskH / 3
        self.setGeometry(0, 0, width, height)
        self.setWindowTitle("BatchTINT - Add Experimenter")

        # ------------- widgets ---------------------------------------------------

        self.cancelbtn = QtGui.QPushButton('Cancel', self)
        self.addbtn = QtGui.QPushButton('Add', self)

        self.backbtn = QtGui.QPushButton('Back', self)

        expter_l = QtGui.QLabel('Experimenter: ')
        self.expter_edit = QtGui.QLineEdit()
        expter_lay = QtGui.QHBoxLayout()
        expter_lay.addWidget(expter_l)
        expter_lay.addWidget(self.expter_edit)

        email_l = QtGui.QLabel('E-Mail: ')
        email_l.setToolTip('Can add multiple e-mails (e-mails separated by a comma followed by a space)')
        self.email_edit = QtGui.QLineEdit()
        self.email_edit.setToolTip('Can add multiple e-mails (e-mails separated by a comma followed by a space)')
        email_lay = QtGui.QHBoxLayout()
        email_lay.addWidget(email_l)
        email_lay.addWidget(self.email_edit)


        # ------------------ layout ---------------------------------------------------------

        layout = QtGui.QVBoxLayout()

        btn_layout = QtGui.QHBoxLayout()
        btn_order = [self.addbtn, self.backbtn, self.cancelbtn]

        # btn_layout.addStretch(1)
        for butn in btn_order:
            btn_layout.addWidget(butn)
            # btn_layout.addStretch(1)

        layout_order = [expter_lay, email_lay, btn_layout]

        for order in layout_order:
            if 'Layout' in order.__str__():
                layout.addLayout(order)
            else:
                layout.addWidget(order)

        self.setLayout(layout)

        center(self)


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

    if 'SmtpSettings' in str(new_window) and 'AddExpter' in str(old_window): # needs to clear the text files
        old_window.expter_edit.setText('')
        old_window.email_edit.setText('')


def center(self):
    """centers the window on the screen"""
    frameGm = self.frameGeometry()
    screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
    centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
    frameGm.moveCenter(centerPoint)
    self.move(frameGm.topLeft())


def new_directory(self, main):
    #main.directory_queue.clear()
    current_directory_name = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory"))
    self.current_directory_name = current_directory_name
    self.cur_dir_e.setText(current_directory_name)
    #main.cur_dir.setText(current_directory_name)
    #main.current_directory_name = current_directory_name


class Worker(QtCore.QObject):
    # def __init__(self, main_window, thread):
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


def addSessions(self):

    while self.reordering_queue:
        # pauses add Sessions when the individual is reordering
        time.sleep(0.1)

    current_directory = self.current_directory_name
    if self.nonbatch == 0:
        # finds the sub directories within the chosen directory
        sub_directories = [d for d in os.listdir(self.current_directory_name)
                           if os.path.isdir(os.path.join(self.current_directory_name, d)) and
                           d not in ['Processed', 'Converted']]  # finds the subdirectories within each folder

    else:
        # current_directory = os.path.dirname(self.current_directory_name)
        current_directory = os.path.dirname(current_directory)
        sub_directories = [os.path.basename(self.current_directory_name)]

    # find items already in the queue
    added_directories = []

    # iterating through queue items
    iterator = QtGui.QTreeWidgetItemIterator(self.directory_queue)
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
                iterator = QtGui.QTreeWidgetItemIterator(self.directory_queue)
                while iterator.value():
                    directory_item = iterator.value()
                    if directory_item.data(0, 0) == directory:
                        break
                    iterator += 1

                # find added sessions
                added_sessions = []
                try:
                    iterator = QtGui.QTreeWidgetItemIterator(directory_item)
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
                    tetrodes = find_tetrodes(set_file, os.path.join(current_directory,
                                                                    directory))  # find all the tetrodes for that set file

                    # check if all the tetrodes within that set file have been analyzed
                    analyzable = session_analyzable(os.path.join(current_directory, directory),
                                                      set_file, tetrodes)

                    if analyzable:
                        # add session
                        if set_file not in added_sessions and set_file != self.current_session:
                            session_item = QtGui.QTreeWidgetItem()
                            session_item.setText(0, set_file)
                            directory_item.addChild(session_item)
                    else:
                        pass

            else:

                '''
                try:
                    ready_to_add = folder_ready(self, os.path.join(current_directory, directory))
                except FileNotFoundError:
                    return
                # check if it's still downloading

                if not ready_to_add:
                    return
                '''
                # add all the sessions within this directory
                directory_item = QtGui.QTreeWidgetItem()
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
                            session_item = QtGui.QTreeWidgetItem()
                            session_item.setText(0, set_file)
                            directory_item.addChild(session_item)

                            self.directory_queue.addTopLevelItem(directory_item)
                else:
                    pass
                    #self.choice = ''
                    #self.LogError.myGUI_signal_str.emit('NoSet')
                    #while self.choice == '':
                    #    time.sleep(0.5)


def silent(self, state):
    with open(self.settings_fname, 'r+') as filename:
        settings = json.load(filename)
        if state == True:
            settings['Silent'] = 1
        else:
            settings['Silent'] = 0
    with open(self.settings_fname, 'w') as filename:
        json.dump(settings, filename)


class Communicate(QtCore.QObject):
    '''A custom pyqtsignal so that errors and popups can be called from the threads
    to the main window'''
    myGUI_signal_str = QtCore.pyqtSignal(str)
    myGUI_signal_QTreeWidgetItem = QtCore.pyqtSignal(QtGui.QTreeWidgetItem)

@QtCore.pyqtSlot()
def add_Expter(self, main):
    """
    Self = the Add Experimenter Window
    Main = the Main Window Object
    """
    expters = {}
    expter_fname = os.path.join(main.SETTINGS_DIR, 'experimenter.json')
    try:
        with open(expter_fname, 'r+') as f:
            expters = json.load(f)
            expters[str(self.expter_edit.text()).title()] = self.email_edit.text()
        with open(expter_fname, 'w') as f:
            json.dump(expters, f)

    except FileNotFoundError:
        with open(expter_fname, 'w') as f:
            expters[str(self.expter_edit.text()).title()] = self.email_edit.text()
            json.dump(expters, f)

    new_item = QtGui.QTreeWidgetItem()
    new_item.setFlags(new_item.flags() | QtCore.Qt.ItemIsEditable)
    new_item.setText(0, str(self.expter_edit.text()).title())
    new_item.setText(1, self.email_edit.text())
    main.expterList.addTopLevelItem(new_item)

    self.backbtn.animateClick()
    self.cancelbtn.animateClick()


def Multi(self, state):
    with open(self.settings_fname, 'r+') as filename:
        settings = json.load(filename)
        if state == True:
            settings['Multi'] = 1
            self.core_num.setEnabled(1)
        else:
            settings['Multi'] = 0
            self.core_num.setDisabled(1)
    with open(self.settings_fname, 'w') as filename:
        json.dump(settings, filename)


def nonbatch(self, state):
    self.directory_queue.clear()

    with open(self.settings_fname, 'r+') as filename:
        settings = json.load(filename)
        if state == True:
            settings['nonbatch'] = 1
            self.nonbatch = 1
        else:
            settings['nonbatch'] = 0
            self.nonbatch = 0
    with open(self.settings_fname, 'w') as filename:
        json.dump(settings, filename)


def BatchTint(main_window, directory):
    # ------- making a function that runs the entire GUI ----------
    '''
    def __init__(self, main_window, directory):
        QtCore.QThread.__init__(self)
        self.main_window = main_window
        self.directory = directory

    def __del__(self):
        self.wait()

    def run(self):
    '''

    # checks if the settings are appropriate to run analysis
    klusta_ready = check_klusta_ready(main_window, directory)

    if klusta_ready:

        #addSessions(main_window)

        main_window.LogAppend.myGUI_signal_str.emit(
            '[%s %s]: Analyzing the following directory: %s!' % (str(datetime.datetime.now().date()),
                                                                 str(datetime.datetime.now().time())[
                                                                 :8], directory))

        if main_window.nonbatch == 0:
            # message that shows how many files were found
            main_window.LogAppend.myGUI_signal_str.emit(
                '[%s %s]: Found %d sub-directories in the directory!' % (str(datetime.datetime.now().date()),
                                                               str(datetime.datetime.now().time())[
                                                               :8], main_window.directory_queue.topLevelItemCount()))

        else:
            directory = os.path.dirname(directory)

        if main_window.directory_queue.topLevelItemCount() == 0:
            # main_window.BatchTintThread.quit()
            # main_window.AddSessionsThread.quit()
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

                if main_window.choice == QtGui.QMessageBox.Abort:
                    main_window.stopBatch()
                    return

        # ----------- cycle through each file and find the tetrode files ------------------------------------------
        # for sub_directory in sub_directories:  # finding all the folders within the directory

        while main_window.batch_tint:

            #addSessions(main_window)

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

                # set_file = []
                # for child_count in range(main_window.directory_item.childCount()):
                #     set_file.append(main_window.directory_item.child(child_count).data(0, 0))
                main_window.current_session = main_window.directory_item.child(0).data(0, 0)
                main_window.child_data_taken = False
                main_window.RemoveSessionData.myGUI_signal_str.emit(str(0))
                while not main_window.child_data_taken:
                    time.sleep(0.1)
                # main_window.directory_item.takeChild(0).data(0, 0)

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
                    # main_window.directory_queue.takeTopLevelItem(0)

                try:
                    # adding the .rhd files to a list of session_files

                    # set_file = [file for file in os.listdir(dir_new) if '.set' in file]  # finds the set file

                    # if not set_file:  # if there is no set file it will return as an empty list
                    #     # message saying no .set file
                    #     main_window.LogAppend.myGUI_signal_str.emit(
                    #         '[%s %s]: The following folder contains no analyzable \'.set\' files: %s' % (
                    #             str(datetime.datetime.now().date()),
                    #             str(datetime.datetime.now().time())[
                    #             :8], str(sub_directory)))
                    #     continue

                    # runs the function that will perform the klusta'ing
                    if not os.path.exists(os.path.join(directory, sub_directory)):
                        main_window.top_level_taken = False
                        main_window.RemoveQueueItem.myGUI_signal_str.emit(str(0))
                        while not main_window.top_level_taken:
                            time.sleep(0.1)
                        # main_window.directory_queue.takeTopLevelItem(0)
                        continue
                    else:
                        klusta(main_window, sub_directory, directory)

                except NotADirectoryError:
                    # if the file is not a directory it prints this message
                    main_window.LogAppend.myGUI_signal_str.emit(
                        '[%s %s]: %s is not a directory!' % (
                            str(datetime.datetime.now().date()),
                            str(datetime.datetime.now().time())[
                            :8], str(sub_directory)))
                    continue


def RepeatAddSessions(main_window):
    try:
        main_window.adding_session = True
        addSessions(main_window)
        main_window.adding_session = False
    except FileNotFoundError:
        pass
    except RuntimeError:
        pass

    while True:
        #time.sleep(0.5)
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
    app = QtGui.QApplication(sys.argv)

    main_w = Window()  # calling the main window
    choose_dir_w = Choose_Dir()  # calling the Choose Directory Window
    settings_w = Settings_Window()  # calling the settings window
    smtp_setting_w = SmtpSettings()  # calling the smtp settings window
    add_exper = AddExpter()

    add_exper.addbtn.clicked.connect(lambda: add_Expter(add_exper, smtp_setting_w))
    # synchs the current directory on the main window
    choose_dir_w.current_directory_name = main_w.current_directory_name

    main_w.raise_()  # making the main window on top

    add_exper.cancelbtn.clicked.connect(lambda: cancel_window(smtp_setting_w, add_exper))
    add_exper.backbtn.clicked.connect(lambda: raise_window(smtp_setting_w, add_exper))

    smtp_setting_w.addbtn.clicked.connect(lambda: raise_window(add_exper, smtp_setting_w))

    main_w.silent_cb.stateChanged.connect(lambda: silent(main_w, main_w.silent_cb.isChecked()))
    main_w.Multithread_cb.stateChanged.connect(lambda: Multi(main_w, main_w.Multithread_cb.isChecked()))
    main_w.nonbatch_check.stateChanged.connect(lambda: nonbatch(main_w, main_w.nonbatch_check.isChecked()))
    # brings the directory window to the foreground
    main_w.choose_dir.clicked.connect(lambda: raise_window(choose_dir_w,main_w))
    # main_w.choose_dir.clicked.connect(lambda: raise_window(choose_dir_w))

    # brings the main window to the foreground
    choose_dir_w.backbtn.clicked.connect(lambda: raise_window(main_w, choose_dir_w))
    choose_dir_w.applybtn.clicked.connect(lambda: choose_dir_w.apply_dir(main_w))
    # choose_dir_w.backbtn.clicked.connect(lambda: raise_window(main_w))  # brings the main window to the foreground

    main_w.setbtn.clicked.connect(lambda: raise_window(settings_w, main_w))
    # main_w.setbtn.clicked.connect(lambda: raise_window(settings_w))

    main_w.smtpbtn.clicked.connect(lambda: raise_window(smtp_setting_w, main_w))

    smtp_setting_w.backbtn.clicked.connect(lambda: raise_window(main_w, smtp_setting_w))

    settings_w.backbtn.clicked.connect(lambda: raise_window(main_w, settings_w))
    # settings_w.backbtn.clicked.connect(lambda: raise_window(main_w))

    settings_w.backbtn2.clicked.connect(lambda: raise_window(main_w, settings_w))
    # settings_w.backbtn2.clicked.connect(lambda: raise_window(main_w))

    choose_dir_w.dirbtn.clicked.connect(lambda: new_directory(choose_dir_w, main_w))  # prompts the user to choose a directory
    # choose_dir_w.dirbtn.clicked.connect(lambda: new_directory(choose_dir_w))  # prompts the user to choose a directory

    sys.exit(app.exec_())  # prevents the window from immediately exiting out

if __name__ == "__main__":
    run()  # the command that calls run()
