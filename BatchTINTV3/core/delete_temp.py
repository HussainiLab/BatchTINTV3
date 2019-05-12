import os


def get_temp_files(set_path, append=None):

    directory = os.path.dirname(set_path)

    basename = os.path.basename(set_path)
    if append is not None:
        basename += append

    file_list = os.listdir(directory)

    temp_files = [os.path.join(directory, file) for file in file_list if
                  basename in file and is_temp_ext(os.path.join(directory, file))]

    return temp_files


def ext_found(filename, ex):
    if filename.find(ex) != -1:
        return True
    return False


def is_temp_ext(filename):
    extensions = ['.temp.clu.', '.klg.', '.initialclusters.', '.fmask.', '.fet.']

    if any(ext_found(filename, ex) for ex in extensions):
        for ex in extensions:
            if ex in filename:
                filename = filename[filename.find(ex):]
                if any(ex == x for x in ['.temp.clu.', '.klg.', '.fmask.', '.fet.']):
                    try:
                        int(os.path.splitext(filename[1:])[-1][1:])
                        return True
                    except ValueError:
                        pass
                elif '.initialclusters.' in ex:
                    filename = filename.split('.')
                    try:
                        int(filename[2])
                        int(filename[4])
                        return True
                    except ValueError:
                        pass
    return False
