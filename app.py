import streamlit as st
import pandas as pd
import yfinance as yf
import time

st.set_page_config(page_title="Aumilux Short-Sell Scanner", layout="wide")
st.title("📉 Aumilux Pro: Short-Sell Trend Scanner")

@st.cache_data
def get_nifty_100():
    try:
        url = "https://archives.nseindia.com/content/indices/ind_nifty100list.csv"
        df = pd.read_csv(url)
        return [s.strip() + ".NS" for s in df['Symbol'].tolist()]
    except:
        return ["RELIANCE.NS", "TCS.NS", "SBIN.NS", "HDFCBANK.NS"]

def scan_logic():
    symbols = get_nifty_100()
    # ഇൻട്രാഡേ (5 മിനിറ്റ്) ഡാറ്റ എടുക്കുന്നു
    data = yf.download(symbols, period="2d", interval="5m", progress=False, group_by='ticker')
    
    hits = []
    for s in symbols:
        try:
            df = data[s]
            if len(df) < 10: continue
            
            # അന്നത്തെ ഓപ്പണിംഗ് മുതലുള്ള ഡാറ്റ
            current_price = float(df['Close'].iloc[-1])
            today_high = float(df['High'].max())
            avg_price = float(df['Close'].mean()) # അന്നത്തെ ശരാശരി വില
            
            # പിവറ്റ് ലെവലുകൾ (Daily)
            daily = yf.download(s, period="2d", interval="1d", progress=False)
            prev_day = daily.iloc[-2]
            h, l, c = float(prev_day['High']), float(prev_day['Low']), float(prev_day['Close'])
            pivot = (h + l + c) / 3
            r1, r2 = (2 * pivot) - l, pivot + (h - l)

            signal = ""
            # സ്ട്രാറ്റജി 1: False Breakout (High കടന്ന ശേഷം താഴെ പോവുക)
            if today_high > r1 and current_price < r1:
                signal = "⚠️ സ്ട്രാറ്റജി 1: False Breakout"

            # സ്ട്രാറ്റജി 2: R2 കടന്ന ശേഷം R1-ന് താഴെ പോവുക (Average check)
            elif today_high > r2 and current_price < r1:
                if r1 < avg_price < r2:
                    signal = "🚨 സ്ട്രാറ്റജി 2: R2 Reversal (Add Qty at Avg)"
                else:
                    signal = "🚨 സ്ട്രാറ്റജി 2: Confirm Trend"

            # സ്ട്രാറ്റജി 3: പോസിറ്റീവ് ക്ലോസിംഗ് + ആവറേജിന് താഴെ (Short Sell next day)
            elif current_price > float(daily.iloc[-1]['Open']) and current_price < (avg_price * 0.97):
                signal = "📉 സ്ട്രാറ്റജി 3: Short Sell near Avg"

            if signal:
                hits.append({
                    "Stock": s.replace(".NS", ""),
                    "LTP": round(current_price, 2),
                    "Today's Avg": round(avg_price, 2),
                    "R1 Level": round(r1, 2),
                    "Signal": signal
                })
        except:
            continue
    return hits

st.info("നിങ്ങളുടെ 3 കൺഫേം ട്രെൻഡുകളും നിഫ്റ്റി 100 സ്റ്റോക്കുകളിൽ സ്കാൻ ചെയ്യുന്നു...")
table_placeholder = st.empty()

while True:
    results = scan_logic()
    if results:
        df_display = pd.DataFrame(results)
        with table_placeholder.container():
            st.table(df_display.style.map(
                lambda x: 'background-color: #ff4b4b; color: white; font-weight: bold' if "🚨" in str(x) or "⚠️" in str(x) else '',
                subset=['Signal']
            ))
    else:
        table_placeholder.warning("സ്കാനിംഗ് തുടരുന്നു... നിലവിൽ സ്ട്രാറ്റജി മാച്ച് ചെയ്യുന്ന സ്റ്റോക്കുകൾ ലഭ്യമല്ല.")
    
    time.sleep(60)
    st.rerun()
