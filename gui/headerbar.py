from PyQt6 import QtWidgets,QtCore
class HeaderBar(QtWidgets.QWidget):
    """Custom header bar that enables draggability on frameless windows."""
    def __init__(self, window: QtWidgets.QMainWindow):
        super(HeaderBar, self).__init__()
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground)

        self.windowobj = window
        self.layoutobj = QtWidgets.QHBoxLayout(self)
        self.layoutobj.setContentsMargins(0, 0, 0, 0)
        self.layoutobj.setSpacing(0)
        
        self.title = QtWidgets.QLabel("JSpider")

        self.icon_label = QtWidgets.QLabel("<html><img src='.\\assets\\head_icon.svg'></html>")
        self.icon_label.setContentsMargins(4, 4, 4, 4)
        self.icon_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)


        button_width = 25
        button_size_policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Expanding)

        self.btn_close = QtWidgets.QPushButton("X")
        self.btn_close.setObjectName("Close_Button")
        self.btn_close.setSizePolicy(button_size_policy)
        self.btn_close.setFixedWidth(button_width)
        
        self.btn_min = QtWidgets.QPushButton("_")
        self.btn_min.setSizePolicy(button_size_policy)
        self.btn_min.setFixedWidth(button_width)
        self.btn_min.setStyleSheet("border:none;")

        self.layoutobj.addWidget(self.icon_label)
        self.layoutobj.addWidget(self.title)
        self.layoutobj.addStretch(1)
        self.layoutobj.addWidget(self.btn_min)
        self.layoutobj.addWidget(self.btn_close)
        self.setLayout(self.layoutobj)

        self.start = QtCore.QPoint(0, 0)
        self.pressing = False

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.windowobj.move(self.windowobj.x() + delta.x(),
                            self.windowobj.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()
