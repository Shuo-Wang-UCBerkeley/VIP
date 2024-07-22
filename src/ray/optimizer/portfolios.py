import numpy as np
import pandas as pd

from src.ray.optimizer.strategies import max_sharpe, minimum_variance
from src.server.data_factory import CacheData
from src.server.data_model import Allocations, PortfolioSummary, StockInputs


def portfolio_return(weights, ret):
    portfolio_return = np.dot(ret, weights)  # annualize data; ~250 trading days in a year
    return portfolio_return


def portfolio_culmulative_return(weights, ret):
    """
    This assumes the portfolio is rebalanced at the end of each day, thus the weights are constant
    """
    return ret.dot(weights).add(1).cumprod().subtract(1).multiply(100)


def portfolio_std(weights, ret):
    portfolio_std = np.dot(ret, weights).std() * np.sqrt(250)
    return portfolio_std


def portfolio_sharpe(ret, std):
    return ret / std


def optimize_portfolio(stocks: StockInputs, data: CacheData, coefficients: pd.DataFrame):
    # data extraction from CacheData and StockInputs
    tickers = stocks.get_tickers()
    train = data.train[tickers]
    test = data.test[tickers]
    index = data.test["SPY"]

    # decide the allocation strategy based on the risk tolerance
    if stocks.risk_tolerance == "low":
        weights = minimum_variance(train, stocks.get_bounds(), coeff=coefficients)
    elif stocks.risk_tolerance == "high":
        weights = max_sharpe(train, stocks.get_bounds(), corr=coefficients)
    elif stocks.risk_tolerance == "moderate":
        weight_1 = minimum_variance(train, stocks.get_bounds(), coeff=coefficients)
        weight_2 = max_sharpe(train, stocks.get_bounds(), corr=coefficients)
        # take the average from these two list of weights
        weights = [(w1 + w2) / 2 for w1, w2 in zip(weight_1, weight_2)]

    # use the weights to calculate the portfolio performance
    port_weight_dict = {}
    port_weight_dict["recommendation"] = weights

    summeries = portfolio_performance(port_weight_dict, test, index)
    ticker_weights = {t: w for t, w in zip(tickers, weights)}

    return Allocations(ticker_weights=ticker_weights, summaries=summeries)


def portfolio_performance(port_weight_dict: dict, return_df: pd.DataFrame, index: pd.Series, verbose: bool = False):

    return_list = []

    portfolio_dict = {k: portfolio_return(v, return_df) for k, v in port_weight_dict.items()}
    portfolio_dict["Index"] = index

    for name, ret_series in portfolio_dict.items():

        annulized_return = ret_series.mean() * 250 * 100
        annulized_vol = ret_series.std() * np.sqrt(250) * 100
        total_return = ((ret_series + 1).prod() - 1) * 100

        ps = PortfolioSummary(
            name=name,
            mean_return=annulized_return,
            total_return=total_return,
            volatility=annulized_vol,
            sharpe_ratio=annulized_return / annulized_vol,
        )
        return_list.append(ps)

        if verbose:
            print(f"---------- {name} ----------")
            # print("Weights:", equally_weighted_weights)
            print(
                f"Annualized Return: {annulized_return:.2%}",
            )
            print(f"Volatility: {annulized_vol: .2%}")
            print(f"Sharpe Ratio: {annulized_return / annulized_vol: .2f}")
            print(f"Total Return: {total_return: .2%}")

            print()

    return return_list
