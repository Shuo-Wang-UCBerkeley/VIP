import numpy as np
import pandas as pd
from scipy.optimize import minimize

BOUND = (0, 1)  # bounds, change to (-1, 1) if shorting is allowed


def equal_weight(n):
    return [1 / n] * n


def print_non_zero_weights(tickers, weights):
    for i in range(len(tickers)):
        if abs(weights[i]) > 0.0001:
            print(f"{tickers[i]}: {weights[i]}")


def minimum_variance(ret):
    def find_port_variance(weights):
        # this is actually std
        cov = ret.cov()
        port_var = np.sqrt(np.dot(weights.T, np.dot(cov, weights)) * 250)
        return port_var

    def weight_cons(weights):
        return np.sum(weights) - 1

    n = len(ret.columns)
    bounds_lim = [BOUND] * n
    constraint = {"type": "eq", "fun": weight_cons}

    optimal = minimize(
        fun=find_port_variance,
        x0=equal_weight(n),
        bounds=bounds_lim,
        constraints=constraint,
        method="SLSQP",
    )

    return list(optimal["x"])


def max_sharpe(ret):
    def sharpe_func(weights):
        hist_mean = ret.mean(axis=0).to_frame()
        hist_cov = ret.cov()

        port_ret = np.dot(weights.T, hist_mean.values) * 250
        port_std = np.sqrt(np.dot(weights.T, np.dot(hist_cov, weights)) * 250)
        return -1 * port_ret / port_std

    def weight_cons(weights):
        return np.sum(weights) - 1

    n = len(ret.columns)
    bounds_lim = [BOUND] * n  # change to (-1, 1) if you want to short
    constraint = {"type": "eq", "fun": weight_cons}

    optimal = minimize(
        fun=sharpe_func,
        x0=equal_weight(n),
        bounds=bounds_lim,
        constraints=constraint,
        method="SLSQP",
    )

    return list(optimal["x"])
