from typing import Optional, List

import pandas as pd
from pandas import DataFrame

from tc2.stock_analysis.AbstractNeuralModel import AbstractNeuralModel
from tc2.env.ExecEnv import ExecEnv
from tc2.data.data_structs.neural_data.NeuralExample import NeuralExample


class DataPrepPipeline(ExecEnv):
    """
    Contains functions to load, normalize, and export AI training data.
    Intended for use in feeding an AI model.
    """

    symbol: str
    df_raw: Optional[DataFrame]
    df: Optional[DataFrame]

    def __init__(self, env: ExecEnv, symbol) -> None:
        super().__init__(env.logfeed_program, env.logfeed_process)
        self.clone_same_thread(env)
        self.symbol = symbol
        self.df = None

    def _create_dataframe(self, feature_names: List[str], output_names: List[str],
                          examples: List[NeuralExample]) -> DataFrame:
        """
        Loads raw model input data into this pipeline's df_raw DataFrame.
        :param feature_names: a list naming model features (e.g. price_1)
        :param feature_names: a list naming model outputs (e.g. predicted_profit)
        :param examples: a list of NeuralExample objects, each containing n_features inputs and n_outputs outputs
        """

        # Ensure all examples contain the expected number of inputs and outputs
        num_features = len(feature_names)
        num_outputs = len(output_names)
        for neural_example in examples:
            if len(neural_example.inputs) != num_features:
                raise ValueError('Each feature name must correspond to an input ({0} != {1}'
                                 .format(num_features, len(neural_example.inputs)))
            if len(neural_example.outputs) != num_outputs:
                raise ValueError('All output name must correspond to an output ({0} != {1})'
                                 .format(num_outputs, len(neural_example.outputs)))

        # Collect data into a dictionary object
        df_data = {'date': []}
        for i in range(0, len(feature_names)):
            feature_name = feature_names[i]
            df_data[feature_name] = []
        for neural_example in examples:
            df_data['time'].append(neural_example.time)
            for i in range(0, len(feature_names)):
                feature_name = feature_names[i]
                df_data[feature_name].append(neural_example.inputs[i])

        # Load the pandas DataFrame using our dict object
        return pd.DataFrame(data=df_data)

    def get_all_data(self, model: AbstractNeuralModel) -> DataFrame:
        """
        Loads training data from mongo and puts it into a pandas DataFrame.
        """
        examples = self.mongo().load_example_collection(self.symbol, model.model_type.value)
        self.df_raw = self._create_dataframe(model.feature_names, model.output_names, examples)
        return self.df_raw

    def normalize_distribution(self, bins: int = 5) -> None:
        """
        Returns a DataFrame containing an equal number of examples for each class.
        If the model performs regression, this ensures an equal distribution across the given number of bins.
        """
        # TODO
        pass
