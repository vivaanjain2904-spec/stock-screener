# Stock Screener — Vivaan Nanda

Fundamental stock screener built with Streamlit + yfinance.
Filters by P/E, EV/EBITDA, P/B, D/E, Profit Margin, and Revenue Growth.
Scores and ranks every stock on a composite 0–100 scale.

---

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at http://localhost:8501

---

## Deploy to Streamlit Community Cloud (Free)

1. Push this folder to a GitHub repo (public or private)
2. Go to https://share.streamlit.io
3. Click **New app**
4. Select your repo, branch (main), and set **Main file path** to `app.py`
5. Click **Deploy** — live in ~2 minutes

Your app will be live at:
`https://<your-username>-stock-screener-<random>.streamlit.app`

You can share this URL on your resume or LinkedIn.

---

## Features

- Live data via Yahoo Finance (cached 30 min)
- Composite scoring system (P/E, EV/EBITDA, P/B, D/E, Margin, Growth)
- Interactive sidebar filters with sliders
- Sector filtering + custom ticker input
- Three views: Results, Charts (scatter + bar), Full Universe
- CSV export
- Scatter plot: P/E vs Profit Margin, sized by Score
- Score ranking bar chart

---

## Stack

- **Streamlit** — UI framework
- **yfinance** — Yahoo Finance data
- **Plotly** — interactive charts
- **Pandas** — data wrangling
