from dataclasses import dataclass

import numpy as np
import pandas as pd
import yfinance as yf

from ray.utils.file_utilities import data_dir, s3_download

TRAIN_S3_PATH = "CRSP/crsp_2018-2023_clean_3.parquet"

# local storage path
TRAIN_FILE_NAME = TRAIN_S3_PATH.split("/")[1]
TRAIN_PATH = data_dir.joinpath(TRAIN_FILE_NAME).absolute()
TICKER_LIST_PATH = data_dir.joinpath("ticker_list.pkl")
CORR_PATH = data_dir.joinpath("corr_matrix.pkl")
COSINE_SIMILARITY_PATH = data_dir.joinpath("cosine_similarity.pkl")

TEST_PATH = data_dir.joinpath("test.parquet").absolute()


@dataclass
class CacheData:
    train: pd.DataFrame
    test: pd.DataFrame
    corr_matrix: pd.DataFrame
    cosine_similarity: pd.DataFrame


def cache_data(refresh_train=False, refresh_test=False):
    train, test = load_data(refresh_train, refresh_test)
    corr_matrix = load_corr_matrix()
    cosine_similarity = load_cosine_similarity()

    # Create an instance of CacheData and populate it
    cache_data = CacheData(train=train, test=test, corr_matrix=corr_matrix, cosine_similarity=cosine_similarity)

    return cache_data


def load_data(refresh_train=False, refresh_test=True):
    """
    This function downloads the train data from s3, and live test data from yahoo finance.
    """

    if not data_dir.exists():
        print(f"Creating data directory in {data_dir}...")
        data_dir.mkdir()

    # cache the training return into memory

    if refresh_train or not TRAIN_PATH.exists():
        print(f"Downloading training data from s3 {TRAIN_S3_PATH}...")
        s3_download(TRAIN_S3_PATH)

    # TODO: don't need to load train data if it's not refreshed
    train_df = pd.read_parquet(TRAIN_PATH)
    train = train_df.pivot(index="date", columns="ticker", values="return")

    if train.isnull().sum().sum() > 0:
        # print(train.isnull().sum())
        train = train[train.columns[train.isnull().sum() == 0]]

    # write the ticker list to a file
    ticker_list = train.columns.tolist()
    pd.to_pickle(ticker_list, TICKER_LIST_PATH)

    corr_matrix = train.corr()
    pd.to_pickle(corr_matrix, CORR_PATH)

    # TODO: s3 download the cosine similarity COSINE_SIMILARITY_PATH

    print(f"Train data shape: {train.shape}, from {train.index.min()} to {train.index.max()}")

    # load the test return data (2024-01-02 till today)

    if refresh_test or not TEST_PATH.exists():
        print("Downloading test data from Yahoo Finance...")
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

    return train, test


def load_corr_matrix():
    """
    This function downloads the correlation matrix from local disk.
    """
    corr_matrix = pd.read_pickle(CORR_PATH)

    return corr_matrix


def load_cosine_similarity():
    """
    This function downloads the embeddings from s3 and return them as a dataframe, with the cosine similarity.
    """

    cosine_similarity = pd.read_pickle(CORR_PATH)
    # TODO: load similarity instead of correlation
    # cosine_similarity = pd.read_pickle(COSINE_SIMILARITY_PATH)
    cosine_similarity.loc[:, :] = 0  # assume all is 0 for now

    return cosine_similarity
