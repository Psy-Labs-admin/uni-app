def run_simulation_history(
    prices: list[float],
    eth_prices: list[float],
    btc_prices: list[float],
    strategy,
    initial_eth: float,
    initial_btc: float,
    fees_usd: list[float] | None = None,
    daily_usd_volume: list[float] | None = None
) -> tuple[dict, object, list[float], list[float], list[float]]:
    """
    Запускает пошаговую симуляцию работы стратегии на заданных ценах и (опционально)
    учитывает реальные комиссии пула из исторических данных.

    :param prices:           list[float] — курс ETH/BTC
    :param eth_prices:       list[float] — курс ETH в USD
    :param btc_prices:       list[float] — курс BTC в USD
    :param strategy:         объект стратегии с методами:
                              - compute_range_boundaries(price) -> (low, high)
                              - simulate_step(cur_price, prev_price) -> (status, progress)
                              - compute_rest_zone(center) -> (rest_low, rest_high)
                              и атрибутами eth, btc, ranges, log (список событий)
    :param initial_eth:      float — стартовый объём ETH для HODL
    :param initial_btc:      float — стартовый объём BTC для HODL
    :param fees_usd:         list[float] или None — комиссии пула в USD (исторические)
    :param daily_usd_volume: list[float] или None — общий объём пула в USD (исторические)
    :return: tuple (
               collected: dict — история симуляции,
               strategy: object — стратегия c обновлёнными полями,
               strategy_usd: list[float] — стоимость портфеля со всеми комиссиями,
               hodl_usd: list[float] — стоимость HODL-портфеля,
               cumulative_fees: list[float] — накопленные комиссии по шагам
            )
    """
    # Инициализация диапазона
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

    # Подготовка структур для сбора результатов
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
        "BTC": [],
        "Fees Earned": []
    }
    strategy_usd: list[float] = []
    hodl_usd:     list[float] = []
    cumulative_fees: list[float] = []
    total_accumulated = 0.0

    # Основной цикл симуляции
    for i in range(1, len(prices)):
        # Шаг стратегии
        status, progress = strategy.simulate_step(prices[i], prices[i - 1])

        # Стоимость стратегии и HODL в USD без учета комиссий
        V_strategy = strategy.eth * eth_prices[i] + strategy.btc * btc_prices[i]
        V_hodl     = initial_eth * eth_prices[i]  + initial_btc * btc_prices[i]

        # Начисление комиссий из исторических данных
        fee_earned = 0.0
        if fees_usd is not None and daily_usd_volume is not None:
            total_volume = daily_usd_volume[i]
            if total_volume > 0:
                share = V_strategy / total_volume
                fee_earned = share * fees_usd[i]
                total_accumulated += fee_earned
                V_strategy += fee_earned

        # Сохраняем в списки
        strategy_usd.append(V_strategy)
        hodl_usd.append(V_hodl)
        collected["Time"].append(i)
        collected["Price"].append(prices[i])
        collected["ETH"].append(strategy.eth)
        collected["BTC"].append(strategy.btc)
        collected["Fees Earned"].append(fee_earned)
        cumulative_fees.append(total_accumulated)

        # Первичный диапазон и зона покоя 1
        if len(strategy.ranges) >= 1:
            pr = strategy.ranges[0]
            rest1_low, rest1_high = strategy.compute_rest_zone(pr["center"])
            collected["Primary Range Low"].append(pr["low"])
            collected["Primary Range High"].append(pr["high"])
            collected["Rest Zone Low 1"].append(rest1_low)
            collected["Rest Zone High 1"].append(rest1_high)
        else:
            for key in ["Primary Range Low", "Primary Range High",
                        "Rest Zone Low 1",  "Rest Zone High 1"]:
                collected[key].append(None)

        # Вторичный диапазон и зона покоя 2
        if len(strategy.ranges) >= 2:
            sr = strategy.ranges[1]
            rest2_low, rest2_high = strategy.compute_rest_zone(sr["center"])
            collected["Secondary Range Low"].append(sr["low"])
            collected["Secondary Range High"].append(sr["high"])
            collected["Rest Zone Low 2"].append(rest2_low)
            collected["Rest Zone High 2"].append(rest2_high)
        else:
            for key in ["Secondary Range Low", "Secondary Range High",
                        "Rest Zone Low 2",    "Rest Zone High 2"]:
                collected[key].append(None)

    return collected, strategy, strategy_usd, hodl_usd, cumulative_fees
