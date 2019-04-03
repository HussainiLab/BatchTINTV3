import os
# ------------- advanced klusta settings -------------

defaultMaxPos = 30
defaultnStarts = 1
defaultRandomSeed = 1
defaultDistThresh = 6.907755
defaultPenaltyK = 1.0
defaultPenaltyKLogN = 0.0
defaultChangedThresh = 0.05
defaultMaxIter = 500
defaultSplitEvery = 40
defaultFullStepEvery = 20
defaultSubset = 1

# ------------- basic klusta settings -------------

# default feature settings
defaultPC1 = 1
defaultPC2 = 1
defaultPC3 = 1
defaultPC4 = 0
defaultA = 0
defaultVt = 0
defaultP = 0
defaultT = 0
defaulttP = 0
defaulttT = 0
defaultEn = 0
defaultAr = 0

# default channels to include
defaultInclude1 = 1
defaultInclude2 = 1
defaultInclude3 = 1
defaultInclude4 = 1

# default reporting options
defaultVerbose = 1
defaultScreen = 1
defaultLogFile = 1

default_reporting = {'Verbose': defaultVerbose, 'Screen': defaultScreen, 'Log File': defaultLogFile}

# --------- misc settings -------------------------

chan_names = ['1', '2', '3', '4']
default_chan_value = {'1': defaultInclude1, '2': defaultInclude2, '3': defaultInclude3, '4': defaultInclude4}

clust_feature_names = ['PC1', 'PC2', 'PC3', 'PC4', 'A', 'Vt', 'P', 'T', 'tP', 'tT', 'En', 'Ar']


default_feature_list = {'PC1': defaultPC1, 'PC2': defaultPC2, 'PC3': defaultPC3, 'PC4': defaultPC4, 'A': defaultA,
                        'Vt': defaultVt, 'P': defaultP, 'T': defaultT, 'tP': defaulttP, 'tT': defaulttT,
                        'En': defaultEn, 'Ar': defaultAr}

chan_inc = [chan for chan in chan_names if default_chan_value[chan] == 1]
feat_inc = [feat for feat in clust_feature_names if default_feature_list[feat] == 1]

defaultUserFeatures = ''
for i in range(len(chan_names)):
    for j in range(len(feat_inc)):
        if str(i + 1) in chan_inc:
            defaultUserFeatures += '1'
        else:
            defaultUserFeatures += '0'

# add an additional 1 for timestamp
defaultUserFeatures += '1'
# defaultUserFeatures = '1111111111111'


defaultNumFeat = len(feat_inc)
defaultSilent = 1

defaultNumThreads = 1
defaultNonBatch = 0
defaultMoveValue = 1

# ------------- default smtp settings ----------------
defaultServerName = 'smtp.gmail.com'
defaultPort = '587'
defaultUsername = ''
defaultPassword = ''
defaultNotification = 'Off'


# ------------- Debug options -----------------------------

DebugSkipKlusta = True

# misc options

defaultAppend = ''


def get_default_settings():
    settings = {}

    settings.update(default_chan_value)
    settings.update(default_feature_list)
    settings.update(default_reporting)

    UseFeatures, numFeats = calculateUseFeatures(settings)

    settings['UseFeatures'] = UseFeatures
    settings['NumFeat'] = numFeats

    settings['NumThreads'] = defaultNumThreads

    settings['MaxPos'] = defaultMaxPos
    settings['nStarts'] = defaultnStarts
    settings['RandomSeed'] = defaultRandomSeed
    settings['DistThresh'] = defaultDistThresh
    settings['FullStepEvery'] = defaultFullStepEvery
    settings['ChangedThresh'] = defaultChangedThresh
    settings['MaxIter'] = defaultMaxIter
    settings['SplitEvery'] = defaultSplitEvery
    settings['Subset'] = defaultSubset
    settings['PenaltyK'] = defaultPenaltyK
    settings['PenaltyKLogN'] = defaultPenaltyKLogN

    settings['Silent'] = defaultSilent
    settings['NumThreads'] = defaultNumThreads
    settings['Cores'] = os.cpu_count()
    settings['nonbatch'] = defaultNonBatch

    settings['MoveFiles'] = defaultMoveValue

    return settings


def calculateUseFeatures(settings):
    """
    Creates a mask of features to use for each channel

    For every channel to include there will be 1 value,
    """

    # figuring which channels are on and off
    chan_values = {}
    for name in chan_names:
        chan_values[name] = settings[name]

    # defining the channels
    feature_values = {}
    for name in clust_feature_names:
        feature_values[name] = settings[name]

    chan_inc = [chan for chan in chan_names if chan_values[chan] == 1]
    feat_inc = [feat for feat in clust_feature_names if feature_values[feat] == 1]

    UseFeatures = ''
    for i in range(len(chan_names)):
        for j in range(len(feat_inc)):
            if str(i + 1) in chan_inc:
                UseFeatures += '1'
            else:
                UseFeatures += '0'
    UseFeatures += '1'  # additional one for the timestamp

    # returns the Feature mask and the number of features to include

    return UseFeatures, len(feat_inc)
