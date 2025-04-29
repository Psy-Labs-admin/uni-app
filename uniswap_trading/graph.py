import requests
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import List, Dict

def fetch_uniswap_v3_pools_by_tokens(
    bearer_token: str,
    token_addresses: list[str],
    first: int = 1000
) -> pd.DataFrame:
    """
    Запрашивает только те пулы, где token0 или token1 совпадает с одним из token_addresses.
    token_addresses: список адресов токенов (в формате checksum или lowercase).
    """
    gateway_url = 'https://gateway.thegraph.com/api/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {bearer_token}'}
    query = '''
    query PoolsByTokens($first: Int!, $skip: Int!, $tokens: [String!]) {
      pools(
        first: $first,
        skip: $skip,
        where: { token0_in: $tokens, token1_in: $tokens }
      ) {
        id
        feeTier
        liquidity
        token0 { id symbol }
        token1 { id symbol }
      }
    }
    '''
    all_rows = []
    skip = 0
    while True:
        vars = {'first': first, 'skip': skip, 'tokens': [t.lower() for t in token_addresses]}
        resp = requests.post(gateway_url, headers=headers, json={'query': query, 'variables': vars})
        resp.raise_for_status()
        pools = resp.json().get('data', {}).get('pools', [])
        if not pools:
            break
        for p in pools:
            all_rows.append({
                'pool_id': p['id'],
                'feeTier': int(p['feeTier']),
                'liquidity': float(p.get('liquidity', 0)),
                'token0_id': p['token0']['id'],
                'token0_symbol': p['token0']['symbol'],
                'token1_id': p['token1']['id'],
                'token1_symbol': p['token1']['symbol'],
            })
        skip += first
    return pd.DataFrame(all_rows)


def fetch_uniswap_v3_pool_volume_hourly(
    pool_address: str,
    start_date: str,
    end_date: str,
    symbols: List[str],
    bearer_token: str,
) -> pd.DataFrame:
    gateway_url = 'https://gateway.thegraph.com/api/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }

    query = '''
    query PoolHourlyVolumes($pool: ID!, $start: Int!, $end: Int!) {
      poolHourDatas(
        where: { pool: $pool, periodStartUnix_gte: $start, periodStartUnix_lt: $end },
        orderBy: periodStartUnix,
        orderDirection: asc
      ) {
        periodStartUnix
        volumeToken0
        volumeToken1
      }
    }
    '''
    # UNIX timestamps в секундах
    start_date, end_date = get_date_timestamps(start_date, end_date)
    variables = {
        'pool': pool_address.lower(),
        'start': start_date,
        'end': end_date
    }

    resp = requests.post(
        gateway_url,
        headers=headers,
        json={'query': query, 'variables': variables}
    )
    resp.raise_for_status()
    data = resp.json()['data']['poolHourDatas']

    rows = []
    for item in data:
        dt = datetime.fromtimestamp(item['periodStartUnix'])
        rows.append({
            'datetime': dt,              # точный час
            symbols[0]: float(item['volumeToken0']),
            symbols[1]: float(item['volumeToken1'])
        })

    return pd.DataFrame(rows)

def fetch_uniswap_v3_pool_volume(
    pool_address: str,
    start_date: datetime.date,
    end_date: datetime.date,
    symbols: List[str],
    bearer_token: str,
) -> pd.DataFrame:
    """
    Возвращает DataFrame с колонками ['date', 'volumeToken0', 'volumeToken1']
    за диапазон дат [start_date, end_date) для заданного пула.
    Запрос идёт на GraphQL Gateway TheGraph.
    """
    # Конечная точка GraphQL Gateway и заголовки
    gateway_url = 'https://gateway.thegraph.com/api/subgraphs/id/5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {bearer_token}'
    }

    # GraphQL-запрос по poolDayDatas
    query = '''
    query PoolVolumes($pool: ID!, $start: Int!, $end: Int!) {
          poolDayDatas(
            where: { pool_in: [$pool], date_gte: $start, date_lt: $end },
            orderBy: date,
            orderDirection: asc
          ) {
            date
            volumeToken0
            volumeToken1
          }
        }
    '''
    start_date, end_date = get_date_timestamps(start_date, end_date)
    variables = {
        'pool': pool_address.lower(),
        'start': start_date,
        'end': end_date
    }

    resp = requests.post(
        gateway_url,
        headers=headers,
        json={'query': query, 
              'variables': variables}
    )
    resp.raise_for_status()
    data = resp.json().get('data', {}).get('poolDayDatas', [])

    rows = []
    for item in data:
        date = datetime.fromtimestamp(item['date']).date()
        vol0 = float(item['volumeToken0'])
        vol1 = float(item['volumeToken1'])
        rows.append({
        'date': date,
        symbols[0]: vol0,
        symbols[1]: vol1
    })

    return pd.DataFrame(rows)

from datetime import datetime, date

def parse_date_range(start_str: str, end_str: str) -> tuple[date, date]:
    """
    Преобразует 'YYYY-MM-DD' → объекты datetime.date.
    """
    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
    end_date   = datetime.strptime(end_str,   '%Y-%m-%d').date()
    return start_date, end_date

def get_date_timestamps(start_str: str, end_str: str) -> tuple[int, int]:
    """
    Преобразует 'YYYY-MM-DD' → Unix-timestamp начала каждого дня.
    """
    start_date, end_date = parse_date_range(start_str, end_str)
    start_ts = int(datetime.combine(start_date, datetime.min.time()).timestamp())
    end_ts   = int(datetime.combine(end_date,   datetime.min.time()).timestamp())
    return start_ts, end_ts


