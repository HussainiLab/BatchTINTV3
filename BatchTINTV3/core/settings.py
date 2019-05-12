from PyQt5 import QtCore, QtWidgets
import json
import os
from .utils import center, background
from .defaultParameters import defaultMaxPos, defaultnStarts, defaultRandomSeed, defaultDistThresh, \
    defaultPenaltyK, defaultPenaltyKLogN, defaultChangedThresh, defaultMaxIter, defaultSplitEvery, defaultFullStepEvery, \
    defaultSubset, defaultPC1, defaultPC2, defaultPC3, defaultInclude1, defaultInclude2, defaultInclude3, defaultInclude4, \
    defaultVerbose, defaultScreen, defaultLogFile, defaultNumFeat, defaultSilent, defaultUserFeatures, \
    defaultNumThreads, defaultNonBatch, defaultPC4, defaultA, defaultVt, defaultP, defaultT, defaulttP, defaulttT, \
    defaultEn, defaultAr, default_delete_temporary, default_move_processed


class Settings_Window(QtWidgets.QTabWidget):
    def __init__(self):
        super(Settings_Window, self).__init__()
        self.Settings()

    def Settings(self):
        """
        This method will create all the QWidgets and be involved for the overall visuals for this window

        :return:
        """

        self.position = {}

        self.previous_basic_settings = None
        self.previous_advanced_settings = None
        self.settings = {}

        self.default_adv = {'MaxPos': defaultMaxPos, 'nStarts': defaultnStarts, 'RandomSeed': defaultRandomSeed,
                       'DistThresh': defaultDistThresh, 'PenaltyK': defaultPenaltyK, 'PenaltyKLogN': defaultPenaltyKLogN,
                       'ChangedThresh': defaultChangedThresh, 'MaxIter': defaultMaxIter, 'SplitEvery': defaultSplitEvery,
                       'FullStepEvery': defaultFullStepEvery, 'Subset': defaultSubset}

        tab1 = QtWidgets.QWidget()  # creates the basic tab
        tab2 = QtWidgets.QWidget()  # creates the advanced tab

        background(self)
        # deskW, deskH = background.Background(self)
        self.setWindowTitle("BatchTINT - Settings Window")

        self.addTab(tab1, 'Basic')
        self.addTab(tab2, 'Advanced')

        # ------------------ clustering features --------------------------------
        clust_l = QtWidgets.QLabel('Clustering Features:')

        grid_ft = QtWidgets.QGridLayout()

        self.clust_ft_names = ['PC1', 'PC2', 'PC3', 'PC4',
                               'A', 'Vt', 'P', 'T',
                               'tP', 'tT', 'En', 'Ar']

        self.clust_ft_cbs = {}

        positions = [(i, j) for i in range(4) for j in range(4)]

        for position, clust_ft_name in zip(positions, self.clust_ft_names):

            if clust_ft_name == '':
                continue
            self.position[clust_ft_name] = position
            self.clust_ft_cbs[position] = QtWidgets.QCheckBox(clust_ft_name)
            grid_ft.addWidget(self.clust_ft_cbs[position], *position)

        clust_feat_lay = QtWidgets.QHBoxLayout()
        clust_feat_lay.addWidget(clust_l)
        clust_feat_lay.addLayout(grid_ft)

        # -------------------------- reporting checkboxes ---------------------------------------

        report_l = QtWidgets.QLabel('Reporting Options:')

        self.report = ['Verbose', 'Screen', 'Log File']

        self.report_cbs = {}

        grid_report = QtWidgets.QGridLayout()

        positions = [(i, j) for i in range(1) for j in range(4)]

        for position, option in zip(positions, self.report):
            if option == '':
                continue
            self.position[option] = position
            self.report_cbs[position] = QtWidgets.QCheckBox(option)
            grid_report.addWidget(self.report_cbs[position], *position)

        grid_lay = QtWidgets.QHBoxLayout()
        grid_lay.addWidget(report_l)
        grid_lay.addLayout(grid_report)

        # --------------------------Channels to Include-------------------------------------------

        chan_inc = QtWidgets.QLabel('Channels to Include:')

        grid_chan = QtWidgets.QGridLayout()
        self.chan_names = ['1', '2', '3', '4']

        self.chan_inc_cbs = {}

        positions = [(i, j) for i in range(1) for j in range(4)]
        for position, chan_name in zip(positions, self.chan_names):

            if chan_name == '':
                continue
            self.position[chan_name] = position
            self.chan_inc_cbs[position] = QtWidgets.QCheckBox(chan_name)
            grid_chan.addWidget(self.chan_inc_cbs[position], *position)

        chan_name_lay = QtWidgets.QHBoxLayout()
        chan_name_lay.addWidget(chan_inc)
        chan_name_lay.addLayout(grid_chan)

        # Miscellaneous Settings
        misc_l = QtWidgets.QLabel('Miscellaneous Settings:')

        self.delete_temporary = QtWidgets.QCheckBox("Delete Temporary Files")
        self.move_processed = QtWidgets.QCheckBox("Move Processed Files")

        misc_widgets = [self.delete_temporary, self.move_processed]
        positions = [(i, j) for i in range(1) for j in range(len(misc_widgets))]
        misc_grid = QtWidgets.QGridLayout()
        for position, widget in zip(positions, misc_widgets):
            misc_grid.addWidget(widget, *position)

        misc_layout = QtWidgets.QHBoxLayout()
        misc_layout.addWidget(misc_l)
        misc_layout.addLayout(misc_grid)

        # --------------------------adv lay doublespinbox------------------------------------------------

        row1 = QtWidgets.QHBoxLayout()
        row2 = QtWidgets.QHBoxLayout()
        row3 = QtWidgets.QHBoxLayout()
        row4 = QtWidgets.QHBoxLayout()
        row5 = QtWidgets.QHBoxLayout()
        row6 = QtWidgets.QHBoxLayout()

        maxposclust_l = QtWidgets.QLabel('MaxPossibleClusters: ')
        self.maxpos = QtWidgets.QLineEdit()

        chThresh_l = QtWidgets.QLabel('ChangedThresh: ')
        self.chThresh = QtWidgets.QLineEdit()

        nStarts_l = QtWidgets.QLabel('nStarts: ')
        self.nStarts = QtWidgets.QLineEdit()

        MaxIter_l = QtWidgets.QLabel('MaxIter: ')
        self.Maxiter = QtWidgets.QLineEdit()

        RandomSeed_l = QtWidgets.QLabel('RandomSeed: ')
        self.RandomSeed = QtWidgets.QLineEdit()

        SplitEvery_l = QtWidgets.QLabel('SplitEvery: ')
        self.SplitEvery = QtWidgets.QLineEdit()

        DistThresh_l = QtWidgets.QLabel('DistThresh: ')
        self.DistThresh = QtWidgets.QLineEdit()

        FullStepEvery_l  = QtWidgets.QLabel('FullStepEvery: ')
        self.FullStepEvery = QtWidgets.QLineEdit()

        PenaltyK_l = QtWidgets.QLabel('PenaltyK: ')
        self.PenaltyK = QtWidgets.QLineEdit()

        Subset_l = QtWidgets.QLabel('Subset: ')
        self.Subset = QtWidgets.QLineEdit()

        PenaltyKLogN_l = QtWidgets.QLabel('PenaltyKLogN: ')
        self.PenaltyKLogN = QtWidgets.QLineEdit()

        row1order = [maxposclust_l, self.maxpos, chThresh_l, self.chThresh]
        for order in row1order:
            row1.addWidget(order)

        row2order = [nStarts_l, self.nStarts, MaxIter_l, self.Maxiter]
        for order in row2order:
            row2.addWidget(order)

        row3order = [RandomSeed_l, self.RandomSeed, SplitEvery_l, self.SplitEvery]
        for order in row3order:
            row3.addWidget(order)

        row4order = [DistThresh_l, self.DistThresh, FullStepEvery_l, self.FullStepEvery]
        for order in row4order:
            row4.addWidget(order)

        row5order = [PenaltyK_l, self.PenaltyK, Subset_l, self.Subset]
        for order in row5order:
            row5.addWidget(order)

        row6order = [PenaltyKLogN_l, self.PenaltyKLogN]
        for order in row6order:
            row6.addWidget(order)

        # ------------------------ buttons ----------------------------------------------------
        self.basicdefaultbtn = QtWidgets.QPushButton("Default", tab1)
        self.basicdefaultbtn.clicked.connect(self.basic_default)
        self.advanceddefaultbtn = QtWidgets.QPushButton("Default", tab2)
        self.advanceddefaultbtn.clicked.connect(self.adv_default)

        self.backbtn = QtWidgets.QPushButton('Back', tab1)
        self.backbtn2 = QtWidgets.QPushButton('Back', tab2)

        self.apply_tab1btn = QtWidgets.QPushButton('Apply', tab1)
        self.apply_tab1btn.clicked.connect(self.apply_tab1)

        self.apply_tab2btn = QtWidgets.QPushButton('Apply', tab2)
        self.apply_tab2btn.clicked.connect(self.apply_tab2)

        basic_butn_order = [self.apply_tab1btn, self.basicdefaultbtn, self.backbtn]
        basic_butn_lay = QtWidgets.QHBoxLayout()
        for order in basic_butn_order:
            basic_butn_lay.addWidget(order, 0, QtCore.Qt.AlignCenter)

        adv_butn_order = [self.apply_tab2btn, self.advanceddefaultbtn, self.backbtn2]
        adv_butn_lay = QtWidgets.QHBoxLayout()
        for order in adv_butn_order:
            adv_butn_lay.addWidget(order, 0, QtCore.Qt.AlignCenter)

        # -------------------------- layouts ----------------------------------------------------
        basic_lay_order = [chan_name_lay, clust_feat_lay, grid_lay, misc_layout, basic_butn_lay]
        basic_lay = QtWidgets.QVBoxLayout()

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
        adv_lay = QtWidgets.QVBoxLayout()

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

                if int(self.settings['delete_temporary']) == 1:
                    self.delete_temporary.toggle()

                if int(self.settings['move_processed']) == 1:
                    self.move_processed.toggle()

        except FileNotFoundError:
            with open(self.settings_fname, 'w') as filename:
                # initialize values
                # self.default_set_feats = self.set_feats
                self.default_set_feats = {}
                self.default_set_feats['PC1'] = defaultPC1
                self.default_set_feats['PC2'] = defaultPC2
                self.default_set_feats['PC3'] = defaultPC3
                self.default_set_feats['PC4'] = defaultPC4
                self.default_set_feats['A'] = defaultA
                self.default_set_feats['Vt'] = defaultVt
                self.default_set_feats['P'] = defaultP
                self.default_set_feats['T'] = defaultT
                self.default_set_feats['tP'] = defaulttP
                self.default_set_feats['tT'] = defaulttT
                self.default_set_feats['En'] = defaultEn
                self.default_set_feats['Ar'] = defaultAr

                # initialize the values
                # self.default_set_channels_inc = self.set_chan_inc
                self.default_set_channels_inc = {}
                self.default_set_channels_inc['1'] = defaultInclude1
                self.default_set_channels_inc['2'] = defaultInclude2
                self.default_set_channels_inc['3'] = defaultInclude3
                self.default_set_channels_inc['4'] = defaultInclude4

                # self.default_reporting = self.reporting
                self.default_reporting = {}
                self.default_reporting['Verbose'] = defaultVerbose
                self.default_reporting['Screen'] = defaultScreen
                self.default_reporting['Log File'] = defaultLogFile

                self.settings = {}
                for dictionary in [self.default_adv, self.default_set_feats, self.default_set_channels_inc,
                                   self.default_reporting]:
                    self.settings.update(dictionary)

                self.settings['NumFeat'] = defaultNumFeat
                self.settings['Silent'] = defaultSilent
                # self.settings['Multi'] = defaultMulti
                self.settings['UseFeatures'] = defaultUserFeatures
                self.settings['NumThreads'] = defaultNumThreads
                self.settings['Cores'] = os.cpu_count()
                self.settings['nonbatch'] = defaultNonBatch
                self.settings['delete_temporary'] = default_delete_temporary
                self.settings['move_processed'] = default_move_processed

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

                if int(self.settings['delete_temporary']) == 1:
                    self.delete_temporary.toggle()

                if int(self.settings['move_processed']) == 1:
                    self.move_processed.toggle()

        center(self)

    def adv_default(self):
        """
        Sets the Advanced Settings to their Default Values
        """
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

        # overwrite the settings file
        self.overwrite_advanced_settings(False)

    def basic_default(self):
        """
        Sets the Basic Settings to their Default Values
        """
        # settting default feature values
        default_set_feats = {'PC1': defaultPC1, 'PC2': defaultPC2, 'PC3': defaultPC3, 'PC4': defaultPC4,
                             'A': defaultA, 'Vt': defaultVt, 'P': defaultP, 'T': defaultT, 'tP': defaulttP,
                             'tT': defaulttT, 'En': defaultEn, 'Ar': defaultAr}

        # setting default channels to include
        default_set_channels_inc = {'1': defaultInclude1, '2': defaultInclude2, '3': defaultInclude3,
                                    '4': defaultInclude4}

        # setting default reporting options
        default_reporting = {'Verbose': defaultVerbose, 'Screen': defaultScreen, 'Log File': defaultLogFile}

        # search through the channels to include, check the ones that are supposed to be checked
        # uncheck the ones that are supposed to be unchecked.
        for name in self.chan_names:
            if default_set_channels_inc[name] == 1:
                if not self.chan_inc_cbs[self.position[name]].isChecked():
                    self.chan_inc_cbs[self.position[name]].toggle()
            elif default_set_channels_inc[name] == 0:
                if self.chan_inc_cbs[self.position[name]].isChecked():
                    self.chan_inc_cbs[self.position[name]].toggle()

        # search through the features to include, check the ones that are supposed to be checked
        # uncheck the ones that are supposed to be unchecked.
        for feat in self.clust_ft_names:
            if feat != '':
                if default_set_feats[feat] == 1:
                    # check unchecked items
                    if not self.clust_ft_cbs[self.position[feat]].isChecked():
                        self.clust_ft_cbs[self.position[feat]].toggle()
                elif default_set_feats[feat] == 0:
                    # uncheck checked items
                    if self.clust_ft_cbs[self.position[feat]].isChecked():
                        self.clust_ft_cbs[self.position[feat]].toggle()

        # search through the reporting options, check the ones that are supposed to be checked
        # uncheck the ones that are supposed to be unchecked.
        for option in self.report:
            if default_reporting[option] == 1:
                # check unchecked items
                if not self.report_cbs[self.position[option]].isChecked():
                    self.report_cbs[self.position[option]].toggle()
            elif default_reporting[option] == 0:
                # uncheck checked items
                if self.report_cbs[self.position[option]].isChecked():
                    self.report_cbs[self.position[option]].toggle()

        default_widgets = [self.delete_temporary, self.move_processed]
        default_values = [default_delete_temporary, default_move_processed]
        for widget, default_value in zip(default_widgets, default_values):
            if int(default_value) == 1:
                if not widget.isChecked():
                    widget.toggle()
            elif int(default_value) == 0:
                if widget.isChecked():
                    widget.toggle()

        # overwrite the settings file
        self.overwrite_basic_settings(False)

    def overwrite_basic_settings(self, overwrite_previous):
        """
        Iterate through all the basic settings and save their values to the settings file

        :return:
        """

        settings = self.get_basic_settings()

        if overwrite_previous:
            self.previous_basic_settings = settings

        for key, value in settings.items():
            self.settings[key] = value

        with open(self.settings_fname, 'w') as filename:
            json.dump(self.settings, filename)  # save the default values to this file

    def apply_tab1(self):
        self.overwrite_basic_settings(True)
        self.backbtn.animateClick()

    def overwrite_advanced_settings(self, overwrite_previous):
        """
        overwrites the settings file with the current values

        :return:
        """

        settings = self. get_advanced_settings()

        if overwrite_previous:
            self.previous_advanced_settings = settings

        for key, value in settings.items():
            self.settings[key] = value

        with open(self.settings_fname, 'w') as filename:
            json.dump(self.settings, filename)  # save the default values to this file

    def apply_tab2(self):
        self.overwrite_advanced_settings(True)
        self.backbtn2.animateClick()

    def backbtn_function(self):
        self.set_previous_advanced_settings(self.previous_advanced_settings)
        self.set_previous_basic_settings(self.previous_basic_settings)

    def raise_window(self):
        self.raise_()

        self.previous_basic_settings = self.get_basic_settings()
        self.previous_advanced_settings = self.get_advanced_settings()

        self.show()

    def get_basic_settings(self):

        settings = {}

        # iterating through the channels to include and setting the value to either 1 or 0 for checked/unchecked
        for name in self.chan_names:
            if self.chan_inc_cbs[self.position[name]].isChecked():
                settings[name] = 1
            else:
                settings[name] = 0

        for feat in self.clust_ft_names:
            if self.clust_ft_cbs[self.position[feat]].isChecked():
                settings[feat] = 1
            else:
                settings[feat] = 0

        for option in self.report:
            if self.report_cbs[self.position[option]].isChecked():
                settings[option] = 1
            else:
                settings[option] = 0

        if self.delete_temporary.isChecked():
            settings['delete_temporary'] = 1
        else:
            settings['delete_temporary'] = 0

        if self.move_processed.isChecked():
            settings['move_processed'] = 1
        else:
            settings['move_processed'] = 0

        chan_inc = [chan for chan in self.chan_names if settings[chan] == 1]
        feat_inc = [feat for feat in self.clust_ft_names if settings[feat] == 1]

        UseFeat = ''
        for i in range(len(self.chan_names)):
            for j in range(len(feat_inc)):
                if str(i + 1) in chan_inc:
                    UseFeat += '1'
                else:
                    UseFeat += '0'
        UseFeat += '1'

        settings['NumFeat'] = len(feat_inc)
        settings['UseFeatures'] = UseFeat

        return settings

    def get_advanced_settings(self):

        settings = {}
        settings['MaxPos'] = self.maxpos.text()
        settings['nStarts'] = self.nStarts.text()
        settings['RandomSeed'] = self.RandomSeed.text()
        settings['DistThresh'] = self.DistThresh.text()
        settings['PenaltyK'] = self.PenaltyK.text()
        settings['PenaltyKLogN'] = self.PenaltyKLogN.text()
        settings['ChangedThresh'] = self.chThresh.text()
        settings['MaxIter'] = self.Maxiter.text()
        settings['SplitEvery'] = self.SplitEvery.text()
        settings['FullStepEvery'] = self.FullStepEvery.text()
        settings['Subset'] = self.Subset.text()

        return settings

    def set_previous_basic_settings(self, settings):
        # search through the channels to include, check the ones that are supposed to be checked
        # uncheck the ones that are supposed to be unchecked.
        for name in self.chan_names:
            if settings[name] == 1:
                if not self.chan_inc_cbs[self.position[name]].isChecked():
                    self.chan_inc_cbs[self.position[name]].toggle()
            elif settings[name] == 0:
                if self.chan_inc_cbs[self.position[name]].isChecked():
                    self.chan_inc_cbs[self.position[name]].toggle()

        # search through the features to include, check the ones that are supposed to be checked
        # uncheck the ones that are supposed to be unchecked.
        for feat in self.clust_ft_names:
            if feat != '':
                if settings[feat] == 1:
                    # check unchecked items
                    if not self.clust_ft_cbs[self.position[feat]].isChecked():
                        self.clust_ft_cbs[self.position[feat]].toggle()
                elif settings[feat] == 0:
                    # uncheck checked items
                    if self.clust_ft_cbs[self.position[feat]].isChecked():
                        self.clust_ft_cbs[self.position[feat]].toggle()

        # search through the reporting options, check the ones that are supposed to be checked
        # uncheck the ones that are supposed to be unchecked.
        for option in self.report:
            if settings[option] == 1:
                # check unchecked items
                if not self.report_cbs[self.position[option]].isChecked():
                    self.report_cbs[self.position[option]].toggle()
            elif settings[option] == 0:
                # uncheck checked items
                if self.report_cbs[self.position[option]].isChecked():
                    self.report_cbs[self.position[option]].toggle()

        widgets = [self.delete_temporary, self.move_processed]
        widget_values = [settings['delete_temporary'], settings['move_processed']]
        for widget, default_value in zip(widgets, widget_values):
            if int(default_value) == 1:
                if not widget.isChecked():
                    widget.toggle()
            elif int(default_value) == 0:
                if widget.isChecked():
                    widget.toggle()

        chan_inc = [chan for chan in self.chan_names if settings[chan] == 1]
        feat_inc = [feat for feat in self.clust_ft_names if settings[feat] == 1]

        UseFeat = ''
        for i in range(len(self.chan_names)):
            for j in range(len(feat_inc)):
                if str(i + 1) in chan_inc:
                    UseFeat += '1'
                else:
                    UseFeat += '0'
        UseFeat += '1'

        self.settings['NumFeat'] = len(feat_inc)
        self.settings['UseFeatures'] = UseFeat

    def set_previous_advanced_settings(self, settings):

        if self.maxpos.text() != settings['MaxPos']:
            self.maxpos.setText(settings['MaxPos'])

        if self.nStarts.text() != settings['nStarts']:
            self.nStarts.setText(settings['nStarts'])

        if self.RandomSeed.text() != settings['RandomSeed']:
            self.RandomSeed.setText(settings['RandomSeed'])

        if self.DistThresh.text() != settings['DistThresh']:
            self.DistThresh.setText(settings['DistThresh'])

        if self.PenaltyK.text() != settings['PenaltyK']:
            self.PenaltyK.setText(settings['PenaltyK'])

        if self.PenaltyKLogN.text() != settings['PenaltyKLogN']:
            self.PenaltyKLogN.setText(settings['PenaltyKLogN'])

        if self.chThresh.text() != settings['ChangedThresh']:
            self.chThresh.setText(settings['ChangedThresh'])

        if self.Maxiter.text() != settings['MaxIter']:
            self.Maxiter.setText(settings['MaxIter'])

        if self.SplitEvery.text() != settings['SplitEvery']:
            self.SplitEvery.setText(settings['SplitEvery'])

        if self.FullStepEvery.text() != settings['FullStepEvery']:
            self.FullStepEvery.setText(settings['FullStepEvery'])

        if self.Subset.text() != settings['Subset']:
            self.Subset.setText(settings['Subset'])

