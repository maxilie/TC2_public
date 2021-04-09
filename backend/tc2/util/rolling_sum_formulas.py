import math


class RollingSumFormulas:
    """
    This kind of sum weights recent additions more heavily while also reflecting past additions.
    It is biased toward zero until it has enough additions.
    """

    @staticmethod
    def combine(rolling_sum: float, measurement: float, weight: float) -> float:
        """
        Averages the new measurement into the current cycle_strategy sum:
            (new_measurement * weight) + (rolling_sum * (1 - weight))
        """
        return rolling_sum * (1 - weight) + (measurement * weight)

    @staticmethod
    def get_evaluation_weight(x: float) -> float:
        """
        Returns the weight of the newest StrategyEvaluation, given the number of days_evaluated already made:
            0.5 - (log(x/15) / 5).
        In essence, this formula takes into account hundreds of measurements, favoring the more recent ones.

        1:   .26a + .74b
        2:   .32(.26a + .74b) + .68c         =  .08z + .24b + .68c
        3:   .36(.08z + .24b + .68c) + .64d  =  .03a + .09b + .24c + .64d
        180: .71( ... ) + .29n
        600: .82( ... ) + .18n
        """
        return 0.5 - (math.log((x / 15), 10) / 5)

    @staticmethod
    def get_30_day_weight() -> float:
        """
        Returns the weight of the latest measurement (constant value): 0.2
        In essence, this formula only takes into account the 30 latest measurements, favoring the most recent ones.

        1:   .2a
        2:   .16a + .2b
        4:   .8(.13a + .16b + .2c) + .2d    =  .1a + .13b + .16c + .2d
        5:   .8(.1a + ...) + .2n
        15:   .8(.009a + ...) + .2n
        30:   .8(.0003a + ...) + .2n
        60:   .8(.0000004a + ...) + .2n
        """
        return 0.2
