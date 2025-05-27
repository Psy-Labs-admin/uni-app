def run_simulation(
    prices: list[float],
    base_prices: list[float],
    quote_prices: list[float],
    strategy,
    initial_base: float,
    initial_quote: float
) -> tuple[dict, object, list[float], list[float]]:
    """
    Запускает пошаговую симуляцию работы стратегии на заданных ценах.

    :param prices:       list[float] — курс base/quote
    :param base_prices:  list[float] — курс базового актива в USD
    :param quote_prices: list[float] — курс вторичного актива в USD
    :param strategy:     объект стратегии с методами compute_range_boundaries, simulate_step, compute_rest_zone
                         и полями base_amount, quote_amount, ranges, log
    :param initial_base: float — стартовый объём базового актива для HODL
    :param initial_quote: float — стартовый объём вторичного актива для HODL
    :return: tuple (
             collected: dict — история симуляции,
             strategy:   object — стратегия с обновлёнными полями,
             strategy_usd: list[float] — USD-стоимость портфеля стратегии,
             hodl_usd:     list[float] — USD-стоимость HODL-портфеля
        )
    """
    # Инициализация диапазона
    initial_price = prices[0]
    low, high = strategy.compute_range_boundaries(initial_price)
    strategy.ranges = [{"low": low, "high": high, "center": initial_price, "weight": 1.0}]
    strategy.log.append({"event": "init_range", "price": initial_price, "range": strategy.ranges[0]})

    # Подготовка структур
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
        "Base Amount": [],
        "Quote Amount": []
    }
    strategy_usd: list[float] = []
    hodl_usd: list[float] = []

    # Основной цикл симуляции
    for i in range(1, len(prices)):
        status, progress = strategy.simulate_step(prices[i], prices[i-1], step=i)

        # USD-стоимость стратегии и HODL
        V_strategy = strategy.base_amount * base_prices[i] + strategy.quote_amount * quote_prices[i]
        V_hodl     = initial_base * base_prices[i]  + initial_quote * quote_prices[i]

        strategy_usd.append(V_strategy)
        hodl_usd.append(V_hodl)

        # Сохранение данных
        collected["Time"].append(i)
        collected["Price"].append(prices[i])

        # Первичный диапазон и зона покоя 1
        pr = strategy.ranges[0]
        collected["Primary Range Low"].append(pr["low"])
        collected["Primary Range High"].append(pr["high"])
        r1_low, r1_high = strategy.compute_rest_zone(pr["center"])
        collected["Rest Zone Low 1"].append(r1_low)
        collected["Rest Zone High 1"].append(r1_high)

        # Вторичный диапазон и зона покоя 2
        if len(strategy.ranges) >= 2:
            sr = strategy.ranges[1]
            collected["Secondary Range Low"].append(sr["low"])
            collected["Secondary Range High"].append(sr["high"])
            r2_low, r2_high = strategy.compute_rest_zone(sr["center"])
            collected["Rest Zone Low 2"].append(r2_low)
            collected["Rest Zone High 2"].append(r2_high)
        else:
            collected["Secondary Range Low"].append(None)
            collected["Secondary Range High"].append(None)
            collected["Rest Zone Low 2"].append(None)
            collected["Rest Zone High 2"].append(None)

        # Балансы активов
        collected["Base Amount"].append(strategy.base_amount)
        collected["Quote Amount"].append(strategy.quote_amount)

    return collected, strategy, strategy_usd, hodl_usd
