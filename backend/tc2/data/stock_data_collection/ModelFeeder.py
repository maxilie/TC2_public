import traceback
from datetime import date
from typing import Optional, List

from tc2.stock_analysis.AbstractModel import AbstractModel
from tc2.stock_analysis.AbstractNeuralModel import AbstractNeuralModel
from tc2.stock_analysis.AbstractSpotModel import AbstractSpotModel
from tc2.data.data_structs.price_data.SymbolDay import SymbolDay
from tc2.env.ExecEnv import ExecEnv
from tc2.util.date_util import DATE_FORMAT
from tc2.util.model_creation import create_models


class ModelFeeder(ExecEnv):
    """
    Provides functionality for training of analysis models.
    """

    models: List[AbstractModel]

    def __init__(self,
                 env: ExecEnv) -> None:
        super().__init__(env.logfeed_program, env.logfeed_process, creator_env=env)
        self.clone_same_thread()

        # Public variables
        self.models = create_models(env=self)

    def train_models(self,
                     symbol: str,
                     day_date: date,
                     day_data: Optional[SymbolDay],
                     stable: bool,
                     possibly_already_trained: bool = False) -> None:
        """
        Trains analysis models using the data provided, or loads the data from mongo/redis.

        :param possibly_already_trained: if True, don't log when we skip over a model
        """

        data_provided = True if day_data is not None else False

        # Train each model
        for model in self.models:

            # Only train models that can be trained
            if isinstance(model, AbstractSpotModel) or isinstance(model, AbstractNeuralModel):
                continue

            # Get first time model was trained
            first_training_date = self.redis().get_analysis_start_date(symbol, model.model_type,
                                                                       self.time().now().date())

            # Get last time model was trained
            last_training_date = self.redis().get_analysis_date(symbol, model.model_type)

            # Restart training from this day if the model is missing a snapshot
            if self.redis().get_analysis_snapshot_raw_output(symbol, model.model_type) is None:
                model.restart_training(symbol)
                self.redis().save_analysis_start_date(symbol, model.model_type, day_date)
                self.info_process(f'{self.env_type.value} restarted {model.model_type} training for {symbol} from '
                                  f'{day_date.strftime(DATE_FORMAT)} (model lacks a snapshot)')

            # Restart training from this day if the model is no longer continuous
            elif last_training_date < self.time().get_prev_mkt_day(day_date):
                model.restart_training(symbol)
                self.redis().save_analysis_start_date(symbol, model.model_type, day_date)
                self.info_process(f'{self.env_type.value} restarted {model.model_type} training for {symbol} from '
                                  f'{day_date.strftime(DATE_FORMAT)} (model training missed a day before this date)')

            # Restart training from this day if the model began training after this day
            elif day_date < first_training_date:
                model.restart_training(symbol)
                self.redis().save_analysis_start_date(symbol, model.model_type, day_date)
                self.info_process(f'{self.env_type.value} restarted {model.model_type} training for {symbol} from '
                                  f'{day_date.strftime(DATE_FORMAT)} (date precedes model\'s current start date)')

            # Don't train the model if it has already been trained on this day's data
            elif day_date <= last_training_date:
                if not possibly_already_trained:
                    self.warn_process(f'{self.env_type.value} tried to train {symbol}\'s {model.model_type} more than '
                                      f'once on {day_date.strftime(DATE_FORMAT)}')
                continue

            # Revert to last stable snapshot if about to be fed new stable data
            elif stable:
                snapshot_date = model.revert_to_snapshot(symbol)
                # Restart training from this day if the snapshot is too old
                if day_date != self.time().get_next_mkt_day(snapshot_date):
                    model.restart_training(symbol)
                    self.redis().save_analysis_start_date(symbol, model.model_type, day_date)
                    self.info_process(f'{self.env_type.value} restarted {model.model_type} training for {symbol} from '
                                      f'{day_date.strftime(DATE_FORMAT)} (snapshot was too old)')

            # Get the data
            if not data_provided:
                day_data = self.mongo().load_symbol_day(symbol, day_date)
                if not SymbolDay.validate_candles(day_data.candles):
                    self.warn_process(f'{self.env_type.value} tried to train {symbol}\'s {model.model_type.value} '
                                      f'model on bad data!')
                    continue

            # Train the model
            try:
                model.feed_model(day_data)
            except Exception as e:
                self.error_process(f'Error training {self.env_type.value} {model.model_type.value}:')
                self.warn_process(traceback.format_exc())

            # Get model's new output
            model_output = model.get_stored_output(symbol)

            # Take a snapshot after being fed stable data
            if stable:
                model.take_snapshot(symbol, model_output, day_date)

    def reset_models(self, symbols: List[str]) -> None:
        self.info_process(f'{self.env_type.value} ModelFeeder resetting analysis models for {symbols}')
        for model in self.models:
            model.reset(symbols)
