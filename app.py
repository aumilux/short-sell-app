import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="Aumilux Short-Sell Scanner", layout="wide")
st.title("📉 Aumilux Pro: Intraday Short-Sell Scanner")

@st.cache_data
def get_nifty_100():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty100list.csv"
        df = pd.read_csv(url)
        return [s.strip() + ".NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "SBIN.NS", "INFY.NS", "HDFCBANK.NS"]

def scan_market():
    symbols = get_nifty_100()
    # Batch download for speed
    data = yf.download(symbols, period="2d", interval="5m", progress=False, group_by='ticker')
    
    hits = []
    for s in symbols:
        try:
            df = data[s]
            if len(df) < 10: continue
            
            # അന്നത്തെ പ്രൈസ് ഡാറ്റ (Fix for FutureWarning)
            current_price = float(df['Close'].iloc[-1])
            today_high = float(df['High'].max())
            avg_price = float(df['Close'].mean()) # അന്നത്തെ ശരാശരി
            
            # പിവറ്റ് ലെവലുകൾക്കായി ഡെയിലി ഡാറ്റ (Fix for FutureWarning)
            daily = yf.download(s, period="2d", interval="1d", progress=False)
            prev_day = daily.iloc[-2]
            h = float(prev_day['High'].iloc[0]) if isinstance(prev_day['High'], pd.Series) else float(prev_day['High'])
            l = float(prev_day['Low'].iloc[0]) if isinstance(prev_day['Low'], pd.Series) else float(prev_day['Low'])
            c = float(prev_day['Close'].iloc[0]) if isinstance(prev_day['Close'], pd.Series) else float(prev_day['Close'])
            
            pivot = (h + l + c) / 3
            r1, r2 = (2 * pivot) - l, pivot + (h - l)

            signal = ""
            # സ്ട്രാറ്റജി 1: False Breakout
            if today_high > (r1 + 2) and current_price < r1:
                signal = "⚠️ സ്ട്രാറ്റജി 1: False Breakout"

            # സ്ട്രാറ്റജി 2: R2 Reversal with Avg Price check
            elif today_high > r2 and current_price < r1:
                if r1 < avg_price < r2:
                    signal = "🚨 സ്ട്രാറ്റജി 2: R2 Reversal (Add Qty at Avg)"
                else:
                    signal = "🚨 സ്ട്രാറ്റജി 2: Confirm Trend"

            # സ്ട്രാറ്റജി 3: Positive Close + Below Avg (Sell Opportunity)
            elif current_price > float(daily['Open'].iloc[-1]) and current_price < (avg_price * 0.97):
                signal = "📉 സ്ട്രാറ്റജി 3: Short Sell near Avg"

            if signal:
                hits.append({
                    "Stock": s.replace(".NS", ""),
                    "Price": round(current_price, 2),
                    "Avg Price": round(avg_price, 2),
                    "Signal": signal
                })
        except:
            continue
    return hits

st.info("നിങ്ങൾ പറഞ്ഞ 3 കൺഫേം ട്രെൻഡുകളും നിഫ്റ്റി 100 സ്റ്റോക്കുകളിൽ സ്കാൻ ചെയ്യുന്നു...")
table_placeholder = st.empty()

while True:
    results = scan_market()
    if results:
        df_hits = pd.DataFrame(results)
        with table_placeholder.container():
            st.table(df_hits.style.map(
                lambda x: 'background-color: #ff4b4b; color: white' if "🚨" in str(x) or "⚠️" in str(x) else '',
                subset=['Signal']
            ))
    else:
        table_placeholder.warning("സ്കാനിംഗ് തുടരുന്നു... നിലവിൽ അവസരങ്ങൾ ലഭ്യമല്ല.")
    
    time.sleep(60)
    st.rerun()
