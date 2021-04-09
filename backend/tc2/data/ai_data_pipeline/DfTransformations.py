from typing import List

from pandas import DataFrame


class DfTransformations:
    """
    Contains functions for transforming a pandas dataframe in preparation for AI model training.
    Some transformations include:
    - Outlier Removal
    - Normalization
    - Filtering out data by relevance
    """

    @classmethod
    def remove_outliers(cls, df: DataFrame, clms_to_ignore: List[str]) -> DataFrame:
        """
        :param df: the pandas DataFrame to transform
        :param clms_to_ignore: the titles of the columns to ignore (i.e.
        :return: df, excluding any rows that contain a value >2.5 stdevs from the median of its column
        """
        # TODO
        return df
