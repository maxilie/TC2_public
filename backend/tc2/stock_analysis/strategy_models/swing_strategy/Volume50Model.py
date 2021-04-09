from numpy import mean

from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.util.date_util import DATE_FORMAT


class Volume50Model(AbstractSpotModel):
    """
    Checks that the latest day's volume was at least 1.25 times the average volume over the previous 50 days.
    E.g. if the mean volume during [t-1, t-51] was 1.4 million, then the volume on day t must be at least 1.75 million.
    """

    OUTPUT_TYPE = bool

    def calculate_output(self, symbol: str) -> OUTPUT_TYPE:
        """
        Returns True if the previous trading day's volume was >= the average volume of the previous 50 days.
        """

        # Fetch latest daily candle
        latest_date = self.time().get_prev_mkt_day(self.time().now().date())
        latest_daily_candle = self.mongo().load_aggregate_candle(symbol, latest_date)
        if latest_daily_candle is None:
            self.debug_process('{} fails Volume50Model since it doesn\'t have yesterday\'s aggregate data ({})'
                               .format(symbol, latest_date.strftime(DATE_FORMAT)))
            return False

        # Fetch aggregate data for the 50 days preceding latest_date
        previous_date = latest_date
        daily_candles_50 = []
        for i in range(50):
            previous_date = self.time().get_prev_mkt_day(previous_date)
            daily_candle = self.mongo().load_aggregate_candle(symbol, previous_date)
            if daily_candle is None:
                self.debug_process('{} fails Volume50Model: missing daily candle for {}'
                                   .format(symbol, previous_date.strftime(DATE_FORMAT)))
                return False
            daily_candles_50.append(daily_candle)

        # Check whether the latest volume is at least 1.25 times the 50-day average volume
        return latest_daily_candle.volume >= 1.25 * mean([daily_candle.volume for daily_candle in daily_candles_50])

    def grade_symbol(self, symbol: str, output: OUTPUT_TYPE) -> SymbolGrade:
        """Assigns a pass/fail grade depending on whether the model output is True/False."""

        # Fail the symbol if it has no output
        if output is None or not output:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.PASS)
