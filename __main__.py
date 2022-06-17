import shutil
import src.gui.ui
import argparse
from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication
from src.logs import *


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTIONS]",
        description="Walk through Cognos's directory tree"
                    "and export the filenames to an excel file."
    )
    parser.add_argument(
        "-H", "--headless", action="store_true",
        help="Start Selenium headless (invisible)"
    )
    parser.add_argument(
        "-u", "--uname",
        help="Specify the user. This can be changed in GUI"
    )
    parser.add_argument(
        "-p", "--passw",
        help="Specify the password. This can be changed in GUI"
    )
    parser.add_argument(
        "-d", "--debuglevel",
        help="Set the logging level"
    )
    parser.add_argument(
        "-x", "--executable",
        help="Set the location of the firefox executable"
    )
    parser.add_argument(
        "-g", "--geckodriver",
        help="Set the location of the geckodriver executable"
    )
    return parser


def main() -> None:
    JSpider.setLevel(logging.INFO)
    try:
        parser = init_argparse()
        args, remaining_args = parser.parse_known_args()
        app = QApplication(remaining_args)
        app.setWindowIcon(QtGui.QIcon(".\\assets\\head_icon.svg"))
        File = QtCore.QFile(".\\assets\\elegantdark.qss")
        if not File.open(QtCore.QFile.OpenModeFlag.ReadOnly
                         | QtCore.QFile.OpenModeFlag.Text):
            JSpider.critical("Error: Couldn't open stylesheet.")
            sys.exit(1)
        qss = QtCore.QTextStream(File)
        app.setStyleSheet(qss.readAll())
    except:
        JSpider.critical("Something went wrong with arg parsing")
        sys.exit(1)

    ui = src.gui.ui.Ui()
    ui.TravelPath = "/Finance/"

    if args.headless:
        ui.runButton.setText("Run Headless")
        ui.worker.headless = True
    else:
        ui.worker.headless = False

    if args.uname:
        ui.usernameInput.setText(args.uname)
        JSpider.info("Username autoset from command line: %s", args.uname)

    if args.passw:
        ui.passwordInput.setText(args.passw)
        JSpider.info("Password autoset from command line (omitted)")

    if args.debuglevel:
        JSpider.setLevel(int(args.debuglevel))
        logging.getLogger("JSpider_worker").setLevel(int(args.debuglevel))
        JSpider.critical(
            "Debug level set from command line: %s", args.debuglevel)

    if args.executable:
        ui.executable = args.executable
    else: 
        if tmp:=shutil.which("firefox.exe"): #try to find firefox with shutil
            ui.executable = tmp
        else:
            JSpider.critical("Could not find a valid firefox distro.")
            sys.exit(1)
    if args.geckodriver:
        ui.geckodriver = args.geckodriver
    else:
        # by default assume that we're using the included geckodriver package
        ui.geckodriver = "./binaries/geckodriver.exe"
    JSpider.debug("UI started")

    # exit
    retval = app.exec()
    JSpider.debug("Exiting with status %d", retval)
    sys.exit(retval)


if __name__ == '__main__':
    main()
