"""
Represent cognos nodes in python. Data storage class
"""
from enum import Enum
class FolderElem():
    """
    Represents an element of the folder. 
    Takes path as a list of locations and stores it 
    internally as a slash delimited path"""

    class ElemType(Enum):
        """Types of element in the Cognos directory tree"""
        UnknownType = -1
        Active_Report = 0
        Agent = 1
        CSV = 2
        Dashboard = 3
        Data_module = 4
        Empty_Folder = 5
        Folder = 6
        Package = 7
        Page = 8
        Query = 9
        Report = 10
        Report_View = 11
        Shortcut = 12
        Story = 13
        Uploaded_file = 14
        XLSX = 15

        @classmethod
        def from_type(cls, rvalue: str) -> "FolderElem.ElemType":
            """Convert a string to an ElemType"""
            try:
                return cls[rvalue.replace(" ", "_")]
            except KeyError as e:
                return cls.UnknownType

    def __init__(self, type: 'FolderElem.ElemType',
                 name: str, path: list[str], link: str = ""):
        self.type = type
        self.name = name
        self.path = f"/{'/'.join(path)}/" if path else "/"
        self.link = link
        self.linkpath = self.path+self.name+"/" if type == "Folder" else None

    def __repr__(self) -> str:
        path = self.path[1:-1].split("/") if self.path == '/' else []
        link = f"'{self.link}'" if self.link else None
        return f"folder_elem('{self.type}','{self.name}',{path},{link})"

    def __str__(self) -> str:
        if self.type == FolderElem.ElemType.Folder:
            return f"{self.path}/{self.name}/"
        else:
            return f"{self.path}/{self.name}"
