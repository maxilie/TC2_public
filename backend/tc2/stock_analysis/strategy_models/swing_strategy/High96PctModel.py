from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.util.date_util import DATE_FORMAT


class High96PctModel(AbstractSpotModel):
    """
    Checks that the 12-hour high is within the upper 4% of the symbol's 75-week price range.
    E.g. if the 75-week range is [$24.19, $29.48], then the price must have exceeded $29.27 within the last 12 hours.
    """

    OUTPUT_TYPE = bool

    def calculate_output(self, symbol: str) -> OUTPUT_TYPE:
        """
        Returns True if the symbol's 12-hour high falls in the upper 4% of its 75-day range, False otherwise.
        """

        # Fetch latest 12 hours of data
        recent_candles = self.get_latest_candles(symbol, 60 * 12)

        # Validate 12-hour data
        if not SymbolDay.validate_candles(recent_candles, min_minutes=60 * 12):
            self.error_process(
                'High96PctModel candles ({}): {}'.format(len(recent_candles),
                                                         [candle.open for candle in recent_candles][0:3]))
            raise ValueError('High96PctModel loaded invalid recent data')

        # Fetch 75-day data
        daily_candles_75 = []
        day_date = self.time().now()
        for i in range(75):
            day_date = self.time().get_prev_mkt_day(day_date)
            daily_candle = self.mongo().load_aggregate_candle(symbol, day_date)
            if daily_candle is None:
                raise ValueError('High96PctModel couldn\'t perform its check because we '
                                 'don\'t have an aggregate candle for {}'.format(day_date.strftime(DATE_FORMAT)))
            daily_candles_75.append(daily_candle)

        # Compute 75-day price range
        low_75 = min([candle.low for candle in daily_candles_75])
        high_75 = max([candle.high for candle in daily_candles_75])

        # Check whether 12-hour high falls in upper 4% of 75-day range
        min_price_required = low_75 + (0.96 * (high_75 - low_75))
        if max([candle.high for candle in recent_candles]) >= min_price_required:
            return True
        else:
            return False

    def grade_symbol(self, symbol: str, output: OUTPUT_TYPE) -> SymbolGrade:
        """Assigns a pass/fail grade depending on whether the model output is True/False."""

        # Fail the symbol if it has no output
        if output is None or not output:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.PASS)
