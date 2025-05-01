import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_yfinance_price_range(
    symbol: str,
    start_date: datetime.date,
    end_date: datetime.date,
    quote_asset: str = 'USD'
) -> pd.DataFrame:
    """
    Fetches daily closing prices for a given asset symbol via yfinance.
    
    :param symbol:        токен, например 'ETH', 'BTC', 'UNI'
    :param quote_asset:   котируемая валюта на Yahoo Finance, по умолчанию 'USD'
    :return:              DataFrame с колонками ['date', '<symbol>_price']
    """
    # поправляем Wrapped-символы на базовые (если нужно)
    sym = symbol.upper()
    if sym.startswith('W') and sym[1:] in ('ETH','BTC'):
        sym = sym[1:]
    
    ticker = f"{sym}-{quote_asset}"
    # yfinance принимает строки '2021-01-01'
    start_str = start_date.isoformat()
    end_str   = end_date.isoformat()
    
    # Забираем данные
    df = yf.download(
        tickers=ticker,
        start=start_str,
        end=(datetime.combine(end_date, datetime.min.time()) + pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
        interval='1d',
        progress=False
    )
    
    # df.index — DatetimeIndex, столбец 'Close' содержит цену закрытия
    df = df[['Close']].reset_index()
    df['date'] = df['Date'].dt.date
    df = df.rename(columns={'Close': f'{symbol}_price'})
    return df[['date', f'{symbol}_price']]

def _flatten_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse any MultiIndex on rows or columns into simple one-level.
    """
    # 1) Flatten a MultiIndex on the row index
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    # 2) Flatten a MultiIndex on the columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns.values]
    return df

def add_prices_flexible(
    vol_df: pd.DataFrame,
    tokens: list[str],
    quote_asset: str = 'USDT'
) -> pd.DataFrame:
    """
    Adds daily price columns for arbitrary tokens onto vol_df['date'].
    Will first collapse any MultiIndex on either DataFrame before merging.
    """
    # 0) make a copy and ensure date is a plain python date
    result = vol_df.copy()
    result['date'] = pd.to_datetime(result['date']).dt.date

    # 1) Flatten vol_df in case it has any MultiIndex
    result = _flatten_df(result)

    start_date, end_date = result['date'].min(), result['date'].max()

    # 2) For each token, fetch its price series and flatten *that* too
    for token in tokens:
        price_df = fetch_yfinance_price_range(token, start_date, end_date)
        price_df = _flatten_df(price_df)

        # 3) Now safe to merge
        result = result.merge(price_df, on='date', how='left')

    return result

