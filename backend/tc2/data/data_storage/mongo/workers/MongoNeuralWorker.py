from datetime import datetime
from typing import Optional, List

from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.data.data_storage.mongo.workers.AbstractMongoWorker import AbstractMongoWorker
from tc2.data.data_structs.neural_data.NeuralExample import NeuralExample


class MongoNeuralWorker(AbstractMongoWorker):
    """
    Contains functionality for saving and loading neural network training data.
    """

    def load_example_collection(self, symbol: str, model_type: AnalysisModelType) -> List[NeuralExample]:
        """Queries MongoDB for a list of examples for the day and puts them into a SymbolDay object."""
        examples = []
        for example_time in self._get_example_times_on_file(symbol, model_type):
            inputs = self._get_example_inputs(symbol, model_type, example_time)
            outputs = self._get_example_outputs(symbol, model_type, example_time)
            examples.append(NeuralExample(example_time, inputs, outputs))
        examples.sort(key=lambda example_to_sort: example_to_sort.time)
        return examples

    def save_neural_collection(self, symbol: str, model_type: AnalysisModelType, examples: List[NeuralExample]) -> None:
        """
        Saves the examples in MongoDB, or clears the (symbol, model) pair from MongoDB.
        """
        self.drop_neural_collection(symbol, model_type)
        for example in examples:
            self._update_neural_example(symbol, model_type, example)

    def _get_example_times_on_file(self, symbol: str, model_type: AnalysisModelType) -> List[datetime]:
        """Returns a list of datetime objects for which we have AI training data."""
        query = {"symbol": symbol.upper(), "model_type": model_type.value}
        requested_fields = {"datetime": 1}
        responses = self.neural_collection.find(query, requested_fields)
        if responses is None:
            return []
        example_datetimes = []
        for doc in responses:
            example_datetimes.append(doc['date'])
        example_datetimes.sort()
        return example_datetimes

    def _get_example_inputs(self, symbol: str, model_type: AnalysisModelType, example_time: datetime) -> List[float]:
        query = {"symbol": symbol.upper(), "model_type": model_type.value, "time": example_time}
        requested_fields = {"inputs": 1}
        response = self.neural_collection.find_one(query, requested_fields)
        if response is None or response == {}:
            return []
        return [float(input_feature) for input_feature in response['inputs']]

    def _get_example_outputs(self, symbol: str, model_type: AnalysisModelType, example_time: datetime) -> List[float]:
        query = {"symbol": symbol.upper(), "model_type": model_type.value, "time": example_time}
        requested_fields = {"outputs": 1}
        response = self.neural_collection.find_one(query, requested_fields)
        if response is None or response == {}:
            return []
        return [float(output_neuron) for output_neuron in response['outputs']]

    def _update_neural_example(self, symbol: str, model_type: AnalysisModelType, example: NeuralExample) -> None:
        """Inserts or replaces the given training example on the given date."""
        query = {"symbol": symbol.upper(), "model_type": model_type.value, "time": example.time}
        new_doc = {"symbol": symbol.upper(), "model_type": model_type.value, "time": example.time,
                   "inputs": [str(neural_input) for neural_input in example.inputs],
                   "outputs": [str(output) for output in example.outputs]}
        self.neural_collection.replace_one(query, new_doc, upsert=True)

    def drop_neural_collection(self, symbol: Optional[str], model_type: AnalysisModelType) -> None:
        """
        :param symbol: set to None to drop all symbols
        Deletes a model's training data from the database.
        This function is not synchronized because it is assumed the the outermost function calling it is synchronized.
        """
        if symbol is not None:
            query = {"symbol": symbol.upper(), "model_type": model_type.value}
        else:
            query = {"model_type": model_type.value}
        self.neural_collection.delete_one(query)
