from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.stock_analysis.AbstractModel import AbstractModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade


class AbstractSpotModel(AbstractModel):
    """
    Any model that does not store previous results but instead performs a calculation "on-the-spot."
    These models use recent data to perform their checks.
    """

    def feed_model(self, day_data: SymbolDay) -> None:
        """
        Does nothing since spot models only run live calculations and not daily training.
        """
        pass

    def calculate_output(self, symbol: str) -> any:
        """
        Returns the model's new output given the latest info.
        Does not save output automatically.
        """
        raise NotImplementedError

    def grade_symbol(self, symbol: str, output: any) -> SymbolGrade:
        """
        Returns a pass/fail or categorical grade for the symbol's output.
        """
        raise NotImplementedError

    def encode_output(self, raw_output: any) -> str:
        """
        This model doesn't encode output since it doesn't store any.
        """
        pass

    def decode_output(self, encoded_output: str) -> any:
        """
        This model doesn't decode output since it doesn't store any.
        """
        pass
