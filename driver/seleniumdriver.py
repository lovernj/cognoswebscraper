import imp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.remote.webelement import WebElement
from typing import Generator, List
from urllib.parse import quote
import time
import logging

from src.driver.folderelem import FolderElem
import src.exceptions
from src.logs import *  # Yes, this is generally a bad idea.
# This file is all the logging defines
# and is tightly managed.


class SeleniumDriver():
    def __init__(self, logger: logging.Logger,
                 gecko_loc: str,
                 exe_loc: str = "",
                 headless: bool = False,
                 my_loc: str = "Team Content"):
        self.path: List[str] = []
        self.logger: logging.Logger = logger
        self.options: Options = Options()
        self.cancel: bool = False  # synchronously cancel the run process
        if exe_loc:
            self.options.binary = exe_loc

        self.gecko_loc: str = gecko_loc

        if headless:
            logger.debug("Running in headless mode")
            self.options.add_argument("--headless")

        # Declare it, but don't define it. Typehinting makes coding easier
        self.driver: webdriver.Firefox
        self.loc: str
        if my_loc == "Team Content":
            self.loc = ".public_folders%2F"
        else:
            self.loc = ".my_folders%2F"
        self.linkpath = "https://cognos-prod.ec.sou.edu/ibmcognos11/bi/?pathRef="+self.loc
        self.driver = webdriver.Firefox(executable_path=self.gecko_loc,
                                        options=self.options)

    @property
    def nodes_queued(self) -> int:
        return self.__nodes_queued

    @nodes_queued.setter
    def nodes_queued(self, value: int) -> None:
        """update nodes queued and report the value"""
        self.__nodes_queued = value
        self.logger.log(NODESQUEUED, str(self.__nodes_queued))

    @property
    def nodes_read(self) -> int:
        return self.__nodes_read

    @nodes_read.setter
    def nodes_read(self, value: int) -> None:
        self.__nodes_read = value
        self.logger.log(NODESFINISHED, self.__nodes_read)

    def login(self, uname: str, passw: str) -> None:
        """Login to cognos. This class does not store login information"""
        self.logger.debug("Navigating to cognos")
        self.driver.get("https://cognos-prod.ec.sou.edu/ibmcognos11/bi")

        WebDriverWait(self.driver, 60).until(
            EC.title_is("IBM Cognos Analytics"))

        self.logger.info("Logging in")
        # Wait until we can send the keys
        WebDriverWait(self.driver, 60).until(
            EC.element_to_be_clickable((By.ID, 'CAMUsername')))
        self.driver.find_element(By.ID, 'CAMUsername').send_keys(uname)
        self.driver.find_element(By.ID, 'CAMPassword').send_keys(passw)
        self.driver.find_element(By.CLASS_NAME, 'signInBtn').click()

        self.logger.debug("Attempted login. Checking for success")

        # Check if we failed the login
        WebDriverWait(self.driver, 60).until(lambda driver:
                                             any([
                                                 # Any error text in the errorbox
                                                 driver.find_element_by_xpath(
                                                     "//div[@class='incorrectLoginText']")
                                                 .get_attribute("innerHTML")
                                                 .startswith("The provided credentials"),
                                                 # document says we've logged in
                                                 EC.title_is("Welcome")]))

        if self.driver.find_element_by_xpath("//div[@class='incorrectLoginText']")\
            .get_attribute("innerHTML")\
                .startswith("The provided credentials"):
            self.logger.error("Error: Incorrect login credentials.")
            raise src.exceptions.LoginException(
                "Cognos did not accept credentials")

        self.logger.info("Successfully logged in")

        # Just some housekeeping in preparation for the next step.
        self.nodes_queued = 0
        self.nodes_read = 0

    def open_slider(self) -> None:
        """Open the cognos slider for the correct area"""
        # disable all animations with css.
        # Technically we only need the -moz property
        # and maybe the blank property. It doesn't hurt to add the other ones
        # Just in case we switch from firefox to e.g. chrome or edge.
        self.driver.execute_script("$('head').append('"
                                   "<style type=\"text/css\">"
                                   "*{-o-transition-property: none !important;"
                                   "-moz-transition-property: none !important;"
                                   "-ms-transition-property: none !important;"
                                   "-webkit-transition-property: none !important;"
                                   "transition-property: none !important;}"
                                   "</style>')")

        WebDriverWait(self.driver, 60).until(
            EC.url_changes("https://cognos-prod.ec.sou.edu/ibmcognos11/bi/")
        )
        if self.loc == ".public_folders%2F":
            WebDriverWait(self.driver, 60).until(
                EC.visibility_of_element_located((By.ID, 'com.ibm.bi.contentApps.teamFoldersSlideout')))

            try:
                self.driver.find_element(
                    By.ID, 'com.ibm.bi.contentApps.teamFoldersSlideout').click()
            # Somet`i`mes the element is obscured. Often waiting 3 seconds works.
            except ElementNotInteractableException as e:
                time.sleep(3)
                try:
                    self.driver.find_element(
                        By.ID, 'com.ibm.bi.contentApps.teamFoldersSlideout').click()
                # If not, something is funky
                except ElementNotInteractableException:
                    self.logger.error("Could not click on Teams Slideout.")
                    raise e

            WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@id="teamFoldersSlideoutContent"]')))
            self.pane = self.driver.find_element(
                By.XPATH, '//div[@id="teamFoldersSlideoutContent"]')

        elif self.loc == ".my_folders%2f":
            WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.ID, 'com.ibm.bi.contentApps.myContentFoldersSlideout')))

            try:
                self.driver.find_element(
                    By.ID, 'com.ibm.bi.contentApps.myContentFoldersSlideout').click()
            except ElementNotInteractableException as e:
                time.sleep(3)
                try:
                    self.driver.find_element(
                        By.ID, 'com.ibm.bi.contentApps.myContentFoldersSlideout').click()
                except ElementNotInteractableException:
                    self.logger.error(
                        "Could not click on My Content Slideout.")
                    raise e

            WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@id="myContentSlideoutContent"]')))
            self.pane = self.driver.find_element(
                By.XPATH, '//div[@id="myContentSlideoutContent"]')

        WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dataTables_scrollBody")))

    def click_elem_by_xpath(self, xpath: str) -> None:
        """
        Try to click anelement using an xpath and js to accomplish it. 
        This is basically a nuclear option, but many of the elements we want to click
        aren't technically in view, so this works. 
        """
        xpath = xpath.replace("'", r"\'")
        self.logger.debug(f"Trying to click {xpath}")
        self.driver.execute_script(
            f"document.evaluate('{xpath}',document,null,XPathResult.FIRST_ORDERED_NODE_TYPE,null).singleNodeValue.click()")

    def readCurrentFolder(self) -> Generator[FolderElem | list[FolderElem], None, None]:
        """
        Yields each element in the current folder. At the end, either:
           - yield a list of folders this folder contains, or
           - yield the folder itself, if it's empty
        """
        tmp_elements: List[WebElement] = self.pane.find_elements(
            By.XPATH, './/tr[@data-name]')

        #Case: The folder is empty. 
        if not tmp_elements:
            self.logger.warning(f"Found an empty folder: {self.path}")
            yield FolderElem(FolderElem.ElemType.Empty_Folder, self.path[-1], self.path)
            return #And we're done. 

        self.nodes_queued += len(tmp_elements)
        folder_elements:List[FolderElem] = []
        # grabs team_pane rows with data-names. (This should isolate it to data rows)
        for element in tmp_elements:
            if self.cancel:
                raise src.exceptions.EarlyLeaveException  # start screaming
            elem = FolderElem(FolderElem.ElemType
                              .from_type(element.find_element(By.XPATH,
                                                              './td/div[@title and @role="img"]')
                                         .get_attribute("title")),  # type
                              element.get_attribute("data-name"),  # title
                              self.path
                              )
            elem.link = self.linkpath + "/".join(self.path+[elem.name])

            self.logger.info("%s: %s", elem.type.name, elem.name)
            self.logger.log(LINK, "link: %s", elem.link)

            #immediately yield it if it's not a folder
            if elem.type != FolderElem.ElemType.Folder:
                self.nodes_queued -= 1
                yield elem  # return the element
                self.nodes_read += 1
            else: #If it *is* a folder, append it to the list of folders
                folder_elements.append(elem)
        yield folder_elements
        return

    def travel_path(self, path: str) -> None:
        """Travel to a particular (global) folder. """
        for folder in path.strip("/ ").split("/"):
            print("Traveling to:", folder)
            self.travel(folder)

    def enableScrollToBottom(self) -> None:
        """
        Install a ResizeObserver on the folder window
        that causes it to scroll to the bottom unconditionally
        """
        script = """
            elem1 = document.getElementsByClassName("dataTables_scrollBody")[0];
            elem2 = document.getElementsByClassName("dataTable")[0];
            let RO = new ResizeObserver(function (){elem1.scrollTop=elem1.scrollHeight;})
            RO.observe(elem2)
            """
        self.driver.execute_script(script)

    def travel(self, folder: str) -> FolderElem:
        """
        Make selenium travel to a particular (local) folder.
        Traveling globally isn't implemented. 
        """
        if (folder == ".."):
            self.click_elem_by_xpath(
                './/ul[@class="breadcrumbPrevious"]//div[@role="button"]')
            self.path.pop()
        elif (folder not in ['', '.']):
            self.pane.find_element(By.XPATH, f'.//tr[td/div/@title="Folder"'
                                   ' and @data-name="{folder}"]'
                                             '//div[@role="link"]').click()
            self.path.append(folder)
        time.sleep(.8)
        if (not self.path):
            return FolderElem(FolderElem.ElemType.Folder, '/', [])

        return FolderElem(FolderElem.ElemType.Folder,
                          self.path[-1],
                          self.path[:-1])
