#!/usr/bin/env python3
import json
import math
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

PORTFOLIO_CONFIG = [
    {"ticker": "AAPL", "purchase_date": "2024-01-16", "purchase_price": 182.50},
    {"ticker": "MSFT", "purchase_date": "2024-02-05", "purchase_price": 405.60},
    {"ticker": "GOOGL", "purchase_date": "2024-03-12", "purchase_price": 138.50},
    {"ticker": "AMZN", "purchase_date": "2024-04-18", "purchase_price": 180.00},
    {"ticker": "NVDA", "purchase_date": "2024-05-22", "purchase_price": 105.00},
    {"ticker": "META", "purchase_date": "2024-06-14", "purchase_price": 500.00},
    {"ticker": "TSLA", "purchase_date": "2024-07-10", "purchase_price": 260.00},
    {"ticker": "JPM", "purchase_date": "2024-08-05", "purchase_price": 210.00},
    {"ticker": "JNJ", "purchase_date": "2024-01-22", "purchase_price": 162.00},
    {"ticker": "V", "purchase_date": "2024-02-15", "purchase_price": 278.00},
    {"ticker": "WMT", "purchase_date": "2024-03-01", "purchase_price": 60.00},
    {"ticker": "PG", "purchase_date": "2024-04-10", "purchase_price": 155.00},
    {"ticker": "UNH", "purchase_date": "2024-05-02", "purchase_price": 490.00},
    {"ticker": "HD", "purchase_date": "2024-06-18", "purchase_price": 345.00},
    {"ticker": "MA", "purchase_date": "2024-07-25", "purchase_price": 440.00},
    {"ticker": "BAC", "purchase_date": "2024-08-12", "purchase_price": 38.50},
    {"ticker": "ABBV", "purchase_date": "2024-01-30", "purchase_price": 165.00},
    {"ticker": "XOM", "purchase_date": "2024-02-20", "purchase_price": 102.00},
    {"ticker": "KO", "purchase_date": "2024-03-18", "purchase_price": 60.50},
    {"ticker": "PEP", "purchase_date": "2024-04-22", "purchase_price": 170.00},
    {"ticker": "COST", "purchase_date": "2024-05-15", "purchase_price": 785.00},
    {"ticker": "MRK", "purchase_date": "2024-06-03", "purchase_price": 128.00},
    {"ticker": "TMO", "purchase_date": "2024-07-08", "purchase_price": 570.00},
    {"ticker": "DIS", "purchase_date": "2024-08-20", "purchase_price": 90.00},
    {"ticker": "ADBE", "purchase_date": "2024-01-10", "purchase_price": 580.00},
    {"ticker": "ACN", "purchase_date": "2024-02-14", "purchase_price": 370.00},
    {"ticker": "CSCO", "purchase_date": "2024-03-08", "purchase_price": 50.00},
    {"ticker": "LIN", "purchase_date": "2024-04-12", "purchase_price": 450.00},
    {"ticker": "NKE", "purchase_date": "2024-05-17", "purchase_price": 85.00},
    {"ticker": "MCD", "purchase_date": "2024-06-25", "purchase_price": 260.00},
    {"ticker": "CRM", "purchase_date": "2024-07-16", "purchase_price": 255.00},
    {"ticker": "PFE", "purchase_date": "2024-08-01", "purchase_price": 30.50},
    {"ticker": "NFLX", "purchase_date": "2024-09-05", "purchase_price": 65.00},
    {"ticker": "AMD", "purchase_date": "2024-01-25", "purchase_price": 180.00},
    {"ticker": "INTC", "purchase_date": "2024-02-28", "purchase_price": 43.00},
    {"ticker": "TXN", "purchase_date": "2024-03-20", "purchase_price": 172.00},
    {"ticker": "CMCSA", "purchase_date": "2024-04-26", "purchase_price": 40.00},
    {"ticker": "QCOM", "purchase_date": "2024-05-30", "purchase_price": 205.00},
    {"ticker": "NEE", "purchase_date": "2024-06-11", "purchase_price": 74.00},
    {"ticker": "UPS", "purchase_date": "2024-07-23", "purchase_price": 145.00},
    {"ticker": "AMAT", "purchase_date": "2024-08-15", "purchase_price": 210.00},
    {"ticker": "HON", "purchase_date": "2024-09-10", "purchase_price": 205.00},
    {"ticker": "LOW", "purchase_date": "2024-01-18", "purchase_price": 220.00},
    {"ticker": "PM", "purchase_date": "2024-02-12", "purchase_price": 92.00},
    {"ticker": "CVS", "purchase_date": "2024-03-25", "purchase_price": 79.00},
    {"ticker": "GS", "purchase_date": "2024-04-16", "purchase_price": 400.00},
    {"ticker": "IBM", "purchase_date": "2024-05-20", "purchase_price": 170.00},
    {"ticker": "MS", "purchase_date": "2024-06-17", "purchase_price": 98.00},
    {"ticker": "CAT", "purchase_date": "2024-07-01", "purchase_price": 340.00},
    {"ticker": "ORCL", "purchase_date": "2024-08-08", "purchase_price": 132.00}
]

OUTPUT_FILE = "portfolio_performance.json"
INPUT_FILE = "stocks.json"

def fetch_last_open(ticker, retries=3):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "curl/8.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    ]

    for attempt in range(retries):
        headers = {"User-Agent": user_agents[attempt % len(user_agents)]}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    result = data.get("chart", {}).get("result", [])
                    if result:
                        quote = result[0].get("indicators", {}).get("quote", [{}])[0]
                        opens = [x for x in quote.get("open", []) if x is not None]
                        if opens:
                            return float(opens[-1])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                raise RuntimeError(f"Failed to fetch market data for {ticker} ({url}): {e}")
    raise RuntimeError(f"Could not retrieve last opening price for {ticker}")

def compute_ground_truth(portfolio_cfg):
    tickers = [item["ticker"] for item in portfolio_cfg]
    
    # Concurrent fetch for speed and responsiveness
    def worker(item):
        ticker = item["ticker"]
        open_price = fetch_last_open(ticker)
        return ticker, open_price

    prices = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for ticker, open_p in executor.map(worker, portfolio_cfg):
            prices[ticker] = open_p

    ground_truth = {
        "stocks": {},
        "portfolio": {}
    }

    total_cost_basis = 0.0
    total_current_value = 0.0

    for item in portfolio_cfg:
        ticker = item["ticker"]
        buy_price = item["purchase_price"]
        last_open = prices[ticker]

        ret_usd = last_open - buy_price
        ret_pct = ((last_open - buy_price) / buy_price) * 100.0

        total_cost_basis += buy_price
        total_current_value += last_open

        ground_truth["stocks"][ticker] = {
            "last_opening_price": last_open,
            "total_return_usd": ret_usd,
            "total_return_percentage": ret_pct
        }

    port_ret_usd = total_current_value - total_cost_basis
    port_ret_pct = (port_ret_usd / total_cost_basis) * 100.0

    ground_truth["portfolio"] = {
        "total_cost_basis": total_cost_basis,
        "total_current_value": total_current_value,
        "total_return_usd": port_ret_usd,
        "total_return_percentage": port_ret_pct
    }

    return ground_truth

def extract_field(obj, possible_keys, default=None):
    for k in possible_keys:
        if k in obj:
            return obj[k]
    return default

def is_numeric(val):
    return isinstance(val, (int, float)) and not isinstance(val, bool)

def main():
    if not os.path.exists(OUTPUT_FILE):
        print(f"Error: {OUTPUT_FILE} does not exist in the working directory.")
        sys.exit(1)

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            agent_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse {OUTPUT_FILE} as JSON: {e}")
        sys.exit(1)

    if not isinstance(agent_data, dict):
        print(f"Error: {OUTPUT_FILE} must contain a JSON object.")
        sys.exit(1)

    # Use stocks.json if available, otherwise PORTFOLIO_CONFIG
    portfolio_cfg = PORTFOLIO_CONFIG
    if os.path.exists(INPUT_FILE):
        try:
            with open(INPUT_FILE, "r", encoding="utf-8") as f:
                loaded_cfg = json.load(f)
                if isinstance(loaded_cfg, list) and len(loaded_cfg) == 50:
                    portfolio_cfg = loaded_cfg
        except Exception:
            pass

    # Normalize agent stocks data: support either dict or list
    agent_stocks_raw = agent_data.get("stocks")
    if agent_stocks_raw is None:
        print(f"Error: Missing 'stocks' key in {OUTPUT_FILE}.")
        sys.exit(1)

    agent_stocks = {}
    if isinstance(agent_stocks_raw, dict):
        agent_stocks = agent_stocks_raw
    elif isinstance(agent_stocks_raw, list):
        for entry in agent_stocks_raw:
            if isinstance(entry, dict) and "ticker" in entry:
                agent_stocks[entry["ticker"]] = entry
            else:
                print(f"Error: Invalid entry format in 'stocks' list: {entry}")
                sys.exit(1)
    else:
        print(f"Error: 'stocks' in {OUTPUT_FILE} must be an object or a list of objects.")
        sys.exit(1)

    agent_portfolio = agent_data.get("portfolio")
    if not isinstance(agent_portfolio, dict):
        print(f"Error: Missing or invalid 'portfolio' object in {OUTPUT_FILE}.")
        sys.exit(1)

    print("Fetching live market prices for ground truth verification...")
    try:
        gt = compute_ground_truth(portfolio_cfg)
    except Exception as e:
        print(f"Error fetching ground truth from market API: {e}")
        sys.exit(1)

    mismatches = []
    missing_stocks = []

    # Validate stock performance
    for item in portfolio_cfg:
        ticker = item["ticker"]
        if ticker not in agent_stocks:
            missing_stocks.append(ticker)
            continue

        stock_info = agent_stocks[ticker]
        if not isinstance(stock_info, dict):
            mismatches.append(f"Stock '{ticker}': value must be an object, got {type(stock_info).__name__}")
            continue

        agent_open = extract_field(stock_info, ["last_opening_price", "opening_price", "open_price", "last_open"])
        agent_ret_usd = extract_field(stock_info, ["total_return_usd", "return_usd", "dollar_return"])
        agent_ret_pct = extract_field(stock_info, ["total_return_percentage", "return_percentage", "return_pct", "percent_return"])

        expected_open = gt["stocks"][ticker]["last_opening_price"]
        expected_ret_usd = gt["stocks"][ticker]["total_return_usd"]
        expected_ret_pct = gt["stocks"][ticker]["total_return_percentage"]

        if not is_numeric(agent_open):
            mismatches.append(f"Stock '{ticker}': 'last_opening_price' must be a numeric value, got {agent_open!r}")
        elif not math.isclose(float(agent_open), expected_open, rel_tol=0.015, abs_tol=1.00):
            mismatches.append(
                f"Stock '{ticker}': last_opening_price mismatch (expected ~{expected_open:.2f}, got {agent_open})"
            )

        if not is_numeric(agent_ret_usd):
            mismatches.append(f"Stock '{ticker}': 'total_return_usd' must be a numeric value, got {agent_ret_usd!r}")
        elif not math.isclose(float(agent_ret_usd), expected_ret_usd, rel_tol=0.02, abs_tol=1.50):
            mismatches.append(
                f"Stock '{ticker}': total_return_usd mismatch (expected ~{expected_ret_usd:.2f}, got {agent_ret_usd})"
            )

        if not is_numeric(agent_ret_pct):
            mismatches.append(f"Stock '{ticker}': 'total_return_percentage' must be a numeric value, got {agent_ret_pct!r}")
        elif not math.isclose(float(agent_ret_pct), expected_ret_pct, rel_tol=0.02, abs_tol=1.50):
            mismatches.append(
                f"Stock '{ticker}': total_return_percentage mismatch (expected ~{expected_ret_pct:.2f}%, got {agent_ret_pct}%)"
            )

    if missing_stocks:
        print(f"Validation failed: Missing {len(missing_stocks)} stock(s) in {OUTPUT_FILE}: {missing_stocks}")
        sys.exit(1)

    # Validate overall portfolio metrics
    p_cost = extract_field(agent_portfolio, ["total_cost_basis", "cost_basis", "total_cost"])
    p_val = extract_field(agent_portfolio, ["total_current_value", "current_value", "total_value"])
    p_ret_usd = extract_field(agent_portfolio, ["total_return_usd", "return_usd", "dollar_return"])
    p_ret_pct = extract_field(agent_portfolio, ["total_return_percentage", "return_percentage", "return_pct", "percent_return"])

    gt_cost = gt["portfolio"]["total_cost_basis"]
    gt_val = gt["portfolio"]["total_current_value"]
    gt_ret_usd = gt["portfolio"]["total_return_usd"]
    gt_ret_pct = gt["portfolio"]["total_return_percentage"]

    if not is_numeric(p_cost):
        mismatches.append(f"Portfolio: 'total_cost_basis' must be numeric, got {p_cost!r}")
    elif not math.isclose(float(p_cost), gt_cost, abs_tol=0.50):
        mismatches.append(f"Portfolio: total_cost_basis mismatch (expected {gt_cost:.2f}, got {p_cost})")

    if not is_numeric(p_val):
        mismatches.append(f"Portfolio: 'total_current_value' must be numeric, got {p_val!r}")
    elif not math.isclose(float(p_val), gt_val, rel_tol=0.015, abs_tol=20.00):
        mismatches.append(f"Portfolio: total_current_value mismatch (expected ~{gt_val:.2f}, got {p_val})")

    if not is_numeric(p_ret_usd):
        mismatches.append(f"Portfolio: 'total_return_usd' must be numeric, got {p_ret_usd!r}")
    elif not math.isclose(float(p_ret_usd), gt_ret_usd, rel_tol=0.02, abs_tol=20.00):
        mismatches.append(f"Portfolio: total_return_usd mismatch (expected ~{gt_ret_usd:.2f}, got {p_ret_usd})")

    if not is_numeric(p_ret_pct):
        mismatches.append(f"Portfolio: 'total_return_percentage' must be numeric, got {p_ret_pct!r}")
    elif not math.isclose(float(p_ret_pct), gt_ret_pct, rel_tol=0.02, abs_tol=1.50):
        mismatches.append(f"Portfolio: total_return_percentage mismatch (expected ~{gt_ret_pct:.2f}%, got {p_ret_pct}%)")

    if mismatches:
        print(f"Validation failed with {len(mismatches)} mismatch(es):")
        for m in mismatches[:15]:
            print(f"  - {m}")
        if len(mismatches) > 15:
            print(f"  ... and {len(mismatches) - 15} more mismatch(es).")
        sys.exit(1)

    print("Validation passed: All 50 stock returns and overall portfolio performance verified successfully against market API.")
    sys.exit(0)

if __name__ == "__main__":
    main()
