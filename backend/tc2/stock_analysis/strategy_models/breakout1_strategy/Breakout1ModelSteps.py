from tc2.stock_analysis.model_output.ModelSteps import ModelSteps


class Breakout1ModelSteps(ModelSteps):
    INITIALIZATION = ('Initialization', 'data must be valid in order to use the model')
    DIPS_TO_SUPPORT = ('Dip Above Support', '-15% to 20% of the period\'s range is good')
    BREAKS_RESISTANCE = ('Surge Above Resistance', '>10% of the period\'s range is good')
    RANGE_CHANGE_1 = ('Range Change 1', '')
    RANGE_CHANGE_2 = ('Range Change 2', '')
    MAX_REWARD = ('Max Reward', '>0.15% is good')
    HIGH_VOL_DROP_RATIO = ('High Volume Drop Ratio', 'we want at least 1.7:1 minutes drop price when volume is high')
    STRONGEST_HIGH_VOL_DIP = ('Strongest Real Dip', 'we want the strongest volume-backed dip to be under 1.7 stdevs '
                                                    'stronger than average')
    EMA_MINUTE_VOLUME = ('EMA Volume (minute)', 'we want this period\'s moving-average-volume to be at least 20% '
                                                'higher than median of the previous 7 period\'s moving-average-volumes')
