import numpy as np
import pandas as pd


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


def portfolio_std_from_covariance(weights, covariance):
    portfolio_std = np.sqrt(np.dot(weights.T, np.dot(covariance, weights)) * 250)
    return portfolio_std


def portfolio_sharpe(ret, std):
    return ret / std


def correlation_to_covariance(correlation_matrix, standard_deviations):
    correlation_matrix = np.array(correlation_matrix)
    standard_deviations = np.array(standard_deviations)

    # Create a diagonal matrix of standard deviations
    sd_matrix = np.diag(standard_deviations)

    # Calculate the covariance matrix
    covariance_matrix = sd_matrix @ correlation_matrix @ sd_matrix

    return covariance_matrix


def portfolio_performance(port_weight_dict: dict, return_df: pd.DataFrame, index: pd.Series, verbose: bool = False):
    return_dict = {k: portfolio_return(v, return_df) for k, v in port_weight_dict.items()}
    return_dict["Index"] = index
    for name, ret in return_dict.items():

        if verbose:
            print(f"---------- {name} ----------")
        # print("Weights:", equally_weighted_weights)
        annulized_return = ret.mean() * 250
        annulized_vol = ret.std() * np.sqrt(250)
        total_return = (ret + 1).prod() - 1

        if verbose:
            print(
                f"Annualized Return: {annulized_return:.2%}",
            )
            print(f"Volatility: {annulized_vol: .2%}")
            print(f"Sharpe Ratio: {annulized_return / annulized_vol: .2f}")
            print(f"Total Return: {total_return: .2%}")

            print()
