import pickle
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from src.ray.utils.file_utilities import data_dir, s3_download, s3_upload

train_s3_path = "CRSP/crsp_2018-2023_clean_3.parquet"
TRAIN_PATH = data_dir.joinpath(train_s3_path.split("/")[1]).absolute()

cosine_similarity_s3_path = "CRSP/crsp_rachel_results_500.pkl"
TRAINING_OUTPUT_PATH = data_dir.joinpath(cosine_similarity_s3_path.split("/")[1]).absolute()

TRAIN_DF_PATH = data_dir.joinpath("train.parquet").absolute()

# local storage path
APP_DATA_DIR = Path(__file__).joinpath("../server_data").resolve()
TRAIN_DATA_PATH = APP_DATA_DIR.joinpath("train_data.pickle").absolute()
TEST_DF_PATH = APP_DATA_DIR.joinpath("test.parquet").absolute()


@dataclass
class TrainData:
    ticker_list: list[str]

    volatilities: pd.Series
    mean_return: pd.Series

    coeff_dict: dict[str, pd.DataFrame]
    """
    key: name of the coefficient matrix
    """

    # supporting work
    permno_to_tickers: pd.DataFrame


def load_data(refresh_train, refresh_test) -> tuple[TrainData, pd.DataFrame]:

    td = load_train_data(refresh_train)
    test = load_test_data(ticker_list=td.ticker_list, refresh_test=refresh_test)

    if refresh_train:
        test_tickers = test.columns.tolist()
        test_permno = td.permno_to_tickers[td.permno_to_tickers["ticker"].isin(test_tickers)].index.tolist()
        with open("test_permno.txt", "w") as file:
            for item in test_permno:
                file.write(f"{item}\n")

    return td, test


def load_train_data(refresh_train) -> TrainData:
    """
    This function downloads the train data from s3, and live test data from yahoo finance.
    """

    if refresh_train or not TRAIN_DATA_PATH.exists():
        if not APP_DATA_DIR.exists():
            print(f"Creating data directory in {APP_DATA_DIR}...")
            APP_DATA_DIR.mkdir()

        print(f"Downloading training outputs from s3 {train_s3_path}...")
        # s3_download(train_s3_path)
        s3_download(cosine_similarity_s3_path)

        # ml baseline cosine similarity
        results = pd.read_pickle(TRAINING_OUTPUT_PATH)
        permno_list = results["permno_id"]
        # get the mapping from permno_id to ticker
        train_df = pd.read_parquet(TRAIN_PATH)
        train_df = train_df[train_df["permno_id"].isin(permno_list)]
        permno_to_tickers = (
            train_df[["permno_id", "ticker"]].drop_duplicates().drop_duplicates(subset="permno_id")
        )  # keep only 1 ticker per permno_id

        # get the same order of tickers based on permno_list
        tickers = permno_to_tickers.set_index("permno_id").loc[permno_list, "ticker"].tolist()
        ml_baseline_cos = pd.DataFrame(results["cosine"], index=tickers, columns=tickers)
        train_df = train_df[train_df["ticker"].isin(tickers)]

        # calculate the other data based on the filtered permno_list
        train = train_df.pivot(index="date", columns="ticker", values="return")
        if train.isnull().sum().sum() > 0:
            # drop any ticker with incomplete data for the full period
            train = train[train.columns[train.isnull().sum() == 0]]
            ml_baseline_cos = ml_baseline_cos.loc[train.columns, train.columns]

        print(f"Train data shape: {train.shape}, from {train.index.min()} to {train.index.max()}")

        ticker_list = train.columns.tolist()
        mean_return = train.mean(axis=0).reindex()
        volatilities = train.std().reindex()
        corr_matrix = train.corr()
        coeff_dict = {
            "baseline": corr_matrix,
            "ml_baseline": ml_baseline_cos,
        }

        assert ml_baseline_cos.columns.tolist() == ticker_list

        train_data = TrainData(
            ticker_list=ticker_list,
            mean_return=mean_return,
            volatilities=volatilities,
            coeff_dict=coeff_dict,
            permno_to_tickers=permno_to_tickers,
        )

        train.to_parquet(TRAIN_DF_PATH)
        s3_upload("CRSP/train.parquet", TRAIN_DF_PATH)

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

    if refresh_test or not TEST_DF_PATH.exists():
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

        test.to_parquet(TEST_DF_PATH)
        s3_upload("CRSP/test.parquet", TEST_DF_PATH)

    else:
        test = pd.read_parquet(TEST_DF_PATH)

    print(f"Test data shape: {test.shape}, from {test.index.min()} to {test.index.max()}")
    return test
