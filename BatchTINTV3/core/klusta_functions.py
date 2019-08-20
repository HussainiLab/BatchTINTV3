# import os, read_data, json, subprocess
import os, json, subprocess, time, datetime, queue, threading
from PyQt5 import QtWidgets
from .utils import print_msg
from .smtpSettings import send_email
from .klusta_utils import addError, get_tetrode_files, move_analyzed_directory, move_files, get_associated_files, \
    write_klusta_ini
from .delete_temp import get_temp_files


threadLock = threading.Lock()


def get_setfile_parameter(parameter, set_filename):
    """
    This function will return the parameter value of a given parameter name for a given set filename.

    Example:
        set_fullpath = 'C:\\example\\tetrode_1.1'
        parameter_name = 'duration
        duration = get_setfile_parameter(parameter_name, set_fullpath)

    Args:
        parameter (str): the name of the set file parameter that you want to obtain.
        set_filename (str): the full path of the .set file that you want to obtain the parameter value from.


    Returns:
        parameter_value (str): the value for the given parameter

    """

    if not os.path.exists(set_filename):
        return

    # adding the encoding because tint data is created via windows and if you want to run this in linux, you need
    # to explicitly say this
    with open(set_filename, 'r+', encoding='cp1252') as f:
        for line in f:
            if parameter in line:
                if line.split(' ')[0] == parameter:
                    # prevents part of the parameter being in another parameter name
                    new_line = line.strip().split(' ')
                    if len(new_line) == 2:
                        return new_line[-1]
                    else:
                        return ' '.join(new_line[1:])


def klusta(set_files, settings, smtp_settings=None, experimenter_settings=None, append=None, self=None):
    """
    This method will perform the klusta analysis of the settings
    """

    if len(set_files) > 1:  # displays messages counting how many set files in directory
        msg = '[%s %s]: There are %d \'.set\' files to analyze!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], len(set_files))

        print_msg(self, msg)

    elif len(set_files) == 1:

        msg = '[%s %s]: There is %d \'.set\' file to analyze!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], len(set_files))

        print_msg(self, msg)

    dirnames = []
    [dirnames.append(os.path.dirname(file)) for file in set_files if os.path.dirname(file) not in dirnames]

    analyzed_set_files = []

    set_file_number = 0

    for dirname in dirnames:
        # iterate through each directory

        sub_directory = None
        sub_directory_fullpath = None
        processed_directory = None

        directory_files = [file for file in set_files if os.path.dirname(file) == dirname]

        errors = {}
        experimenter = None

        for i in range(len(directory_files)):  # loops through each set file

            # define the sub directory for the current set file
            set_file = directory_files[i]
            # this is called sub-directory because we generally use batch mode so directory is the
            # parent of sub-directory
            sub_directory_fullpath = os.path.dirname(set_file)
            sub_directory = os.path.basename(os.path.dirname(set_file))
            directory = os.path.dirname(sub_directory_fullpath)

            logfile_directory = os.path.join(sub_directory_fullpath, 'LogFiles')  # defines directory for log files
            inifile_directory = os.path.join(sub_directory_fullpath, 'IniFiles')  # defines directory for .ini files

            processed_directory = os.path.join(directory, 'Processed')  # defines processed file directory

            # makes the directories if they don't exist
            for _ in [processed_directory, logfile_directory, inifile_directory]:
                if not os.path.exists(_):
                    os.makedirs(_)

            # finds the files within that directory
            f_list = os.listdir(sub_directory_fullpath)

            set_basename = os.path.basename(os.path.splitext(set_file)[0])
            # set file used to not include the filepath, just the basename, so we will remove the filepath
            # set_path = os.path.join(sub_directory_fullpath, set_basename)  # defines set file path

            msg = '[%s %s]: Now analyzing tetrodes associated with the %s \'.set\' file (%d/%d)!' % (
                    str(datetime.datetime.now().date()),
                    str(datetime.datetime.now().time())[
                    :8], set_basename, set_file_number+1, len(set_files))

            print_msg(self, msg)

            set_file_number += 1
            # acquires tetrode files within directory

            tet_list = get_tetrode_files(f_list, set_basename)
            #  if there are no tetrodes then skips

            analyzable, error_return = check_session_files(sub_directory_fullpath, set_basename, tet_list, self=self)

            if analyzable:
                q = queue.Queue()
                for u in tet_list:
                    q.put(u)

                ThreadCount = int(settings['NumThreads'])

                if ThreadCount > len(tet_list):
                    ThreadCount = len(tet_list)

                experimenter = get_setfile_parameter('experimenter', set_file)

                while not q.empty():
                    Threads = []
                    for i in range(ThreadCount):
                        t = threading.Thread(target=analyze_tetrode, args=(q, settings, errors, set_file,
                                                                           logfile_directory,
                                                                           inifile_directory),
                                             kwargs={'self': self,
                                                     'append': append})

                        t.daemon = True
                        t.start()
                        Threads.append(t)

                    for t in Threads:
                        t.join()  # waits for the threads to be finished before continuing

                q.join()  # waits for the queue to be finished
            else:

                addError(errors, experimenter, error_return)
                continue

            analyzed_set_files.append(os.path.join(sub_directory_fullpath, set_file))

        msg = '[%s %s]: Analysis for the following directory has been completed: %s!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], dirname)

        print_msg(self, msg)

        if smtp_settings is None:
            if self is not None:
                smtpfile = os.path.join(self.SETTINGS_DIR, 'smtp.json')
                try:
                    with open(smtpfile, 'r+') as filename:
                        smtp_settings = json.load(filename)
                except FileNotFoundError:
                    smtp_settings = None

        if experimenter_settings is None:
            if self is not None:
                expter_fname = os.path.join(self.SETTINGS_DIR, 'experimenter.json')
                try:
                    with open(expter_fname, 'r+') as f:
                        experimenter_settings = json.load(f)
                except FileNotFoundError:
                    experimenter_settings = None

        if smtp_settings is not None and experimenter_settings is not None:
            send_email(errors, sub_directory, processed_directory, smtp_settings, experimenter_settings, self=self)

        directory_source = sub_directory_fullpath
        directory_destination = os.path.join(processed_directory, sub_directory)

        # delete the temporary files
        if settings['delete_temporary'] == 1:
            msg = '[%s %s]: Deleting temporary files within the following directory: %s!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], sub_directory)

            print_msg(self, msg)

            for file in analyzed_set_files:
                set_path = os.path.splitext(file)[0]

                if hasattr(self, 'append_cut'):
                    append = self.append_cut.text()
                else:
                    append = None
                temp_files = get_temp_files(set_path, append=append)
                for _f in temp_files:
                    os.remove(_f)

        # move this directory to the analyzed directory
        if int(settings['move_processed']) == 1:
            moving = True
            verbose = True
            while moving:
                time.sleep(0.1)
                moving, verbose = move_analyzed_directory(directory_destination, directory_source, processed_directory,
                                                          verbose=verbose, self=self)

    return analyzed_set_files


def analyze_tetrode(q, settings, errors, set_file, logfile_directory, inifile_directory, append=None, self=None):
    """

    This function will take the queue of files, and analyze them through klustakwik

    q is the queue which contains list of tetrodes.
    settings is a dictionary that contains all the secttings values


    """

    experimenter = get_setfile_parameter('experimenter', set_file)

    sub_directory_fullpath = os.path.dirname(set_file)

    set_path = os.path.splitext(set_file)[0]
    # set_basename = os.path.basename(set_path)

    file_list = os.listdir(sub_directory_fullpath)  # finds the files within that directory

    # file directory that will contain files with inactive tetrodes
    inactive_tet_dir = os.path.join(sub_directory_fullpath, 'InactiveTetrodeFiles')

    # file directory that will contain the files with no spikes
    no_spike_dir = os.path.join(sub_directory_fullpath, 'NoSpikeFiles')

    # data_file unread files
    data_unread_directory = os.path.join(sub_directory_fullpath, 'DataFileUnread')
    if q.empty():
        try:
            q.task_done()
        except ValueError:
            pass
    else:
        tet_list = [q.get()]
        for tet_fname in tet_list:

            tetrode = int(os.path.splitext(tet_fname)[-1][1:])

            msg = '[%s %s]: Now analyzing the following file: %s!' % (
                    str(datetime.datetime.now().date()),
                    str(datetime.datetime.now().time())[
                    :8], tet_fname)

            print_msg(self, msg)

            if append is not None:
                cut_path = '%s%s_%d.cut' % (set_path, append, tetrode)
            else:
                cut_path = '%s_%d.cut' % (set_path, tetrode)

            cut_name = os.path.basename(cut_path)

            if cut_name in file_list:
                msg = '[%s %s]: The %s file has already been analyzed!' % (
                        str(datetime.datetime.now().date()),
                        str(datetime.datetime.now().time())[
                        :8], tet_fname)

                print_msg(self, msg)

                q.task_done()
                continue

            tet_path = os.path.join(sub_directory_fullpath, tet_fname)

            if append is not None:
                ini_fpath = '%s%s.ini' % (tet_path, append)  # .ini filename
            else:
                ini_fpath = tet_path + '.ini'  # .ini filename

            if os.path.exists(ini_fpath):
                os.remove(ini_fpath)

            # write the .ini necessary for Tint to perform the correct analysis
            fileID = write_klusta_ini(settings, ini_fpath, set_path, tetrode, append=append)

            if append is not None:
                log_fpath = '%s%s_log.txt' % (tet_path, append)  # log file path
            else:
                log_fpath = tet_path + '_log.txt'

            if os.path.exists(log_fpath):
                os.remove(log_fpath)

            # generating command and adding it to the command prompt
            cmdline = ["cmd", "/q", "/k", "echo off"]

            cmd = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            if int(settings['Silent']) == 0:
                command = 'tint "%s" %d "%s" /runKK /KKoptions "%s" /convertkk2cut /visible\nexit\n' % (set_path,
                                                                               int(tetrode),
                                                                               log_fpath,
                                                                               ini_fpath)
            else:
                command = 'tint "%s" %d "%s" /runKK /KKoptions "%s" /convertkk2cut\nexit\n' % (set_path,
                                                                                                          int(tetrode),
                                                                                                          log_fpath,
                                                                                                          ini_fpath)
            command = bytes(command, 'ascii')

            cmd.stdin.write(command)
            cmd.stdin.flush()

            # waiting for the analysis to be complete

            processing = True
            files_moved = False
            # wait for the cut file to be created
            while processing:
                time.sleep(2)
                sub_dir_flist = os.listdir(sub_directory_fullpath)
                if cut_name in sub_dir_flist:
                    # cut file in the directory

                    new_log_filepath = os.path.join(logfile_directory, os.path.basename(log_fpath))
                    new_ini_filepath = os.path.join(inifile_directory, os.path.basename(ini_fpath))

                    files_moved = move_files(log_fpath, new_log_filepath, ini_fpath, new_ini_filepath)

                    # files have moved properly, can set processing to False
                    if files_moved:
                        processing = False

                    if processing is False:
                        # files moved successfully
                        msg = '[%s %s]: The analysis of the %s file has finished!' % (
                            str(datetime.datetime.now().date()),
                            str(datetime.datetime.now().time())[
                            :8], tet_fname)

                        print_msg(self, msg)

                        break

                # check the log filename to see if there are any error to report
                elif os.path.basename(log_fpath) in sub_dir_flist:
                    with open(log_fpath, 'r') as f:
                        for line in f:
                            if 'list of active tetrodes:' in line:
                                if str(tetrode) not in str(line):
                                    # create the folder that will contain sessions with inactive tetrodes
                                    if not os.path.exists(inactive_tet_dir):
                                        try:
                                            os.makedirs(inactive_tet_dir)
                                        except FileExistsError:
                                            pass

                                    message = '[%s %s]: Tetrode %s is not active within the following set file: %s!' % (
                                        str(datetime.datetime.now().date()),
                                        str(datetime.datetime.now().time())[:8],
                                        str(tetrode),
                                        set_file
                                    )

                                    print_msg(self, message + '#red')

                                    addError(errors, experimenter, message)

                                    new_log_filepath = os.path.join(inactive_tet_dir, os.path.basename(log_fpath))
                                    new_ini_filepath = os.path.join(inactive_tet_dir, os.path.basename(ini_fpath))

                                    # move the files
                                    moving = True
                                    while moving:
                                        moving = move_files(log_fpath, new_log_filepath, ini_fpath, new_ini_filepath)

                                    processing = False
                                    break

                            elif 'reading 0 spikes' in line:

                                # create the folder that will contains sessions with no spikes
                                if not os.path.exists(no_spike_dir):
                                    try:
                                        os.makedirs(no_spike_dir)
                                    except FileExistsError:
                                        pass

                                message = '[%s %s]: Tetrode %s within the following set file has no spikes: %s!' % (
                                    str(datetime.datetime.now().date()),
                                    str(datetime.datetime.now().time())[:8],
                                    str(tetrode),
                                    set_file
                                )

                                print_msg(self, message + '#red')

                                addError(errors, experimenter, message)

                                new_log_filepath = os.path.join(no_spike_dir, os.path.basename(log_fpath))
                                new_ini_filepath = os.path.join(no_spike_dir, os.path.basename(ini_fpath))

                                # move the files
                                moving = True
                                while moving:
                                    moving = move_files(log_fpath, new_log_filepath, ini_fpath, new_ini_filepath)

                                processing = False
                                break

                            elif 'data_file unread' in line:

                                if not os.path.exists(data_unread_directory):
                                    try:
                                        os.makedirs(data_unread_directory)
                                    except FileExistsError:
                                        pass

                                message = '[%s %s]: Tetrode %s within the following set file was unreadable: %s, check logs!' % (
                                    str(datetime.datetime.now().date()),
                                    str(datetime.datetime.now().time())[:8],
                                    str(tetrode),
                                    set_file
                                )

                                print_msg(self, message + '#red')

                                new_log_filepath = os.path.join(data_unread_directory, os.path.basename(log_fpath))
                                new_ini_filepath = os.path.join(data_unread_directory, os.path.basename(ini_fpath))

                                # move the files
                                moving = True
                                while moving:
                                    moving = move_files(log_fpath, new_log_filepath, ini_fpath, new_ini_filepath)

                                processing = False
                                break

            try:
                q.task_done()
            except ValueError:
                pass


def check_klusta_ready(settings, directory, self=None, settings_filename=None, numThreads=None, numCores=None):
    klusta_ready = True

    settings['NumThreads'] = str(numThreads)
    settings['Cores'] = str(numCores)

    if settings_filename is not None:
        # overwrite settings filename with current settings
        with open(settings_filename, 'w') as filename:
            json.dump(settings, filename)

    if settings['NumFeat'] > 4:

        if self is not None:
            self.choice = None
            self.LogError.myGUI_signal_str.emit('ManyFet')

            while self.choice is None:
                time.sleep(1)

            if self.choice == QtWidgets.QMessageBox.No:
                klusta_ready = False
            elif self.choice == QtWidgets.QMessageBox.Yes:
                klusta_ready = True
        else:

            message = '[%s %s]: You have chosen more than four features. clustering will take a long time!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[:8])

            print_msg(self, message)

    if directory == 'No Directory Currently Chosen!':

        if self is None:
            self.choice = None
            self.LogError.myGUI_signal_str.emit('NoDir')
            while self.choice is None:
                time.sleep(1)

            if self.choice == QtWidgets.QMessageBox.Ok:
                return False

    if 'Google Drive' in directory:
        if self is None:
            self.choice = None
            self.LogError.myGUI_signal_str.emit('GoogleDir')
            while self.choice is None:
                time.sleep(1)

            if self.choice == QtWidgets.QMessageBox.Yes:
                klusta_ready = True
            elif self.choice == QtWidgets.QMessageBox.No:
                klusta_ready = False

    return klusta_ready


def check_session_files(sub_directory_fullpath, set_file, tet_list, self=None):
    """
    This method will ensure that all the necessary files exist before continuing.
    :param sub_directory_fullpath:
    :param set_file:
    :param tet_list:
    :param self:
    :return:
    """
    error = []
    analyzable = True
    f_list = os.listdir(sub_directory_fullpath)  # finds the files within that directory

    if not tet_list:

        msg = '[%s %s]: The %s \'.set\' file has no tetrodes to analyze!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file)

        print_msg(self, msg)

        # appends error to error list
        error.append(msg)
        analyzable = False

        # if eeg not in the f_list move the files to the missing associated file folder
    if not set([set_file + '.eeg', set_file + '.pos']).issubset(f_list):
        msg = '[%s %s]: There is no %s or %s file in this folder, skipping analysis!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file + '.eeg', set_file + '.pos')

        print_msg(self, msg)
        error.append(msg)
        analyzable = False

    elif set_file + '.eeg' not in f_list:

        msg = '[%s %s]: There is no %s file in this folder, skipping analysis!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file + '.eeg')

        print_msg(self, msg)

        error.append(msg)
        analyzable = False

        # if .pos not in the f_list move the files to the missing associated file folder
    elif set_file + '.pos' not in f_list:

        msg = '[%s %s]: There is no %s file in this folder, skipping analysis!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file + '.pos')

        print_msg(self, msg)

        error.append(msg)
        analyzable = False

    if not analyzable:
        associated_files = get_associated_files(f_list, set_file)
        missing_dir = os.path.join(sub_directory_fullpath, 'MissingAssociatedFiles')
        if not os.path.exists(missing_dir):
            os.makedirs(missing_dir)

        for file in associated_files:
            os.rename(os.path.join(sub_directory_fullpath, file), os.path.join(missing_dir, file))

    return analyzable, error


