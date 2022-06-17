import logging
import time
from PyQt6 import QtCore
from src.gui import worker, ui
from src import exceptions
import logging
from src.logs import *
from enum import Enum

class Controller(QtCore.QObject,logging.Handler):
    """MVC Controller object for the program"""

    class Task(Enum):
        """A task that the controller can do"""
        togglePause  = 1
        Cancel       = 3
        quit         = 4

    #Signal to tell the gui we're done running so that it can close up shop
    finished = QtCore.pyqtSignal()

    #to send logs back to the parent thread
    logger = QtCore.pyqtSignal(logging.LogRecord) 

    def __init__(self,myUI:'ui.Ui',myWorker:worker.Worker):
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self)
        self.worker = myWorker
        self.ui = myUI
        JSpider_controller.addHandler(self)
        self.__is_paused = False

    def pause(self)->None:
        """Pause the worker."""
        if not self.__is_paused:
            JSpider_controller.info("Getting to a safe place...")
            JSpider_controller.log(LOCK,"consumelock locking")
            #Pause the worker. This method blocks until the worker is paused.
            self.worker.consume.lock()
            self.__is_paused = True
            self.ui.pauseButton.setText("Unpause")
        else:
            raise exceptions.StateException("Tried to pause a paused worker")

    def unpause(self)->None:
        """Unpause the worker"""
        if self.__is_paused:     #if we were the one that locked it 
            JSpider_controller.info("Unpausing")
            self.worker.consume.unlock() #unlock it
            JSpider_controller.log(LOCK,"consumelock unlocked")
            self.__is_paused = False
            self.ui.pauseButton.setText("Pause")
        else:
            raise exceptions.StateException("Tried to unpause an running worker")
 
    def togglePause(self):
        """Toggle the UI between paused and unpaused states"""
        self.ui.pauseButton.setEnabled(False)
        if self.__is_paused: 
            self.unpause()
        else:
            self.pause()
        self.ui.pauseButton.setEnabled(True)

    def cancel(self)->None:
        """Kill the worker in the middle of a run"""
        #Get worker.run to exit with a cascade failure
        self.ui.cancelButton.setEnabled(False)
        self.ui.pauseButton.setEnabled(False)

        self.worker.driver.cancel = True 
        #Asynchronously pass the cancel flag to the worker's driver. 
        #Yes, this violates thread safety. 
        #However, the worker atomically checks the cancel flag
        #and never alters it except at setup time. 
        JSpider_controller.debug("Waiting for worker to finish cascading...")
        #Busywait for worker to finish cascading
        while self.worker.driver.cancel: time.sleep(0.1) 
        #When worker.run() finishes erroring out it'll set cancel to false
        
        #Kill firefox
        JSpider_controller.log(LOCK,"setupLock locking")
        self.worker.setupLock.lock()

        try:
            self.worker.driver.driver.quit()
        #There's a chance the driver doesn't exist yet
        except AttributeError as ex: 
            pass

        self.worker.setupLock.unlock()
        JSpider_controller.log(LOCK,"setupLock unlocked")

    def quitUI(self)->None:
        """Kill the UI"""
        JSpider_controller.debug("Killing the ui")
        if self.ui.work_thread.isRunning():
            self.cancel()
            self.ui.work_thread.terminate()
            JSpider_controller.debug("worker killed.")
        self.finished.emit()

    @QtCore.pyqtSlot(Task)
    def execute(self,task:Task):
        print("Received task: ",task.name)
        if task==self.Task.togglePause:
            self.togglePause()
        elif task == self.Task.Cancel:
            self.cancel()
        elif task == self.Task.quit:
            self.quitUI()
        else: raise NotImplementedError

    def emit(self,record:logging.LogRecord)->None:
        record.msg ="[C]:"+record.msg
        self.logger.emit(record)