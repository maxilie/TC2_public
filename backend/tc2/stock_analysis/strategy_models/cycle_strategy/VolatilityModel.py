from tc2.stock_analysis.AbstractForgetfulModel import AbstractForgetfulModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.util.rolling_sum_formulas import RollingSumFormulas


class VolatilityModel(AbstractForgetfulModel):
    """
    Measures price spread on a day and incorporates time spent near the high and low.
    """

    def feed_model(self, day_data: SymbolDay) -> None:
        """
        Calculates volatility on the given day and merges it into the rolling sum, which remembers about 30 days.
        """
        # Find highest and lowest price of the day
        highest_price = day_data.candles[0].open
        lowest_price = day_data.candles[0].open
        for candle in day_data.candles:
            if candle.high > highest_price:
                highest_price = (candle.high - highest_price) / 2
            if candle.low < lowest_price:
                lowest_price = (candle.low - lowest_price) / 2

        # Calculate volatility on the day
        volatility = (highest_price - lowest_price) / day_data.candles[0].open

        # Merge this day into the running sum
        current_sum = self.redis().get_analysis_rolling_sum(day_data.symbol, self.model_type)
        output = RollingSumFormulas.combine(current_sum, volatility, RollingSumFormulas.get_30_day_weight())

        self.save_output(symbol=day_data.symbol, raw_output=output, day_date=day_data.day_date)

    def grade_symbol(self, symbol: str, output: any) -> SymbolGrade:
        """Passes the symbol if its average daily price spread is at least 0.8%. Fails otherwise."""
        if output is None or output < 0.008:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)
        return SymbolGrade(symbol, self.model_type, SymbolGradeValue.PASS)

    def encode_output(self, raw_output: float) -> str:
        return super().encode_output(raw_output)

    def decode_output(self, encoded_output: str) -> float:
        return super().decode_output(encoded_output)
