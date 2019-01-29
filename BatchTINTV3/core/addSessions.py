import time
import os
from PyQt5 import QtWidgets
from core.KlustaFunctions import find_tetrodes, session_analyzable


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

                for set_file in set_files:
                    if set_file == self.current_session:
                        continue

                    # find all the tetrodes for that set file
                    tetrodes = find_tetrodes(set_file, os.path.join(current_directory,
                                                                    directory))

                    # check if all the tetrodes within that set file have been analyzed
                    analyzable = session_analyzable(os.path.join(current_directory, directory),
                                                      set_file, tetrodes)

                    if analyzable:
                        # add session
                        session_item = QtWidgets.QTreeWidgetItem()
                        session_item.setText(0, set_file)
                        directory_item.addChild(session_item)

                        self.directory_queue.addTopLevelItem(directory_item)


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
