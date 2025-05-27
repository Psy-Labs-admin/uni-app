import math

class UniswapV4Strategy:
    def __init__(
        self,
        epsilon_ticks: int = 30,
        range_ticks: int = 300,
        alpha: float = 0.33,
        lambda_: float = 0.9,
        initial_base: float = 1000.0,
        initial_quote: float = 20.0
    ):
        """
        epsilon_ticks – полуширина зоны покоя (в тиках)
        range_ticks   – полуширина основного диапазона (в тиках)
        alpha         – вес нового диапазона при пробое
        lambda_       – коэффициент EWMA волатильности
        initial_base  – стартовый объём базового актива
        initial_quote – стартовый объём вторичного актива
        """
        self.epsilon_ticks = epsilon_ticks
        self.range_ticks = range_ticks
        self.alpha = alpha
        self.lambda_ = lambda_
        self.sigma = 0.02
        # Балансы активов
        self.base_amount = initial_base
        self.quote_amount = initial_quote

        # Две активные позиции (диапазоны)
        self.ranges: list[dict] = []
        self.log: list[dict] = []

    @staticmethod
    def tick_from_price(price: float) -> int:
        return math.floor(math.log(price) / math.log(1.0001))

    @staticmethod
    def price_from_tick(tick: int) -> float:
        return 1.0001 ** tick

    def compute_range_boundaries(self, center_price: float) -> tuple[float, float]:
        ct = self.tick_from_price(center_price)
        return (
            self.price_from_tick(ct - self.range_ticks),
            self.price_from_tick(ct + self.range_ticks)
        )

    def compute_rest_zone(self, center_price: float) -> tuple[float, float]:
        ct = self.tick_from_price(center_price)
        return (
            self.price_from_tick(ct - self.epsilon_ticks),
            self.price_from_tick(ct + self.epsilon_ticks)
        )

    def update_volatility(self, price: float, prev_price: float) -> None:
        r = math.log(price / prev_price)
        self.sigma = math.sqrt(
            self.lambda_ * self.sigma ** 2 + (1 - self.lambda_) * r ** 2
        )

    def rebalance_within_range(self, price: float, price_range: dict) -> float:
        """
        Ребалансирует портфель внутри заданного диапазона, не допуская отрицательных балансов.

        :param price:       текущая цена base/quote
        :param price_range: словарь {"low", "high", "center", "weight"}
        :return:            изменение base_amount (delta)
        """
        pl, ph, pc = price_range["low"], price_range["high"], price_range["center"]
        half = (ph - pl) / 2
        if half <= 0:
            return 0.0

        # интенсивность ребаланса в зависимости от отклонения и волатильности
        D = abs(price - pc) / half
        if self.sigma < 0.02:
            intensity = math.log1p(D)
        elif self.sigma < 0.05:
            intensity = D
        else:
            intensity = D ** 2

        target_weight = 0.5 + 0.5 * intensity if price >= pc else 0.5 - 0.5 * intensity

        # текущая общая стоимость в единицах quote
        total_quote = self.quote_amount + self.base_amount * price
        # желаемый объём base
        desired_base = (target_weight * total_quote) / price
        raw_delta = desired_base - self.base_amount

        # ограничиваем покупку/продажу во избежание отрицательных остатков
        if raw_delta > 0:
            # можем купить не больше, чем хватает quote
            max_buy = self.quote_amount / price
            delta = min(raw_delta, max_buy)
        else:
            # можем продать не больше, чем есть base
            max_sell = self.base_amount
            delta = max(raw_delta, -max_sell)

        # применяем безопасное изменение
        self.base_amount += delta
        self.quote_amount -= delta * price

        return delta


    def get_new_range_from_breakout(self, old_range: dict, direction: str = 'up') -> dict:
        base_tick = self.tick_from_price(
            old_range['high'] if direction == 'up' else old_range['low']
        )
        new_center = self.price_from_tick(
            base_tick + (self.epsilon_ticks if direction == 'up' else -self.epsilon_ticks)
        )
        low, high = self.compute_range_boundaries(new_center)
        return {'low': low, 'high': high, 'center': new_center, 'weight': 1.0}

    def _compute_transition_progress(
        self, price: float, old_range: dict, new_range: dict, direction: str
    ) -> float:
        old_tick = self.tick_from_price(
            old_range['high'] if direction == 'up' else old_range['low']
        )
        price_tick = self.tick_from_price(price)
        prog = (price_tick - old_tick) / self.epsilon_ticks if direction == 'up' else (old_tick - price_tick) / self.epsilon_ticks
        if (direction == 'up' and price > new_range['high']) or (direction == 'down' and price < new_range['low']):
            prog = 1.0
        return max(0.0, min(prog, 1.0))

    def simulate_step(self, price: float, prev_price: float, step: int | None = None) -> tuple[str, any]:
        self.update_volatility(price, prev_price)
        entry = {'time': step, 'price': price}

        if len(self.ranges) == 1:
            cr = self.ranges[0]
            rl, rh = self.compute_rest_zone(cr['center'])
            if rl <= price <= rh:
                event, result = 'rest', None
            else:
                d1 = self.rebalance_within_range(price, cr) if cr['low'] <= price <= cr['high'] else 0.0
                dir = 'up' if price > cr['center'] else 'down'
                nr = self.get_new_range_from_breakout(cr, dir)
                cr['weight'], nr['weight'] = 1 - self.alpha, self.alpha
                eff = {
                    'low': cr['low'] * (1 - self.alpha) + nr['low'] * self.alpha,
                    'high': cr['high'] * (1 - self.alpha) + nr['high'] * self.alpha,
                    'center': cr['center'] * (1 - self.alpha) + nr['center'] * self.alpha
                }
                d2 = self.rebalance_within_range(price, eff)
                self.ranges.append(nr)
                event, result = 'initiate', {'delta_old': d1, 'delta_eff': d2}
        elif len(self.ranges) == 2:
            o, n = self.ranges
            dir = 'up' if price > o['high'] else 'down' if price < o['low'] else None
            prog = self._compute_transition_progress(price, o, n, dir) if dir else n['weight']
            o['weight'], n['weight'] = 1 - prog, prog
            eff = {
                'low': o['low'] * (1 - prog) + n['low'] * prog,
                'high': o['high'] * (1 - prog) + n['high'] * prog,
                'center': o['center'] * (1 - prog) + n['center'] * prog
            }
            d_eff = self.rebalance_within_range(price, eff)
            if dir and prog >= 0.99:
                self.ranges.pop(0)
                if price > n['high'] or price < n['low']:
                    d3 = self.simulate_step(price, prev_price)[1]
                    event, result = 'accelerate', {'delta_eff': d_eff, 'delta_new': d3}
                else:
                    event, result = 'finalize', {'delta_eff': d_eff}
            else:
                event, result = 'update', {'delta_eff': d_eff}
        else:
            center = price
            l, h = self.compute_range_boundaries(center)
            self.ranges = [{'low': l, 'high': h, 'center': center, 'weight': 1.0}]
            event, result = 'init', None

        entry['event'], entry['result'] = event, result
        self.log.append(entry)
        return event, result
