from enum import Enum
from PyQt6 import QtWidgets, QtGui
from typing import Dict, List
from src.logs import *


class QPlainTextEditLogger(logging.Handler, QtWidgets.QPlainTextEdit):
    """Log and refilter messages in a QPlainTextEdit object. """

    class debugLevel(Enum):
        Lock = LOCK  # Custom level
        Pathref = PATHREF
        Debug = 10
        Link = LINK
        Info = 20
        Warning = 30
        Error = 40
        Critical = 50

        @classmethod
        def convert(cls, value: int) -> "QPlainTextEditLogger.debugLevel":
            for item in cls:
                if item.value == value:
                    return item
            raise Exception("Could not find enum item")

    def __init__(self, parent: QtWidgets.QWidget | None,
                 parent_logger: logging.Logger) -> None:
        logging.Handler.__init__(self)
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        self.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

        # receive ALL messages. We're going to filter them ourself
        self.setLevel(0)
        self.setReadOnly(True)
        parent_logger.addHandler(self)

        self.rclickMenu = QtWidgets.QMenu(self)
        self.actions: Dict[QPlainTextEditLogger.debugLevel,
                           QtGui.QAction] = {}
        for item in QPlainTextEditLogger.debugLevel:
            self.actions[item] = QtGui.QAction(item.name)
            self.actions[item].setCheckable(True)
            self.actions[item].setChecked(True)
            self.actions[item].triggered.connect(self.refilterLogs)
            self.rclickMenu.addAction(self.actions[item])
        #By default disable anything below lvl 20
        tmp = self.debugLevel
        for item in [tmp.Lock,
                     tmp.Pathref,
                     tmp.Debug,
                     tmp.Link]:
            self.actions[item].setChecked(False)
            
        self.messages: List[logging.LogRecord] = []

    def contextMenuEvent(self, e: QtGui.QContextMenuEvent) -> None:
        self.rclickMenu.popup(QtGui.QCursor.pos())

    def conditionalPrint(self, record: logging.LogRecord):
        tmp = self.debugLevel.convert(record.levelno)
        if self.actions[tmp].isChecked():
            self.appendPlainText(self.format(record))

    def refilterLogs(self) -> None:
        self.setPlainText("")
        for record in self.messages:
            self.conditionalPrint(record)

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record)
        self.conditionalPrint(record)
