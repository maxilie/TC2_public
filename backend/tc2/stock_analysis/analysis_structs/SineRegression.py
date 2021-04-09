import math
from datetime import datetime
from typing import List

import numpy
import scipy.optimize

from tc2.data.data_structs.price_data.Candle import Candle


class SineRegression:
    """
    A sine wave fit to local minima and maxima of a period's prices.
    """

    # The candles used to generate the sine curve
    candles: List[Candle]

    def __init__(self, candles: List[Candle]):
        self.candles = candles
        tt = numpy.array([self.moment_to_x(candle.moment) for candle in candles])
        yy = numpy.array([candle.open for candle in candles])
        ff = numpy.fft.fftfreq(len(tt), (tt[1] - tt[0]))
        Fyy = abs(numpy.fft.fft(yy))
        guess_freq = abs(
            ff[numpy.argmax(Fyy[1:]) + 1])
        guess_amp = numpy.std(yy) * 2.0 ** 0.5
        guess_offset = numpy.mean(yy)
        guess = numpy.array([guess_amp, 2.0 * numpy.pi * guess_freq, 0.0, guess_offset])

        def sinfunc(t, A, w, p, c):
            return A * numpy.sin(w * t + p) + c

        try:
            popt, pcov = scipy.optimize.curve_fit(sinfunc, tt, yy, p0=guess)
        except Exception as e:
            popt, pcov = ([0, 1, 0, 0], numpy.array([0]))
        A, w, p, c = popt
        f = w / (2.0 * numpy.pi)
        fitfunc = lambda t: A * numpy.sin(w * numpy.array([self.moment_to_x(t_date) for t_date in t]) + p) + c
        self.amplitude = A
        self.omega = w
        self.phase = p
        self.offset = c
        self.frequency = f
        self.period = 1.0 / f
        self.fitfunc = fitfunc
        self.maxcov = numpy.max(pcov)
        self.rawres = (guess, popt, pcov)

    def y_of_x(self,
               x_moment: datetime) -> float:
        """
        Evaluates the sine wave function at the given moment, returning a price value.
        """
        try:
            self.offset + self.amplitude * math.sin(self.omega * self.moment_to_x(x_moment) + self.phase)
        except Exception as e:
            print(f'sin regression parameters: offset "{self.offset}"   amplitude: "{self.amplitude}"   omega: "'
                  f'{self.omega}"   x: "{self.moment_to_x(x_moment)}"   phase: "{self.phase}"')
        return self.offset + self.amplitude * math.sin(self.omega * self.moment_to_x(x_moment) + self.phase)

    def moment_to_x(self,
                    x_moment: datetime) -> float:
        """
        Converts a moment in time to a decimal number relative to the wave's origin time.
        """
        return (x_moment - self.candles[0].moment).total_seconds()
