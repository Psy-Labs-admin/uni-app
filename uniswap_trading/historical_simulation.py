import pandas as pd
from strategy import UniswapV4Strategy
from simulation import run_simulation

def simulate_on_historical(
    symbol: str,
    strategy,
    initial_eth: float,
    initial_quote: float,
    start_date: str = None,
    end_date: str = None
):
    """
    Загружает исторические данные по паре ETH–<symbol>, фильтрует по датам и запускает run_simulation.

    :param symbol:       'WBTC', 'CRV' или 'LDO'
    :param strategy:     объект стратегии (с методами compute_range_boundaries, simulate_step, compute_rest_zone и полем log)
    :param initial_eth:  стартовый объём ETH для HODL & стратегии
    :param initial_quote: стартовый объём вторичного актива (WBTC/CRV/LDO) для HODL & стратегии
    :param start_date:   строка 'YYYY-MM-DD' или None
    :param end_date:     строка 'YYYY-MM-DD' или None
    :return: tuple (collected, strategy, strategy_usd, hodl_usd) из run_simulation
    """

    # 1) Карта файла по символу
    file_map = {
        "WBTC": "./data/vol_with_usd_with_fee_eth_btc.csv",
        "CRV":  "./data/vol_with_usd_with_fee_eth_crv.csv",
        "LDO":  "./data/vol_with_usd_with_fee_eth_ldo.csv",
    }
    csv_path = file_map.get(symbol.upper())
    if csv_path is None:
        raise ValueError(f"Unknown symbol «{symbol}», допустимые: {list(file_map)}")

    # 2) Читаем и парсим дату
    df = pd.read_csv(csv_path, parse_dates=["date"])

    # 3) Фильтруем по start/end (если заданы) и сортируем
    if start_date is not None:
        df = df[df["date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        df = df[df["date"] <= pd.to_datetime(end_date)]
    df = df.sort_values("date").reset_index(drop=True)

    # 4) Достаём серии цен:
    #    - курс ETH в USD
    #    - курс вторичного актива в USD
    #    - их отношение ETH/quote
    eth_prices   = df["WETH_price"].tolist()
    quote_prices = df[f"{symbol}_price"].tolist()
    pair_prices  = (df["WETH_price"] / df[f"{symbol}_price"]).tolist()

    # 5) Идём в вашу симуляцию
    return run_simulation(
        prices=pair_prices,
        eth_prices=eth_prices,
        btc_prices=quote_prices,   # здесь вторичный актив «ведёт себя как BTC»
        strategy=strategy,
        initial_eth=initial_eth,
        initial_btc=initial_quote
    )


if __name__ == '__main__':
    initial_eth = 10
    initial_btc = 0.5

    # Инициализация стратегии
    strategy = UniswapV4Strategy(
        epsilon_ticks=100,
        range_ticks=600,
        alpha=0.5,
        lambda_=0.94,
        initial_eth=initial_eth,
        initial_btc=initial_btc
    )
    collected, strategy, strategy_usd, hodl_usd = simulate_on_historical(["WBTC"], strategy, initial_eth, initial_btc, "2023-01-01", "2025-05-01")
    print(strategy_usd, hodl_usd)