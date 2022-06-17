from PyQt6 import QtWidgets, QtCore, QtGui
from src.gui import headerbar, logger, worker, controller
from src.logs import *
import os


class Ui(QtWidgets.QMainWindow):
    # Signals for controlling the worker
    controllerDo = QtCore.pyqtSignal(controller.Controller.Task)

    def __init__(self):
        super().__init__()
        self.setupUi()
        self.setupThreading()
        self.setupSlots()
        
        self.geckodriver:str
        self.executable:str
        self.show()

    @property
    def model_Progress(self) -> int:
        """The current status of the progress bar"""
        return self.progressBar.value()

    @model_Progress.setter
    def model_Progress(self, value: int) -> None:
        self.progressBar.setValue(value)

    @property
    def model_NodesRead(self):
        """How many nodes have been fully read?"""
        return int(self.num_nodes_read.text())

    @model_NodesRead.setter
    def model_NodesRead(self, count: int):
        self.num_nodes_read.setText(str(count))

    @property
    def model_NodesQueued(self):
        """How many nodes are queued to run"""
        return int(self.num_nodes_queued.text())

    @model_NodesQueued.setter
    def model_NodesQueued(self, count: int):
        self.num_nodes_queued.setText(str(count))

    def setupSlots(self):
        """Setup all the signals/slots we'll need to use"""
        # Make the minimize and close buttons work
        self.headerBar.btn_close.clicked.connect(
            lambda: self.controllerDo.emit(
                controller.Controller.Task.quit))
        self.headerBar.btn_min.clicked.connect(
            self.showMinimized)

        self.selectFileButton.clicked.connect(self.doFileDialog)

        # Setup the startup functions for each of the worker control buttons
        self.runButton.clicked.connect(self.runButtonClicked)

        self.pauseButton.clicked.connect(
            lambda: self.controllerDo.emit(
                controller.Controller.Task.togglePause))
        
        self.cancelButton.clicked.connect(
            lambda: self.controllerDo.emit(
                controller.Controller.Task.Cancel))

        # Connect myself to the controller
        self.controllerDo.connect(self.controller.execute)

        # and connect it back to me
        self.controller.finished.connect(self.endController)

    def setupThreading(self):
        """Initialize the controller and worker threads"""
        # make the thread contexts
        self.work_thread = QtCore.QThread(self)
        self.control_thread = QtCore.QThread(self)

        self.worker = worker.Worker(self)
        self.worker.moveToThread(self.work_thread)

        self.controller = controller.Controller(self, self.worker)
        self.controller.moveToThread(self.control_thread)

        self.control_thread.start()

        # Connect the worker and thread signals together
        self.worker.finished.connect(self.endWorker)
        self.work_thread.started.connect(self.worker.run)

        # Connect the threads' signals to their View counterparts
        self.worker.logger.connect(JSpider.handle)
        self.controller.logger.connect(JSpider.handle)
        self.worker.progressBar.connect(self.set_progress)
        self.worker.nodesQueued.connect(self.set_nodes_queued)
        self.worker.nodesFinished.connect(self.set_nodes_read)

    def endController(self):
        self.control_thread.terminate()
        self.close()

    def runButtonClicked(self):
        """Start the worker object."""
        self.loginSettingsGroupBox.setEnabled(False)
        self.traversalSettingsGroupBox.setEnabled(False)
        self.outputSettingsGroupBox.setEnabled(False)

        self.runButton.setEnabled(False)
        #Does it say "Run" or "Run Headless?"
        self.Run_old_text = self.runButton.text()
        self.runButton.setText("Running...")
        
        #Enable the pause and cancel buttons
        self.pauseButton.setEnabled(True)
        self.cancelButton.setEnabled(True)

        self.work_thread.start()

    def endWorker(self):
        JSpider.debug("Thread terminated?")
        self.work_thread.quit()
        self.work_thread.wait()
        JSpider.debug("Thread terminated!")

        self.pauseButton.setEnabled(False)
        self.pauseButton.setText("Pause")
        self.cancelButton.setEnabled(False)
        self.runButton.setText(self.Run_old_text)
        self.runButton.setEnabled(True)
        self.loginSettingsGroupBox.setEnabled(True)
        self.traversalSettingsGroupBox.setEnabled(True)
        self.outputSettingsGroupBox.setEnabled(True)
        
    # Utility functions that make the signals work.
    def set_nodes_queued(self, value: int) -> None:
        self.model_NodesQueued = value
        try:
            self.model_Progress = int(1000*self.model_NodesRead
                                      / (self.model_NodesQueued
                                         + self.model_NodesRead))
        except ZeroDivisionError:
            self.model_Progress = 0

    def set_nodes_read(self, value: int) -> None:
        self.model_NodesRead = value
        try:
            self.model_Progress = int(1000*self.model_NodesRead
                                      / (self.model_NodesQueued
                                         + self.model_NodesRead))
        except ZeroDivisionError:
            self.model_Progress = 0

    def set_progress(self, value: int) -> None:
        self.model_Progress = value

    @property
    def Auth(self) -> tuple[str, str]:
        """A tuple containing the login credentials"""
        return (self.usernameInput.text(), self.passwordInput.text())

    @Auth.setter
    def Auth(self, value: tuple[str, str]) -> None:
        self.usernameInput.setText(value[0])
        self.passwordInput.setText(value[1])

    @property
    def TeamContent(self) -> bool:
        """Are we running across My content (false) or Team Content (true)"""
        return self.teamContentRadioButton.isChecked()

    @TeamContent.setter
    def TeamContent(self, value: bool) -> None:
        self.teamContentRadioButton.setChecked(value)

    @property
    def TravelPath(self) -> str:
        """The path to travel before starting traversal"""
        return self.startPathLineEdit.text()

    @TravelPath.setter
    def TravelPath(self, value: str) -> None:
        self.startPathLineEdit.setText(value)

    @property
    def ExportFileName(self) -> str:
        """The file name to export to"""
        return self.filenameLineEdit.text()

    @ExportFileName.setter
    def ExportFileName(self, value: str) -> None:
        self.filenameLineEdit.setText(value)

    def doFileDialog(self) -> str:
        """Utility function to cause a file dialog to open"""
        old_location = os.path.normpath(self.filenameLineEdit.text())
        myfile = QtWidgets.QFileDialog.getSaveFileName(
            self, "Select File to Export",
            old_location, "Excel File (*.xlsx)")[0]
        if myfile:
            self.filenameLineEdit.setText(os.path.normpath(myfile))
        return myfile


    def setupUi(self) -> None:
        """Setup the UI elements."""

        self.setWindowModality(
            QtCore.Qt.WindowModality.ApplicationModal)
        self.setEnabled(True)
        self.resize(550, 800)
        self.setMinimumSize(400, 460)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)

        self.centralwidget = QtWidgets.QWidget(self)

        self.mainLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)

        self.headerBar = headerbar.HeaderBar(self)
        self.headerBar.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                                     QtWidgets.QSizePolicy.Policy.Fixed)

        self.bodyLayout = QtWidgets.QVBoxLayout()
        self.bodyLayout.setContentsMargins(5, 0, 5, 5)
        
        self.mainLayout.addWidget(self.headerBar)
        self.mainLayout.addLayout(self.bodyLayout)
        #No more setup for mainLayout

        self.loginSettingsGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.loginSettingsGroupBox.setFlat(True)

        # Policy for username and password inputs
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Fixed)

        self.usernameLabel = QtWidgets.QLabel(self.loginSettingsGroupBox)

        self.usernameInput = QtWidgets.QLineEdit(self.loginSettingsGroupBox)
        self.usernameInput.setSizePolicy(sizePolicy)

        self.passwordLabel = QtWidgets.QLabel(self.loginSettingsGroupBox)

        self.passwordInput = QtWidgets.QLineEdit(self.loginSettingsGroupBox)
        self.passwordInput.setSizePolicy(sizePolicy)
        self.passwordInput.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.loginSettingsLayout = QtWidgets.QFormLayout(
            self.loginSettingsGroupBox)

        self.loginSettingsLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole,
            self.usernameLabel)
        self.loginSettingsLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole,
            self.usernameInput)
        self.loginSettingsLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.LabelRole,
            self.passwordLabel)
        self.loginSettingsLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.FieldRole,
            self.passwordInput)
        #No more setup for loginSettingsLayout
        

        self.traversalSettingsGroupBox = QtWidgets.QGroupBox(
            self.centralwidget)
        self.traversalSettingsGroupBox.setFlat(True)

        self.traversalSettingsLayout = QtWidgets.QFormLayout(
            self.traversalSettingsGroupBox)

        self.fileLabel = QtWidgets.QLabel(self.traversalSettingsGroupBox)
        self.fileLabel.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Fixed)


        self.contentSrcRadioButtonLayout = QtWidgets.QVBoxLayout()

        self.myContentRadioButton = QtWidgets.QRadioButton(
            self.traversalSettingsGroupBox)
        self.teamContentRadioButton = QtWidgets.QRadioButton(
            self.traversalSettingsGroupBox)
            
        self.teamContentRadioButton.setChecked(True)

        self.contentSrcRadioButtonLayout.addWidget(self.myContentRadioButton)
        self.contentSrcRadioButtonLayout.addWidget(self.teamContentRadioButton)


        self.startPathLabel = QtWidgets.QLabel(self.traversalSettingsGroupBox)

        self.startPathLineEdit = QtWidgets.QLineEdit(
            self.traversalSettingsGroupBox)
        

        self.traversalSettingsLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole,
            self.fileLabel)
        self.traversalSettingsLayout.setLayout(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole,
            self.contentSrcRadioButtonLayout)
        self.traversalSettingsLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.LabelRole,
            self.startPathLabel)
        self.traversalSettingsLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.FieldRole,
            self.startPathLineEdit)


        self.outputSettingsGroupBox = QtWidgets.QGroupBox(self.centralwidget)
        self.outputSettingsGroupBox.setFlat(True)

        self.exportLabel = QtWidgets.QLabel(self.outputSettingsGroupBox)

        self.filenameLineEdit = QtWidgets.QLineEdit(
            self.outputSettingsGroupBox)
        self.filenameLineEdit.setText(os.path.expanduser(
            "~\\Documents\\export.xlsx"))  # Default file

        self.selectFileButton = QtWidgets.QPushButton(
            self.outputSettingsGroupBox)

        self.fileSelectorLayout = QtWidgets.QHBoxLayout()
        self.fileSelectorLayout.addWidget(self.filenameLineEdit)
        self.fileSelectorLayout.addWidget(self.selectFileButton)

        self.outputSettingsLayout = QtWidgets.QFormLayout(
            self.outputSettingsGroupBox)
        self.outputSettingsLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole,
            self.exportLabel)
        self.outputSettingsLayout.setLayout(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole,
            self.fileSelectorLayout)



        self.runButton = QtWidgets.QPushButton(self.centralwidget)

        self.pauseButton = QtWidgets.QPushButton(self.centralwidget)
        self.pauseButton.setEnabled(False)

        self.cancelButton = QtWidgets.QPushButton(self.centralwidget)
        self.cancelButton.setEnabled(False)


        self.workerControlButtonsLayout = QtWidgets.QHBoxLayout()
        spacerItem = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum)
        
        self.workerControlButtonsLayout.addItem(spacerItem)
        self.workerControlButtonsLayout.addWidget(self.runButton)
        self.workerControlButtonsLayout.addWidget(self.pauseButton)
        self.workerControlButtonsLayout.addWidget(self.cancelButton)

        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)


        self.logWidget = logger.QPlainTextEditLogger(
            self.centralwidget, JSpider)
        self.logWidget.setFont(QtGui.QFont("Lucida Console"))



        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setMaximum(1000)



        spacerItem1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum)

        self.statsLabel1 = QtWidgets.QLabel(self.centralwidget)
        self.num_nodes_read = QtWidgets.QLabel(self.centralwidget)
        self.statsLabel2 = QtWidgets.QLabel(self.centralwidget)
        self.num_nodes_queued = QtWidgets.QLabel(self.centralwidget)
        self.statsLabel3 = QtWidgets.QLabel(self.centralwidget)

        self.statsLayout = QtWidgets.QHBoxLayout()
        self.statsLayout.addSpacerItem(spacerItem1)
        self.statsLayout.addWidget(self.statsLabel1)
        self.statsLayout.addWidget(self.num_nodes_read)
        self.statsLayout.addWidget(self.statsLabel2)
        self.statsLayout.addWidget(self.num_nodes_queued)
        self.statsLayout.addWidget(self.statsLabel3)
        self.statsLayout.addWidget(
            QtWidgets.QSizeGrip(self.centralwidget))

        self.bodyLayout.addWidget(self.loginSettingsGroupBox)
        self.bodyLayout.addWidget(self.traversalSettingsGroupBox)
        self.bodyLayout.addWidget(self.outputSettingsGroupBox)
        self.bodyLayout.addLayout(self.workerControlButtonsLayout)
        self.bodyLayout.addWidget(self.line)
        self.bodyLayout.addWidget(self.logWidget)
        self.bodyLayout.addWidget(self.progressBar)
        self.bodyLayout.addLayout(self.statsLayout)
        
        self.setCentralWidget(self.centralwidget)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, MainWindow: QtWidgets.QMainWindow) -> None:
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate(
            "MainWindow", "Cognos Webscraper"))
        self.loginSettingsGroupBox.setTitle(
            _translate("MainWindow", "Login Settings"))
        self.usernameLabel.setText(_translate("MainWindow", "Username"))
        self.passwordLabel.setText(_translate("MainWindow", "Password"))
        self.traversalSettingsGroupBox.setTitle(
            _translate("MainWindow", "Traversal Settings"))

        self.fileLabel.setText(_translate("MainWindow", "Files Area"))
        self.myContentRadioButton.setText(
            _translate("MainWindow", "My Content"))
        self.teamContentRadioButton.setText(
            _translate("MainWindow", "Team content"))
        self.startPathLabel.setText(
            _translate("MainWindow", "Starting Path"))
        self.outputSettingsGroupBox.setTitle(
            _translate("MainWindow", "Output Settings"))
        self.exportLabel.setText(
            _translate("MainWindow", "Export Filename"))
        self.selectFileButton.setText(
            _translate("MainWindow", "Select File..."))

        self.runButton.setText(_translate("MainWindow", "Run"))
        self.pauseButton.setText(_translate("MainWindow", "Pause"))
        self.cancelButton.setText(_translate("MainWindow", "Cancel"))

        self.statsLabel1.setText(_translate("MainWindow", "Progress:"))
        self.num_nodes_read.setText(_translate("MainWindow", "0"))
        self.statsLabel2.setText(_translate("MainWindow", "nodes read, "))
        self.num_nodes_queued.setText(_translate("MainWindow", "0"))
        self.statsLabel3.setText(_translate("MainWindow", "nodes queued"))
