from graph import fetch_uniswap_v3_pools_by_tokens, fetch_uniswap_v3_pool_volume_hourly
from binance import add_prices_flexible
from fees import add_daily_fees_usd_dynamic
from plots import generate_fee_visualizations_hourly
from uniswap import fetch_token_addresses
import numpy as np

def produce_fees(
    symbols,
    start_date,
    end_date,
    bearer_token="5c3c9b508800616e25f0cb4e07237198"
):
    tokens = fetch_token_addresses(symbols)
    token_0 = tokens[symbols[0]]
    token_1 = tokens[symbols[1]]

    pools_df = fetch_uniswap_v3_pools_by_tokens(bearer_token, [token_0, token_1])
    pools_df = (
        pools_df[pools_df['liquidity'] > 0]
        .sort_values('liquidity', ascending=False)
        .reset_index(drop=True)
    )
    
    vol_df = fetch_uniswap_v3_pool_volume_hourly(pools_df[pools_df.index == 0].pool_id[0], start_date, end_date, symbols, bearer_token)
    vol_df[symbols] = (
        vol_df[symbols]
        .replace(0, np.nan)
        .ffill()
    )
    vol_with_usd = add_prices_flexible(vol_df, symbols)
    vol_with_usd_with_fee = add_daily_fees_usd_dynamic(
        vol_with_usd,
        symbols,
        pools_df[pools_df.index == 0].feeTier[0])
    return generate_fee_visualizations_hourly(vol_with_usd_with_fee)