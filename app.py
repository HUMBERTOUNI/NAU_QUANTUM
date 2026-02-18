import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
from nau_quantum_engine import NAUQuantumAlphaIndicator, generate_html_chart
import json

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="NAU Quantum v3.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",   # sidebar hidden by default
)

# ── Hide Streamlit chrome for a cleaner look ──
st.markdown("""
<style>
    /* Hide hamburger, header, footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Tighter padding */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Dark scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0a0e17; }
    ::-webkit-scrollbar-thumb { background: #1e2a3a; border-radius: 3px; }

    /* Style the selectbox to look like TradingView search */
    div[data-testid="stSelectbox"] > div > div {
        background: #131722 !important;
        border: 1px solid #2a2e39 !important;
        color: #e8ecf1 !important;
        border-radius: 6px;
    }

    /* Sidebar dark styling */
    section[data-testid="stSidebar"] {
        background: #0a1220 !important;
        border-right: 1px solid #1e2a3a;
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #c8d0dc; }

    /* Custom metric styling */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace;
    }
</style>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# SYMBOL DATABASE — Searchable by name or ticker
# ══════════════════════════════════════════════════════════════════
SYMBOLS = {
    # ── Technology ──
    "AAPL  ·  Apple Inc.": "AAPL",
    "MSFT  ·  Microsoft Corp.": "MSFT",
    "GOOGL  ·  Alphabet Inc.": "GOOGL",
    "AMZN  ·  Amazon.com Inc.": "AMZN",
    "NVDA  ·  NVIDIA Corp.": "NVDA",
    "META  ·  Meta Platforms": "META",
    "TSLA  ·  Tesla Inc.": "TSLA",
    "PLTR  ·  Palantir Technologies": "PLTR",
    "AMD  ·  Advanced Micro Devices": "AMD",
    "INTC  ·  Intel Corp.": "INTC",
    "NFLX  ·  Netflix Inc.": "NFLX",
    "CRM  ·  Salesforce Inc.": "CRM",
    "ORCL  ·  Oracle Corp.": "ORCL",
    "ADBE  ·  Adobe Inc.": "ADBE",
    "UBER  ·  Uber Technologies": "UBER",
    "SHOP  ·  Shopify Inc.": "SHOP",
    "SNOW  ·  Snowflake Inc.": "SNOW",
    "NET  ·  Cloudflare Inc.": "NET",
    "CRWD  ·  CrowdStrike Holdings": "CRWD",
    "PANW  ·  Palo Alto Networks": "PANW",
    "AVGO  ·  Broadcom Inc.": "AVGO",
    "MU  ·  Micron Technology": "MU",
    "QCOM  ·  Qualcomm Inc.": "QCOM",
    "ARM  ·  ARM Holdings": "ARM",
    "SMCI  ·  Super Micro Computer": "SMCI",
    # ── Finance ──
    "JPM  ·  JPMorgan Chase": "JPM",
    "BAC  ·  Bank of America": "BAC",
    "GS  ·  Goldman Sachs": "GS",
    "MS  ·  Morgan Stanley": "MS",
    "V  ·  Visa Inc.": "V",
    "MA  ·  Mastercard Inc.": "MA",
    "PYPL  ·  PayPal Holdings": "PYPL",
    "COIN  ·  Coinbase Global": "COIN",
    "SQ  ·  Block Inc.": "SQ",
    "BRK-B  ·  Berkshire Hathaway": "BRK-B",
    # ── Healthcare ──
    "JNJ  ·  Johnson & Johnson": "JNJ",
    "UNH  ·  UnitedHealth Group": "UNH",
    "PFE  ·  Pfizer Inc.": "PFE",
    "LLY  ·  Eli Lilly": "LLY",
    "ABBV  ·  AbbVie Inc.": "ABBV",
    "MRK  ·  Merck & Co.": "MRK",
    # ── Energy ──
    "XOM  ·  Exxon Mobil": "XOM",
    "CVX  ·  Chevron Corp.": "CVX",
    "OXY  ·  Occidental Petroleum": "OXY",
    # ── Consumer / Retail ──
    "WMT  ·  Walmart Inc.": "WMT",
    "COST  ·  Costco Wholesale": "COST",
    "HD  ·  Home Depot": "HD",
    "DIS  ·  Walt Disney Co.": "DIS",
    "MCD  ·  McDonald's Corp.": "MCD",
    "SBUX  ·  Starbucks Corp.": "SBUX",
    "KO  ·  Coca-Cola Co.": "KO",
    "PEP  ·  PepsiCo Inc.": "PEP",
    "NKE  ·  Nike Inc.": "NKE",
    # ── Industrial / Other ──
    "BA  ·  Boeing Co.": "BA",
    "CAT  ·  Caterpillar Inc.": "CAT",
    "DE  ·  Deere & Co.": "DE",
    "LMT  ·  Lockheed Martin": "LMT",
    # ── Index ETFs ──
    "SPY  ·  S&P 500 ETF": "SPY",
    "QQQ  ·  Nasdaq 100 ETF": "QQQ",
    "DIA  ·  Dow Jones ETF": "DIA",
    "IWM  ·  Russell 2000 ETF": "IWM",
    "ARKK  ·  ARK Innovation ETF": "ARKK",
    "SOXX  ·  Semiconductor ETF": "SOXX",
    "XLF  ·  Financial Select ETF": "XLF",
    "XLE  ·  Energy Select ETF": "XLE",
    "XLK  ·  Technology Select ETF": "XLK",
    "XLV  ·  Healthcare Select ETF": "XLV",
    # ── Commodities ──
    "GLD  ·  Gold ETF (SPDR)": "GLD",
    "SLV  ·  Silver ETF (iShares)": "SLV",
    "USO  ·  Oil ETF": "USO",
    "GC=F  ·  Gold Futures": "GC=F",
    "CL=F  ·  Crude Oil Futures": "CL=F",
    "SI=F  ·  Silver Futures": "SI=F",
    # ── Crypto ──
    "BTC-USD  ·  Bitcoin": "BTC-USD",
    "ETH-USD  ·  Ethereum": "ETH-USD",
    "SOL-USD  ·  Solana": "SOL-USD",
    "BNB-USD  ·  Binance Coin": "BNB-USD",
    "XRP-USD  ·  Ripple": "XRP-USD",
    "ADA-USD  ·  Cardano": "ADA-USD",
    "DOGE-USD  ·  Dogecoin": "DOGE-USD",
    "AVAX-USD  ·  Avalanche": "AVAX-USD",
    # ── Forex ──
    "EURUSD=X  ·  EUR/USD": "EURUSD=X",
    "GBPUSD=X  ·  GBP/USD": "GBPUSD=X",
    "USDJPY=X  ·  USD/JPY": "USDJPY=X",
}

# Reverse lookup for default
SYMBOL_LABELS = {v: k for k, v in SYMBOLS.items()}


# ══════════════════════════════════════════════════════════════════
# TIMEFRAME CONFIG
# ══════════════════════════════════════════════════════════════════
PERIOD_MAP = {
    "1m": "7d", "5m": "60d", "15m": "60d", "30m": "60d",
    "1h": "730d", "4h": "730d", "1d": "2y",
}


# ══════════════════════════════════════════════════════════════════
# SESSION STATE — persistent settings
# ══════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        "symbol": "PLTR",
        "timeframe": "1d",
        "refresh_sec": 60,
        "conf_threshold": 60,
        # Visual settings
        "up_color": "#26A69A",
        "down_color": "#EF5350",
        "bg_color": "#131722",
        "kalman_color": "#FFD700",
        "signal_line_color": "#2196F3",
        "long_color": "#00E676",
        "short_color": "#FF1744",
        "font_size": 12,
        "line_width": 2,
        "signal_line_width": 2,
        "marker_font_size": 11,
        "show_volume": True,
        "show_kalman": True,
        "show_signals": True,
        "show_fractals": True,
        "show_regime": True,
        "show_confidence": True,
        "show_factor_panel": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ══════════════════════════════════════════════════════════════════
# SIDEBAR — Settings & Visual Customization
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 12px 0 8px 0;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size:18px; font-weight:700; color:#4a9eff; letter-spacing:2px;">⚡ NAU QUANTUM</span><br>
        <span style="font-family: 'JetBrains Mono', monospace; font-size:11px; color:#5a7a9a;">Settings & Customization</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Refresh & Threshold ──
    st.markdown("##### ⏱ Refresh")
    st.session_state.refresh_sec = st.slider(
        "Auto-refresh (seconds)", 30, 300,
        st.session_state.refresh_sec, key="slider_refresh"
    )
    st.session_state.conf_threshold = st.slider(
        "Confidence threshold (%)", 40, 95,
        st.session_state.conf_threshold, key="slider_conf"
    )

    st.divider()

    # ── Visual: Colors ──
    st.markdown("##### 🎨 Colors")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.up_color = st.color_picker(
            "Bullish", st.session_state.up_color, key="cp_up")
        st.session_state.kalman_color = st.color_picker(
            "Kalman", st.session_state.kalman_color, key="cp_kalman")
        st.session_state.long_color = st.color_picker(
            "Buy signal", st.session_state.long_color, key="cp_long")
    with c2:
        st.session_state.down_color = st.color_picker(
            "Bearish", st.session_state.down_color, key="cp_down")
        st.session_state.signal_line_color = st.color_picker(
            "Signal line", st.session_state.signal_line_color, key="cp_sig")
        st.session_state.short_color = st.color_picker(
            "Sell signal", st.session_state.short_color, key="cp_short")

    st.divider()

    # ── Visual: Sizes ──
    st.markdown("##### 📐 Sizes")
    st.session_state.font_size = st.slider(
        "Font size", 9, 18, st.session_state.font_size, key="sl_font")
    st.session_state.line_width = st.slider(
        "Line width", 1, 5, st.session_state.line_width, key="sl_lw")
    st.session_state.marker_font_size = st.slider(
        "Signal label size", 0, 16, st.session_state.marker_font_size,
        key="sl_marker", help="Set to 0 to hide signal labels completely")

    st.divider()

    # ── Toggles ──
    st.markdown("##### 👁 Show / Hide")
    st.session_state.show_volume = st.toggle("Volume", st.session_state.show_volume, key="t_vol")
    st.session_state.show_kalman = st.toggle("Kalman filter", st.session_state.show_kalman, key="t_kal")
    st.session_state.show_signals = st.toggle("Buy/Sell signals", st.session_state.show_signals, key="t_sig")
    st.session_state.show_regime = st.toggle("Regime shading", st.session_state.show_regime, key="t_reg")
    st.session_state.show_confidence = st.toggle("Confidence band", st.session_state.show_confidence, key="t_conf")
    st.session_state.show_factor_panel = st.toggle("Factor panel", st.session_state.show_factor_panel, key="t_fac")

    st.divider()

    # Reset button
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# TOP BAR — Symbol Search + Timeframe
# ══════════════════════════════════════════════════════════════════
top_col1, top_col2, top_col3, top_col4 = st.columns([3, 2, 2, 1])

with top_col1:
    # TradingView-style symbol search (searchable selectbox)
    current_label = SYMBOL_LABELS.get(
        st.session_state.symbol,
        f"{st.session_state.symbol}  ·  Custom"
    )
    selected_label = st.selectbox(
        "🔍 Symbol",
        options=list(SYMBOLS.keys()),
        index=list(SYMBOLS.keys()).index(current_label) if current_label in SYMBOLS else 0,
        key="symbol_search",
        label_visibility="collapsed",
        placeholder="Search symbol or company name...",
    )
    st.session_state.symbol = SYMBOLS[selected_label]

with top_col2:
    tf_options = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    st.session_state.timeframe = st.selectbox(
        "Timeframe",
        tf_options,
        index=tf_options.index(st.session_state.timeframe),
        key="tf_select",
        label_visibility="collapsed",
    )

with top_col3:
    # Manual custom symbol input
    custom = st.text_input(
        "Or type custom ticker",
        value="",
        placeholder="e.g. MARA, RIOT...",
        label_visibility="collapsed",
        key="custom_sym_input",
    )
    if custom.strip():
        st.session_state.symbol = custom.strip().upper()

with top_col4:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    settings_btn = st.button("⚙ Settings", use_container_width=True)
    if settings_btn:
        st.session_state.sidebar_open = True
        st.rerun()


# ══════════════════════════════════════════════════════════════════
# DATA DOWNLOAD
# ══════════════════════════════════════════════════════════════════
def download_data(sym: str, interval: str) -> pd.DataFrame:
    period = PERIOD_MAP.get(interval, "60d")
    raw = yf.download(
        sym, period=period, interval=interval,
        prepost=False, auto_adjust=True, progress=False,
    )
    if raw.empty:
        return pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    col_map = {}
    for c in raw.columns:
        lc = str(c).lower()
        if lc == "open":            col_map[c] = "Open"
        elif lc == "high":          col_map[c] = "High"
        elif lc == "low":           col_map[c] = "Low"
        elif lc in ("close", "adj close"): col_map[c] = "Close"
        elif lc == "volume":        col_map[c] = "Volume"
    raw = raw.rename(columns=col_map)

    needed = ["Open", "High", "Low", "Close", "Volume"]
    if any(c not in raw.columns for c in needed):
        return pd.DataFrame()

    df = raw[needed].copy()
    for col in needed:
        df[col] = pd.to_numeric(df[col].squeeze(), errors="coerce")
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return df


# ══════════════════════════════════════════════════════════════════
# MAIN ANALYSIS
# ══════════════════════════════════════════════════════════════════
def run_live_analysis():
    symbol = st.session_state.symbol
    timeframe = st.session_state.timeframe

    with st.spinner(f"Loading {symbol} ({timeframe}) …"):
        try:
            df = download_data(symbol, timeframe)
        except Exception as exc:
            st.error(f"Download error: {exc}")
            return

        if df.empty:
            st.error(f"No data for **{symbol}** on **{timeframe}**. Check the symbol or try a different timeframe.")
            return

        if len(df) < 50:
            st.warning(f"Only {len(df)} candles for {symbol} ({timeframe}). Try a longer timeframe (1h or 1d).")
            return

        try:
            indicator = NAUQuantumAlphaIndicator()
            df = indicator.compute(df)
        except Exception as exc:
            st.error(f"Indicator error: {exc}")
            import traceback
            st.code(traceback.format_exc(), language="python")
            return

        # ── Build visual_config from session state ──
        visual_config = {
            'bg_color': st.session_state.bg_color,
            'text_color': '#D1D4DC',
            'grid_color': '#1E222D',
            'up_color': st.session_state.up_color,
            'down_color': st.session_state.down_color,
            'signal_line_color': st.session_state.signal_line_color,
            'long_color': st.session_state.long_color,
            'short_color': st.session_state.short_color,
            'kalman_color': st.session_state.kalman_color,
            'volume_up_color': f'rgba({_hex_to_rgb(st.session_state.up_color)},0.5)',
            'volume_down_color': f'rgba({_hex_to_rgb(st.session_state.down_color)},0.5)',
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
            'show_order_blocks': True,
            'show_fvg': True,
            'show_structure': True,
            'show_regime': st.session_state.show_regime,
            'show_confidence': st.session_state.show_confidence,
            'show_factor_panel': st.session_state.show_factor_panel,
            'marker_font_size': st.session_state.marker_font_size,
        }

        try:
            html_chart = generate_html_chart(
                df,
                visual_config=visual_config,
                title=f"{symbol} · {timeframe}",
            )
            st.components.v1.html(html_chart, height=980, scrolling=False)
        except Exception as exc:
            st.error(f"Chart error: {exc}")
            return

        # ── Metrics bar ──
        latest = df.iloc[-1]
        prev   = df.iloc[-2] if len(df) > 1 else latest
        sig_now  = float(latest["NAU_Signal"])
        sig_prev = float(prev["NAU_Signal"])
        conf_now = float(latest["NAU_Confidence"]) * 100
        regime_text = {0: "🟢 BULL", 1: "🔴 BEAR", 2: "🟡 RANGE"}.get(
            int(latest["NAU_Regime"]), "🟡 RANGE"
        )
        price_now = float(latest["Close"])
        price_prev = float(prev["Close"])
        pct_change = ((price_now - price_prev) / price_prev * 100)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Price", f"${price_now:.2f}", f"{pct_change:+.2f}%")
        m2.metric("NAU Signal", f"{sig_now:.1f}", f"{sig_now - sig_prev:+.1f}")
        m3.metric("Confidence", f"{conf_now:.1f}%")
        m4.metric("Candles", len(df))
        m5.metric("Regime", regime_text)

        # ── Trade alerts ──
        if conf_now / 100 > st.session_state.conf_threshold / 100:
            if sig_now > 20:
                st.success(f"✅ **STRONG LONG SIGNAL** — NAU Score: {sig_now:.1f} | Confidence: {conf_now:.0f}%")
            elif sig_now < -20:
                st.error(f"❌ **STRONG SHORT SIGNAL** — NAU Score: {sig_now:.1f} | Confidence: {conf_now:.0f}%")


def _hex_to_rgb(hex_color: str) -> str:
    """Convert #RRGGBB to 'R,G,B' string."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return f"{r},{g},{b}"
    return "128,128,128"


# ── Run ──
run_live_analysis()
st_autorefresh(interval=st.session_state.refresh_sec * 1000, limit=None, key="datarefresh")

