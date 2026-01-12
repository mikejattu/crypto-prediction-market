import json
import time
import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import BookParams
from py_clob_client.exceptions import PolyApiException

GAMMA = "https://gamma-api.polymarket.com"
CLOB_HOST = "https://clob.polymarket.com"

client = ClobClient(host=CLOB_HOST, chain_id=137)

def fetch_events_page(limit: int, offset: int):
    params = {
        "order": "id",
        "ascending": "false",
        "closed": "false",
        "limit": limit,
        "offset": offset,
    }
    r = requests.get(f"{GAMMA}/events", params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def parse_clob_token_ids(market_obj):
    ids = market_obj.get("clobTokenIds")
    if isinstance(ids, str):
        try:
            ids = json.loads(ids)
        except json.JSONDecodeError:
            return None
    return ids

def try_mid_and_price(token_id: str):
    try:
        mid = client.get_midpoint(token_id)
        buy = client.get_price(token_id, side="BUY")
        sell = client.get_price(token_id, side="SELL")
        return mid, buy, sell
    except PolyApiException as e:
        if getattr(e, "status_code", None) == 404:
            return None
        raise  

def main(pages=2, limit=20, sleep_s=0.15):
    offset = 0
    for page in range(pages):
        events = fetch_events_page(limit=limit, offset=offset)
        if not events:
            break

        print(f"\n=== Page {page+1} (offset={offset}) ===")
        for ev in events:
            title = ev.get("title") or ev.get("name") or ev.get("slug")
            print(f"\nEVENT: {title}")
            print(f"  slug: {ev.get('slug')}")
            print(f"  end:  {ev.get('endDate') or ev.get('end_date')}")

            markets = ev.get("markets") or []
            print(f"  markets: {len(markets)}")

            for m in markets:
                q = m.get("question") or m.get("title") or m.get("slug")
                print(f"    - {q}")

                token_ids = parse_clob_token_ids(m)
                if not token_ids or len(token_ids) < 2:
                    print("      (no clobTokenIds)")
                    continue

                yes_id, no_id = token_ids[0], token_ids[1]

                yes = try_mid_and_price(yes_id)
                no  = try_mid_and_price(no_id)

                if not yes and not no:
                    print("      (skipping: no CLOB orderbook yet)")
                    continue

                if yes:
                    mid, buy, sell = yes
                    print(f"      YES mid={mid} buy={buy} sell={sell}")
                else:
                    print("      YES (no orderbook)")

                if no:
                    mid, buy, sell = no
                    print(f"      NO  mid={mid} buy={buy} sell={sell}")
                else:
                    print("      NO  (no orderbook)")

                time.sleep(sleep_s)

        offset += limit

if __name__ == "__main__":
    main(pages=3, limit=20)
