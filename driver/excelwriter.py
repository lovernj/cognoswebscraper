import openpyxl
from datetime import date

from src.driver.folderelem import FolderElem
from src.logs import *

class ExcelWriter():
    """Take in folder_elems and write them to an excel file."""
    def __init__(self):
        self._internal_array:list[FolderElem] = []
    def append(self,listing:FolderElem)->None:
        self._internal_array.append(listing)
    
    def write_wb(self,filename: str)->None:
        """Write the workbook to filename. """
        #This lets us defer excel ops until the end.
        headers = ["Path","File","Type","Description","Link"]
        
        self.wb = openpyxl.Workbook(write_only=True)
        ws = self.wb.create_sheet() #write-only workbooks don't come with a starter sheet. 
        ws.append(["This file was created on",date.today()])
        ws.append(headers)

        for elem in self._internal_array:
            #style the hyperlink
            linkcell = openpyxl.cell.WriteOnlyCell(ws,    #type:ignore
                       value=f'=HYPERLINK("{elem.link}")' if elem.link else '') 
            linkcell.style = "Hyperlink"
            
            #write the data
            ws.append([elem.path,
                       elem.name,
                       elem.type.name,
                       '',
                       linkcell])
        self.wb.save(filename)