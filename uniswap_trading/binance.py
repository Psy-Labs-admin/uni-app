import os
import pandas as pd
from datetime import datetime

def add_prices_from_csv(
    vol_df: pd.DataFrame,
    tokens: list[str],
    prices_dir: str = './data'
) -> pd.DataFrame:
    """
    Для каждого токена из tokens подгружает <BASE>_prices.csv из prices_dir
    и мёрджит его по дате в vol_df. Если токен начинается с 'W' (например WBTC),
    то этот префикс отбрасывается при поиске файла, а затем колонка переименовывается
    обратно в {token}_price.
    
    :param vol_df:    DataFrame с колонкой 'date' (str или datetime)
    :param tokens:    список токенов, пример ['BTC', 'WBTC', 'CRV', 'WLDO']
    :param prices_dir: папка, где лежат CSV-файлы <BASE>_prices.csv
    :return:          тот же vol_df + колонки {token}_price
    """
    df = vol_df.copy()
    # нормализуем дату к date
    df['date'] = pd.to_datetime(df['date']).dt.date

    for token in tokens:
        # Если токен начинается на 'W', убираем префикс
        if token.upper().startswith('W') and len(token) > 1:
            base = token[1:].upper()
        else:
            base = token.upper()

        csv_path = os.path.join(prices_dir, f"{base}_prices.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Не найден файл цен для {base}: {csv_path}")

        # читаем исторические цены
        price_df = pd.read_csv(csv_path, parse_dates=['date'])
        price_df['date'] = price_df['date'].dt.date

        # мёржим по дате
        base_col = f"{base}_price"
        df = df.merge(
            price_df[['date', base_col]],
            on='date',
            how='left'
        )

        # если был префикс W — переименуем колонку обратно
        target_col = f"{token}_price"
        if base != token.upper():
            df = df.rename(columns={base_col: target_col})
        # в противном случае оставляем {BASE}_price

    return df
