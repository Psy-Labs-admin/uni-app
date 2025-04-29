import pandas as pd
import numpy as np

# Константа для перевода цены в тик (Uniswap логарифмическая шкала)
LOG_BASE = np.log(1.0001)

def price_to_tick(price):
    return int(np.floor(np.log(price) / LOG_BASE))

def tick_to_price(tick):
    return 1.0001 ** tick

def simulate_prices(
    start_price_eth=2000,
    start_price_btc=30000,
    start_price_unk=2000,
    rho=0.7,
    sigma_eth=0.02,
    sigma_btc=0.015,
    sigma_unk=0.03,
    trend_eth=0.0001,
    trend_btc=0.0,
    trend_unk=0.0,
    T=1000,
    seed=None
):
    """
    Симулирует временные ряды цен ETH, BTC и UNK в долларах с возможностью использования Монте-Карло.
    Если seed=None, каждый запуск генерирует разные траектории. Использует логнормальные доходности.

    Параметры:
    - trend_eth/btc/unk: логарифмический тренд доходности (направление движения в среднем)
    - sigma_eth/btc/unk: стандартное отклонение (волатильность)
    - rho: корреляция между ETH и BTC
    - T: количество шагов (например, дней или часов)
    - seed: целое число или None (если None — Монте-Карло)
    """
    if seed is not None:
        np.random.seed(seed)

    mean_returns = [trend_eth, trend_btc]
    cov_matrix = np.array([
        [sigma_eth**2, rho * sigma_eth * sigma_btc],
        [rho * sigma_eth * sigma_btc, sigma_btc**2]
    ])

    log_returns_eth_btc = np.random.multivariate_normal(mean_returns, cov_matrix, size=T)
    log_returns_eth = log_returns_eth_btc[:, 0]
    log_returns_btc = log_returns_eth_btc[:, 1]
    log_returns_unk = np.random.normal(trend_unk, sigma_unk, T)

    prices_eth = start_price_eth * np.exp(np.cumsum(log_returns_eth))
    prices_btc = start_price_btc * np.exp(np.cumsum(log_returns_btc))
    prices_unk = start_price_unk * np.exp(np.cumsum(log_returns_unk))

    eth_btc_ratio = prices_eth / prices_btc
    eth_unk_ratio = prices_eth / prices_unk

    df = pd.DataFrame({
        'ETH': prices_eth,
        'BTC': prices_btc,
        'UNK': prices_unk,
        'ETH/BTC': eth_btc_ratio,
        'ETH/UNK': eth_unk_ratio,
        'tick_ETH': [price_to_tick(p) for p in prices_eth],
        'tick_ETH_BTC': [price_to_tick(p) for p in eth_btc_ratio],
        'tick_ETH_UNK': [price_to_tick(p) for p in eth_unk_ratio]
    })

    return df
