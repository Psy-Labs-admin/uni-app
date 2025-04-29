import math

class UniswapV4Strategy:
    def __init__(self, epsilon_ticks=30, range_ticks=300, alpha=0.33, lambda_=0.9,
                 initial_eth=1000.0, initial_btc=20.0):
        """
        epsilon_ticks – половина ширины зоны покоя (в тиках)
        range_ticks   – половина ширины полного диапазона (в тиках)
        alpha         – доля ликвидности, переводимая в новый диапазон при переходе
        lambda_       – параметр сглаживания EWMA-волатильности
        """
        self.epsilon_ticks = epsilon_ticks
        self.range_ticks = range_ticks
        self.alpha = alpha
        self.lambda_ = lambda_
        self.sigma = 0.02
        self.eth = initial_eth
        self.btc = initial_btc

        # Будем держать в памяти открытыми максимум два диапазона.
        # Когда создаётся третий, самый старый сразу закрывается.
        self.ranges = []
        self.log = []

    # ------- Вспомогательные функции по работе с тиками -------
    @staticmethod
    def tick_from_price(price):
        return math.floor(math.log(price) / math.log(1.0001))

    @staticmethod
    def price_from_tick(tick):
        return 1.0001 ** tick

    # ------- Расчёт границ диапазона и зоны покоя -------
    def compute_range_boundaries(self, center_price):
        """
        Полный диапазон определяется как диапазон ±range_ticks от центра.
        """
        center_tick = self.tick_from_price(center_price)
        low_tick = center_tick - self.range_ticks
        high_tick = center_tick + self.range_ticks
        return (self.price_from_tick(low_tick),
                self.price_from_tick(high_tick))

    def compute_rest_zone(self, center_price):
        """
        Зона покоя определяется как диапазон ±epsilon_ticks от центра.
        """
        center_tick = self.tick_from_price(center_price)
        rest_low_tick = center_tick - self.epsilon_ticks
        rest_high_tick = center_tick + self.epsilon_ticks
        return (self.price_from_tick(rest_low_tick),
                self.price_from_tick(rest_high_tick))

    # ------- Обновление волатильности -------
    def update_volatility(self, pt, pt_prev):
        """
        EWMA по лог-доходности:
          σ²_t = λ * σ²_(t-1) + (1-λ) * (log(pt/pt_prev))²
        """
        r_t = math.log(pt / pt_prev)
        self.sigma = math.sqrt(self.lambda_ * self.sigma**2 + (1 - self.lambda_) * r_t**2)

    # ------- Ребалансировка внутри диапазона -------
    def rebalance_within_range(self, pt, current_range):
        """
        Если цена находится внутри полного диапазона, но вне его зоны покоя,
        выполняется ребалансировка ликвидности.
        
        1) Вычисляем относительное отклонение D.
        2) В зависимости от текущей волатильности выбираем силу ребалансировки.
        3) Рассчитываем целевую долю ETH и изменяем портфель.
        
        Возвращает величину изменения в ETH.
        """
        Plow, Phigh = current_range["low"], current_range["high"]
        Pcenter = current_range["center"]
        half_width = (Phigh - Plow) / 2
        if half_width <= 0:
            return 0.0
        D = abs(pt - Pcenter) / half_width
        if self.sigma < 0.02:
            freb = math.log(1 + D)
        elif self.sigma < 0.05:
            freb = D
        else:
            freb = D**2
        if pt >= Pcenter:
            w_target = 0.5 + 0.5 * freb
        else:
            w_target = 0.5 - 0.5 * freb
        # Общая стоимость портфеля в BTC-единицах (ETH оцениваются по pt)
        V_btc = self.btc + self.eth * pt
        target_eth = (w_target * V_btc) / pt
        delta_B = target_eth - self.eth
        # Перераспределяем активы
        self.eth += delta_B
        self.btc -= delta_B * pt
        return delta_B

    # ------- Создание нового диапазона при пробое -------
    def get_new_range_from_breakout(self, old_range, direction='up'):
        """
        При пробое создаём новый диапазон.
          - Если direction == 'up': новый центр = tick(old_range["high"]) + epsilon_ticks
          - Если direction == 'down': новый центр = tick(old_range["low"]) - epsilon_ticks
          
        Возвращаем словарь с границами, центром и весом (ликвидностью).
        """
        if direction == 'up':
            base_price = old_range["high"]
            base_tick = self.tick_from_price(base_price)
            new_center_tick = base_tick + self.epsilon_ticks
        else:
            base_price = old_range["low"]
            base_tick = self.tick_from_price(base_price)
            new_center_tick = base_tick - self.epsilon_ticks
        new_center = self.price_from_tick(new_center_tick)
        low, high = self.compute_range_boundaries(new_center)
        return {
            "low": low,
            "high": high,
            "center": new_center,
            "weight": 1.0   # Новый диапазон начинает с полной ликвидностью (потом корректируется)
        }

    def _compute_transition_progress(self, pt, old_range, new_range, direction):
        """
        Вычисляем progress перехода как отношение (расстояние от границы old_range до pt) / epsilon_ticks.
        Если при движении вверх pt > new_range["high"] или при движении вниз pt < new_range["low"],
        форсируем progress = 1.
        """
        if direction == 'up':
            old_high_tick = self.tick_from_price(old_range["high"])
            pt_tick = self.tick_from_price(pt)
            progress = (pt_tick - old_high_tick) / self.epsilon_ticks
            if pt > new_range["high"]:
                progress = 1.0
        else:
            old_low_tick = self.tick_from_price(old_range["low"])
            pt_tick = self.tick_from_price(pt)
            progress = (old_low_tick - pt_tick) / self.epsilon_ticks
            if pt < new_range["low"]:
                progress = 1.0
        return min(max(progress, 0.0), 1.0)

    # ------- Основная функция simulate_step -------
    def simulate_step(self, pt, pt_prev, step=None):
        self.update_volatility(pt, pt_prev)
        log_entry = {"time": step, "price": pt}
        event = None
        result = None
    
        # ——— Один диапазон ———
        if len(self.ranges) == 1:
            cr = self.ranges[0]
            rest_low, rest_high = self.compute_rest_zone(cr["center"])
    
            if rest_low <= pt <= rest_high:
                event, result = "in_rest_zone", 0.0
            else:
                # 1) обычный ребаланс внутри старого диапазона (если внутри полного)
                delta1 = 0.0
                if cr["low"] <= pt <= cr["high"]:
                    delta1 = self.rebalance_within_range(pt, cr)
    
                # 2) создаём второй диапазон, распределяем веса
                direction = 'up' if pt > cr["center"] else 'down'
                nr = self.get_new_range_from_breakout(cr, direction)
                cr["weight"], nr["weight"] = 1 - self.alpha, self.alpha
    
                # 3) делаем ребаланс «эффективного» диапазона (между cr и nr)
                eff_center = cr["center"]*(1-self.alpha) + nr["center"]*self.alpha
                eff_low    = cr["low"]   *(1-self.alpha) + nr["low"]   *self.alpha
                eff_high   = cr["high"]  *(1-self.alpha) + nr["high"]  *self.alpha
                eff_range = {"center": eff_center, "low": eff_low, "high": eff_high}
                delta2 = self.rebalance_within_range(pt, eff_range)
    
                # 4) сохраняем оба диапазона
                self.ranges.append(nr)
                event = "initiate_transition"
                result = {"delta_old": delta1, "delta_eff": delta2, "alpha": self.alpha}
    
        # ——— Переход (два диапазона) ———
        elif len(self.ranges) == 2:
            old_r, new_r = self.ranges
            # направление относительно старого диапазона
            if pt > old_r["high"]:
                dir0 = 'up'
            elif pt < old_r["low"]:
                dir0 = 'down'
            else:
                dir0 = None
    
            # считаем progress если есть направление
            if dir0:
                progress = self._compute_transition_progress(pt, old_r, new_r, dir0)
                old_r["weight"], new_r["weight"] = 1-progress, progress
            else:
                progress = new_r["weight"]
    
            # вычисляем эффективный диапазон
            eff_center = old_r["center"]*(1-progress) + new_r["center"]*progress
            eff_low    = old_r["low"]   *(1-progress) + new_r["low"]   *progress
            eff_high   = old_r["high"]  *(1-progress) + new_r["high"]  *progress
            eff_range  = {"center": eff_center, "low": eff_low, "high": eff_high}
    
            # 1) всегда ребалансим по effective
            delta_eff = self.rebalance_within_range(pt, eff_range)
    
            # 2) если вошли в финал перехода
            if dir0 and progress >= 0.99:
                removed = self.ranges.pop(0)
                # а) ускоренный переход: если сразу новый пробой за new_r
                if pt > new_r["high"] or pt < new_r["low"]:
                    d2 = 'up' if pt > new_r["high"] else 'down'
                    r3 = self.get_new_range_from_breakout(new_r, d2)
                    new_r["weight"], r3["weight"] = 1-self.alpha, self.alpha
                    # ребаланс третьего диапазона
                    eff2_center = new_r["center"]*(1-self.alpha) + r3["center"]*self.alpha
                    eff2_low    = new_r["low"]   *(1-self.alpha) + r3["low"]   *self.alpha
                    eff2_high   = new_r["high"]  *(1-self.alpha) + r3["high"]  *self.alpha
                    eff2_range = {"center": eff2_center, "low": eff2_low, "high": eff2_high}
                    delta3 = self.rebalance_within_range(pt, eff2_range)
    
                    self.ranges.append(r3)
                    event = "accelerated_transition"
                    result = {"delta_eff": delta_eff, "delta_third": delta3}
                else:
                    event = "finalize_transition"
                    result = {"progress": progress, "delta_eff": delta_eff}
            else:
                # просто обновляем прогресс
                event = "update_transition"
                result = {"progress": progress, "delta_eff": delta_eff}
    
        # ——— Ни одного диапазона ———
        else:
            # инициализируем первый
            center = pt
            low, high = self.compute_range_boundaries(center)
            self.ranges = [{"low":low, "high":high, "center":center, "weight":1.0}]
            event, result = "init_range", None
    
        log_entry["event"] = event
        log_entry["result"] = result
        self.log.append(log_entry)
        return event, result
