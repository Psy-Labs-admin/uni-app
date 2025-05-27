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
        range_ticks   – полуширина полного диапазона (в тиках)
        alpha         – базовый параметр для EWMA, но здесь не используется напрямую
        lambda_       – коэффициент EWMA волатильности
        initial_base  – стартовый объём базового актива
        initial_quote – стартовый объём вторичного актива
        """
        self.epsilon_ticks = epsilon_ticks
        self.range_ticks = range_ticks
        self.lambda_ = lambda_
        self.sigma = 0.02
        self.base_amount = initial_base
        self.quote_amount = initial_quote

        # Список текущих диапазонов (до двух активных)
        self.ranges: list[dict] = []
        # Лог действий
        self.log: list[dict] = []

    @staticmethod
    def tick_from_price(price: float) -> int:
        return math.floor(math.log(price) / math.log(1.0001))

    @staticmethod
    def price_from_tick(tick: int) -> float:
        return 1.0001 ** tick

    def compute_range_boundaries(self, center: float) -> tuple[float, float]:
        ct = self.tick_from_price(center)
        return (
            self.price_from_tick(ct - self.range_ticks),
            self.price_from_tick(ct + self.range_ticks)
        )

    def compute_rest_zone(self, center: float) -> tuple[float, float]:
        ct = self.tick_from_price(center)
        return (
            self.price_from_tick(ct - self.epsilon_ticks),
            self.price_from_tick(ct + self.epsilon_ticks)
        )

    def update_volatility(self, price: float, prev_price: float) -> None:
        r = math.log(price / prev_price)
        self.sigma = math.sqrt(
            self.lambda_ * self.sigma**2 + (1 - self.lambda_) * r**2
        )

    def rebalance_delta(self, delta_base: float, price: float) -> None:
        """
        Применяет частичный ребаланс: delta_base базового актива,
        обновляет base_amount и quote_amount безопасно.
        """
        # Ограничение по текущим остаткам
        if delta_base > 0:
            max_buy = self.quote_amount / price
            delta_base = min(delta_base, max_buy)
        else:
            max_sell = self.base_amount
            delta_base = max(delta_base, -max_sell)

        self.base_amount += delta_base
        self.quote_amount -= delta_base * price
        return delta_base

    def simulate_step(self, price: float, prev_price: float, step: int | None = None) -> tuple[str, dict]:
        # Обновление волатильности и лог
        self.update_volatility(price, prev_price)
        entry = {"time": step, "price": price}

        # Если нет диапазонов — init
        if len(self.ranges) == 0:
            low, high = self.compute_range_boundaries(price)
            self.ranges = [{"low": low, "high": high, "center": price, "weight": 1.0}]
            event, result = "init_range", {}

        # Один диапазон: проверяем rest-zone или пробой
        elif len(self.ranges) == 1:
            cr = self.ranges[0]
            rl, rh = self.compute_rest_zone(cr["center"])
            if rl <= price <= rh:
                event, result = "in_rest_zone", {}
            else:
                # Пробой — создаём второй диапазон сразу
                direction = "up" if price > cr["center"] else "down"
                nr = self._create_new_range(cr, direction)
                # Изначально weight нового = 0, старого = 1, будем постепенно переносить
                cr["weight"], nr["weight"] = 1.0, 0.0
                self.ranges.append(nr)
                event, result = "start_transition", {"direction": direction}

        # Два диапазона: плавный или ускоренный переход
        else:
            old_r, new_r = self.ranges
            rl, rh = self.compute_rest_zone(old_r["center"])
            # Определяем направление
            if price > old_r["high"]:
                direction = "up"
            elif price < old_r["low"]:
                direction = "down"
            else:
                direction = None

            # Считаем новый вес new_r
            if direction:
                prog = self._compute_progress(price, old_r, new_r, direction)
            else:
                prog = new_r["weight"]

            # Ограничим прогресс в [0,1]
            prog = max(0.0, min(prog, 1.0))
            old_weight, new_weight = 1 - prog, prog

            # Рассчитываем изменение веса за шаг
            weight_delta = new_weight - new_r["weight"]
            old_r["weight"], new_r["weight"] = old_weight, new_weight

            # Эффективный диапазон для full_delta
            eff = {
                "low":   old_r["low"]   * old_weight + new_r["low"]   * new_weight,
                "high":  old_r["high"]  * old_weight + new_r["high"]  * new_weight,
                "center":old_r["center"]* old_weight + new_r["center"]* new_weight
            }

            # full delta: сколько базового надо сменить для полного ребаланса
            full_delta = self._full_delta(price, eff)
            # части ребаланса пропорционально weight_delta
            delta_base = full_delta * (weight_delta / new_weight) if new_weight > 0 else 0.0

            applied = self.rebalance_delta(delta_base, price)
            result = {"delta_base": applied, "new_weight": new_weight}

            # Если перешли за 99%, финализируем
            if direction and prog >= 0.99:
                # Удаляем старый диапазон
                self.ranges.pop(0)
                event = "finalize_transition"
            else:
                event = "update_transition"

        entry["event"], entry["result"] = event, result
        self.log.append(entry)
        return event, result

    def _create_new_range(self, old_range: dict, direction: str) -> dict:
        # Вытягиваем границу и создаём range
        boundary = old_range["high"] if direction == "up" else old_range["low"]
        tick = self.tick_from_price(boundary)
        center = self.price_from_tick(tick + (self.epsilon_ticks if direction == "up" else -self.epsilon_ticks))
        low, high = self.compute_range_boundaries(center)
        return {"low": low, "high": high, "center": center, "weight": 0.0}

    def _compute_progress(self, price: float, old_r: dict, new_r: dict, direction: str) -> float:
        # Доля пути от границы old_r до границы new_r
        old_tick = self.tick_from_price(old_r["high"] if direction == "up" else old_r["low"])
        price_tick = self.tick_from_price(price)
        raw = (price_tick - old_tick) / self.epsilon_ticks if direction == "up" else (old_tick - price_tick) / self.epsilon_ticks
        return raw

    def _full_delta(self, price: float, eff_range: dict) -> float:
        # Полное ребалансирование: сколько base нужно поменять для eff_range
        pl, ph, pc = eff_range["low"], eff_range["high"], eff_range["center"]
        half = (ph - pl) / 2
        if half <= 0:
            return 0.0
        D = abs(price - pc) / half
        # интенсивность ребаланса
        if self.sigma < 0.02:
            intensity = math.log1p(D)
        elif self.sigma < 0.05:
            intensity = D
        else:
            intensity = D**2
        target_w = 0.5 + 0.5 * intensity if price >= pc else 0.5 - 0.5 * intensity
        total_quote = self.quote_amount + self.base_amount * price
        desired_base = (target_w * total_quote) / price
        return desired_base - self.base_amount


# import math


# class UniswapV4Strategy:
#     def __init__(
#         self,
#         epsilon_ticks: int = 30,
#         range_ticks: int = 300,
#         alpha: float = 0.33,
#         lambda_: float = 0.9,
#         initial_base: float = 1000.0,
#         initial_quote: float = 20.0
#     ):
#         """
#         epsilon_ticks – полуширина зоны покоя (в тиках)
#         range_ticks   – полуширина основного диапазона (в тиках)
#         alpha         – доля ликвидности, переводимая в новый диапазон при пробое
#         lambda_       – коэффициент EWMA волатильности
#         initial_base  – стартовый объём базового актива
#         initial_quote – стартовый объём вторичного актива
#         """
#         self.epsilon_ticks = epsilon_ticks
#         self.range_ticks = range_ticks
#         self.alpha = alpha
#         self.lambda_ = lambda_
#         self.sigma = 0.02
#         # Балансы активов
#         self.base_amount = initial_base
#         self.quote_amount = initial_quote

#         # Храним до двух активных диапазонов
#         self.ranges: list[dict] = []
#         # Лог событий
#         self.log: list[dict] = []

#     @staticmethod
#     def tick_from_price(price: float) -> int:
#         return math.floor(math.log(price) / math.log(1.0001))

#     @staticmethod
#     def price_from_tick(tick: int) -> float:
#         return 1.0001 ** tick

#     def compute_range_boundaries(self, center_price: float) -> tuple[float, float]:
#         # Диапазон ± range_ticks тиков вокруг центра
#         ct = self.tick_from_price(center_price)
#         return (
#             self.price_from_tick(ct - self.range_ticks),
#             self.price_from_tick(ct + self.range_ticks)
#         )

#     def compute_rest_zone(self, center_price: float) -> tuple[float, float]:
#         # Зона покоя ± epsilon_ticks тиков
#         ct = self.tick_from_price(center_price)
#         return (
#             self.price_from_tick(ct - self.epsilon_ticks),
#             self.price_from_tick(ct + self.epsilon_ticks)
#         )

#     def update_volatility(self, price: float, prev_price: float) -> None:
#         # EWMA волатильности по лог-доходности
#         r = math.log(price / prev_price)
#         self.sigma = math.sqrt(
#             self.lambda_ * self.sigma**2 + (1 - self.lambda_) * r**2
#         )

#     def rebalance_within_range(self, price: float, price_range: dict) -> float:
#         """
#         Безопасный ребаланс внутри диапазона: не допускает отрицательных остатков.
#         Возвращает delta базового актива.
#         """
#         pl, ph, pc = price_range['low'], price_range['high'], price_range['center']
#         half = (ph - pl) / 2
#         if half <= 0:
#             return 0.0

#         D = abs(price - pc) / half
#         if self.sigma < 0.02:
#             intensity = math.log1p(D)
#         elif self.sigma < 0.05:
#             intensity = D
#         else:
#             intensity = D**2

#         target_weight = 0.5 + 0.5 * intensity if price >= pc else 0.5 - 0.5 * intensity
#         total_quote = self.quote_amount + self.base_amount * price
#         desired_base = (target_weight * total_quote) / price
#         raw_delta = desired_base - self.base_amount

#         # Клинг delta
#         if raw_delta > 0:
#             max_buy = self.quote_amount / price
#             delta = min(raw_delta, max_buy)
#         else:
#             max_sell = self.base_amount
#             delta = max(raw_delta, -max_sell)

#         self.base_amount += delta
#         self.quote_amount -= delta * price
#         return delta

#     def get_new_range_from_breakout(self, old_range: dict, direction: str = 'up') -> dict:
#         # Новый центр за epsilon_ticks за границей old_range
#         boundary = old_range['high'] if direction == 'up' else old_range['low']
#         tick = self.tick_from_price(boundary)
#         new_center = self.price_from_tick(
#             tick + (self.epsilon_ticks if direction == 'up' else -self.epsilon_ticks)
#         )
#         low, high = self.compute_range_boundaries(new_center)
#         return {'low': low, 'high': high, 'center': new_center, 'weight': 1.0}

#     def _compute_transition_progress(
#         self, price: float, old_range: dict, new_range: dict, direction: str
#     ) -> float:
#         # Прогресс перехода между old и new
#         old_tick = self.tick_from_price(
#             old_range['high'] if direction == 'up' else old_range['low']
#         )
#         pt_tick = self.tick_from_price(price)
#         prog = ((pt_tick - old_tick) / self.epsilon_ticks
#                 if direction == 'up' else
#                 (old_tick - pt_tick) / self.epsilon_ticks)
#         if (direction == 'up' and price > new_range['high']) or (direction == 'down' and price < new_range['low']):
#             prog = 1.0
#         return max(0.0, min(prog, 1.0))

#     def simulate_step(
#         self, price: float, prev_price: float, step: int | None = None
#     ) -> tuple[str, dict]:
#         # Обновляем волатильность и логируем шаг
#         self.update_volatility(price, prev_price)
#         entry = {'time': step, 'price': price}

#         if len(self.ranges) == 1:
#             cr = self.ranges[0]
#             rl, rh = self.compute_rest_zone(cr['center'])
#             if rl <= price <= rh:
#                 event, result = 'rest', {}
#             else:
#                 d1 = self.rebalance_within_range(price, cr) if cr['low'] <= price <= cr['high'] else 0.0
#                 direction = 'up' if price > cr['center'] else 'down'
#                 nr = self.get_new_range_from_breakout(cr, direction)
#                 cr['weight'], nr['weight'] = 1 - self.alpha, self.alpha
#                 eff = {
#                     'low':  cr['low'] * (1 - self.alpha) + nr['low'] * self.alpha,
#                     'high': cr['high'] * (1 - self.alpha) + nr['high'] * self.alpha,
#                     'center': cr['center'] * (1 - self.alpha) + nr['center'] * self.alpha
#                 }
#                 d2 = self.rebalance_within_range(price, eff)
#                 self.ranges.append(nr)
#                 event, result = 'initiate', {'delta_old': d1, 'delta_eff': d2}

#         elif len(self.ranges) == 2:
#             old, new = self.ranges
#             direction = ('up' if price > old['high'] else
#                          'down' if price < old['low'] else None)
#             prog = (self._compute_transition_progress(price, old, new, direction)
#                     if direction else new['weight'])
#             old['weight'], new['weight'] = 1-prog, prog
#             eff = {
#                 'low':  old['low'] * (1-prog) + new['low'] * prog,
#                 'high': old['high'] * (1-prog) + new['high'] * prog,
#                 'center': old['center'] * (1-prog) + new['center'] * prog
#             }
#             d_eff = self.rebalance_within_range(price, eff)
#             if direction and prog >= 0.99:
#                 self.ranges.pop(0)
#                 if price > new['high'] or price < new['low']:
#                     nr = self.get_new_range_from_breakout(new, direction)
#                     new['weight'], nr['weight'] = 1-self.alpha, self.alpha
#                     d_new = self.rebalance_within_range(price, {
#                         'low':  new['low'] * (1-self.alpha) + nr['low'] * self.alpha,
#                         'high': new['high'] * (1-self.alpha) + nr['high'] * self.alpha,
#                         'center': new['center'] * (1-self.alpha) + nr['center'] * self.alpha
#                     })
#                     self.ranges.append(nr)
#                     event, result = 'accelerated', {'delta_eff': d_eff, 'delta_third': d_new}
#                 else:
#                     event, result = 'finalize', {'delta_eff': d_eff}
#             else:
#                 event, result = 'update', {'delta_eff': d_eff}

#         else:
#             low, high = self.compute_range_boundaries(price)
#             self.ranges = [{'low': low, 'high': high, 'center': price, 'weight':1.0}]
#             event, result = 'init', {}

#         entry['event'], entry['result'] = event, result
#         self.log.append(entry)
#         return event, result
