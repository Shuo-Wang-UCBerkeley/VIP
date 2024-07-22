import numpy as np
import pandas as pd
from scipy.optimize import minimize

BOUND = (0, 1)


def equal_weight(n):
    return [1 / n] * n


def print_non_zero_weights(tickers, weights):
    for i in range(len(tickers)):
        if abs(weights[i]) > 0.0001:
            print(f"{tickers[i]}: {weights[i]}")


def coeff_to_cov(coeff_matrix, standard_deviations):
    """
    This function converts the correlation/cosine similarity matrix to a covariance matrix.
    """
    coeff_matrix = np.array(coeff_matrix)
    standard_deviations = np.array(standard_deviations)

    # Create a diagonal matrix of standard deviations
    sd_matrix = np.diag(standard_deviations)

    # Calculate the covariance matrix
    covariance_matrix = sd_matrix @ coeff_matrix @ sd_matrix

    return covariance_matrix


def minimum_variance(ret, bounds: list[float] = None, coeff=None):
    def find_port_variance(weights):
        # this is actually std
        cov = ret.cov() if coeff is None else coeff_to_cov(coeff, ret.std())
        port_var = np.sqrt(np.dot(weights.T, np.dot(cov, weights)) * 250)
        return port_var

    def weight_cons(weights):
        return np.sum(weights) - 1

    n = len(ret.columns)
    bounds_to_use = bounds if bounds is not None else [BOUND] * n
    constraint = {"type": "eq", "fun": weight_cons}

    optimal = minimize(
        fun=find_port_variance,
        x0=equal_weight(n),
        bounds=bounds_to_use,
        constraints=constraint,
        method="SLSQP",
    )

    return list(optimal["x"])


def max_sharpe(ret, bounds=None, corr=None):
    def sharpe_func(weights):
        hist_mean = ret.mean(axis=0).to_frame()
        hist_cov = ret.cov() if corr is None else coeff_to_cov(corr, ret.std())

        port_ret = np.dot(weights.T, hist_mean.values) * 250
        port_std = np.sqrt(np.dot(weights.T, np.dot(hist_cov, weights)) * 250)
        return -1 * port_ret / port_std

    def weight_cons(weights):
        return np.sum(weights) - 1

    n = len(ret.columns)
    bounds_to_use = bounds if bounds is not None else [BOUND] * n
    constraint = {"type": "eq", "fun": weight_cons}

    optimal = minimize(
        fun=sharpe_func,
        x0=equal_weight(n),
        bounds=bounds_to_use,
        constraints=constraint,
        method="SLSQP",
    )

    return list(optimal["x"])
