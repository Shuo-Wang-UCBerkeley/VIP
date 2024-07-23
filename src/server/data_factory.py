import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from src.ray.utils.file_utilities import data_dir, s3_download

train_s3_path = "CRSP/crsp_2018-2023_clean_3.parquet"
train_file_name = train_s3_path.split("/")[1]
TRAIN_PATH = data_dir.joinpath(train_file_name).absolute()

# local storage path
APP_DATA_DIR = Path(__file__).joinpath("../data").resolve()
TRAIN_DATA_PATH = APP_DATA_DIR.joinpath("train_data.pickle").absolute()
TEST_PATH = APP_DATA_DIR.joinpath("test.parquet").absolute()


@dataclass
class TrainData:
    ticker_list: list[str]

    volatilities: pd.Series
    mean_return: pd.Series

    corr_matrix: pd.DataFrame
    cosine_similarity: pd.DataFrame


def load_data(refresh_train=False, refresh_test=False) -> tuple[TrainData, pd.DataFrame]:

    train = load_train_data(refresh_train)
    test = load_test_data(ticker_list=train.ticker_list, refresh_test=refresh_test)

    return train, test


def load_train_data(refresh_train) -> TrainData:
    """
    This function downloads the train data from s3, and live test data from yahoo finance.
    """

    if refresh_train or not TRAIN_DATA_PATH.exists():
        if not APP_DATA_DIR.exists():
            print(f"Creating data directory in {APP_DATA_DIR}...")
            APP_DATA_DIR.mkdir()

        print(f"Downloading training data from s3 {train_s3_path}...")
        s3_download(train_s3_path)

        train_df = pd.read_parquet(TRAIN_PATH)
        train = train_df.pivot(index="date", columns="ticker", values="return")

        if train.isnull().sum().sum() > 0:
            # print(train.isnull().sum())
            train = train[train.columns[train.isnull().sum() == 0]]
        print(f"Train data shape: {train.shape}, from {train.index.min()} to {train.index.max()}")

        ticker_list = train.columns.tolist()
        mean_return = train.mean(axis=0).reindex()
        volatilities = train.std().reindex()

        corr_matrix = train.corr()
        cosine_similarity = pd.DataFrame(
            np.ones((len(ticker_list), len(ticker_list))), index=ticker_list, columns=ticker_list
        )  # TODO: s3 download the cosine similarity COSINE_SIMILARITY_PATH

        train_data = TrainData(
            ticker_list=ticker_list,
            mean_return=mean_return,
            volatilities=volatilities,
            corr_matrix=corr_matrix,
            cosine_similarity=cosine_similarity,
        )

        # put train_data into pickle file for future use
        with open(TRAIN_DATA_PATH, "wb") as f:
            pickle.dump(train_data, f)
    else:
        with open(TRAIN_DATA_PATH, "rb") as f:
            train_data = pickle.load(f)

    return train_data


def load_test_data(ticker_list: list[str], refresh_test) -> pd.DataFrame:
    """
    load the test return data (2024-01-02 till today)
    """

    if refresh_test or not TEST_PATH.exists():
        print("Refreshing test data from Yahoo Finance...")
        test_tickers = ticker_list + ["SPY"]
        test_df = yf.download(test_tickers, start="2023-12-29")
        test_close = pd.DataFrame(test_df["Adj Close"])

        test = pd.DataFrame(np.log(test_close / test_close.shift()))
        test = test.drop(test.index[0])  # drop the first day with NaN

        # Count the number of nulls in each column
        null_counts = test.isnull().sum()
        total_rows = len(test)
        null_percentages = (null_counts / total_rows) * 100
        print(f"Tickers with >1% null: {null_percentages[null_percentages > 1].index}")
        test = test[null_percentages[null_percentages <= 1].index]

        # fill 0 for the rest of NaN
        if test.isnull().sum().sum() > 0:
            print(f"still has null but filling with NaN: {test.isnull().sum()}")
            test = test.fillna(0)
        test.to_parquet(TEST_PATH)
    else:
        test = pd.read_parquet(TEST_PATH)

    print(f"Test data shape: {test.shape}, from {test.index.min()} to {test.index.max()}")
    return test
