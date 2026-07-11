"""Check HK inverse ETF prices to determine affordable budget."""
import yfinance as yf

etfs = ['7500.HK', '7552.HK', '7300.HK', '7330.HK']
print("HK Inverse ETF Prices:")
for e in etfs:
    try:
        h = yf.Ticker(e).history(period='5d')
        if not h.empty:
            p = float(h['Close'].iloc[-1])
            print(f"  {e}: {p:.2f} HKD (lot=100, min cost={p*100:.0f} HKD)")
        else:
            print(f"  {e}: no data")
    except Exception as ex:
        print(f"  {e}: error - {ex}")