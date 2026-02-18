import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from streamlit_autorefresh import st_autorefresh
from nau_quantum_engine import NAUQuantumAlphaIndicator, generate_html_chart

st.set_page_config(page_title="NAU Quantum Alpha Live", layout="wide")
st.title("🚀 NAU Quantum Alpha Engine v3.0 - Dashboard en Tiempo Real")

# ── Timeframe → period mapping (yfinance limits) ──────────────────────────────
PERIOD_MAP = {
    "1m":  "7d",
    "5m":  "60d",
    "15m": "60d",
    "30m": "60d",
    "1h":  "730d",
    "4h":  "730d",
    "1d":  "2y",
}

# Panel lateral de configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    symbol = st.text_input("Símbolo (ej: AAPL, BTC-USD)", value="AAPL")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "30m", "1h", "4h", "1d"])
    refresh_seconds = st.slider("Actualizar cada (segundos)", 30, 300, 60)
    confidence_threshold = st.slider("Umbral de confianza (%)", 50, 90, 60)


# ── Helper: download + flatten yfinance MultiIndex ────────────────────────────
def download_data(sym: str, interval: str) -> pd.DataFrame:
    """Download OHLCV from yfinance and return a clean flat DataFrame."""
    period = PERIOD_MAP.get(interval, "60d")
    raw = yf.download(
        sym,
        period=period,
        interval=interval,
        prepost=False,
        auto_adjust=True,
        progress=False,
    )
    if raw.empty:
        return pd.DataFrame()

    # ── Flatten MultiIndex columns (yfinance >= 0.2.x returns them) ──
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    # Rename to standard names
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
    # Ensure plain 1-D float arrays (squeeze kills any residual MultiIndex)
    for col in needed:
        df[col] = pd.to_numeric(df[col].squeeze(), errors="coerce")
    df = df.dropna(subset=["Open", "High", "Low", "Close"])
    return df


# ── Main analysis ─────────────────────────────────────────────────────────────
def run_live_analysis():
    with st.spinner(f"Descargando {symbol} ({timeframe}) …"):
        try:
            df = download_data(symbol.strip().upper(), timeframe)
        except Exception as exc:
            st.error(f"Error al descargar datos: {exc}")
            st.info("Prueba con AAPL y timeframe 1h")
            return

        if df.empty:
            st.error("No se obtuvieron datos. Verifica el símbolo o el timeframe.")
            return

        if len(df) < 50:
            st.warning(
                f"Solo {len(df)} velas para {symbol} ({timeframe}). "
                "Usa un timeframe mayor (1h o 1d) para más historia."
            )
            return

        try:
            indicator = NAUQuantumAlphaIndicator()
            df = indicator.compute(df)
        except Exception as exc:
            st.error(f"Error calculando el indicador: {exc}")
            import traceback
            st.code(traceback.format_exc(), language="python")
            return

        try:
            html_chart = generate_html_chart(df, title=f"{symbol} · {timeframe}")
            st.components.v1.html(html_chart, height=980, scrolling=False)
        except Exception as exc:
            st.error(f"Error generando el gráfico: {exc}")
            return

        latest   = df.iloc[-1]
        prev     = df.iloc[-2] if len(df) > 1 else latest
        sig_now  = float(latest["NAU_Signal"])
        sig_prev = float(prev["NAU_Signal"])
        conf_now = float(latest["NAU_Confidence"]) * 100
        regime_text = {0: "🟢 BULL", 1: "🔴 BEAR", 2: "🟡 RANGE"}.get(
            int(latest["NAU_Regime"]), "🟡 RANGE"
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("NAU Signal",          f"{sig_now:.1f}",  f"{sig_now - sig_prev:+.1f}")
        col2.metric("Confianza Bayesiana", f"{conf_now:.1f}%")
        col3.metric("Velas analizadas",    len(df))
        col4.metric("Régimen de Mercado",  regime_text)

        if conf_now / 100 > confidence_threshold / 100:
            if sig_now > 20:
                st.success("✅ SEÑAL FUERTE LONG — ¡Considera comprar!")
            elif sig_now < -20:
                st.error("❌ SEÑAL FUERTE SHORT — ¡Considera vender!")


run_live_analysis()
st_autorefresh(interval=refresh_seconds * 1000, limit=None, key="datarefresh")
