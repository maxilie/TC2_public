from typing import List

from tc2.env.ExecEnv import ExecEnv
from tc2.util.Config import BrokerEndpoint


class Settings:
    """Contains class methods that convert setting strings into proper objects."""

    # The default maximum percentage of our account balance to use on any single strategy
    DEFAULT_STRATEGY_MAX_PURCHASE_PCT = 0.2

    # The default maximum amount of money to use on any single strategy
    DEFAULT_STRATEGY_MAX_PURCHASE_USD = 6000

    @classmethod
    def get_endpoint(cls, env: ExecEnv) -> BrokerEndpoint:
        """
        Returns the alpaca endpoint being used for live trading: LIVE or PAPER.
        """
        return BrokerEndpoint.LIVE if env.get_setting('alpaca.endpoint').lower() == 'live' else BrokerEndpoint.PAPER

    @classmethod
    def get_symbols(cls, env: ExecEnv) -> List[str]:
        """
        Returns the list of symbols being watched by the program.
        """
        return [symbol.upper().strip() for symbol in env.get_setting('symbols').split(',')]

    @classmethod
    def get_strategy_max_purchase_pct(cls, env: ExecEnv, strategy_id: str) -> float:
        """
        Returns the maximum percentage of our account balance to use on the given strategy.
        """
        setting_str = env.get_setting('max_purchase_pct.' + strategy_id)
        if setting_str == '':
            env.warn_main(f'Maximum purchase percent for {strategy_id} not set. Using default value of '
                          f'{100 * cls.DEFAULT_STRATEGY_MAX_PURCHASE_PCT:.0f}%')
            return cls.DEFAULT_STRATEGY_MAX_PURCHASE_PCT
        else:
            return float(setting_str)

    @classmethod
    def get_strategy_max_purchase_usd(cls, env: ExecEnv, strategy_id: str) -> float:
        """
        Returns the maximum amount of money to use on the given strategy.
        """
        setting_str = env.get_setting('max_purchase_usd.' + strategy_id)
        if setting_str == '':
            env.warn_main(f'Maximum purchase amount for {strategy_id} not set. '
                          f'Using default value of ${cls.DEFAULT_STRATEGY_MAX_PURCHASE_USD}')
            return cls.DEFAULT_STRATEGY_MAX_PURCHASE_USD
        else:
            return float(setting_str)
