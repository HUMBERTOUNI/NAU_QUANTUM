import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
from nau_quantum_engine import NAUQuantumAlphaIndicator, generate_html_chart

st.set_page_config(page_title="NAU Quantum v4.0", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# ── Clean UI ──
st.markdown("""
<style>
#MainMenu,header,footer,.stDeployButton{visibility:hidden;display:none}
.block-container{padding:0.3rem 1rem 0 1rem!important}
div[data-testid="stSelectbox"]>div>div{background:#131722!important;border:1px solid #2a2e39!important;color:#e8ecf1!important;border-radius:6px}
section[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1e2a3a}
[data-testid="stMetricValue"]{font-family:'JetBrains Mono',monospace;font-size:1.1rem!important}
[data-testid="stMetricDelta"]{font-family:'JetBrains Mono',monospace}
div[data-testid="stColorPicker"]>div{min-height:0!important}
</style>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# ═══ SYMBOL DATABASE ═══
SYMBOLS = {
    "AAPL · Apple Inc.":"AAPL","MSFT · Microsoft":"MSFT","GOOGL · Alphabet":"GOOGL",
    "AMZN · Amazon":"AMZN","NVDA · NVIDIA":"NVDA","META · Meta":"META",
    "TSLA · Tesla":"TSLA","PLTR · Palantir":"PLTR","AMD · AMD":"AMD",
    "INTC · Intel":"INTC","NFLX · Netflix":"NFLX","CRM · Salesforce":"CRM",
    "ORCL · Oracle":"ORCL","ADBE · Adobe":"ADBE","UBER · Uber":"UBER",
    "SHOP · Shopify":"SHOP","SNOW · Snowflake":"SNOW","NET · Cloudflare":"NET",
    "CRWD · CrowdStrike":"CRWD","AVGO · Broadcom":"AVGO","MU · Micron":"MU",
    "QCOM · Qualcomm":"QCOM","ARM · ARM Holdings":"ARM","SMCI · Super Micro":"SMCI",
    "MARA · Marathon Digital":"MARA","RIOT · Riot Platforms":"RIOT","MSTR · MicroStrategy":"MSTR",
    "JPM · JPMorgan":"JPM","BAC · Bank of America":"BAC","GS · Goldman Sachs":"GS",
    "V · Visa":"V","MA · Mastercard":"MA","PYPL · PayPal":"PYPL",
    "COIN · Coinbase":"COIN","SQ · Block":"SQ","BRK-B · Berkshire":"BRK-B",
    "JNJ · Johnson & Johnson":"JNJ","UNH · UnitedHealth":"UNH","LLY · Eli Lilly":"LLY",
    "ABBV · AbbVie":"ABBV","MRK · Merck":"MRK","PFE · Pfizer":"PFE",
    "XOM · Exxon Mobil":"XOM","CVX · Chevron":"CVX","OXY · Occidental":"OXY",
    "WMT · Walmart":"WMT","COST · Costco":"COST","HD · Home Depot":"HD",
    "DIS · Disney":"DIS","MCD · McDonald's":"MCD","KO · Coca-Cola":"KO",
    "PEP · PepsiCo":"PEP","NKE · Nike":"NKE","SBUX · Starbucks":"SBUX",
    "BA · Boeing":"BA","CAT · Caterpillar":"CAT","LMT · Lockheed Martin":"LMT",
    "SPY · S&P 500 ETF":"SPY","QQQ · Nasdaq 100 ETF":"QQQ","DIA · Dow Jones ETF":"DIA",
    "IWM · Russell 2000 ETF":"IWM","ARKK · ARK Innovation":"ARKK",
    "SOXX · Semiconductor ETF":"SOXX","XLF · Financial ETF":"XLF",
    "XLE · Energy ETF":"XLE","XLK · Tech ETF":"XLK","XLV · Healthcare ETF":"XLV",
    "GLD · Gold ETF":"GLD","SLV · Silver ETF":"SLV","USO · Oil ETF":"USO",
    "BTC-USD · Bitcoin":"BTC-USD","ETH-USD · Ethereum":"ETH-USD",
    "SOL-USD · Solana":"SOL-USD","XRP-USD · Ripple":"XRP-USD",
    "DOGE-USD · Dogecoin":"DOGE-USD","ADA-USD · Cardano":"ADA-USD",
    "EURUSD=X · EUR/USD":"EURUSD=X","GBPUSD=X · GBP/USD":"GBPUSD=X",
}
SYMBOL_LABELS = {v: k for k, v in SYMBOLS.items()}

# Timeframes including monthly and yearly (via period mapping)
TF_OPTIONS = ["1m","5m","15m","30m","1h","4h","1d","1wk","1mo","3mo"]
TF_DISPLAY = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"1H","4h":"4H","1d":"1D","1wk":"1W","1mo":"1M","3mo":"3M"}
PERIOD_MAP = {
    "1m":"7d","5m":"60d","15m":"60d","30m":"60d",
    "1h":"730d","4h":"730d","1d":"5y","1wk":"10y","1mo":"max","3mo":"max",
}

# ═══ SESSION STATE DEFAULTS ═══
DEFAULTS = dict(
    symbol="PLTR", timeframe="1d", refresh_sec=60, conf_threshold=60,
    up_color="#26A69A", down_color="#EF5350", bg_color="#131722",
    kalman_color="#FFD700", signal_line_color="#2196F3",
    long_color="#00E676", short_color="#FF1744",
    font_size=12, line_width=2, signal_line_width=2, marker_font_size=11,
    show_volume=True, show_kalman=True, show_signals=True,
    show_fractals=True, show_regime=True, show_confidence=True,
    show_factor_panel=True,
)
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ═══ SIDEBAR — Settings ═══
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:10px 0'><span style='font-family:JetBrains Mono;font-size:16px;font-weight:700;color:#4a9eff;letter-spacing:2px'>⚡ NAU QUANTUM v4.0</span><br><span style='font-size:11px;color:#5a7a9a'>18-Factor AI/ML Engine</span></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("##### ⏱ Refresh")
    st.session_state.refresh_sec = st.slider("Auto-refresh (sec)", 30, 300, st.session_state.refresh_sec)
    st.session_state.conf_threshold = st.slider("Confidence threshold %", 40, 95, st.session_state.conf_threshold)
    st.divider()
    st.markdown("##### 🎨 Colors")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.up_color = st.color_picker("Bullish", st.session_state.up_color)
        st.session_state.kalman_color = st.color_picker("Kalman", st.session_state.kalman_color)
        st.session_state.long_color = st.color_picker("Buy signal", st.session_state.long_color)
    with c2:
        st.session_state.down_color = st.color_picker("Bearish", st.session_state.down_color)
        st.session_state.signal_line_color = st.color_picker("Signal line", st.session_state.signal_line_color)
        st.session_state.short_color = st.color_picker("Sell signal", st.session_state.short_color)
    st.divider()
    st.markdown("##### 📐 Sizes")
    st.session_state.font_size = st.slider("Font size", 9, 18, st.session_state.font_size)
    st.session_state.line_width = st.slider("Line width", 1, 5, st.session_state.line_width)
    st.session_state.marker_font_size = st.slider("Signal label size (0=hide)", 0, 16, st.session_state.marker_font_size)
    st.divider()
    st.markdown("##### 👁 Show / Hide")
    st.session_state.show_volume = st.toggle("Volume", st.session_state.show_volume)
    st.session_state.show_kalman = st.toggle("Kalman filter", st.session_state.show_kalman)
    st.session_state.show_signals = st.toggle("Buy/Sell signals", st.session_state.show_signals)
    st.session_state.show_regime = st.toggle("Regime shading", st.session_state.show_regime)
    st.session_state.show_confidence = st.toggle("Confidence band", st.session_state.show_confidence)
    st.session_state.show_factor_panel = st.toggle("Factor panel", st.session_state.show_factor_panel)
    st.divider()
    if st.button("🔄 Reset All Settings", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# ═══ TOP BAR ═══
t1, t2, t3, t4 = st.columns([3, 1.5, 2, 0.8])
with t1:
    cur = SYMBOL_LABELS.get(st.session_state.symbol, f"{st.session_state.symbol} · Custom")
    opts = list(SYMBOLS.keys())
    idx = opts.index(cur) if cur in opts else 0
    sel = st.selectbox("🔍", opts, index=idx, label_visibility="collapsed", placeholder="Search symbol or company...")
    st.session_state.symbol = SYMBOLS[sel]
with t2:
    tf = st.selectbox("TF", TF_OPTIONS, index=TF_OPTIONS.index(st.session_state.timeframe),
                       format_func=lambda x: TF_DISPLAY.get(x, x), label_visibility="collapsed")
    st.session_state.timeframe = tf
with t3:
    custom = st.text_input("custom", value="", placeholder="Custom ticker (MARA, RIOT...)", label_visibility="collapsed")
    if custom.strip(): st.session_state.symbol = custom.strip().upper()
with t4:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    if st.button("⚙", use_container_width=True): st.rerun()

# ═══ DATA DOWNLOAD ═══
def download_data(sym, interval):
    period = PERIOD_MAP.get(interval, "60d")
    raw = yf.download(sym, period=period, interval=interval, prepost=False, auto_adjust=True, progress=False)
    if raw.empty: return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex): raw.columns = raw.columns.get_level_values(0)
    cmap = {}
    for c in raw.columns:
        lc = str(c).lower()
        if lc == "open": cmap[c] = "Open"
        elif lc == "high": cmap[c] = "High"
        elif lc == "low": cmap[c] = "Low"
        elif lc in ("close","adj close"): cmap[c] = "Close"
        elif lc == "volume": cmap[c] = "Volume"
    raw = raw.rename(columns=cmap)
    needed = ["Open","High","Low","Close","Volume"]
    if any(c not in raw.columns for c in needed): return pd.DataFrame()
    df = raw[needed].copy()
    for col in needed: df[col] = pd.to_numeric(df[col].squeeze(), errors="coerce")
    return df.dropna(subset=["Open","High","Low","Close"])

def _hex_rgb(h):
    h = h.lstrip('#')
    if len(h)==6: return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    return "128,128,128"

# ═══ MAIN ═══
def run():
    sym = st.session_state.symbol
    tf = st.session_state.timeframe
    with st.spinner(f"Loading {sym} ({TF_DISPLAY.get(tf,tf)})…"):
        try: df = download_data(sym, tf)
        except Exception as e: st.error(f"Download error: {e}"); return
        if df.empty: st.error(f"No data for **{sym}** on **{TF_DISPLAY.get(tf,tf)}**"); return
        if len(df) < 50: st.warning(f"Only {len(df)} candles. Try a longer timeframe."); return

        try:
            indicator = NAUQuantumAlphaIndicator()
            df = indicator.compute(df)
        except Exception as e:
            st.error(f"Indicator error: {e}")
            import traceback; st.code(traceback.format_exc()); return

        vc = {
            'bg_color': st.session_state.bg_color, 'text_color': '#D1D4DC', 'grid_color': '#1E222D',
            'up_color': st.session_state.up_color, 'down_color': st.session_state.down_color,
            'signal_line_color': st.session_state.signal_line_color,
            'long_color': st.session_state.long_color, 'short_color': st.session_state.short_color,
            'kalman_color': st.session_state.kalman_color,
            'volume_up_color': f'rgba({_hex_rgb(st.session_state.up_color)},0.5)',
            'volume_down_color': f'rgba({_hex_rgb(st.session_state.down_color)},0.5)',
            'candle_border_up': st.session_state.up_color,
            'candle_border_down': st.session_state.down_color,
            'candle_wick_up': st.session_state.up_color,
            'candle_wick_down': st.session_state.down_color,
            'font_size': st.session_state.font_size,
            'line_width': st.session_state.line_width,
            'signal_line_width': st.session_state.signal_line_width,
            'confidence_opacity': 0.3,
            'show_volume': st.session_state.show_volume,
            'show_kalman': st.session_state.show_kalman,
            'show_signals': st.session_state.show_signals,
            'show_fractals': st.session_state.show_fractals,
            'show_order_blocks': True, 'show_fvg': True, 'show_structure': True,
            'show_regime': st.session_state.show_regime,
            'show_confidence': st.session_state.show_confidence,
            'show_factor_panel': st.session_state.show_factor_panel,
            'marker_font_size': st.session_state.marker_font_size,
        }

        try:
            html = generate_html_chart(df, visual_config=vc, title=f"{sym} · {TF_DISPLAY.get(tf,tf)}")
            st.components.v1.html(html, height=980, scrolling=False)
        except Exception as e: st.error(f"Chart error: {e}"); return

        # Metrics
        latest = df.iloc[-1]; prev = df.iloc[-2] if len(df)>1 else latest
        sig = float(latest["NAU_Signal"]); sig_p = float(prev["NAU_Signal"])
        conf = float(latest["NAU_Confidence"])*100
        regime = {0:"🟢 BULL",1:"🔴 BEAR",2:"🟡 RANGE"}.get(int(latest["NAU_Regime"]),"🟡 RANGE")
        price = float(latest["Close"]); price_p = float(prev["Close"])
        pct = (price-price_p)/price_p*100

        m1,m2,m3,m4,m5 = st.columns(5)
        m1.metric("Price", f"${price:.2f}", f"{pct:+.2f}%")
        m2.metric("NAU Signal", f"{sig:.1f}", f"{sig-sig_p:+.1f}")
        m3.metric("Confidence", f"{conf:.1f}%")
        m4.metric("Candles", len(df))
        m5.metric("Regime", regime)

        if conf/100 > st.session_state.conf_threshold/100:
            if sig > 20: st.success(f"✅ **STRONG LONG** — Score: {sig:.1f} | Conf: {conf:.0f}%")
            elif sig < -20: st.error(f"❌ **STRONG SHORT** — Score: {sig:.1f} | Conf: {conf:.0f}%")

run()
st_autorefresh(interval=st.session_state.refresh_sec * 1000, limit=None, key="datarefresh")
