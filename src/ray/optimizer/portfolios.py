import numpy as np
import pandas as pd

from src.ray.optimizer.strategies import max_sharpe, minimum_variance
from src.server.data_factory import TrainData
from src.server.data_model import Allocations, PortfolioSummary, StockInputs


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


def optimize_portfolio(stocks: StockInputs, train_data: TrainData, coefficients: pd.DataFrame):
    # data extraction from CacheData and StockInputs
    tickers = stocks.get_tickers()
    mean_return = train_data.mean_return[tickers]
    volatilities = train_data.volatilities[tickers]
    coeff = coefficients.loc[tickers, tickers]

    # decide the allocation strategy based on the risk tolerance
    if stocks.risk_tolerance == "low":
        weights = minimum_variance(volatilities, stocks.get_bounds(), coeff=coeff)
    elif stocks.risk_tolerance == "high":
        weights = max_sharpe(mean_return, volatilities, stocks.get_bounds(), corr=coeff)
    elif stocks.risk_tolerance == "moderate":
        weight_1 = minimum_variance(volatilities, stocks.get_bounds(), coeff=coeff)
        weight_2 = max_sharpe(mean_return, volatilities, stocks.get_bounds(), corr=coeff)
        # take the average from these two list of weights
        weights = [(w1 + w2) / 2 for w1, w2 in zip(weight_1, weight_2)]

    ticker_weights = {t: w for t, w in zip(tickers, weights)}

    return ticker_weights


def portfolio_performance(
    ticker_weights: dict, testData: pd.DataFrame, verbose: bool = False
) -> list[PortfolioSummary]:

    # use the weights to calculate the portfolio performance
    tickers = list(ticker_weights.keys())
    weights = np.array(list(ticker_weights.values()))
    test = testData[tickers]
    index = testData["SPY"]

    portfolio_dict = {"index": index, "recommendation": np.dot(test, weights)}

    summaries = []
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
        summaries.append(ps)

        if verbose:
            print(f"---------- {name} ----------")
            # print("Weights:", equally_weighted_weights)
            print(
                f"Annualized Return: {annulized_return:.2f}",
            )
            print(f"Volatility: {annulized_vol:.2f}")
            print(f"Sharpe Ratio: {annulized_return / annulized_vol:.2f}")
            print(f"Total Return: {total_return:.2f}")

            print()
    return summaries
