"""This file centralizes logging across the package"""
import logging,sys

default_handler = logging.StreamHandler(sys.stdout)

#Loggers for each of the threads in this program
JSpider            = logging.Logger("JSpider")
JSpider_worker     = logging.Logger("JSpider_worker")
JSpider_controller = logging.Logger("JSpider_controller")
JSpider.addHandler(default_handler)

JSpider.setLevel(logging.DEBUG)

PROGRESSBAR = logging.CRITICAL - 1
NODESQUEUED = logging.CRITICAL - 2
NODESFINISHED = logging.CRITICAL - 3

LINK = logging.INFO - 1

LOCK = logging.DEBUG - 1
PATHREF = logging.DEBUG - 2
logging.addLevelName(PROGRESSBAR, 'PROGRESSBAR')
logging.addLevelName(NODESQUEUED, 'NODESQUEUED')
logging.addLevelName(NODESFINISHED, 'NODESFINISHED')

logging.addLevelName(LINK,'LINK')

logging.addLevelName(LOCK, 'LOCK')
logging.addLevelName(PATHREF, 'PATHREF')

