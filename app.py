"""
Stock Screener — Vivaan Nanda
Streamlit app with yfinance, scoring, and filtering.
Run: streamlit run app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Stock Screener · Vivaan Nanda",
    page_icon="📈",
    layout="wide",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #0d0d0d; }
  [data-testid="stSidebar"] { background: #111; border-right: 1px solid #222; }
  h1 { font-size: 1.6rem !important; font-weight: 600 !important; letter-spacing: -0.5px; }
  .metric-card {
    background: #181818;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
  }
  .metric-label { font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
  .metric-value { font-size: 28px; font-weight: 600; color: #f0f0f0; }
  .metric-sub   { font-size: 11px; color: #555; margin-top: 2px; }
  .stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Ticker Universe ────────────────────────────────────────────────────────
TICKERS = {
    "Tech":       ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "CRM", "ADBE"],
    "Finance":    ["JPM", "GS", "MS", "BAC", "WFC", "BLK", "SCHW"],
    "Retail":     ["TGT", "WMT", "COST", "AMZN", "HD", "LOW"],
    "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY"],
    "Energy":     ["XOM", "CVX", "COP", "SLB"],
}

ALL_TICKERS = [t for tickers in TICKERS.values() for t in tickers]

# ── Scoring ────────────────────────────────────────────────────────────────
def calc_score(row):
    scores = []
    def add(val, best, worst, lower_better=True):
        if pd.isna(val):
            return
        norm = max(0.0, min(1.0, (val - worst) / (best - worst))) if lower_better \
               else max(0.0, min(1.0, (val - worst) / (best - worst)))
        scores.append(norm * 100)

    add(row.get("P/E"),          8,   55,  lower_better=True)
    add(row.get("EV/EBITDA"),    4,   35,  lower_better=True)
    add(row.get("P/B"),          0.5, 20,  lower_better=True)
    add(row.get("D/E"),          0,   5,   lower_better=True)
    add(row.get("Profit Margin"),0.35, 0,  lower_better=False)
    add(row.get("Rev Growth"),   0.4, -0.1,lower_better=False)

    return round(sum(scores) / len(scores)) if scores else 0

# ── Data Fetching ──────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def fetch_all(tickers):
    rows = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            sector = next((s for s, lst in TICKERS.items() if ticker in lst), "Other")
            rows.append({
                "Ticker":        ticker,
                "Name":          info.get("shortName", ticker)[:22],
                "Sector":        sector,
                "Price":         info.get("currentPrice") or info.get("regularMarketPrice"),
                "Mkt Cap ($B)":  round(info.get("marketCap", 0) / 1e9, 1) if info.get("marketCap") else None,
                "P/E":           info.get("trailingPE"),
                "EV/EBITDA":     info.get("enterpriseToEbitda"),
                "P/B":           info.get("priceToBook"),
                "D/E":           info.get("debtToEquity"),
                "Profit Margin": info.get("profitMargins"),
                "Rev Growth":    info.get("revenueGrowth"),
            })
        except Exception:
            pass
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["Score"] = df.apply(calc_score, axis=1)
    return df

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Screener Settings")

    selected_sectors = st.multiselect(
        "Sectors", list(TICKERS.keys()), default=list(TICKERS.keys())
    )

    custom_input = st.text_input(
        "Add custom tickers (comma-separated)", placeholder="e.g. TSLA, NFLX, SPOT"
    )

    st.markdown("---")
    st.markdown("**Valuation Filters**")
    max_pe      = st.slider("Max P/E",          5,  80,  35)
    max_ev      = st.slider("Max EV/EBITDA",    2,  50,  20)
    max_pb      = st.slider("Max P/B",          0.5,25.0, 8.0, step=0.5)

    st.markdown("**Quality Filters**")
    max_de      = st.slider("Max D/E",          0.0, 6.0, 2.0, step=0.1)
    min_margin  = st.slider("Min Profit Margin %", 0, 40, 8)
    min_growth  = st.slider("Min Rev Growth %", -10, 40, 3)

    st.markdown("---")
    st.markdown("**Sort By**")
    sort_col = st.selectbox("Column", ["Score", "P/E", "EV/EBITDA", "P/B", "D/E", "Profit Margin", "Rev Growth", "Mkt Cap ($B)"])
    sort_asc = st.checkbox("Ascending", value=False)

    refresh = st.button("🔄 Refresh Data", use_container_width=True)
    if refresh:
        st.cache_data.clear()

# ── Load Data ──────────────────────────────────────────────────────────────
active_tickers = [t for s, lst in TICKERS.items() if s in selected_sectors for t in lst]

if custom_input.strip():
    extras = [t.strip().upper() for t in custom_input.split(",") if t.strip()]
    active_tickers = list(set(active_tickers + extras))

with st.spinner(f"Fetching data for {len(active_tickers)} tickers..."):
    df = fetch_all(tuple(active_tickers))

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("# 📈 Stock Screener")
st.markdown(f"<span style='color:#555;font-size:13px;'>Live data via Yahoo Finance · {len(df)} tickers loaded</span>", unsafe_allow_html=True)
st.markdown("")

if df.empty:
    st.error("No data loaded. Check ticker list or try refreshing.")
    st.stop()

# ── Apply Filters ──────────────────────────────────────────────────────────
mask = pd.Series([True] * len(df), index=df.index)
mask &= (df["P/E"].isna()          | (df["P/E"]           <= max_pe))
mask &= (df["EV/EBITDA"].isna()    | (df["EV/EBITDA"]     <= max_ev))
mask &= (df["P/B"].isna()          | (df["P/B"]            <= max_pb))
mask &= (df["D/E"].isna()          | (df["D/E"]            <= max_de))
mask &= (df["Profit Margin"].isna()| (df["Profit Margin"] >= min_margin / 100))
mask &= (df["Rev Growth"].isna()   | (df["Rev Growth"]    >= min_growth / 100))

df_pass = df[mask].copy()
df_fail = df[~mask].copy()

# ── Summary Cards ──────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Universe</div>
      <div class="metric-value">{len(df)}</div>
      <div class="metric-sub">tickers tracked</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Passing Filters</div>
      <div class="metric-value" style="color:{'#4ade80' if len(df_pass)>0 else '#f87171'};">{len(df_pass)}</div>
      <div class="metric-sub">of {len(df)} screened</div>
    </div>""", unsafe_allow_html=True)

with c3:
    avg = round(df_pass["Score"].mean()) if len(df_pass) else 0
    color = "#4ade80" if avg >= 60 else "#facc15" if avg >= 40 else "#f87171"
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Avg Score</div>
      <div class="metric-value" style="color:{color};">{avg}</div>
      <div class="metric-sub">composite 0–100</div>
    </div>""", unsafe_allow_html=True)

with c4:
    if len(df_pass):
        top = df_pass.loc[df_pass["Score"].idxmax()]
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">Top Pick</div>
          <div class="metric-value" style="color:#60a5fa;">{top['Ticker']}</div>
          <div class="metric-sub">score {top['Score']} · {top['Sector']}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div class="metric-card">
          <div class="metric-label">Top Pick</div>
          <div class="metric-value">—</div>
          <div class="metric-sub">no results</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Results", "📊 Charts", "🗃️ Full Universe"])

# ── Tab 1: Results Table ───────────────────────────────────────────────────
with tab1:
    if df_pass.empty:
        st.warning("No stocks match current filters. Try loosening the sliders.")
    else:
        display = df_pass.sort_values(sort_col, ascending=sort_asc).reset_index(drop=True)
        display.index += 1

        def fmt_pct(v):
            if pd.isna(v): return "—"
            return f"{v*100:.1f}%"

        def fmt_num(v, dec=1):
            if pd.isna(v): return "—"
            return f"{v:.{dec}f}"

        display_fmt = display.copy()
        display_fmt["Price"]         = display_fmt["Price"].apply(lambda v: f"${v:.2f}" if pd.notna(v) else "—")
        display_fmt["Mkt Cap ($B)"]  = display_fmt["Mkt Cap ($B)"].apply(lambda v: f"${v:.1f}B" if pd.notna(v) else "—")
        display_fmt["P/E"]           = display_fmt["P/E"].apply(lambda v: fmt_num(v))
        display_fmt["EV/EBITDA"]     = display_fmt["EV/EBITDA"].apply(lambda v: fmt_num(v))
        display_fmt["P/B"]           = display_fmt["P/B"].apply(lambda v: fmt_num(v))
        display_fmt["D/E"]           = display_fmt["D/E"].apply(lambda v: fmt_num(v))
        display_fmt["Profit Margin"] = display_fmt["Profit Margin"].apply(fmt_pct)
        display_fmt["Rev Growth"]    = display_fmt["Rev Growth"].apply(fmt_pct)

        st.dataframe(
            display_fmt[["Ticker","Name","Sector","Price","Mkt Cap ($B)","P/E","EV/EBITDA","P/B","D/E","Profit Margin","Rev Growth","Score"]],
            use_container_width=True,
            height=min(60 + len(display_fmt) * 35, 600),
        )

        csv = display.to_csv(index=False).encode()
        st.download_button("⬇️ Export CSV", csv, "screener_results.csv", "text/csv")

# ── Tab 2: Charts ──────────────────────────────────────────────────────────
with tab2:
    if df_pass.empty:
        st.info("No passing stocks to chart.")
    else:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Score Rankings**")
            top_n = df_pass.sort_values("Score", ascending=False).head(10)
            colors = ["#4ade80" if s >= 65 else "#facc15" if s >= 45 else "#f87171" for s in top_n["Score"]]
            fig1 = go.Figure(go.Bar(
                x=top_n["Ticker"], y=top_n["Score"],
                marker_color=colors, text=top_n["Score"],
                textposition="outside",
            ))
            fig1.update_layout(
                paper_bgcolor="#181818", plot_bgcolor="#181818",
                font_color="#aaa", margin=dict(t=20,b=20,l=10,r=10),
                yaxis=dict(range=[0,105], gridcolor="#222"),
                xaxis=dict(gridcolor="#222"),
                showlegend=False, height=300,
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_b:
            st.markdown("**P/E vs Profit Margin**")
            scatter_df = df_pass.dropna(subset=["P/E","Profit Margin"])
            fig2 = px.scatter(
                scatter_df, x="P/E", y="Profit Margin",
                text="Ticker", color="Sector",
                size="Score", size_max=25,
                hover_data=["Name","Score","EV/EBITDA"],
            )
            fig2.update_traces(textposition="top center", textfont_size=10)
            fig2.update_layout(
                paper_bgcolor="#181818", plot_bgcolor="#181818",
                font_color="#aaa", margin=dict(t=20,b=20,l=10,r=10),
                xaxis=dict(gridcolor="#222"),
                yaxis=dict(gridcolor="#222", tickformat=".0%"),
                height=300, legend=dict(font_size=10),
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Sector Breakdown — Passing Stocks**")
        sector_counts = df_pass["Sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector","Count"]
        fig3 = px.bar(
            sector_counts, x="Sector", y="Count",
            color="Sector", text="Count",
        )
        fig3.update_layout(
            paper_bgcolor="#181818", plot_bgcolor="#181818",
            font_color="#aaa", margin=dict(t=20,b=20,l=10,r=10),
            xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
            showlegend=False, height=250,
        )
        st.plotly_chart(fig3, use_container_width=True)

# ── Tab 3: Full Universe ───────────────────────────────────────────────────
with tab3:
    st.markdown("All tickers — passing stocks highlighted.")
    all_display = df.sort_values("Score", ascending=False).reset_index(drop=True)
    all_display.index += 1

    def highlight_pass(row):
        color = "background-color: #1a2e1a;" if row["Score"] >= df_pass["Score"].min() if not df_pass.empty else 0 else ""
        return [color] * len(row)

    st.dataframe(
        all_display[["Ticker","Name","Sector","P/E","EV/EBITDA","P/B","D/E","Profit Margin","Rev Growth","Score"]],
        use_container_width=True,
        height=500,
    )

    csv_all = all_display.to_csv(index=False).encode()
    st.download_button("⬇️ Export Full Universe CSV", csv_all, "screener_universe.csv", "text/csv")

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<span style='color:#444;font-size:12px;'>Built by Vivaan Nanda · Data via Yahoo Finance (yfinance) · Not financial advice</span>",
    unsafe_allow_html=True
)
