from datetime import datetime
from typing import List


class NeuralExample:
    """Contains info for a single training data point/example."""
    time: datetime
    inputs: List[float]
    outputs: List[float]

    def __init__(self, time: datetime, inputs: List[float], outputs: List[float]) -> None:
        self.time = time
        self.inputs = inputs
        self.outputs = outputs