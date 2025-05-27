def run_simulation_history(
    prices: list[float],
    base_prices: list[float],
    quote_prices: list[float],
    strategy,
    initial_base: float,
    initial_quote: float,
    fees_usd: list[float] | None = None,
    daily_usd_volume: list[float] | None = None,
    compound_fees: bool = False
) -> tuple[dict, object, list[float], list[float], list[float]]:
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
        "Quote Amount": [],
        "Fees Earned": []
    }
    strategy_usd: list[float] = []
    hodl_usd: list[float] = []
    cumulative_fees: list[float] = []
    total_accumulated = 0.0

    for i in range(1, len(prices)):
        status, progress = strategy.simulate_step(prices[i], prices[i-1], step=i)

        base_amt = strategy.base_amount
        quote_amt = strategy.quote_amount
        V_base_usd = base_amt * base_prices[i]
        V_quote_usd = quote_amt * quote_prices[i]
        V_before_fee = V_base_usd + V_quote_usd

        fee_earned = 0.0
        if fees_usd and daily_usd_volume:
            vol = daily_usd_volume[i]
            if vol > 0:
                share = V_before_fee / vol
                fee_earned = share * fees_usd[i]
                total_accumulated += fee_earned

        if compound_fees and fee_earned > 0:
            if V_before_fee > 0:
                w_base = V_base_usd / V_before_fee
                w_quote = V_quote_usd / V_before_fee
            else:
                w_base, w_quote = 1.0, 0.0
            added_base = (fee_earned * w_base) / base_prices[i]
            added_quote = (fee_earned * w_quote) / quote_prices[i]
            strategy.base_amount += added_base
            strategy.quote_amount += added_quote
            base_amt = strategy.base_amount
            quote_amt = strategy.quote_amount
            V_base_usd = base_amt * base_prices[i]
            V_quote_usd = quote_amt * quote_prices[i]
            V_strategy = V_base_usd + V_quote_usd
        else:
            V_strategy = V_before_fee + fee_earned

        V_hodl = initial_base * base_prices[i] + initial_quote * quote_prices[i]

        strategy_usd.append(V_strategy)
        hodl_usd.append(V_hodl)
        collected["Time"].append(i)
        collected["Price"].append(prices[i])

        pr = strategy.ranges[0]
        collected["Primary Range Low"].append(pr["low"])
        collected["Primary Range High"].append(pr["high"])
        r1_low, r1_high = strategy.compute_rest_zone(pr["center"])
        collected["Rest Zone Low 1"].append(r1_low)
        collected["Rest Zone High 1"].append(r1_high)

        if len(strategy.ranges) > 1:
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

        collected["Base Amount"].append(base_amt)
        collected["Quote Amount"].append(quote_amt)
        collected["Fees Earned"].append(fee_earned)
        cumulative_fees.append(total_accumulated)
    return collected, strategy, strategy_usd, hodl_usd, cumulative_fees