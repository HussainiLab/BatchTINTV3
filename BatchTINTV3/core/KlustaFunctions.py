# import os, read_data, json, subprocess
import os, json, subprocess, time, datetime, queue, threading, shutil
from distutils.dir_util import copy_tree
from PyQt5 import QtWidgets
from core.utils import print_msg
from core.Tint_Matlab import get_setfile_parameter
from core.smtpSettings import send_email


def is_tetrode(file, session):

    if os.path.splitext(file)[0] == session:
        try:
            tetrode_number = int(os.path.splitext(file)[1][1:])
            return True
        except ValueError:
            return False
    else:
        return False


def get_tetrode_files(file_list, session):
    tetrode_files = [file for file in file_list if is_tetrode(file, session)]
    return tetrode_files


def addError(errors, experimenter, error):
    """Associates the error with the correct experimenter"""
    if experimenter not in errors.keys():
        errors[experimenter] = [error]
    else:
        errors[experimenter].append(error)


threadLock = threading.Lock()


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
                    :8], set_basename, i+1, len(set_files))

            print_msg(self, msg)

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

            analyzed_set_files.append(os.path.join(sub_directory_fullpath, set_file + '.set'))

        msg = '[%s %s]: Analysis for the following directory has been completed: %s!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], dirname)

        print_msg(self, msg)

        if smtp_settings is None:
            if self is not None:
                smtpfile = os.path.join(self.SETTINGS_DIR, 'smtp.json')
                with open(smtpfile, 'r+') as filename:
                    smtp_settings = json.load(filename)

        if experimenter_settings is None:
            if self is not None:
                expter_fname = os.path.join(self.SETTINGS_DIR, 'experimenter.json')
                with open(expter_fname, 'r+') as f:
                    experimenter_settings = json.load(f)

        if smtp_settings is not None and experimenter_settings is not None:
            send_email(errors, sub_directory, processed_directory, smtp_settings, experimenter_settings, self=self)

        directory_source = sub_directory_fullpath
        directory_destination = os.path.join(processed_directory, sub_directory)

        # move this directory to the analyzed directory

        moving = True
        verbose = True
        while moving:
            time.sleep(0.1)
            moving, verbose = move_analyzed_directory(directory_destination, directory_source, processed_directory,
                                                      verbose=verbose, self=self)

    return analyzed_set_files


def move_analyzed_directory(directory_destination, directory_source, processed_directory, verbose=True, self=None):
    try:
        # moves the entire folder to the processed folder
        if os.path.exists(directory_destination):
            copy_tree(directory_source, directory_destination)
            shutil.rmtree(directory_source)
        else:
            shutil.move(directory_source, processed_directory)
    except PermissionError as error:

        if verbose:
            msg = '[%s %s]: Error while moving the following directory: %s\n\n%s!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], directory_source, error)

            print_msg(self, msg)
            verbose = False  # we only want this message to appear once
        return True, verbose
    except shutil.Error as error:
        if verbose:
            msg = '[%s %s]: Error while moving the following directory: %s\n\n%s!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], directory_source, error)

            print_msg(self, msg)
            verbose = False  # we only want this message to appear once
        return True, verbose
    return False, verbose


def move_files(log_filepath, new_log_filepath, ini_filepath, new_ini_filepath):
    """
    Moves all the files to their appropriate directories

    returns True when properly moved

    returns False when not properly moved
    """

    try:
        if os.path.exists(new_log_filepath):
            os.remove(new_log_filepath)

        os.rename(log_filepath, new_log_filepath)

        if os.path.exists(new_ini_filepath):
            os.remove(new_ini_filepath)

        os.rename(ini_filepath, new_ini_filepath)

    except FileNotFoundError:
        return False
    except PermissionError:
        return False

    return True


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

            # klusta kwik parameters to utilize
            kkparmstr = ' '.join(['-MaxPossibleClusters', str(settings['MaxPos']),
                                         '-UseFeatures', str(settings['UseFeatures']),
                                         '-nStarts', str(settings['nStarts']),
                                         '-RandomSeed', str(settings['RandomSeed']),
                                         '-DistThresh', str(settings['DistThresh']),
                                         '-FullStepEvery', str(settings['FullStepEvery']),
                                         '-ChangedThresh', str(settings['ChangedThresh']),
                                         '-MaxIter', str(settings['MaxIter']),
                                         '-SplitEvery', str(settings['SplitEvery']),
                                         '-Subset', str(settings['Subset']),
                                         '-PenaltyK', str(settings['PenaltyK']),
                                         '-PenaltyKLogN', str(settings['PenaltyKLogN']),
                                         '-UseDistributional', '1',
                                         '-UseMaskedInitialConditions', '1',
                                         '-AssignToFirstClosestMask', '1',
                                         '-PriorPoint', '1',
                                         ])

            # channels to include
            inc_channels = "\n".join(['[IncludeChannels]',
                                   '1=' + str(settings['1']),
                                   '2=' + str(settings['2']),
                                   '3=' + str(settings['3']),
                                   '4=' + str(settings['4'])
                                   ])

            # write these settings to the .ini file
            with open(ini_fpath, 'w') as f:
                if append is None:
                    ini_filename_value = str('Filename="%s"' % set_path)
                else:
                    ini_filename_value = str('Filename="%s%s"' % (set_path, append))

                main_seq = "\n".join(['[Main]',
                                   ini_filename_value,
                                   str('IDnumber=' + str(tetrode)),
                                   str('KKparamstr=' + kkparmstr),
                                   str(inc_channels)
                                   ])

                clust_ft_seq = "\n".join(['\n[ClusteringFeatures]',
                                       str('PC1=' + str(settings['PC1'])),
                                       str('PC2=' + str(settings['PC2'])),
                                       str('PC3=' + str(settings['PC3'])),
                                       str('PC4=' + str(settings['PC4'])),
                                       str('A=' + str(settings['A'])),
                                       str('Vt=' + str(settings['Vt'])),
                                       str('P=' + str(settings['P'])),
                                       str('T=' + str(settings['T'])),
                                       str('tP=' + str(settings['tP'])),
                                       str('tT=' + str(settings['tT'])),
                                       str('En=' + str(settings['En'])),
                                       str('Ar=' + str(settings['Ar']))
                                       ])

                report_seq = "\n".join(['\n[Reporting]',
                                     'Log=' + str(settings['Log File']),
                                     'Verbose=' + str(settings['Verbose']),
                                     'Screen=' + str(settings['Screen'])
                                     ])
                # write to the settings to the .ini file
                for write_order in [main_seq, clust_ft_seq, report_seq]:
                    f.seek(0, 2)  # seek the files end
                    f.write(write_order)

            if append is not None:
                log_fpath = '%s%s_log.txt' % (tet_path, append)  # log file path
            else:
                log_fpath = tet_path + '_log.txt'

            log_fname = tet_fname + '_log.txt'

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

            processing = True
            files_moved = False
            # wait for the cut file to be created
            while processing:
                time.sleep(2)
                sub_dir_flist = os.listdir(sub_directory_fullpath)
                if cut_name in sub_dir_flist:
                    # cut file in the directory

                    new_log_filepath = os.path.join(logfile_directory, tet_fname + '_log.txt')
                    new_ini_filepath = os.path.join(inifile_directory, tet_fname + '.ini')

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
                elif log_fname in sub_dir_flist:
                    with open(log_fpath, 'r') as f:
                        for line in f:
                            if 'list of active tetrodes:' in line:
                                if str(tetrode) not in str(line):
                                    # create the folder that will contain sessions with inactive tetrodes
                                    if not os.path.exists(inactive_tet_dir):
                                        os.makedirs(inactive_tet_dir)

                                    message = '[%s %s]: Tetrode %s is not active within the following set file: %s!' % (
                                        str(datetime.datetime.now().date()),
                                        str(datetime.datetime.now().time())[:8],
                                        str(tetrode),
                                        set_file
                                    )

                                    print_msg(self, message + '#red')

                                    addError(errors, experimenter, message)

                                    new_log_filepath = os.path.join(inactive_tet_dir, tet_fname + '_log.txt')
                                    new_ini_filepath = os.path.join(inactive_tet_dir, tet_fname + '.ini')

                                    # move the files
                                    moving = True
                                    while moving:
                                        moving = move_files(log_fpath, new_log_filepath, ini_fpath, new_ini_filepath)

                                    processing = False
                                    break

                            elif 'reading 0 spikes' in line:

                                # create the folder that will contains sessions with no spikes
                                if not os.path.exists(no_spike_dir):
                                    os.makedirs(no_spike_dir)

                                message = '[%s %s]: Tetrode %s within the following set file has no spikes: %s!' % (
                                    str(datetime.datetime.now().date()),
                                    str(datetime.datetime.now().time())[:8],
                                    str(tetrode),
                                    set_file
                                )

                                print_msg(self, message + '#red')

                                addError(errors, experimenter, message)

                                new_log_filepath = os.path.join(no_spike_dir, tet_fname + '_log.txt')
                                new_ini_filepath = os.path.join(no_spike_dir, tet_fname + '.ini')

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
        error.append('\tThe ' +
                     set_file + " '.set' file had no tetrodes to analyze, couldn't perform analysis.\n")
        analyzable = False

        # if eeg not in the f_list move the files to the missing associated file folder
    if not set([set_file + '.eeg', set_file + '.pos']).issubset(f_list):
        msg = '[%s %s]: There is no %s or %s file in this folder, skipping analysis!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file + '.eeg', set_file + '.pos')

        print_msg(self, msg)

        error.append('\tThe "' + str(
            set_file) +
                     '" \'.set\' file was not analyzed due to not having an \'.eeg\' and a \'.pos\' file.\n')
        analyzable = False

    elif set_file + '.eeg' not in f_list:

        msg = '[%s %s]: There is no %s file in this folder, skipping analysis!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file + '.eeg')

        print_msg(self, msg)

        error.append('\tThe "' + set_file +
                     '" \'.set\' file was not analyzed due to not having an \'.eeg\' file.\n')
        analyzable = False

        # if .pos not in the f_list move the files to the missing associated file folder
    elif set_file + '.pos' not in f_list:

        msg = '[%s %s]: There is no %s file in this folder, skipping analysis!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file + '.pos')

        print_msg(self, msg)

        error.append('\tThe "' + set_file +
                     '" \'.set\' file was not analyzed due to not having a \'.pos\' file.\n')
        analyzable = False

    if not analyzable:
        associated_files = get_associated_files(f_list, set_file)
        # associated_files = [file for file in f_list if set_file in file]
        missing_dir = os.path.join(sub_directory_fullpath, 'MissingAssociatedFiles')
        if not os.path.exists(missing_dir):
            os.makedirs(missing_dir)

        for file in associated_files:
            os.rename(os.path.join(sub_directory_fullpath, file), os.path.join(missing_dir, file))

    return analyzable, error


def get_associated_files(file_list, set_filename):
    return [file for file in file_list if set_filename == os.path.splitext(file)[0]]


def find_sessions(directory):

    set_files = [file for file in os.listdir(directory) if '.set' in file and
                 os.path.splitext(file)[0]]

    return set_files


def find_tetrodes(session, directory):
    """returns a list of tetrode files given a session and directory name"""
    session_basename = os.path.splitext(session)[0]

    tetrodes = [file for file in os.listdir(directory)
                if is_tetrode(file, session_basename)]
    return tetrodes


def is_tetrode(file, session):

    if os.path.splitext(file)[0] == session:
        try:
            tetrode_number = int(os.path.splitext(file)[1][1:])
            return True
        except ValueError:
            return False
    else:
        return False


def session_analyzable(directory, session, append=None):

    # find all the tetrodes for that set file
    tetrodes = find_tetrodes(session, directory)

    session_basename = os.path.splitext(session)[0]
    if append is None:
        analyzable = [file for file in tetrodes if not os.path.exists(os.path.join(directory,
                                                                                    '%s_%s.cut' % (session_basename,
                                                                                                   os.path.splitext(file)[
                                                                                                       1][1:])))]
    else:
        analyzable = [file for file in tetrodes if not os.path.exists(os.path.join(directory,
                                                                                   '%s%s_%s.cut' % (session_basename,
                                                                                                    append,
                                                                                                  os.path.splitext(
                                                                                                      file)[
                                                                                                      1][1:])))]
    if analyzable:
        return True
    else:
        return False


def folder_ready(main_window, directory):
    """ensures that the folder is done copying/moving"""
    try:
        contents = os.listdir(directory)  # lists the contents of the directory (folders)
    except FileNotFoundError:
        return True

    consecutive_same_size = 0
    dirmtime = os.stat(directory).st_mtime  # finds the modification time of the file

    time.sleep(5)

    # creation of a while loop that will constantly check for new folders added to the directory
    newmtime = os.stat(directory).st_mtime  # finds the new modification time

    if newmtime != dirmtime:  # only execute if the new mod time doesn't equal the old mod time
        dirmtime = newmtime  # sets the mod time to the new mod time for future iterations
        # lists the new contents of the directory including added folders

        start_path = directory
        total_size_old = 0
        file_complete = False

        while not file_complete:
            newcontents = os.listdir(directory)
            # finds the differences between the contents to state the files that were added
            added = list(set(newcontents).difference(contents))

            if added:  # runs if added exists as a variable

                time.sleep(5)

                consecutive_same_size = 0
                contents = newcontents
                continue

            total_size = 0
            for dirpath, dirnames, filenames in os.walk(start_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)

                    main_window.LogAppend.myGUI_signal_str.emit(
                        '[%s %s]: %s is downloading... (%s bytes downloaded)!' % (
                            str(datetime.datetime.now().date()),
                            str(datetime.datetime.now().time())[
                            :8], start_path, str(total_size)))

            # if total_size > total_size_old and len(start_path) > count_old:
            if total_size > total_size_old:
                consecutive_same_size = 0
                total_size_old = total_size

                time.sleep(5)

            elif total_size == total_size_old:

                if consecutive_same_size == 0:
                    consecutive_same_size = 1
                    continue

                main_window.LogAppend.myGUI_signal_str.emit(
                    '[%s %s]: %s has finished downloading!' % (
                        str(datetime.datetime.now().date()),
                        str(datetime.datetime.now().time())[
                        :8], start_path))
                file_complete = True

    else:
        return True
