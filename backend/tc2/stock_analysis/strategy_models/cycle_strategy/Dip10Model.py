from datetime import timedelta, datetime, time

from tc2.stock_analysis.AbstractForgetfulModel import AbstractForgetfulModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.data.data_structs.price_data.Candle import Candle
from tc2.util.rolling_sum_formulas import RollingSumFormulas


class Dip10Model(AbstractForgetfulModel):

    def feed_model(self, day_data: SymbolDay) -> None:
        """
        Calculates the strongest percent dip during the first 10 minutes of CycleStrategy's typical run window.
        i.e. it predicts the worst dip that should be expected within 10 minutes of buying the symbol.
        """

        # Find price at minute 60
        start_candle: Candle = day_data.get_candle_at_sec(
            datetime.combine(day_data.day_date, time(hour=10, minute=30)))
        if start_candle is None:
            self.warn_process("Couldn't update dip_10 analysis_model for CycleStrategy. Bad data at minute 60.")
            return

        # Find lowest price within 10 minutes after minute 60
        start_time = datetime.combine(day_data.day_date, time(hour=10, minute=30))
        end_time = datetime.combine(day_data.day_date, time(hour=10, minute=30)) + timedelta(
            minutes=10)
        lowest_candle: Candle = Candle(start_candle.moment, start_candle.open, start_candle.high, start_candle.low,
                                       start_candle.close, start_candle.volume)
        for candle in day_data.candles:
            if candle.low < lowest_candle.low and start_time < candle.moment < end_time:
                lowest_candle = candle
                lowest_candle = lowest_candle

        # Calculate the greatest downward price change as a percentage
        strongest_dip_pct = 100.0 * max(0.0, start_candle.low - lowest_candle.low) / start_candle.low

        # Load the current running sum
        current_sum = self.redis().get_analysis_rolling_sum(day_data.symbol, self.model_type)

        # Skip days that don't dip since this model is only interested in forecasting dips
        if strongest_dip_pct == 0:
            output = current_sum

        # Merge this day into the running sum
        else:
            output = RollingSumFormulas.combine(current_sum, strongest_dip_pct, RollingSumFormulas.get_30_day_weight())

        # Save model's output
        self.save_output(symbol=day_data.symbol, raw_output=output, day_date=day_data.day_date)

    def grade_symbol(self, symbol: str, output: AbstractForgetfulModel.OUTPUT_TYPE) -> SymbolGrade:
        # Fail the symbol if it has no output
        if output is None:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # Assign a good grade if strongest percent dip is not too little or too much
        # Essentially the sweet spot is anywhere between 0.1% and 0.3%
        if output < 0.025 or output > 0.5:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)
        elif output < 0.05 or output > 0.45:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.RISKY)
        elif output < 0.075 or output > 0.4:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.UNPROMISING)
        elif output < 0.125 or output > 0.35:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GOOD)
        elif output < 0.15 or output > 0.3:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GREAT)
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.EXCELLENT)
