from typing import Optional

from tc2.stock_analysis.AbstractModel import AbstractModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay


class AbstractForgetfulModel(AbstractModel):
    """
    Any model that iteratively takes data in one day at a time and factors it into a weighted sum.
    This class of models "forgets" old data as it gets replaced by newer data.
    """

    OUTPUT_TYPE = Optional[float]

    def feed_model(self, day_data: SymbolDay) -> None:
        """Calculates and stores a new output given a previous day's info. Does not return output."""
        raise NotImplementedError

    def calculate_output(self, symbol: str) -> OUTPUT_TYPE:
        """Returns the model's stored output."""
        return self.get_stored_output(symbol=symbol)

    def grade_symbol(self, symbol: str, output: any) -> SymbolGrade:
        """Returns a pass/fail or categorical grade for the symbol's output."""
        raise NotImplementedError

    def encode_output(self, raw_output: OUTPUT_TYPE) -> str:
        """Converts model output float to a string."""
        return str(raw_output) if raw_output is not None else ''

    def decode_output(self, encoded_output: str) -> OUTPUT_TYPE:
        """Converts model's output to a float."""
        return float(encoded_output) if encoded_output != '' else None
