from PyQt5 import QtCore, QtWidgets
from .utils import background, center
from .defaultParameters import defaultServerName, defaultPort, defaultUsername, defaultPassword, \
    defaultNotification
import os, json, datetime
import smtplib


def send_email(errors, analyzed_directory, processed_directory, smtp_settings, expter_settings, self=None):

    if smtp_settings['Notification'] == 1:
        for experimenter, experimenter_errors in errors.items():
            toaddrs = []
            for key, value in expter_settings.items():
                if str(key).lower() in str(experimenter).lower():
                    addresses = value.split(',')
                    for address in addresses:
                        toaddrs.append(address.strip())

            username = smtp_settings['Username']
            password = smtp_settings['Password']

            fromaddr = username

            subject = '%s folder processed! [Automated Message]' % str(analyzed_directory)

            text_list = ['Greetings from the Batch-TINTV3 automated messaging system!\n\n The "%s" ' % analyzed_directory + \
                         '" directory has finished processing and is now located in the "%s" folder.\n\n' % processed_directory + \
                         'The errors that occurred during processing are the following:\n\n']

            if len(experimenter_errors) == 0:
                text_list.append(['\n\nNo errors to report on the processing of this folder!\n\n'])
            else:
                for error in experimenter_errors:
                    text_list.append('\n\n%s' % error)

            text_list.append('\nHave a nice day,\n')
            text_list.append('Batch-TINTV3\n\n')
            text = ''.join(text_list)

            # Prepare actual message
            message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
                """ % (fromaddr, ", ".join(toaddrs), subject, text)

            try:
                # server = smtplib.SMTP('smtp.gmail.com:587')
                server = smtplib.SMTP(str(smtp_settings['ServerName']) + ':' + str(smtp_settings['Port']))
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


class SmtpSettings(QtWidgets.QWidget):
    def __init__(self):
        super(SmtpSettings, self).__init__()
        background(self)
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
                self.smtp_data['ServerName'] = defaultServerName
                self.smtp_data['Port'] = defaultPort
                self.smtp_data['Username'] = defaultUsername
                self.smtp_data['Password'] = defaultPassword
                self.smtp_data['Notification'] = defaultNotification
                json.dump(self.smtp_data, filename)

        self.setWindowTitle("BatchTINT - SMTP Settings")

        # ----------------- smtp widgets ------------------------
        self.expterList = QtWidgets.QTreeWidget()
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
            new_item = QtWidgets.QTreeWidgetItem()
            new_item.setFlags(new_item.flags() |QtCore.Qt.ItemIsEditable)
            new_item.setText(0, key)
            new_item.setText(1, value)
            self.expterList.addTopLevelItem(new_item)

        self.backbtn = QtWidgets.QPushButton('Back', self)
        applybtn = QtWidgets.QPushButton('Apply', self)
        applybtn.clicked.connect(self.ApplyBtn)

        rembtn = QtWidgets.QPushButton('Delete Selected Experimenters', self)
        rembtn.clicked.connect(self.removeItems)

        self.addbtn = QtWidgets.QPushButton('Add Experimenter', self)

        server_name_l = QtWidgets.QLabel('Server Name: ')
        self.server_name_edit = QtWidgets.QLineEdit()
        self.server_name_edit.setText(self.smtp_data['ServerName'])
        server_lay = QtWidgets.QHBoxLayout()
        server_lay.addWidget(server_name_l)
        server_lay.addWidget(self.server_name_edit)

        port_l = QtWidgets.QLabel('Port: ')
        self.port_edit = QtWidgets.QLineEdit()
        self.port_edit.setText(self.smtp_data['Port'])
        port_lay = QtWidgets.QHBoxLayout()
        port_lay.addWidget(port_l)
        port_lay.addWidget(self.port_edit)

        pass_l = QtWidgets.QLabel('Password: ')
        self.pass_edit = QtWidgets.QLineEdit()
        self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pass_edit.setText(self.smtp_data['Password'])
        pass_lay = QtWidgets.QHBoxLayout()
        pass_lay.addWidget(pass_l)
        pass_lay.addWidget(self.pass_edit)

        username_l = QtWidgets.QLabel('Username: ')
        self.username_edit = QtWidgets.QLineEdit()
        self.username_edit.setText(self.smtp_data['Username'])
        username_lay = QtWidgets.QHBoxLayout()
        username_lay.addWidget(username_l)
        username_lay.addWidget(self.username_edit)

        server_layout = QtWidgets.QHBoxLayout()
        server_layout.addLayout(server_lay)
        server_layout.addLayout(port_lay)

        user_layout = QtWidgets.QHBoxLayout()
        user_layout.addLayout(username_lay)
        user_layout.addLayout(pass_lay)

        self.notification_cb = QtWidgets.QCheckBox('Allow Email Notifications: ')
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
        layout = QtWidgets.QVBoxLayout()

        btn_layout = QtWidgets.QHBoxLayout()
        btn_order = [applybtn, self.addbtn, rembtn, self.backbtn]

        for butn in btn_order:
            btn_layout.addWidget(butn)

        layout_order = [self.notification_cb, server_layout, user_layout, self.expterList, btn_layout]

        for order in layout_order:
            if 'Layout' in order.__str__():
                layout.addLayout(order)
            else:
                layout.addWidget(order)

        self.setLayout(layout)

        center(self)

    def removeItems(self):
        root = self.expterList.invisibleRootItem()
        try:
            with open(self.expter_fname, 'r+') as f:
                expters = json.load(f)
        except FileNotFoundError:
            return

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


class AddExpter(QtWidgets.QWidget):
    """This method is used to provide a dialog for the user to add a user to the SMTP Settings"""
    def __init__(self):
        super(AddExpter, self).__init__()
        background(self)
        # deskW, deskH = background.Background(self)
        width = self.deskW / 3
        height = self.deskH / 3
        self.setGeometry(0, 0, width, height)
        self.setWindowTitle("BatchTINT - Add Experimenter")

        # ------------- widgets ---------------------------------------------------

        self.cancelbtn = QtWidgets.QPushButton('Cancel', self)
        self.addbtn = QtWidgets.QPushButton('Add', self)

        self.backbtn = QtWidgets.QPushButton('Back', self)

        expter_l = QtWidgets.QLabel('Experimenter: ')
        self.expter_edit = QtWidgets.QLineEdit()
        expter_lay = QtWidgets.QHBoxLayout()
        expter_lay.addWidget(expter_l)
        expter_lay.addWidget(self.expter_edit)

        email_l = QtWidgets.QLabel('E-Mail: ')
        email_l.setToolTip('Can add multiple e-mails (e-mails separated by a comma followed by a space)')
        self.email_edit = QtWidgets.QLineEdit()
        self.email_edit.setToolTip('Can add multiple e-mails (e-mails separated by a comma followed by a space)')
        email_lay = QtWidgets.QHBoxLayout()
        email_lay.addWidget(email_l)
        email_lay.addWidget(self.email_edit)

        # ------------------ layout ---------------------------------------------------------

        layout = QtWidgets.QVBoxLayout()

        btn_layout = QtWidgets.QHBoxLayout()
        btn_order = [self.addbtn, self.backbtn, self.cancelbtn]

        for butn in btn_order:
            btn_layout.addWidget(butn)

        layout_order = [expter_lay, email_lay, btn_layout]

        for order in layout_order:
            if 'Layout' in order.__str__():
                layout.addLayout(order)
            else:
                layout.addWidget(order)

        self.setLayout(layout)

        center(self)


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

    new_item = QtWidgets.QTreeWidgetItem()
    new_item.setFlags(new_item.flags() | QtCore.Qt.ItemIsEditable)
    new_item.setText(0, str(self.expter_edit.text()).title())
    new_item.setText(1, self.email_edit.text())
    main.expterList.addTopLevelItem(new_item)

    self.backbtn.animateClick()
    self.cancelbtn.animateClick()
