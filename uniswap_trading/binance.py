import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_yfinance_price_hourly(
    asset_id: str,
    start_date: datetime.date,
    end_date: datetime.date,
    quote_asset: str = 'USD'
) -> pd.DataFrame:
    """
    Fetches hourly closing prices for a given asset via yfinance.
    
    :param asset_id:    тикер без котировки, например 'ETH', 'BTC', 'UNI'
    :param start_date:  дата начала (inclusive)
    :param end_date:    дата конца (inclusive)
    :param quote_asset: котируемая валюта на Yahoo Finance (по умолчанию 'USD')
    :return:            DataFrame с колонками ['datetime', '<asset_id>_price']
    """
    symbol = asset_id.upper()
    ticker = f"{symbol}-{quote_asset.upper()}"

    # yfinance ждёт строку 'YYYY-MM-DD' или полный timestamp, но для почасовых данных
    # лучше указывать и дату и время:
    start_ts = datetime.combine(start_date, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
    # Чтобы включить весь end_date, прибавим день и возьмём 00:00 следующего дня:
    end_ts = (datetime.combine(end_date, datetime.min.time()) + timedelta(days=1))\
                .strftime('%Y-%m-%d %H:%M:%S')

    # Запрос почасовых данных
    data = yf.download(
        tickers=ticker,
        start=start_ts,
        end=end_ts,
        interval='1h',    # <-- здесь ключевое изменение
        progress=False
    )

    # Вышестоящий DataFrame имеет индекс DatetimeIndex и столбцы ['Open','High',...,'Close',...]
    df = data[['Close']].reset_index()
    df = df.rename(columns={
        'Datetime': 'datetime',  # в зависимости от версии yfinance может быть 'Date' или 'Datetime'
        'Close': f'{asset_id}_price'
    })
    # Уберём информацию о таймзоне, если она есть
    print(df.head())
    df['datetime'] = df['datetime'].dt.tz_localize(None)

    return df[['datetime', f'{asset_id}_price']]

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
