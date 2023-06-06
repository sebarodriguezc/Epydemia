import pandas as pd
import numpy as np

def from_file_proportion(filename, sample_size, stream, prop_col='proportion'):
    df = pd.read_csv(filename)
    metadata = {col: {val: i for i, val in enumerate(df[col].unique())}
                for col in df.columns if col != prop_col}
    assert(df[prop_col].sum() == 1)
    X = df.sample(n=sample_size, replace=True, random_state=stream, weights=prop_col)
    X.drop(columns=prop_col, inplace=True)
    for col, map_dict in metadata.items():
        X[col] = X[col].map(map_dict)
    X = {key:np.array(item) for key, item in X.to_dict(orient='list').items()}
    return X, metadata


def dict_to_csv(dictionary, filename, **kwargs):
    df = pd.DataFrame.from_dict(dictionary, **kwargs)
    df.to_csv(filename)
