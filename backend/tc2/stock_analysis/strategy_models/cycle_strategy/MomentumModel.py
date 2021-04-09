from math import exp
from statistics import median, stdev

from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.util.data_constants import MIN_CANDLES_PER_MIN


class MomentumModel(AbstractSpotModel):
    """
    Models momentum within the first 45 minutes as a number between -100 and +100.
    Momentum is price-per-second adjusted for volume-per-second compared to average volume.
    More recent candles are given more weight in the calculation than older candles.
    """

    OUTPUT_TYPE = float

    def calculate_output(self, symbol: str) -> OUTPUT_TYPE:
        """
        This tells us is whether the price has been trending downward (accounting for volume) today, not long-term.
        """

        # Fetch latest 45 mins of data
        candles = self.get_latest_candles(symbol, 45)

        # TODO REMOVE LATER: Debug candle validation
        if len(candles) > MIN_CANDLES_PER_MIN * 45:
            debug_lines = ['\n']
            debug_lines.append('candle validation debug output:')
            SymbolDay.validate_candles(candles, min_minutes=45, debug_output=debug_lines)
            debug_lines.append('\n')

        # Validate data
        if not SymbolDay.validate_candles(candles, min_minutes=45):
            self.error_process(
                'MomentumModel candles ({}): {}'.format(len(candles), [candle.open for candle in candles][0:3]))
            raise ValueError('Momentum calculation given invalid data')

        # Find "typical" volume change for the period, using median and std dev
        volume_changes = []
        for i in range(1, len(candles)):
            volume_changes.append(candles[i].volume - candles[i - 1].volume)
        med_vol_chg = median(volume_changes)
        vol_chg_stdev = stdev(volume_changes)

        # Collect normalized volume and price changes to see what direction the stock is going
        # This is a slightly fancier way of multiplying trade price by number of trades
        weighted_price_changes = []
        last_candle = candles[0]
        for candle in candles[1:-1]:
            vol_change = candle.volume - last_candle.volume
            price_change = (candle.low - last_candle.low) / last_candle.low
            """
            < 2: least volume within the 45-min period
            < 0: less volume than usual for the 45-min period
            > 0: more volume than usual for the 45-min period
            > 2: most volume within the 45-min period
            """
            std_devs = (vol_change - med_vol_chg) / vol_chg_stdev
            # Always positive, high value means more volume than usual
            weight = max(0, std_devs + 1.8)
            # Sign indicates direction of the price movement, value indicates significance
            weighted_change = 100 * price_change * 100 * weight
            weighted_price_changes.append(weighted_change)

            last_candle = candle

        # Calculate a sum that favors recent data
        sum_pct_price_changes = 0
        x = 0
        incr = 3.0 / len(weighted_price_changes)
        for change in weighted_price_changes[-1:0:-1]:
            x += incr
            weight = exp(-x)
            sum_pct_price_changes += change * weight
            # The longer movement stays negative, the more we should expect it to change and vice versa
            if abs(sum_pct_price_changes) > 3:
                sum_pct_price_changes += -2 if sum_pct_price_changes > 0 else 0.2
        sum_pct_price_changes = sum_pct_price_changes / 2

        # The symbol is risky if the momentum is in a downward direction
        return sum_pct_price_changes

    def grade_symbol(self, symbol: str, output: OUTPUT_TYPE) -> SymbolGrade:
        """Assigns a good grade to a high momentum value."""

        # Fail the symbol if it has no output
        if output is None:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # Fail the symbol if price is trending strongly downward
        if output < -0.5:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # Assign a bad grade if price is trending moderately downward
        elif output < -0.2:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.RISKY)

        # Assign a mediocre grade if price is trending somewhat downward
        elif output < -0.09:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.UNPROMISING)

        # Assign a neutral grade if price trending flat or up & down
        elif output < 0.09:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.SATISFACTORY)

        # Assign a good grade if price is trending somewhat upward
        elif output < 0.15:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GOOD)

        # Assign a great grade if price is trending strongly upward
        elif output < 0.5:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GREAT)

        # Assign a mediocre grade if price is trending strongly upward (because we likely won't catch a price dip)
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.UNPROMISING)
