from datetime import date
from typing import List, Optional

from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.env.ExecEnv import ExecEnv


class AbstractModel(ExecEnv):
    """
    The base class for an analysis model.
    Three kinds of analysis models:
        Forgetful model that factors in each successive data point and slowly forgets data as it ages.
        Neural model that weekly resets + re-trains a neural network so it can look at all data points at once.
        Spot model that uses the latest data to run a quick calculation right before buying.
    """

    model_type: AnalysisModelType

    def __init__(self, env: ExecEnv,
                 model_type: AnalysisModelType) -> None:
        super().__init__(env.logfeed_program, env.logfeed_process)
        self.clone_same_thread(env)
        self.model_type = model_type

    def feed_model(self, day_data: SymbolDay) -> None:
        """Calculates and stores a new output given a previous day's info. Does not return output."""
        raise NotImplementedError

    def calculate_output(self, symbol: str) -> any:
        """Returns the model's new output given the latest info. Does not save output."""
        raise NotImplementedError

    def encode_output(self, raw_output: any) -> str:
        """Makes a string from the model's raw output, which could be a float, neuron activation array, or other."""
        raise NotImplementedError

    def decode_output(self, encoded_output: str) -> any:
        """Converts a string to usable model output, which could be a float, neuron activation array, or other."""
        raise NotImplementedError

    def get_stored_output(self, symbol: str) -> any:
        """Returns the decoded output that was last saved in redis for the symbol."""
        return self.decode_output(
            self.redis().get_analysis_raw_output(symbol, self.model_type))

    def grade_symbol(self, symbol: str, output: any) -> SymbolGrade:
        """Returns a pass/fail or categorical grade for the symbol's output."""
        raise NotImplementedError

    def save_output(self, symbol: str, raw_output: any, day_date: date) -> None:
        """
        :param raw_output: the output (usually a float) to be encoded by self.encode_output()
        :param day_date: the date for which this model was updated
        """
        self.redis().save_analysis_result(symbol, self.model_type, self.encode_output(raw_output))
        self.redis().save_analysis_date(symbol, self.model_type, day_date)

    def take_snapshot(self, symbol: str, model_output: Optional[str], day_date: date) -> None:
        """
        Takes a snapshot of the model's output, assuming it was just trained on stable data.
        This is used to revert back to later.
        """
        self.redis().save_analysis_snapshot_date(symbol=symbol,
                                                 model_type=self.model_type,
                                                 day_date=day_date)
        self.redis().save_analysis_snapshot_result(symbol=symbol,
                                                   model_type=self.model_type,
                                                   encoded_result=str(model_output))

    def revert_to_snapshot(self,
                           symbol: str) -> date:
        """
        Reverts the model's output and date values to those of its last snapshot.
        :return: the date to which the model was reverted
        """
        snapshot_date = self.redis().get_analysis_snapshot_date(symbol, self.model_type)
        snapshot_value = self.redis().get_analysis_snapshot_raw_output(symbol, self.model_type)
        self.save_output(symbol, snapshot_value, snapshot_date)
        return snapshot_date

    def restart_training(self,
                         symbol: str) -> None:
        """Clears redis analysis data for the symbol."""
        self.redis().remove_analysis_data(self.model_type, [symbol])
        self.mongo().drop_neural_collection(symbol, self.model_type)

    def reset(self,
              symbols: List[str]) -> None:
        """Wipes any analysis data stored in redis and mongo for the symbols."""
        self.redis().remove_analysis_data(self.model_type, symbols)
        for symbol in symbols:
            self.mongo().drop_neural_collection(symbol, self.model_type)
