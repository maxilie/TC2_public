from typing import List, Optional

from tc2.stock_analysis.AbstractModel import AbstractModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.data_structs.neural_data.NeuralExample import NeuralExample

"""
TODO NEXT: Start a task to train models weekly but not at the same time (in ModelFeeder).
TODO Set network parameters in DataPrepPipeline or another class so that we don't hard-code it in train_and_save
"""


class AbstractNeuralModel(AbstractModel):
    """
    Any model that takes as input the entire data collection.

    Since these models cannot be trained iteratively, they are updated weekly rather than daily.
    """

    OUTPUT_TYPE = Optional[List[float]]

    feature_names: List[str]
    output_names: List[str]

    def feed_model(self, day_data: SymbolDay) -> None:
        """Does nothing since the training scheme for a neural model is atomic and weekly, not iterative and daily."""
        pass

    def calculate_output(self, symbol: str) -> OUTPUT_TYPE:
        """
        Performs forward-pass on the neural net to return a prediction given the latest info.
        Does NOT train the neural network.
        """
        raise NotImplementedError

    def grade_symbol(self, symbol: str, output: OUTPUT_TYPE) -> SymbolGrade:
        """Returns a pass/fail or categorical grade for the given ANN output neurons."""
        raise NotImplementedError

    def encode_output(self, raw_output: OUTPUT_TYPE) -> str:
        """Converts ANN's output neurons to a string."""
        return ','.join([str(output_neuron for output_neuron in raw_output)]) if raw_output is not None else ''

    def decode_output(self, encoded_output: str) -> OUTPUT_TYPE:
        """Converts model's string-encoded output neurons to a list of floats."""
        return [float(cls_prediction) for cls_prediction in encoded_output.split(',')] if encoded_output != '' else None

    """
    Methods specific to Neural Models
    """

    def train_and_save(self, symbol: str) -> None:
        """
        Trains the neural network using the symbol's entire history.
        This is called weekly for each model.
        """
        # TODO Get self.create_data_points
        # TODO Use DataPrepPipeline to train and save
        pass

    def create_data_points(self) -> List[NeuralExample]:
        """
        Loads + processes price history, news headlines, etc. into NeuralExample objects
        :return: a list of (vector-x, vector-y) data points
        """
        raise NotImplementedError
