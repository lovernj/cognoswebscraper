from typing import List, Generator
from PyQt6 import QtCore
import logging
from src.exceptions import *
from src.driver import folderelem
from src.logs import *
import src.driver.excelwriter as excelwriter
import src.driver.seleniumdriver as sd
import src.gui.ui as ui
from selenium.common.exceptions import ElementClickInterceptedException,NoSuchElementException
ElemType = folderelem.FolderElem.ElemType  # convenience rename


class Worker(QtCore.QObject, logging.Handler):
    """Traverse Cognos and prepare a file for saving"""

    # Signals for passing worker state back to the main thread
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(int, int)

    # Signals for passing logs back to the main thread
    logger = QtCore.pyqtSignal(logging.LogRecord)
    nodesQueued = QtCore.pyqtSignal(int)
    nodesFinished = QtCore.pyqtSignal(int)
    progressBar = QtCore.pyqtSignal(int)

    def __init__(self, ui: 'ui.Ui') -> None:
        """Initialize the worker. Setup the logging handler"""
        self.headless = False
        QtCore.QObject.__init__(self)
        logging.Handler.__init__(self)

        self.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))
        JSpider_worker.addHandler(self)  # Always use the worker

        self.ui = ui
        self.consume = QtCore.QMutex()
        JSpider_worker.log(LOCK, "consumelock locking")
        # We can't consume until we're done setting up.
        # (I know this isn't quite atomic but w/e)
        self.consume.lock()

        #Status flags. 
        self.runningLock = QtCore.QMutex()
        self.paused = False
        self.setupLock = QtCore.QMutex()

        # For typing reasons, driver is a SeleniumDriver
        self.driver: sd.SeleniumDriver

    def run(self):
        """Run the actual process and save the file afterwards."""

        self.username, self.password = self.ui.Auth
        # If there's no uname/passw, this is a dead run.
        if self.username == "" or self.password == "":
            JSpider_worker.error("Username and password cannot be blank")
            self.finished.emit()
            return

        self.direction = "Team Content" if self.ui.TeamContent else "My Content"

        JSpider_worker.log(LOCK, "setuplock locking")
        self.setupLock.lock()
        self.driver = sd.SeleniumDriver(JSpider_worker,
                                        self.ui.geckodriver,
                                        self.ui.executable,
                                        self.headless,
                                        "Team Content" if self.ui.TeamContent
                                        else "My Content")

        self.setupLock.unlock()
        JSpider_worker.log(LOCK, "setupLock unlocked")

        self.driver.login(self.username, self.password)
        self.driver.open_slider()
        try:
            self.driver.travel_path(self.ui.TravelPath)

            JSpider_worker.info(
                "Selenium is queued and ready. Initializing excel file")
            self.excel_file = excelwriter.ExcelWriter()
            self.driver.enableScrollToBottom()
            self.nq = self.nr = 0
            self.level = 1
            JSpider_worker.debug("Traversing")
            self.consume.unlock()  # We're cleared for launch
            try:
                for element in self.__traverse():
                    self.excel_file.append(element)
            except EarlyLeaveException:
                self.driver.driver.quit()    
                self.driver.cancel = False #We're done failing out. Worker is closed. 
            JSpider_worker.info("Saving")
            self.excel_file.write_wb(self.ui.ExportFileName)
            JSpider_worker.log(NODESFINISHED, 0)
            JSpider_worker.log(NODESQUEUED, 0)
            JSpider_worker.log(PROGRESSBAR, 0)
            self.driver.driver.quit()
            JSpider_worker.info("Run finished")

            self.finished.emit()
        # No guarantee that self.driver exists. If it doesn't, that's OK
        except AttributeError:
            JSpider_worker.debug("Error: Couldn't find driver")
        # Helps us cancel the program in a happy way
        except EarlyLeaveException:
            pass #Fail out of the run loop quietly. 
                 #This is an expected condition, and doesn't need to be handled
        except LoginException:
            JSpider_worker.error("Closing driver.")
            pass #Notification is handled in seleniumdriver
                 # and cleanup is handled in finally clause
        except (NoSuchElementException,
                ElementClickInterceptedException):
            #Looks like something went wrong with the driver. 
            JSpider_worker.error("Something went wrong with the driver. Please check logs.")

        finally:
            self.driver.driver.quit()
            self.finished.emit()

    def __traverse(self) -> Generator[folderelem.FolderElem, None, None]:
        """Actually do the traversal. This method is recursive"""
        JSpider_worker.log(LOCK, "consumelock locking")
        self.consume.lock()
        for element in self.driver.readCurrentFolder():
            if isinstance(element, folderelem.FolderElem):
                yield element

            # At the very end of a run, the generator will
            # yield a list of folders
            elif isinstance(element, List):
                # Typehinting assertion: folders contains folderelems.
                folders: List[folderelem.FolderElem] = element
                for folder in folders:
                    JSpider_worker.debug(f"found a folder item: {element}")
                    self.driver.travel(folder.name)

                    self.consume.unlock()  # A safe place to PAUSE or QUIT
                    JSpider_worker.log(LOCK, "consumelock unlocked")

                    JSpider_worker.debug(f"{folder.path}")
                    yield from self.__traverse()

                    JSpider_worker.log(LOCK, "consumelock locking")
                    self.consume.lock()

                    self.driver.travel("..")  # go back up
            else:
                raise TypeError(   #This should never be hit, but better safe than sorry
                    "Received an unknown type from selenium driver")

        self.consume.unlock()  # done with the function. Free up consumelock
        JSpider_worker.log(LOCK, "consumelock unlocked")
        return

    def emit(self, record: logging.LogRecord) -> None:
        """
        Sort out the correct channel 
        for the log record to send on and send it
        """
        if record.levelno == PROGRESSBAR:
            self.progressBar.emit(int(record.msg))
        elif record.levelno == NODESQUEUED:
            self.nodesQueued.emit(int(record.msg))
        elif record.levelno == NODESFINISHED:
            self.nodesFinished.emit(int(record.msg))
        else:
            record.msg = "[W]:"+record.msg
            self.logger.emit(record)
