from enum import Enum
from typing import List

from tc2.stock_analysis.AbstractNeuralModel import AbstractNeuralModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.env.Settings import Settings
from tc2.util.data_constants import START_DATE, MIN_CANDLES_PER_MIN, MIN_CANDLES_PER_DAY
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.data_structs.neural_data.NeuralExample import NeuralExample
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.market_util import FIRST_45_MINS


class RallyStrength(Enum):
    WEAKEST = 'WEAKEST'
    WEAK = 'WEAK'
    STRONG = 'STRONG'
    STRONGEST = 'STRONGEST'


# TODO Predict rally strength (pct price change by end of a rally) using recent price and volume.
# TODO Ignore values that border on multiple ranges.
class RallyAIModel(AbstractNeuralModel):
    # Model inputs: 44 price changes, 44 volume changes
    feature_names = []
    for i in range(1, 44):
        feature_names.append('price_change_' + str(i))
        feature_names.append('vol_change_' + str(i))

    # Model outputs: category of rally strength
    output_names = [rally_strength.value for rally_strength in RallyStrength]

    def create_data_points(self) -> List[NeuralExample]:
        examples = []

        # Mix in examples from all symbols
        for symbol in Settings.get_symbols(self):
            dates = self.mongo().get_dates_on_file(symbol, START_DATE, self.time().now())
            for day_date in dates:
                # Load symbol's candles on day_date
                day_data = self.mongo().load_symbol_day(symbol, day_date)

                # Ensure first 45 minutes of data is present
                first_45_candles = SymbolDay.get_ordered_candles(day_data.candles, FIRST_45_MINS)
                if len(first_45_candles) < 45 * MIN_CANDLES_PER_MIN or len(day_data.candles) < MIN_CANDLES_PER_DAY:
                    continue

                # TODO Calculate minute-to-minute price and volume changes

                # TODO Classify rally strength on the day

                # TODO Create a data point

        return examples

    def calculate_output(self, candles: List[Candle]) -> AbstractNeuralModel.OUTPUT_TYPE:
        """
        Makes a quick prediction using the previously-trained neural network.
        Uses AI to predict the 80th percentile rally strength (pct price change by end of a rally).
        i.e. it predicts the highest non-outlier rally strength.
        :param candles: the first 45 minutes of data for the day in question
        :return: the highest rally strength we can reasonably expect to see today
        """
        # TODO Check that the neural network was trained within past two weeks (return 'unusable model' otherwise)
        # TODO Load the keras model
        # TODO Forward prop on the keras model to return output
        pass

    """
    Private utility methods...
    """

    def grade_symbol(self, symbol: str, output: AbstractNeuralModel.OUTPUT_TYPE) -> SymbolGrade:
        # Fail the symbol if it has no output
        if output is None:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # TODO Convert list of floats to a RallyStrength

        # Assign the symbol a grade based on its predicted rally strength
        if output == RallyStrength.WEAKEST:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.RISKY)
        elif output == RallyStrength.WEAK:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.SATISFACTORY)
        elif output == RallyStrength.STRONG:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GREAT)
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.EXCELLENT)

    def _price_volume_changes(self, ) -> List[float]:
        """
        :return: a list of changes (e.g. [price_chng_1, vol_chng_1, price_chng_2, vol_chng_2, ...])
        """
        # TODO tally price + volume after going thru all the seconds in a minute
        pass
