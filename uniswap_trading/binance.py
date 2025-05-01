import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# def normalize_yf_df(df: pd.DataFrame, asset_id: str) -> pd.DataFrame:
#     """
#     Take a raw yfinance DataFrame (single- or multi-ticker) and
#     return one with:
#       - a column named 'datetime' (tz-naive)
#       - a column named '{asset_id}_price'
#     """
#     # 1) Flatten MultiIndex columns, if present
#     if isinstance(df.columns, pd.MultiIndex):
#         df.columns = ['_'.join(map(str, col)).strip() for col in df.columns.values]

#     # 2) Ensure the index is brought into a column if there's no Date/Datetime column
#     if not any(col in df.columns for col in ('Date', 'Datetime')):
#         df = df.reset_index()

#     # 3) Build our rename mapping
#     rename_map = {}
#     if 'Date'     in df.columns: rename_map['Date']     = 'datetime'
#     if 'Datetime' in df.columns: rename_map['Datetime'] = 'datetime'

#     #  if the flattened-close exists (e.g. "BTC-USD_Close"), pick that, else default "Close"
#     candidate_close = f'{asset_id}_Close'
#     close_col = candidate_close if candidate_close in df.columns else 'Close'
#     rename_map[close_col] = f'{asset_id}_price'

#     df = df.rename(columns=rename_map)

#     # 4) If we still somehow lack a 'datetime' column, take it from the index
#     if 'datetime' not in df.columns:
#         df['datetime'] = df.index

#     # 5) Ensure it's a proper datetime and drop any tz info
#     df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize(None)

#     return df

# def fetch_yfinance_price_hourly(
#     asset_id: str,
#     start_date: datetime.date,
#     end_date: datetime.date,
#     quote_asset: str = 'USD'
# ) -> pd.DataFrame:
#     """
#     Fetches hourly closing prices for a given asset via yfinance.
    
#     :param asset_id:    тикер без котировки, например 'ETH', 'BTC', 'UNI'
#     :param start_date:  дата начала (inclusive)
#     :param end_date:    дата конца (inclusive)
#     :param quote_asset: котируемая валюта на Yahoo Finance (по умолчанию 'USD')
#     :return:            DataFrame с колонками ['datetime', '<asset_id>_price']
#     """
#     symbol = asset_id.upper()
#     ticker = f"{symbol}-{quote_asset.upper()}"

#     # yfinance ждёт строку 'YYYY-MM-DD' или полный timestamp, но для почасовых данных
#     # лучше указывать и дату и время:
#     start_ts = datetime.combine(start_date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
#     # Чтобы включить весь end_date, прибавим день и возьмём 00:00 следующего дня:
#     end_ts = (datetime.combine(end_date, datetime.min.time()) + timedelta(days=1))\
#                 .strftime('%Y-%m-%d %H:%M:%S')

#     # Запрос почасовых данных
#     data = yf.download(
#         tickers=ticker,
#         start=start_ts,
#         end=end_ts,
#         interval='1h',
#         progress=False
#     )

#     # Вышестоящий DataFrame имеет индекс DatetimeIndex и столбцы ['Open','High',...,'Close',...]
#     # Normalize column names and tz handling
#     clean = normalize_yf_df(data, asset_id)

#     # Only return datetime and price
#     return clean[['datetime', f'{asset_id}_price']]

def add_prices_flexible(
    vol_df: pd.DataFrame,
    tokens: list[str],
    quote_asset: str = 'USDT'
) -> pd.DataFrame:
    """
    Adds price columns for arbitrary tokens. Attempts Binance first; on failure falls back to CoinCap.
    :param vol_df: DataFrame with 'date' column
    :param tokens: list of token symbols, e.g. ['WETH','WBTC','UNI']
    :param quote_asset: quote currency for Binance (default USDT)
    """
    df = vol_df.copy()
    df['datetime'] = pd.to_datetime(df['datetime']).dt.date
    start_date, end_date = df['datetime'].min(), df['datetime'].max()

    # Merge prices for all tokens
    result = df
    for token in tokens:
        price_df = fetch_yfinance_price_hourly(token, start_date, end_date)
        result = result.merge(price_df, on='datetime', how='left')
    return result

import datetime
from datetime import datetime as dt, timedelta
import pandas as pd
import yfinance as yf

def normalize_yf_df(df: pd.DataFrame, asset_id: str) -> pd.DataFrame:
    """
    Take a raw yfinance DataFrame (single- or multi-ticker) and return one with:
      - a tz-naive 'datetime' column
      - an '{asset_id}_price' column (empty if no data)
    """
    # 1) Flatten MultiIndex columns, if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns.values]

    # 2) Reset index → 'datetime' if no Date/Datetime column exists
    if 'Date' not in df.columns and 'Datetime' not in df.columns:
        df = df.reset_index()
        idx_col = df.columns[0]
        df = df.rename(columns={idx_col: 'datetime'})
    else:
        # rename whichever is present
        rename_map = {}
        if 'Date' in df.columns:     rename_map['Date']     = 'datetime'
        if 'Datetime' in df.columns: rename_map['Datetime'] = 'datetime'
        df = df.rename(columns=rename_map)

    # 3) Find any 'close' column (case‐insensitive), else create an empty price column
    close_candidates = [c for c in df.columns if 'close' in c.lower()]
    if close_candidates:
        df = df.rename(columns={close_candidates[0]: f'{asset_id}_price'})
    else:
        # no data → make an empty price series
        df[f'{asset_id}_price'] = pd.Series(dtype=float)

    # 4) Guarantee 'datetime' exists
    if 'datetime' not in df.columns:
        # fallback: grab the index
        df['datetime'] = df.index

    # 5) Cast + strip tz
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce').dt.tz_localize(None)

    # 6) Keep only the two desired cols
    return df[['datetime', f'{asset_id}_price']]

def fetch_yfinance_price_hourly(
    asset_id:   str,
    start_date: datetime.date,
    end_date:   datetime.date,
    quote_asset:str = 'USD'
) -> pd.DataFrame:
    """
    Fetches hourly closing prices for a given asset via yfinance,
    always returns a DataFrame with ['datetime', '<asset_id>_price'].
    """
    symbol = asset_id.upper()
    ticker = f"{symbol}-{quote_asset.upper()}"

    # inclusive start at 00:00:00
    start_ts = dt.combine(start_date, dt.min.time()).strftime('%Y-%m-%d %H:%M:%S')
    # exclusive end: 00:00:00 next day
    end_ts   = (dt.combine(end_date, dt.min.time()) + timedelta(days=1))\
                   .strftime('%Y-%m-%d %H:%M:%S')

    raw = yf.download(
        tickers=ticker,
        start=start_ts,
        end=end_ts,
        interval='1h',
        progress=False
    )

    return normalize_yf_df(raw, asset_id)