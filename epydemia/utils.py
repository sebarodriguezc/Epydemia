import pandas as pd
import numpy as np
from . import MASKING_STATES
from datetime import datetime


class DateToSim:
    FORMAT = '%m/%d/%Y'
    START = datetime.strptime('01/01/2020', FORMAT)

    @classmethod
    def set_format(format):
        """

        Args:
            format (str): _description_
        """
        DateToSim.FORMAT = format

    @classmethod
    def set_start(start):
        """

        Args:
            start (str): _description_
        """
        DateToSim.START = datetime.strptime(start, DateToSim.FORMAT)

    @classmethod
    def to_simtime(date, unit='days'):
        """_summary_

        Args:
            date (_type_): _description_

        Returns:
            int: difference between start date and input date in desired unit.
        """
        dt = datetime.strptime(date, DateToSim.FORMAT)
        difference = dt - DateToSim.START
        if unit == 'days':
            return difference.total_seconds()/86400
        elif unit == 'hours':
            return difference.total_seconds()/3600
        elif unit == 'minutes':
            return difference.total_seconds()/60
        elif unit == 'seconds':
            return difference.total_seconds()
        else:
            raise NotImplementedError


def from_file_proportion(filename, sample_size, stream, prop_col='proportion'):
    df = pd.read_csv(filename)
    metadata = {col: {val: i for i, val in enumerate(df[col].unique())}
                for col in df.columns if col != prop_col}
    assert(df[prop_col].sum() == 1)
    X = df.sample(n=sample_size, replace=True, random_state=stream,
                  weights=prop_col)
    X.drop(columns=prop_col, inplace=True)
    for col, map_dict in metadata.items():
        X[col] = X[col].map(map_dict)
    X = {key: np.array(item) for key, item in X.to_dict(orient='list').items()}
    return X, metadata


def dict_to_csv(dictionary, filename, **kwargs):
    df = pd.DataFrame.from_dict(dictionary, **kwargs)
    df.to_csv(filename)


def vaccinate_age(population, stream, age_target, coverage):
    idx_ = np.where((population['age'] >= age_target[0]) &
                    (population['age'] <= age_target[1]))[0]
    return stream.choice(idx_, size=round(int(len(idx_)*coverage)),
                         replace=False)
