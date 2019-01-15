from PyQt5 import QtCore, QtWidgets
import functools, json
import os
from core.utils import center, background


class Settings_Window(QtWidgets.QTabWidget):
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

        for feat in self.clust_ft_names:
            if feat != '':
                self.set_feats[feat] = 0

        self.clust_ft_cbs = {}

        positions = [(i, j) for i in range(4) for j in range(4)]

        for position, clust_ft_name in zip(positions, self.clust_ft_names):

            if clust_ft_name == '':
                continue
            self.position[clust_ft_name] = position
            self.clust_ft_cbs[position] = QtWidgets.QCheckBox(clust_ft_name)
            grid_ft.addWidget(self.clust_ft_cbs[position], *position)
            self.clust_ft_cbs[position].stateChanged.connect(
                functools.partial(self.channel_feats, clust_ft_name, position))

        # self.clust_ft_cbs.toggle()

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
            self.report_cbs[position].stateChanged.connect(
                functools.partial(self.reporting_options, option, position))

        grid_lay = QtWidgets.QHBoxLayout()
        grid_lay.addWidget(report_l)
        grid_lay.addLayout(grid_report)

        # --------------------------Channels to Include-------------------------------------------

        chan_inc = QtWidgets.QLabel('Channels to Include:')

        grid_chan = QtWidgets.QGridLayout()
        self.chan_names = ['1', '2', '3', '4']

        for chan in self.chan_names:
            self.set_chan_inc[chan] = 0

        self.chan_inc_cbs = {}

        positions = [(i, j) for i in range(1) for j in range(4)]

        for position, chan_name in zip(positions, self.chan_names):

            if chan_name == '':
                continue
            self.position[chan_name] = position
            self.chan_inc_cbs[position] = QtWidgets.QCheckBox(chan_name)
            grid_chan.addWidget(self.chan_inc_cbs[position], *position)
            self.chan_inc_cbs[position].stateChanged.connect(
                functools.partial(self.channel_include, chan_name, position))
            self.chan_inc_cbs[position].setToolTip('Include channel ' + str(chan_name) + ' in the analysis.')

        chan_name_lay = QtWidgets.QHBoxLayout()
        chan_name_lay.addWidget(chan_inc)
        chan_name_lay.addLayout(grid_chan)

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

        self.apply_tab2btn = QtWidgets.QPushButton('Apply',tab2)
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
        basic_lay_order = [chan_name_lay, clust_feat_lay, grid_lay, basic_butn_lay]
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
                # self.num_tet.setText(str(self.settings['NumTet']))

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

                self.settings['NumFet'] = 3
                self.settings['Silent'] = 1
                self.settings['Multi'] = 0
                self.settings['UseFeatures'] = '1111111111111'
                self.settings['NumThreads'] = 1
                self.settings['Cores'] = os.cpu_count()
                self.settings['nonbatch'] = 0

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
        center(self)

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
        default_set_feats = {'PC1': 1, 'PC2': 1, 'PC3': 1}
        default_set_channels_inc = {'1': 1, '2': 1, '3': 1, '4': 1}
        default_reporting = {'Verbose': 1, 'Screen': 1, 'Log File': 1}

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
            for i in range(len(self.chan_names)):
                for j in range(len(feat_inc)):
                    if str(i+1) in chan_inc:
                        UseFeat += '1'
                    else:
                        UseFeat += '0'
            UseFeat += '1'

            self.settings['NumFet'] = len(feat_inc)
            self.settings['UseFeatures'] = UseFeat

            self.backbtn.animateClick()

        with open(self.settings_fname, 'w') as filename:
            json.dump(self.settings, filename)  # save the default values to this file

    def apply_tab2(self):

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

    def raise_window(self):
        self.raise_()
        self.show()
