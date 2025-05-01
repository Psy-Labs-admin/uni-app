from graph import fetch_uniswap_v3_pools_by_tokens, fetch_uniswap_v3_pool_volume
from binance import add_prices_from_csv
from fees import add_daily_fees_usd_dynamic
from plots import generate_fee_visualizations
# from uniswap import fetch_token_addresses
import numpy as np

def produce_fees(
    symbols,
    start_date,
    end_date,
    bearer_token="5c3c9b508800616e25f0cb4e07237198"
):
    # tokens = fetch_token_addresses(symbols)
    # token_0 = tokens[symbols[0]]
    # token_1 = tokens[symbols[1]]

    token_0 = '0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    token_1 = '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599'

    pools_df = fetch_uniswap_v3_pools_by_tokens(bearer_token, [token_0, token_1])
    pools_df = (
        pools_df[pools_df['liquidity'] > 0]
        .sort_values('liquidity', ascending=False)
        .reset_index(drop=True)
    )
    
    vol_df = fetch_uniswap_v3_pool_volume(pools_df[pools_df.index == 0].pool_id[0], start_date, end_date, symbols, bearer_token)
    print(vol_df.head())
    vol_with_usd = add_prices_from_csv(vol_df, symbols)
    print("WITH USD:", vol_with_usd.head())
    vol_with_usd_with_fee = add_daily_fees_usd_dynamic(
        vol_with_usd,
        symbols,
        pools_df[pools_df.index == 0].feeTier[0])
    return generate_fee_visualizations(vol_with_usd_with_fee)

if __name__ == '__main__':
    fig_daily, fig_cum, fig_heatmap = produce_fees(["WETH", "WBTC"], "2024-07-01", "2025-04-01")
    fig_daily.show()