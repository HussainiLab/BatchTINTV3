import os
from distutils.dir_util import copy_tree
import distutils
from core.utils import print_msg
import datetime
import shutil
import time


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
    except distutils.errors.DistutilsFileError as error:
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


def write_klusta_ini(settings, ini_fpath, set_path, tetrode, append=None):
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

    return ini_filename_value


def get_temp_files(set_path, append=None):

    if append is None:
        ini_filename_value = str('Filename="%s"' % set_path)
    else:
        ini_filename_value = str('Filename="%s%s"' % (set_path, append))

    ini_filename_value = str('Filename="%s%s"' % (set_path, append))

    directory = os.path.dirname(fileID)

    file_list = os.path.dirname()