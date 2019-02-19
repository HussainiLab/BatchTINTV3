# import os, read_data, json, subprocess
import os, json, subprocess, time, datetime, queue, threading, smtplib, shutil
from distutils.dir_util import copy_tree
from PyQt5 import QtWidgets
# from multiprocessing.dummy import Pool as ThreadPool
# from email.mime.text import MIMEText
from core.utils import print_msg


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


def klusta(set_files, settings, self=None):
    """
    This method will perform the klusta analysis of the settings
    """

    # sub_directory_fullpath = os.path.join(directory, sub_directory)  # defines fullpath
    sub_directory_fullpath = os.path.dirname(set_files[0])
    sub_directory = os.path.basename(os.path.dirname(set_files[0]))
    directory = os.path.dirname(sub_directory_fullpath)

    logfile_directory = os.path.join(sub_directory_fullpath, 'LogFiles')  # defines directory for log files
    inifile_directory = os.path.join(sub_directory_fullpath, 'IniFiles')  # defines directory for .ini files

    processed_directory = os.path.join(directory, 'Processed')  # defines processed file directory

    for _ in [processed_directory, logfile_directory, inifile_directory]:
        if not os.path.exists(_):  # makes the directories if they don't exist
            os.makedirs(_)

    f_list = os.listdir(sub_directory_fullpath)  # finds the files within that directory

    # set_files = [file for file in f_list if '.set' in file]  # fines .set files

    if len(set_files) > 1:  # displays messages counting how many set files in directory
        msg = '[%s %s]: There are %d \'.set\' files in this directory!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], len(set_files))

        print_msg(self, msg)

    elif len(set_files) == 1:

        msg = '[%s %s]: There is %d \'.set\' file in this directory!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], len(set_files))

        print_msg(self, msg)

    skipped = 0
    experimenter = []  # initializing experimenter list
    error = []  # initializing error list
    for i in range(len(set_files)):  # loops through each set file
        set_file = os.path.splitext(set_files[i])[0]  # define set file without extension
        set_file = os.path.basename(set_file)  # we needed to add this because we changed the functionality
        # set file used to not include the filepath, just the basename, so we will remove the filepath
        set_path = os.path.join(sub_directory_fullpath, set_file)  # defines set file path

        msg = '[%s %s]: Now analyzing tetrodes associated with the %s \'.set\' file (%d/%d)!' % (
                str(datetime.datetime.now().date()),
                str(datetime.datetime.now().time())[
                :8], set_file, i+1, len(set_files))

        print_msg(self, msg)

        # acquires tetrode files within directory

        tet_list = get_tetrode_files(f_list, set_file)
        #  if there are no tetrodes then skips

        analyzable, error_return = check_session_files(sub_directory_fullpath, set_file, tet_list, self=self)

        if analyzable:
            q = queue.Queue()
            for u in tet_list:
                q.put(u)

            ThreadCount = int(settings['NumThreads'])

            if ThreadCount > len(tet_list):
                ThreadCount = len(tet_list)
            skipped_mat = []

            with open(set_path + '.set', 'r+') as f:
                for line in f:
                    if 'experimenter ' in line:
                        expter_line = line.split(' ', 1)
                        expter_line.remove('experimenter')
                        experimenter.append(' '.join(expter_line))
                        break

            while not q.empty():
                Threads = []
                for i in range(ThreadCount):
                    t = threading.Thread(target=analyze_tetrode, args=(q, settings, experimenter, error, skipped_mat,
                                                                       i, set_path, set_file, f_list,
                                                                       sub_directory_fullpath, logfile_directory,
                                                                       inifile_directory), kwargs={'self': self})
                    time.sleep(1)
                    t.daemon = True
                    t.start()
                    Threads.append(t)

                # q.join()
                for t in Threads:
                    t.join()
            q.join()
        else:
            error.extend(error_return)
            continue

    msg = '[%s %s]: Analysis in the %s directory has been completed!' % (
            str(datetime.datetime.now().date()),
            str(datetime.datetime.now().time())[
            :8], sub_directory)

    print_msg(self, msg)

    processed_directory = os.path.join(directory, 'Processed')

    send_email(experimenter, error, sub_directory, processed_directory, self=self)

    directory_source = sub_directory_fullpath
    directory_destination = os.path.join(processed_directory, sub_directory)

    processing = 1
    while processing == 1:
        time.sleep(0.1)
        processing = 0
        try:
            # moves the entire folder to the processed folder
            if os.path.exists(directory_destination):
                try:
                    copy_tree(directory_source, directory_destination)
                except PermissionError:
                    return
                shutil.rmtree(directory_source)
            else:
                shutil.move(directory_source, processed_directory)
        except PermissionError:
            processing = 1


def analyze_tetrode(q, settings,  experimenter,
                    error, skipped_mat, index, set_path, set_file, f_list, sub_directory_fullpath,
                    logfile_directory, inifile_directory, self=None):

    inactive_tet_dir = os.path.join(sub_directory_fullpath, 'InactiveTetrodeFiles')
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

            clu_name = '%s.clu.%d' % (set_path, tetrode)
            cut_path = '%s_%d.cut' % (set_path, tetrode)
            cut_name = os.path.basename(cut_path)

            if cut_name in f_list:
                msg = '[%s %s]: The %s file has already been analyzed!' % (
                        str(datetime.datetime.now().date()),
                        str(datetime.datetime.now().time())[
                        :8], tet_fname)

                print_msg(self, msg)

                q.task_done()
                continue

            tet_path = os.path.join(sub_directory_fullpath, tet_fname)

            ini_fpath = tet_path + '.ini'  # .ini filename
            ini_fname = tet_fname + '.ini'  # .ini fullpath

            parm_space = ' '
            # klusta kwik parameters to utilize
            kkparmstr = parm_space.join(['-MaxPossibleClusters', str(settings['MaxPos']),
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

            s = "\n"
            # channels to include
            inc_channels = s.join(['[IncludeChannels]',
                                   '1=' + str(settings['1']),
                                   '2=' + str(settings['2']),
                                   '3=' + str(settings['3']),
                                   '4=' + str(settings['4'])
                                   ])
            # write these settings to the .ini file
            with open(ini_fpath, 'w') as fname:

                s = "\n"
                main_seq = s.join(['[Main]',
                                   str('Filename=' + '"' + set_path + '"'),
                                   str('IDnumber=' + str(tetrode)),
                                   str('KKparamstr=' + kkparmstr),
                                   str(inc_channels)
                                   ])

                clust_ft_seq = s.join(['\n[ClusteringFeatures]',
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

                report_seq = s.join(['\n[Reporting]',
                                     'Log=' + str(settings['Log File']),
                                     'Verbose=' + str(settings['Verbose']),
                                     'Screen=' + str(settings['Screen'])
                                     ])

                for write_order in [main_seq, clust_ft_seq, report_seq]:
                    fname.seek(0, 2)  # seek the files end
                    fname.write(write_order)

                fname.close()

            log_fpath = tet_path + '_log.txt'
            log_fname = tet_fname + '_log.txt'

            cmdline = ["cmd", "/q", "/k", "echo off"]

            reading = 1
            with open(tet_path, 'rb') as f:
                while reading == 1:
                    line = f.readline()
                    if 'experimenter ' in str(line):
                        expter_line = str(line).split(' ', 1)
                        expter_line.remove("b'experimenter")
                        experimenter.append(' '.join(expter_line))
                        reading = 0
                    elif 'data_start' in str(line):
                        reading = 0

            cmd = subprocess.Popen(cmdline, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            if settings['Silent'] == 0:
                batch = bytes(
                    'tint ' + '"' + set_path + '" ' + str(
                        tetrode) + ' "' + log_fpath + '" /runKK /KKoptions "' +
                    ini_fpath + '" /convertkk2cut /visible\n'
                    'exit\n', 'ascii')
            else:
                batch = bytes(
                    'tint ' + '"' + set_path + '" ' + str(
                        tetrode) + ' "' + log_fpath + '" /runKK /KKoptions "' +
                    ini_fpath + '" /convertkk2cut\n'
                                'exit\n', 'ascii')

            cmd.stdin.write(batch)
            cmd.stdin.flush()

            processing = 1

            while processing == 1:
                time.sleep(2)
                new_cont = os.listdir(sub_directory_fullpath)

                if cut_name in new_cont:
                    processing = 0
                    try:
                        try:
                            # moves the log files
                            try:
                                os.rename(log_fpath, os.path.join(logfile_directory, tet_fname + '_log.txt'))
                            except FileNotFoundError:
                                pass

                        except FileExistsError:
                            os.remove(os.path.join(logfile_directory, tet_fname + '_log.txt'))
                            os.rename(log_fpath, os.path.join(logfile_directory, tet_fname + '_log.txt'))
                        try:
                            # moves the .ini files
                            os.rename(ini_fpath, os.path.join(inifile_directory, tet_fname + '.ini'))
                        except FileExistsError:
                            os.remove(os.path.join(inifile_directory, tet_fname + '.ini'))
                            os.rename(ini_fpath, os.path.join(inifile_directory, tet_fname + '.ini'))

                        msg = '[%s %s]: The analysis of the %s file has finished!' % (
                                str(datetime.datetime.now().date()),
                                str(datetime.datetime.now().time())[
                                :8], tet_fname)

                        print_msg(self, msg)
                        pass

                    except PermissionError:
                        processing = 1

                elif log_fname in new_cont:
                    active_tet = []
                    no_spike = []
                    with open(log_fpath, 'r') as f:
                        for line in f:
                            if 'list of active tetrodes:' in line:
                                activ_tet = line
                                if str(tetrode) not in str(line):

                                    if not os.path.exists(inactive_tet_dir):
                                        os.makedirs(inactive_tet_dir)

                                    cur_date = datetime.datetime.now().date()
                                    cur_time = datetime.datetime.now().time()
                                    not_active = ': Tetrode ' + str(tetrode) + ' is not active within the ' + \
                                                 set_file + ' set file!'
                                    error.append('\tTetrode ' + str(tetrode) + ' was not active within the ' + \
                                                 set_file + ' \'.set\' file, couldn\'t perform analysis.\n')
                                    print('[' + str(cur_date) + ' ' + str(cur_time)[:8] + ']' + not_active)
                                    break
                            elif 'reading 0 spikes' in line:

                                if not os.path.exists(no_spike_dir):
                                    os.makedirs(no_spike_dir)

                                no_spike = 1
                                # skipped_mat.append(1)
                                cur_date = datetime.datetime.now().date()
                                cur_time = datetime.datetime.now().time()
                                not_spike = ': Tetrode ' + str(tetrode) + ' within the ' + \
                                             set_file + ' \'.set\' file, has no spikes, skipping analysis!'

                                error.append('\tTetrode ' + str(tetrode) + ' within the ' + \
                                             set_file + ' \'.set\' file, had no spikes, couldn\'t perform analysis\n')

                                print('[' + str(cur_date) + ' ' + str(cur_time)[:8] + ']' + not_spike)
                                break

                            else:
                                activ_tet = []

                    if 'activ_tet' in locals() and activ_tet != [] and str(tetrode) not in str(activ_tet):
                        x = 1
                        while x == 1:
                            try:
                                try:
                                    # moves the log files
                                    try:
                                        os.rename(log_fpath,
                                                  os.path.join(logfile_directory, tet_fname + '_log.txt'))
                                    except FileNotFoundError:
                                        pass

                                except FileExistsError:
                                    os.remove(os.path.join(logfile_directory, tet_fname + '_log.txt'))
                                    os.rename(log_fpath,
                                              os.path.join(logfile_directory, tet_fname + '_log.txt'))
                                try:
                                    # moves the .ini files
                                    os.rename(ini_fpath, os.path.join(inifile_directory, tet_fname + '.ini'))
                                except FileExistsError:
                                    os.remove(os.path.join(inifile_directory, tet_fname + '.ini'))
                                    os.rename(ini_fpath, os.path.join(inifile_directory, tet_fname + '.ini'))

                                os.rename(tet_path, os.path.join(inactive_tet_dir, tet_fname))

                                x = 0

                            except PermissionError:
                                x = 1
                            processing = 0

                    if 'no_spike' in locals() and no_spike == 1:
                        x = 1
                        while x == 1:
                            try:
                                try:
                                    # moves the log files
                                    try:
                                        os.rename(log_fpath,
                                                  os.path.join(logfile_directory, tet_fname + '_log.txt'))
                                    except FileNotFoundError:
                                        pass

                                except FileExistsError:
                                    os.remove(os.path.join(logfile_directory, tet_fname + '_log.txt'))
                                    os.rename(log_fpath,
                                              os.path.join(logfile_directory, tet_fname + '_log.txt'))
                                try:
                                    # moves the .ini files
                                    os.rename(ini_fpath, os.path.join(inifile_directory, tet_fname + '.ini'))
                                except FileExistsError:
                                    os.remove(os.path.join(inifile_directory, tet_fname + '.ini'))
                                    os.rename(ini_fpath, os.path.join(inifile_directory, tet_fname + '.ini'))

                                os.rename(tet_path, os.path.join(no_spike_dir, tet_fname))

                                x = 0

                            except PermissionError:
                                x = 1
                            processing = 0

            try:
                q.task_done()
            except ValueError:
                pass


def check_klusta_ready(settings, directory, self=None, settings_filename=None, numThreads=None, numCores=None):
    klusta_ready = True

    # with open(settings_filename, 'r+') as f:  # opens setting file
    #     settings = json.load(f)  # loads settings

    settings['NumThreads'] = str(numThreads)
    settings['Cores'] = str(numCores)

    if settings_filename is not None:
        # overwrite settings filename with current settings
        with open(settings_filename, 'w') as filename:
            json.dump(settings, filename)

    if settings['NumFet'] > 4:

        if self is not None:
            self.choice = ''
            self.LogError.myGUI_signal_str.emit('ManyFet')

            while self.choice == '':
                time.sleep(1)

            if self.choice == QtWidgets.QMessageBox.No:
                klusta_ready = False
            elif self.choice == QtWidgets.QMessageBox.Yes:
                klusta_ready = True
        else:
            print("You have chosen more than four features. clustering will take a long time!")

    if directory == 'No Directory Currently Chosen!':

        if self is None:
            self.choice = ''
            self.LogError.myGUI_signal_str.emit('NoDir')
            while self.choice == '':
                time.sleep(1)

            if self.choice == QtWidgets.QMessageBox.Ok:
                return False

    if 'Google Drive' in directory:
        if self is None:
            self.choice = ''
            self.LogError.myGUI_signal_str.emit('GoogleDir')
            while self.choice == '':
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


def send_email(experimenter, error, sub_directory, processed_directory, self=None):

    smtpfile = os.path.join(self.SETTINGS_DIR, 'smtp.json')
    with open(smtpfile, 'r+') as filename:
        smtp_data = json.load(filename)

        if smtp_data['Notification'] == 'On':

            expter_fname = os.path.join(self.SETTINGS_DIR, 'experimenter.json')
            with open(expter_fname, 'r+') as f:
                expters = json.load(f)

            toaddrs = []
            for key, value in expters.items():
                if str(key).lower() in str(experimenter).lower():
                    if ',' in value and ', ' not in value:
                        addresses = value.split(', ', 1)
                        for address in addresses:
                            toaddrs.append(address)
                    elif ', ' in value:
                        addresses = value.split(', ', 1)
                        for address in addresses:
                            toaddrs.append(address)
                    else:
                        addresses = [value]
                        for address in addresses:
                            toaddrs.append(address)

            username = smtp_data['Username']
            password = smtp_data['Password']

            fromaddr = username

            if not error:
                error = ['\tNo errors to report on the processing of this folder!\n\n']

            subject = str(sub_directory) + ' folder processed! [Automated Message]'

            text_list = ['Greetings from the Batch-TINTV2 automated messaging system!\n\n',
                         'The "' + sub_directory + '" directory has finished processing and is now located in the "' +
                         processed_directory + '" folder.\n\n',
                         'The errors that occurred during processing are the following:\n\n']

            for i in range(len(error)):
                text_list.append(error[i])

            '''
            for i in range(len(error)):
                for k in range(1, int(self.settings['NumTet']) + 1):
                    if '%s %d' % ('Tetrode', k) in error[i]:
                        while
                        text_list.append(error[i])
            '''
            text_list.append('\nHave a nice day,\n')
            text_list.append('Batch-TINTV2\n\n')
            text = ''.join(text_list)

            # Prepare actual message
            message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
                """ % (fromaddr, ", ".join(toaddrs), subject, text)

            try:
                # server = smtplib.SMTP('smtp.gmail.com:587')
                server = smtplib.SMTP(str(smtp_data['ServerName']) + ':' + str(smtp_data['Port']))
                server.ehlo()
                server.starttls()
                server.login(username, password)
                server.sendmail(fromaddr, toaddrs, message)
                server.close()

                self.LogAppend.myGUI_signal_str.emit(
                    '[%s %s]: Successfully sent e-mail to: %s!' % (
                        str(datetime.datetime.now().date()),
                        str(datetime.datetime.now().time())[
                        :8], experimenter))
            except:
                if not toaddrs:
                    self.LogAppend.myGUI_signal_str.emit(
                        '[%s %s]: Failed to send e-mail, could not establish an address to send the e-mail to!' % (
                            str(datetime.datetime.now().date()),
                            str(datetime.datetime.now().time())[
                            :8]))

                else:
                    self.LogAppend.myGUI_signal_str.emit(
                        '[%s %s]: Failed to send e-mail, could be due to security settings of your e-mail!' % (
                            str(datetime.datetime.now().date()),
                            str(datetime.datetime.now().time())[
                            :8]))


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


def session_analyzable(directory, session, tetrodes):
    session_basename = os.path.splitext(session)[0]
    analyzable = [file for file in tetrodes if not os.path.exists(os.path.join(directory,
                                                                                '%s_%s.cut' % (session_basename,
                                                                                               os.path.splitext(file)[
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
