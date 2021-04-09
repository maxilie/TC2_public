import json
import traceback
from datetime import datetime
from typing import Optional, List, Dict

from tc2.data.data_storage.redis.workers.AbstractRedisWorker import AbstractRedisWorker
from tc2.data.data_structs.account_data.RoundTripTrade import RoundTripTrade
from tc2.strategy.execution.StrategyRun import StrategyRun
from tc2.util.Config import BrokerEndpoint
from tc2.util.date_util import DATE_TIME_FORMAT


class RedisStrategiesWorker(AbstractRedisWorker):
    """
    Contains functionality for saving and loading trade history data and strategy execution & optimization data.
    """

    def get_symbols_traded(self) -> List[str]:
        """Returns a list of all symbols ever traded by the program."""
        symbols_traded = self.client.lrange(self.get_prefix() + 'SYMBOLS-TRADED', 0, -1)
        return [smbl.decode("utf-8") for smbl in symbols_traded]

    def get_trade_history(self, symbols: Optional[List[str]] = None, paper: bool = False,
                          limit: int = 999) -> List[RoundTripTrade]:
        """
        Returns a list containing buy/sell price + time info for each completed trade.
        :param symbols: the symbols for which to fetch trade data (default is None, which means all symbols)
        :param paper: set to True to fetch data for trades made on the paper account instead of the live account
        :param limit: fetch up to this many recent trades (default is 999)
        """

        # Load up to 'limit' trades for each symbol
        if symbols is None or len(symbols) == 0:
            symbols = self.get_symbols_traded()
        trade_strs = []
        if paper:
            for symbol in symbols:
                num_trades = self.client.llen(self.get_prefix() + 'PAPER-TRADES_' + symbol)
                symbl_trade_strs = self.client.lrange(self.get_prefix() + 'PAPER-TRADES_' + symbol,
                                                      max(0, num_trades - limit - 1), -1)
                if symbl_trade_strs is not None:
                    trade_strs.extend(symbl_trade_strs)
        else:
            for symbol in symbols:
                num_trades = self.client.llen(self.get_prefix() + 'LIVE-TRADES_' + symbol)
                symbl_trade_strs = self.client.lrange(self.get_prefix() + 'LIVE-TRADES_' + symbol,
                                                      max(0, num_trades - limit - 1), -1)
                if symbl_trade_strs is not None:
                    trade_strs.extend(symbl_trade_strs)
        print('trade history: {0}'.format(trade_strs))
        print('decoded trades: {0}'.format([trade_str_b.decode("utf-8") for trade_str_b in trade_strs]))
        if len(trade_strs) == 0:
            return []

        # Decode trades
        trades: List[RoundTripTrade] = [RoundTripTrade.from_string(trade_str_b.decode("utf-8")) for trade_str_b in
                                        trade_strs]

        # Sort runs ascending by date
        trades.sort(key=lambda trade: trade.buy_time)

        # Return only up to 'limit' trades total
        return trades if len(trades) < 3 else trades[0:min(limit, len(trades) - 1)]

    def record_trade(self, trade: RoundTripTrade, endpoint: BrokerEndpoint = BrokerEndpoint.PAPER) -> None:
        # Decode the trade into a string
        try:
            trade_str = str(trade)
        except Exception as e:
            self.error_main('Invalid encoded trade: {0}:'
                            .format(str(trade.symbol) + '\n' +
                                    str(trade.buy_time) + '\n' +
                                    str(trade.sell_time) + '\n' +
                                    str(trade.buy_price) + '\n' +
                                    str(trade.sell_price) + '\n' +
                                    str(trade.qty)))
            self.error_main('Error encoding trade object into string: {0}:')
            self.warn_main(traceback.format_exc())
            return

        # Delete the trade from database history if it's already present
        self.client.lrem(self.get_prefix() + 'LIVE-TRADES_' + trade.symbol, 1, trade_str)
        self.client.lrem(self.get_prefix() + 'PAPER-TRADES_' + trade.symbol, 1, trade_str)

        # Save the trade at the end of database history
        if endpoint == BrokerEndpoint.PAPER:
            self.client.rpush(self.get_prefix() + 'PAPER-TRADES_' + trade.symbol, trade_str)
        else:
            self.client.rpush(self.get_prefix() + 'LIVE-TRADES_' + trade.symbol, trade_str)
        self.client.lrem(self.get_prefix() + 'SYMBOLS-TRADED', 0, trade.symbol)
        self.client.rpush(self.get_prefix() + 'SYMBOLS-TRADED', trade.symbol)

    def clear_trade_history(self) -> None:
        """
        Purges redis of trade history for all symbols.
        """
        for symbol in self.get_symbols_traded():
            self.client.delete(self.get_prefix() + 'LIVE-TRADES_' + symbol)
            self.client.delete(self.get_prefix() + 'PAPER-TRADES_' + symbol)
        self.client.delete(self.get_prefix() + 'SYMBOLS-TRADED')

    def get_live_run_history(self, strategies: List[str], paper: bool = False, limit: int = 999,
                             symbols: Optional[List[str]] = None) -> List[StrategyRun]:
        """
        Returns a list containing metadata about the execution.
        :param strategies: fetch run data for these strategy names (see DAY_STRATEGY_IDS in strategy_creation.py)
        :param paper: set to True to return executions on the paper account instead of the live account
        :param limit: fetch up to this many runs (default is 999)
        :param symbols: fetch runs for only these symbols (default is None, which means all symbols)
        """

        # Load up to 'limit' runs for each strategy
        run_strs = []
        if paper:
            for strategy_id in strategies:
                num_runs = self.client.llen(self.get_prefix() + 'PAPER-RUNS_' + strategy_id)
                strat_run_strs = self.client.lrange(self.get_prefix() + 'PAPER-RUNS_' + strategy_id,
                                                    max(0, num_runs - limit - 1), -1)
                if strat_run_strs is not None:
                    run_strs.extend(strat_run_strs)
        else:
            for strategy_id in strategies:
                num_runs = self.client.llen(self.get_prefix() + 'LIVE-RUNS_' + strategy_id)
                strat_run_strs = self.client.lrange(self.get_prefix() + 'LIVE-RUNS_' + strategy_id,
                                                    max(0, num_runs - limit - 1), -1)
                if strat_run_strs is not None:
                    run_strs.extend(strat_run_strs)
        if len(run_strs) == 0:
            return []

        # Decode runs
        runs: List[StrategyRun] = [StrategyRun.from_string(run_str_b.decode("utf-8")) for run_str_b in run_strs]

        # Get runs for only the desired symbols
        if symbols is not None and len(symbols) > 0:
            runs = [run for run in runs if any(symbol_run.symbol in symbols for symbol_run in run.symbol_runs)]

        # Sort runs ascending by date
        runs.sort(key=lambda run: run.strategy_start_time)

        # Return only up to 'limit' runs
        return runs if len(runs) < 3 else runs[0:min(limit, len(runs) - 1)]

    def record_live_run(self, strategy_id: str,
                        run: StrategyRun,
                        endpoint: BrokerEndpoint = BrokerEndpoint.PAPER) -> None:
        """
        Stores the run in redis in the strategy's list of live runs.
        """
        if endpoint == BrokerEndpoint.PAPER:
            self.client.rpush(self.get_prefix() + 'PAPER-RUNS_' + strategy_id, str(run))
        else:
            self.client.rpush(self.get_prefix() + 'LIVE-RUNS_' + strategy_id, str(run))

        # Record the fact that we attempted to trade these symbol(s)
        for symbol in [symbol_run.symbol for symbol_run in run.symbol_runs]:
            self.client.lrem(self.get_prefix() + 'SYMBOLS-TRADED', 0, symbol)
            self.client.rpush(self.get_prefix() + 'SYMBOLS-TRADED', symbol)

    def remove_live_run(self, strategy_id: str,
                        execution: StrategyRun) -> None:
        """
        Called by admin panel to remove old and erroneous runs.
        """
        self.client.lrem(self.get_prefix() + 'PAPER-RUNS_' + strategy_id, 1, str(execution))
        self.client.lrem(self.get_prefix() + 'LIVE-RUNS_' + strategy_id, 1, str(execution))

    def get_virtual_run_history(self, strategy_ids: List[str],
                                limit: int = 999,
                                symbols: Optional[List[str]] = None) -> List[StrategyRun]:
        """
        Returns a list containing metadata about the execution.
        :param strategy_ids: fetch run data for these strategies (strategy_obj.__class__.__name__)
        :param limit: fetch up to this many runs (default is 999)
        :param symbols: fetch runs for only these symbols (default is None, which means all symbols)
        """

        # Load up to 'limit' runs for each strategy
        run_strs = []
        for strategy_id in strategy_ids:
            num_runs = self.client.llen(self.get_prefix() + 'VIRTUAL-RUNS_' + strategy_id)
            strat_run_strs = self.client.lrange(self.get_prefix() + 'VIRTUAL-RUNS_' + strategy_id,
                                                max(0, num_runs - limit - 1), -1)
            if strat_run_strs is not None:
                run_strs.extend(strat_run_strs)
        if len(run_strs) == 0:
            return []

        # Decode runs
        runs: List[StrategyRun] = [StrategyRun.from_string(run_str_b.decode("utf-8")) for run_str_b in run_strs]

        # Get runs for only the desired symbols
        if symbols is not None and len(symbols) > 0:
            runs = [run for run in runs if any(symbol_run.symbol in symbols for symbol_run in run.symbol_runs)]

        # Sort runs ascending by date
        runs.sort(key=lambda run: run.start_time)

        # Return only up to 'limit' runs
        return runs if len(runs) < 3 else runs[0:min(limit, len(runs) - 1)]

    def record_virtual_run(self,
                           strategy_id: str,
                           run: StrategyRun) -> None:
        """
        Stores the run in redis in the strategy's list of virtual runs.
        """
        self.client.rpush(self.get_prefix() + 'VIRTUAL-RUNS_' + strategy_id, str(run))

    def remove_virtual_run(self,
                           strategy_id: str,
                           run: StrategyRun) -> None:
        """Called by admin panel to remove old and erroneous runs."""
        self.client.lrem(self.get_prefix() + 'VIRTUAL-RUNS_' + strategy_id, 1, str(run))

    def clear_run_history(self,
                          strategy_ids: List[str]) -> None:
        """
        Purges redis of strategy run history (both real and virtual) for all symbols.
        """
        for strategy_id in strategy_ids:
            self.client.delete(self.get_prefix() + 'PAPER-RUNS_' + strategy_id)
            self.client.delete(self.get_prefix() + 'LIVE-RUNS_' + strategy_id)
            self.client.delete(self.get_prefix() + 'VIRTUAL-RUNS_' + strategy_id)

    def get_optimization_time(self,
                              symbol: str,
                              strategy_id: str) -> datetime:
        """
        Returns the last time the strategy was evaluated on the symbol,
            or 2015/01/01 if not yet evaluated.
        """
        time_str = self.client.hget(self.get_prefix() + symbol + '_' + strategy_id, 'optimization_time')
        return datetime(year=2015, month=1, day=1) if time_str is None \
            else datetime.strptime(time_str.decode("utf-8"), DATE_TIME_FORMAT)

    def set_optimization_time(self,
                              symbol: str,
                              strategy_id: str,
                              optimization_time: datetime) -> None:
        """
        Marks the strategy as last evaluated for the symbol at eval_time.
        """
        self.client.hset(self.get_prefix() + symbol + '_' + strategy_id, 'optimization_time',
                         optimization_time.strftime(DATE_TIME_FORMAT))

    def get_simulation_output(self) -> Optional[Dict]:
        """
        Returns the json output of the last simulated strategy execution.
        """

        sim_output_str = self.client.get(self.get_prefix() + 'simulation_output')
        if sim_output_str is None or len(sim_output_str) < 2:
            return None
        return json.loads(sim_output_str)

    def save_simulation_output(self,
                               sim_output: Dict) -> None:
        """
        Saves the json output of the last simulated strategy execution.
        """
        assert sim_output is not None

        self.client.set(self.get_prefix() + 'simulation_output', json.dumps(sim_output))

    def clear_simulation_output(self) -> None:
        """
        Unsaves the json output of the last simulated strategy execution.
        """
        self.client.delete(self.get_prefix() + 'simulation_output')
