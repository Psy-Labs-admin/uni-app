import requests

def fetch_token_addresses(symbols: list[str], token_list_url: str = 'https://tokens.uniswap.org') -> dict[str, str]:
    """
    Fetches contract addresses for given token symbols using the Uniswap token list.
    
    :param symbols: List of token symbols, e.g. ['WBTC', 'WETH']
    :param token_list_url: URL to JSON token list (default: Uniswap's official list)
    :return: Dict mapping symbol -> address (checksum format), or None if not found
    """
    resp = requests.get(token_list_url)
    resp.raise_for_status()
    tokens = resp.json().get('tokens', [])
    
    mapping: dict[str, str] = {}
    for sym in symbols:
        # find first matching symbol
        matches = [t for t in tokens if t.get('symbol') == sym]
        mapping[sym] = matches[0]['address'] if matches else None
    return mapping