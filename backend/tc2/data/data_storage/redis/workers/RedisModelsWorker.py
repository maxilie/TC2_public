from datetime import datetime, date
from typing import List

from tc2.stock_analysis.AnalysisModelType import AnalysisModelType
from tc2.data.data_storage.redis.workers.AbstractRedisWorker import AbstractRedisWorker
from tc2.util.data_constants import START_DATE
from tc2.util.date_util import DATE_FORMAT


class RedisModelsWorker(AbstractRedisWorker):
    """
    Contains functionality for saving and loading analysis model data.
    """

    def get_analysis_rolling_sum(self, symbol: str, model_type: AnalysisModelType) -> float:
        """
        Returns the stored output of a Forgetful Model.
        :param symbol:
        :param model_type: the analysis model which calculated the rolling sum
        :return: the current rolling sum; defaults to 0
        """
        sum_str = self.get_analysis_raw_output(symbol, model_type)
        return 0 if sum_str == '' else float(sum_str)

    def get_analysis_raw_output(self, symbol: str, model_type: AnalysisModelType) -> str:
        """
        Returns the stored output of an Analysis Model.
        :param symbol:
        :param model_type: the analysis model which produced the output
        :return: the model's raw output to be decoded by AbstractAnalysisModel.decode(); defaults to ''
        """
        output_str = self.client.hget(self.get_prefix() + 'ANALYSIS-LATEST-RESULT-' + model_type.value, symbol)
        return '' if output_str is None else output_str.decode("utf-8")

    def save_analysis_result(self, symbol: str, model_type: AnalysisModelType, encoded_result: str) -> None:
        """
        Stores the output of an Analysis Model.
        :param model_type: the analysis model which produced the result
        :param encoded_result: the analysis model_type/model's result encoded into a string
        """
        self.client.hset(self.get_prefix() + 'ANALYSIS-LATEST-RESULT-' + model_type.value, symbol, encoded_result)

    def get_analysis_date(self, symbol: str, model_type: AnalysisModelType) -> date:
        """
        :param symbol:
        :param model_type: the analysis model which analyzes the symbol
        :return: the latest date for which data was applied to the model, defaults to START_DATE
        """
        date_str = self.client.hget(self.get_prefix() + 'ANALYSIS-LATEST-DATE-' + model_type.value, symbol)
        return START_DATE if date_str is None or date_str == '' else \
            datetime.strptime(date_str.decode("utf-8"), DATE_FORMAT).date()

    def get_analysis_start_date(self,
                                symbol: str,
                                model_type: AnalysisModelType,
                                today: date) -> date:
        """
        :param symbol:
        :param model_type: the analysis model which analyzes the symbol
        :return: the earliest date for which data was applied to the model, defaults to today
        """
        date_str = self.client.hget(self.get_prefix() + 'ANALYSIS-START-DATE-' + model_type.value, symbol)
        return today if date_str is None or date_str == '' else \
            datetime.strptime(date_str.decode("utf-8"), DATE_FORMAT).date()

    def save_analysis_date(self, symbol: str, model_type: AnalysisModelType, day_date: date) -> None:
        """
        Records the latest model update date.
        :param symbol:
        :param model_type: the analysis model which analyzed the symbol
        :param day_date: the latest date on which the model was fed data for the symbol
        """
        self.client.hset(self.get_prefix() + 'ANALYSIS-LATEST-DATE-' + model_type.value, symbol,
                         day_date.strftime(DATE_FORMAT))

    def save_analysis_start_date(self,
                                 symbol: str,
                                 model_type: AnalysisModelType,
                                 day_date: date) -> None:
        """
        Records the earliest model update date.
        :param symbol:
        :param model_type: the analysis model which analyzed the symbol
        :param day_date: the earliest date on which the model was fed data for the symbol
        """
        self.client.hset(self.get_prefix() + 'ANALYSIS-START-DATE-' + model_type.value, symbol,
                         day_date.strftime(DATE_FORMAT))

    def get_analysis_snapshot_raw_output(self, symbol: str, model_type: AnalysisModelType) -> str:
        """
        Returns the stored output of an Analysis Model.
        :param symbol:
        :param model_type: the analysis model which produced the output
        :return: the model's raw output to be decoded by AbstractAnalysisModel.decode(); defaults to ''
        """
        output_str = self.client.hget(self.get_prefix() + 'ANALYSIS-SNAPSHOT-RESULT-' + model_type.value, symbol)
        return '' if output_str is None else output_str.decode("utf-8")

    def save_analysis_snapshot_result(self, symbol: str, model_type: AnalysisModelType, encoded_result: str) -> None:
        """
        Stores the output of an Analysis Model.
        :param symbol:
        :param model_type: the analysis model which produced the result
        :param encoded_result: the analysis model_type/model's result encoded into a string
        """
        self.client.hset(self.get_prefix() + 'ANALYSIS-SNAPSHOT-RESULT-' + model_type.value, symbol, encoded_result)

    def get_analysis_snapshot_date(self, symbol: str, model_type: AnalysisModelType) -> date:
        """
        :param model_type: the analysis model which analyzes the symbol
        :return: the latest date for which data was applied to the model, defaults to START_DATE
        """
        date_str = self.client.hget(self.get_prefix() + 'ANALYSIS-SNAPSHOT-DATE-' + model_type.value, symbol)
        return START_DATE if date_str is None or date_str == '' else \
            datetime.strptime(date_str.decode("utf-8"), DATE_FORMAT).date()

    def save_analysis_snapshot_date(self, symbol: str, model_type: AnalysisModelType, day_date: date) -> None:
        """
        Records the latest model update date.
        :param symbol:
        :param model_type: the analysis model which analyzed the symbol
        :param day_date: the latest date on which the model was fed data for the symbol
        """
        self.client.hset(self.get_prefix() + 'ANALYSIS-SNAPSHOT-DATE-' + model_type.value, symbol,
                         day_date.strftime(DATE_FORMAT))

    def remove_analysis_snapshot(self, model_type: AnalysisModelType) -> None:
        """
        Un-saves all symbol data (output and last-update-date) produced by the Analysis Model in the given environment.
        :param model_type:
        """
        self.client.delete(self.get_prefix() + 'ANALYSIS-SNAPSHOT-RESULT-' + model_type.value)
        self.client.delete(self.get_prefix() + 'ANALYSIS-SNAPSHOT-DATE-' + model_type.value)

    def remove_analysis_data(self, model_type: AnalysisModelType, symbols: List[str] = None) -> None:
        """
        Un-saves symbol data (output and last-update-date) produced by the Analysis Model in the given environment.
        :param model_type:
        :param symbols: if specified, only clear data on these symbols
        """
        if symbols is None:
            self.client.delete(self.get_prefix() + 'ANALYSIS-LATEST-RESULT-' + model_type.value)
            self.client.delete(self.get_prefix() + 'ANALYSIS-SNAPSHOT-RESULT-' + model_type.value)
            self.client.delete(self.get_prefix() + 'ANALYSIS-START-DATE-' + model_type.value)
            self.client.delete(self.get_prefix() + 'ANALYSIS-LATEST-DATE-' + model_type.value)
            self.client.delete(self.get_prefix() + 'ANALYSIS-SNAPSHOT-DATE-' + model_type.value)
            return
        for symbol in symbols:
            self.client.hdel(self.get_prefix() + 'ANALYSIS-LATEST-RESULT-' + model_type.value, symbol)
            self.client.hdel(self.get_prefix() + 'ANALYSIS-SNAPSHOT-RESULT-' + model_type.value, symbol)
            self.client.hdel(self.get_prefix() + 'ANALYSIS-START-DATE-' + model_type.value, symbol)
            self.client.hdel(self.get_prefix() + 'ANALYSIS-LATEST-DATE-' + model_type.value, symbol)
            self.client.hdel(self.get_prefix() + 'ANALYSIS-SNAPSHOT-DATE-' + model_type.value, symbol)
