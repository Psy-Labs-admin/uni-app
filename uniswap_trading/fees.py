import requests
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import List, Dict

def add_daily_fees_usd_dynamic(
    vol_df: pd.DataFrame,
    tokens: List[str],
    fee_tier: float,
    price_suffix: str = '_price'
) -> pd.DataFrame:
    """
    Расширённая версия add_daily_fees_usd, где список токенов и названия колонок передаются динамически.
    
    :param vol_df: DataFrame с колонкой 'date' и парами колонок для каждого токена:
                   - <TOKEN>        — объём токена за день
                   - <TOKEN><price_suffix> — цена токена в USD за день
    :param tokens: список символов токенов, например ['WBTC', 'WETH', 'DAI']
    :param fee_tier: комиссия пула (в базе ppm или дробью). Если >1 — считается как ppm (3000 → 0.003).
    :param price_suffix: суффикс для колонки с ценой (по умолчанию '_usd_price')
    :return: копия vol_df с дополнительными колонками:
             - <TOKEN>_usd_volume для каждого токена
             - daily_volume_usd — общий объём в USD
             - fees_usd        — начисленные комиссии в USD
    """
    df = vol_df.copy()
    # нормализуем fee_tier
    fee_rate = fee_tier / 1_000_000 if fee_tier > 1 else fee_tier

    usd_vol_cols = []
    for token in tokens:
        vol_col = token
        price_col = f"{token}{price_suffix}"
        usd_vol_col = f"{token}_usd_volume"
        df[usd_vol_col] = df[vol_col] * df[price_col]
        usd_vol_cols.append(usd_vol_col)

    # общий дневной объём в USD
    df['daily_volume_usd'] = df[usd_vol_cols].sum(axis=1)
    # начисленные комиссии
    df['fees_usd'] = df['daily_volume_usd'] * fee_rate

    return df