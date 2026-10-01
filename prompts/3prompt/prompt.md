You are provided with a portfolio of 50 stocks with their purchase dates and purchase prices. Assuming exactly 1 share was purchased for each stock at its specified purchase price:

1. Look up the most recent (last) opening price for each stock using market data / financial API.
2. Calculate the total return or loss for each stock both in USD (`last_opening_price - purchase_price`) and as a percentage (`((last_opening_price - purchase_price) / purchase_price) * 100`).
3. Calculate the overall portfolio performance:
   - `total_cost_basis`: Sum of all stock purchase prices.
   - `total_current_value`: Sum of all stock last opening prices.
   - `total_return_usd`: Overall dollar gain or loss (`total_current_value - total_cost_basis`).
   - `total_return_percentage`: Overall percentage return (`((total_current_value - total_cost_basis) / total_cost_basis) * 100`).

The 50 stocks in the portfolio are (also available in `stocks.json` in this directory):
- **AAPL**: Purchased on 2024-01-16 at $182.50
- **MSFT**: Purchased on 2024-02-05 at $405.60
- **GOOGL**: Purchased on 2024-03-12 at $138.50
- **AMZN**: Purchased on 2024-04-18 at $180.00
- **NVDA**: Purchased on 2024-05-22 at $105.00
- **META**: Purchased on 2024-06-14 at $500.00
- **TSLA**: Purchased on 2024-07-10 at $260.00
- **JPM**: Purchased on 2024-08-05 at $210.00
- **JNJ**: Purchased on 2024-01-22 at $162.00
- **V**: Purchased on 2024-02-15 at $278.00
- **WMT**: Purchased on 2024-03-01 at $60.00
- **PG**: Purchased on 2024-04-10 at $155.00
- **UNH**: Purchased on 2024-05-02 at $490.00
- **HD**: Purchased on 2024-06-18 at $345.00
- **MA**: Purchased on 2024-07-25 at $440.00
- **BAC**: Purchased on 2024-08-12 at $38.50
- **ABBV**: Purchased on 2024-01-30 at $165.00
- **XOM**: Purchased on 2024-02-20 at $102.00
- **KO**: Purchased on 2024-03-18 at $60.50
- **PEP**: Purchased on 2024-04-22 at $170.00
- **COST**: Purchased on 2024-05-15 at $785.00
- **MRK**: Purchased on 2024-06-03 at $128.00
- **TMO**: Purchased on 2024-07-08 at $570.00
- **DIS**: Purchased on 2024-08-20 at $90.00
- **ADBE**: Purchased on 2024-01-10 at $580.00
- **ACN**: Purchased on 2024-02-14 at $370.00
- **CSCO**: Purchased on 2024-03-08 at $50.00
- **LIN**: Purchased on 2024-04-12 at $450.00
- **NKE**: Purchased on 2024-05-17 at $85.00
- **MCD**: Purchased on 2024-06-25 at $260.00
- **CRM**: Purchased on 2024-07-16 at $255.00
- **PFE**: Purchased on 2024-08-01 at $30.50
- **NFLX**: Purchased on 2024-09-05 at $65.00
- **AMD**: Purchased on 2024-01-25 at $180.00
- **INTC**: Purchased on 2024-02-28 at $43.00
- **TXN**: Purchased on 2024-03-20 at $172.00
- **CMCSA**: Purchased on 2024-04-26 at $40.00
- **QCOM**: Purchased on 2024-05-30 at $205.00
- **NEE**: Purchased on 2024-06-11 at $74.00
- **UPS**: Purchased on 2024-07-23 at $145.00
- **AMAT**: Purchased on 2024-08-15 at $210.00
- **HON**: Purchased on 2024-09-10 at $205.00
- **LOW**: Purchased on 2024-01-18 at $220.00
- **PM**: Purchased on 2024-02-12 at $92.00
- **CVS**: Purchased on 2024-03-25 at $79.00
- **GS**: Purchased on 2024-04-16 at $400.00
- **IBM**: Purchased on 2024-05-20 at $170.00
- **MS**: Purchased on 2024-06-17 at $98.00
- **CAT**: Purchased on 2024-07-01 at $340.00
- **ORCL**: Purchased on 2024-08-08 at $132.00

Save the output to a file named `portfolio_performance.json` in the root of this environment directory.

The JSON output should contain:
- `stocks`: An object mapping each stock ticker to its metrics:
  - `last_opening_price`: The stock's last opening price in USD.
  - `total_return_usd`: Dollar return or loss (`last_opening_price - purchase_price`).
  - `total_return_percentage`: Percentage return or loss (`((last_opening_price - purchase_price) / purchase_price) * 100`).
- `portfolio`: An object representing overall portfolio performance:
  - `total_cost_basis`: Total purchase cost ($10,971.10).
  - `total_current_value`: Total value at last opening prices.
  - `total_return_usd`: Portfolio total return or loss in USD (`total_current_value - total_cost_basis`).
  - `total_return_percentage`: Portfolio overall percentage return.

Example format:
```json
{
  "stocks": {
    "AAPL": {
      "last_opening_price": 230.15,
      "total_return_usd": 47.65,
      "total_return_percentage": 26.11
    },
    "MSFT": {
      "last_opening_price": 445.20,
      "total_return_usd": 39.60,
      "total_return_percentage": 9.76
    }
  },
  "portfolio": {
    "total_cost_basis": 10971.10,
    "total_current_value": 14120.50,
    "total_return_usd": 3149.40,
    "total_return_percentage": 28.71
  }
}
```
All dollar values and percentages may be rounded to 2 decimal places. Positive numbers indicate a gain, and negative numbers indicate a loss.
