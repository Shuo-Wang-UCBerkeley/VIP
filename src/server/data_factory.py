import numpy as np
import pandas as pd
import yfinance as yf

from ray.utils.file_utilities import data_dir, s3_download

train_s3_path = "CRSP/crsp_2018-2023_clean_3.parquet"

# local storage path

file_name = train_s3_path.split("/")[1]
train_path = data_dir.joinpath(file_name).absolute()
ticker_list_path = data_dir.joinpath("ticker_list.pkl")
corr_matrix_path = data_dir.joinpath("corr_matrix.pkl")
test_path = data_dir.joinpath("test.parquet").absolute()


def load_data(refresh_train=False, refresh_test=True):
    """
    This function downloads the train data from s3, and live test data from yahoo finance.
    """

    if not data_dir.exists():
        print("Creating data directory...")
        data_dir.mkdir()

    # cache the training return into memory

    if refresh_train or not train_path.exists():
        print("Downloading training data from s3...")
        s3_download(train_s3_path)

    train_df = pd.read_parquet(train_path)
    train = train_df.pivot(index="date", columns="ticker", values="return")

    if train.isnull().sum().sum() > 0:
        # print(train.isnull().sum())
        train = train[train.columns[train.isnull().sum() == 0]]

    # write the ticker list to a file
    ticker_list = train.columns
    pd.to_pickle(ticker_list, ticker_list_path)

    corr_matrix = train.corr()
    pd.to_pickle(corr_matrix, corr_matrix_path)

    print(f"Train data shape: {train.shape}, from {train.index.min()} to {train.index.max()}")

    # load the test return data (2024-01-02 till today)

    if refresh_test or not test_path.exists():
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
        test.to_parquet(test_path)
    else:
        test = pd.read_parquet(test_path)
    print(f"Test data shape: {test.shape}, from {test.index.min()} to {test.index.max()}")

    return train, test


def load_corr_matrix():
    """
    This function downloads the correlation matrix from local disk.
    """
    corr_matrix = pd.read_pickle(corr_matrix_path)

    return corr_matrix


def load_embeddings():
    """
    This function downloads the embeddings from s3 and return them as a dataframe, with the cosine similarity.
    TODO: load the embeddings from s3
    """

    corr_matrix = pd.read_pickle(corr_matrix_path)

    return corr_matrix
