import traceback
from statistics import mean, median, stdev
from typing import List

from tc2.data.data_structs.price_data.Candle import Candle
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.stock_analysis.ModelWeightingSystem import SymbolGrade, SymbolGradeValue
from tc2.stock_analysis.analysis_structs.SimpleLinearRegression import SimpleLinearRegression
from tc2.stock_analysis.analysis_structs.SineRegression import SineRegression
from tc2.strategy.strategies.long_short.longshort_constants import OSCILLATION_PERIOD_LENGTH
from tc2.util.candle_util import find_mins_maxs, get_steady_range


class OscillationModel(AbstractSpotModel):
    """
    Defines the condition for starting LongShortStrategy, which requires the market to
        be oscillating back and forth frequently rather than trending up or down.
    Ensures that the S&P-500 is oscillating, and that the current price is within the
        middle of the oscillation range.
    """

    # A number between 0 and 1, measuring how closely the price graph resembles a sine wave.
    OUTPUT_TYPE = float

    # The minimum price range needed in order to consider a period oscillatory.
    MIN_STEADY_RANGE_PCT = 0.032

    # The maximum linear trend allowed in order to consider a period oscillatory.
    MAX_ABS_LINEAR_TREND_PCT = 50

    # The minimum number of peaks in a wave needed in order to consider a period oscillatory.
    MIN_SINE_PEAKS = 2

    # The minimum distance from a wave's high to low, as a percent of price range, needed in
    # order to consider a period oscillatory.
    MIN_SINE_COVERAGE_PCT = 30

    # The minimum percent the recent S&P-500 prices must resemble a sine wave in order
    # for LongShortStrategy to pass this viability check.
    PASSING_OSC_PCT = 0

    def calculate_output(self,
                         symbol: str) -> OUTPUT_TYPE:
        """
        Returns a number between 0 and 1, indicating how closely the price graph resembles
            a sine wave during the period.
        """

        # Only run this model on SPY.
        if symbol != 'SPY':
            return 0

        # Fetch data during the period.
        candles = self.get_latest_candles(symbol, OSCILLATION_PERIOD_LENGTH / 60)

        # Validate data.
        if not SymbolDay.validate_candles(candles, min_minutes=int(0.8 * OSCILLATION_PERIOD_LENGTH / 60)):
            self.error_process(
                'OscillationModel candles ({}): {}'.format(len(candles), [candle.open for candle in candles][0:3]))
            raise ValueError('OscillationModel could not fetch valid data')

        try:
            oscillation_val = self.get_oscillation_val(candles)
        except Exception as e:
            self.error_process(f'Error calculating oscillation value: {traceback.format_exc()}')
            oscillation_val = 0
        return oscillation_val

    def get_oscillation_val(self,
                            candles: List[Candle]) -> float:
        """
        Returns the period's resemblance to a sine wave, on a scale from 0-1.
        """

        # Check that the period's price range is large enough.
        low_steady, high_steady = get_steady_range(candles, percentile=0.9)
        range_steady = high_steady - low_steady
        # print(f'Steady low / high / range: {low_steady:.2f} / {high_steady:.2f} /'
        #      f'{100 * range_steady / low_steady:.2f}%')
        if range_steady / max(0.1, low_steady) < self.MIN_STEADY_RANGE_PCT / 100.0:
            narrow_range = range_steady / max(0.1, low_steady)
            self.debug_process(f'No oscillation value: price range too narrow ({100 * narrow_range:.3f}%)')
            return 0

        # Remove seconds with anomalous price data.
        candles = [candle for candle in list(candles)
                   if min(candle.open, candle.high, candle.low, candle.close) >= low_steady
                   and max(candle.open, candle.high, candle.low, candle.close) <= high_steady]

        # Ensure the period's latest prices fall in the middle of the period's price range.
        middle_low = low_steady
        middle_high = high_steady
        latest_candles = candles[int(len(candles) * 0.9):]
        min_latest_prices = min([candle.close for candle in latest_candles])
        max_latest_prices = max([candle.close for candle in latest_candles])
        med_latest_prices = median([candle.close for candle in latest_candles])
        min_all_prices = min([candle.close for candle in candles])
        max_all_prices = max([candle.close for candle in candles])
        med_all_prices = median([candle.close for candle in candles])
        if med_latest_prices < med_all_prices and \
                min_latest_prices < middle_low:
            self.debug_process(f'No oscillation value: latest prices below steady range')
            return 0
        elif med_latest_prices > med_all_prices and \
                max_latest_prices > middle_high:
            self.debug_process(f'No oscillation value: latest prices above steady range')
            return 0

        # Ensure there is no significant trend (using linear regression).
        regr = SimpleLinearRegression(candles)
        regr_range = abs(regr.y_of_x(candles[-1].moment) - regr.y_of_x(candles[0].moment))
        # print(f'Linear regression range: {100 * regr_range / range_steady:.2f}%')
        if regr_range / max(0.1, range_steady) > self.MAX_ABS_LINEAR_TREND_PCT / 100.0:
            trend_pct = 100 * regr_range / max(0.1, range_steady)
            self.debug_process(f'No oscillation value: significant trend detected ({trend_pct:.1f}%)')
            return 0

        # Detect local minima and maxima during the period.
        try:
            mins, maxs = find_mins_maxs(candles)
        except Exception as e:
            # In case of too few candles to find minima/maxima, consider the period non-oscillatory.
            self.debug_process(f'No oscillation value: could not find mins and maxes')
            return 0
        mins_and_maxs = sorted(mins + maxs, key=lambda candle: candle.moment)

        # Fit a sine wave to the period's local minima and maxima.
        sine_regr = SineRegression(mins_and_maxs)

        # Ensure high frequency: i.e. the wave oscillates at least n times.
        # print(f'Peaks: {sine_regr.frequency * period_length:.1f}')
        if sine_regr.frequency * OSCILLATION_PERIOD_LENGTH < self.MIN_SINE_PEAKS:
            self.debug_process(f'No oscillation value: sine wave only has '
                               f'{sine_regr.frequency * OSCILLATION_PERIOD_LENGTH:.1f} peak(s)')
            return 0

        # Ensure high amplitude: i.e. the wave covers enough of the period's price range.
        sine_high = abs(sine_regr.amplitude) + sine_regr.offset
        sine_low = -1 * abs(sine_regr.amplitude) + sine_regr.offset
        sine_range = sine_high - sine_low
        # print(f'Price range covered: {100 * sine_range / range_steady:.0f}%')
        if sine_range / max(0.1, range_steady) < self.MIN_SINE_COVERAGE_PCT / 100:
            self.debug_process(f'No oscillation value: sine wave only covers '
                               f'{100 * sine_range / max(0.1, range_steady):.2f}% of the price range')
            return 0

        # Calculate error pct between sine wave and actual prices.
        errors = [(sine_regr.y_of_x(candle.moment) - candle.open) / max(0.1, range_steady) for candle in candles]

        # Drop miniscule errors (err < 5%).
        errors = [error for error in errors if abs(error) > 0.05]

        # Drop extreme errors (stdev > 3).
        initial_error_mean = mean(errors)
        error_stdev = stdev(errors)
        errors = [error for error in errors if abs(error - initial_error_mean) < error_stdev * 3]

        # Define oscillation value as 1 minus mean error percent.
        oscillation_val = 0.1 + max(0, 0.9 - abs(mean(errors)))
        print(f'Oscillation value: {100 * oscillation_val:.1f}%')

        return oscillation_val

    def grade_symbol(self,
                     symbol: str,
                     output: OUTPUT_TYPE) -> SymbolGrade:
        """
        Assigns a good grade if the price graph looks like a sine wave.
        """

        # Fail the symbol if it has no output.
        if output is None or symbol is not 'SPY':
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)

        # Fail the symbol if price graph has little to no resemblance with a sine wave.
        self.debug_process(f'S&P-500 oscillation value: {100 * output:.2f}%')
        if output < self.PASSING_OSC_PCT / 100.0:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.FAIL)
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.PASS)

        """
        # Assign a bad grade if price graph has barely resembles a sine wave.
        elif output < 0.1:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.RISKY)

        # Assign a mediocre grade if price graph has little resemblance with a sine wave
        elif output < 0.2:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.UNPROMISING)

        # Assign a neutral grade if price graph has some resemblance with a sine wave
        elif output < 0.35:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.SATISFACTORY)

        # Assign a good grade if price graph has significant resemblance with a sine wave
        elif output < 0.5:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GOOD)

        # Assign a great grade if price graph has strong resemblance with a sine wave
        elif output < 0.7:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.GREAT)

        # Assign an excellent grade if price graph has very strong resemblance with a sine wave
        else:
            return SymbolGrade(symbol, self.model_type, SymbolGradeValue.EXCELLENT)
        """
