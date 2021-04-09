from enum import Enum


class ModelSteps(Enum):

    def __init__(self,
                 label: str,
                 info: str):
        self.label = label
        self.info = info
