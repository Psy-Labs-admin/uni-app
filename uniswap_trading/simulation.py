def run_simulation(prices, eth_prices, btc_prices, strategy, initial_eth, initial_btc):
    """
    Запускает пошаговую симуляцию работы стратегии на заданных ценах.

    :param prices:       list[float] — курс ETH/BTC
    :param eth_prices:   list[float] — курс ETH в USD
    :param btc_prices:   list[float] — курс BTC в USD
    :param strategy:     объект стратегии с методами:
                         - compute_range_boundaries(price) -> (low, high)
                         - simulate_step(cur_price, prev_price) -> (status, progress)
                         - compute_rest_zone(center) -> (rest_low, rest_high)
                         и атрибутами eth, btc, ranges, log (список событий)
    :param initial_eth:  float — стартовый объём ETH для HODL
    :param initial_btc:  float — стартовый объём BTC для HODL
    :return: tuple (collected, strategy, strategy_usd, hodl_usd)
             collected     — dict со списками истории симуляции
             strategy      — тот же объект стратегии (с обновлёнными полями)
             strategy_usd  — list стоимости портфеля стратегии в USD на каждом шаге
             hodl_usd      — list стоимости HODL‑портфеля в USD на каждом шаге
    """
    # инициализация диапазона
    initial_price = prices[0]
    low, high = strategy.compute_range_boundaries(initial_price)
    strategy.ranges = [{
        "low": low,
        "high": high,
        "center": initial_price,
        "weight": 1.0
    }]
    strategy.log.append({
        "event": "init_range",
        "price": initial_price,
        "range": strategy.ranges[0]
    })

    # подготовка структур
    collected = {
        "Time": [],
        "Price": [],
        "Primary Range Low": [],
        "Primary Range High": [],
        "Secondary Range Low": [],
        "Secondary Range High": [],
        "Rest Zone Low 1": [],
        "Rest Zone High 1": [],
        "Rest Zone Low 2": [],
        "Rest Zone High 2": [],
        "ETH": [],
        "BTC": []
    }
    strategy_usd = []
    hodl_usd = []

    # основной цикл
    for i in range(1, len(prices)):
        status, progress = strategy.simulate_step(prices[i], prices[i - 1])

        # стоимость стратегии и HODL в USD
        V_strategy = strategy.eth * eth_prices[i] + strategy.btc * btc_prices[i]
        V_hodl     = initial_eth * eth_prices[i]  + initial_btc * btc_prices[i]

        strategy_usd.append(V_strategy)
        hodl_usd.append(V_hodl)

        # записываем базовые величины
        collected["Time"].append(i)
        collected["Price"].append(prices[i])
        collected["ETH"].append(strategy.eth)
        collected["BTC"].append(strategy.btc)

        # первичный диапазон + зона покоя 1
        if len(strategy.ranges) >= 1:
            pr = strategy.ranges[0]
            rest1_low, rest1_high = strategy.compute_rest_zone(pr["center"])
            collected["Primary Range Low"].append(pr["low"])
            collected["Primary Range High"].append(pr["high"])
            collected["Rest Zone Low 1"].append(rest1_low)
            collected["Rest Zone High 1"].append(rest1_high)
        else:
            for key in ["Primary Range Low","Primary Range High",
                        "Rest Zone Low 1","Rest Zone High 1"]:
                collected[key].append(None)

        # вторичный диапазон + зона покоя 2
        if len(strategy.ranges) >= 2:
            sr = strategy.ranges[1]
            rest2_low, rest2_high = strategy.compute_rest_zone(sr["center"])
            collected["Secondary Range Low"].append(sr["low"])
            collected["Secondary Range High"].append(sr["high"])
            collected["Rest Zone Low 2"].append(rest2_low)
            collected["Rest Zone High 2"].append(rest2_high)
        else:
            for key in ["Secondary Range Low","Secondary Range High",
                        "Rest Zone Low 2","Rest Zone High 2"]:
                collected[key].append(None)

    return collected, strategy, strategy_usd, hodl_usd
