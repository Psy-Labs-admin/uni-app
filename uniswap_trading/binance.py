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

def add_prices_flexible(
    vol_df: pd.DataFrame,
    tokens: list[str],
    quote_asset: str = 'USDT'
) -> pd.DataFrame:
    # 1) copy and flatten any MultiIndex on rows or columns
    df = vol_df.copy()
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns.values]

    # 2) make sure we have a proper date column
    df['date'] = pd.to_datetime(df['date']).dt.date
    start_date, end_date = df['date'].min(), df['date'].max()

    # 3) merge in each token’s price series
    result = df
    for token in tokens:
        price_df = fetch_yfinance_price_range(token, start_date, end_date)
        # price_df is already a simple 2-column, RangeIndex DF
        result = result.merge(price_df, on='date', how='left')

    return result

