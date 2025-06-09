import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Value Investing Framework", layout="wide")
st.title("📊 Graham-Dodd Value Investing Score (100-point)")

ticker_input = st.text_input("Enter a stock ticker (e.g. AAPL, VOD.L, TSLA):")

def normalize_score(actual, target, weight, better_lower=True):
    if actual in [None, 0]:
        return 0
    try:
        score = (1 - abs(actual - target) / target) if better_lower else (actual / target)
        score = max(0, min(1, score))
        return score * weight
    except:
        return 0

def calculate_score(info, hist, stock):
    weights = {
        "pe": 15, "pb": 10, "dividend": 10, "market_cap": 10,
        "eps_growth": 15, "price_growth": 10, "de_ratio": 10,
        "roe": 10, "current_ratio": 5, "fcf": 5
    }
    breakdown = {}

    # Pull base metrics
    price = info.get("currentPrice")
    eps = info.get("earningsPerShare")
    pe = info.get("trailingPE") or info.get("forwardPE")

    # If EPS missing or zero, try quarterly earnings EPS as fallback
    if (eps is None or eps == 0):
        try:
            eps_quarterly = stock.quarterly_earnings
            if eps_quarterly is not None and not eps_quarterly.empty:
                eps_latest = eps_quarterly['Earnings'][-1]
                if eps_latest and eps_latest > 0:
                    eps = eps_latest
        except Exception:
            pass

    # If PE still missing and EPS available, calculate manually
    if not pe and eps and eps > 0 and price:
        try:
            pe = price / eps
        except:
            pe = None

    pb = info.get("priceToBook")
    dividend = (info.get("dividendYield") or 0) * 100
    market_cap = info.get("marketCap")
    roe = info.get("returnOnEquity")
    de_ratio = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")
    fcf = info.get("freeCashflow")
    eps_growth = info.get("earningsQuarterlyGrowth")

    # Compute price growth over 10 years
    price_growth_score = 0
    if not hist.empty:
        try:
            price_growth = hist["Close"].iloc[-1] / hist["Close"].iloc[0]
            price_growth_score = normalize_score(price_growth, 2.0, weights["price_growth"], better_lower=False)
        except:
            pass

    # Score all criteria
    breakdown["P/E Ratio"] = round(normalize_score(pe, 15, weights["pe"], better_lower=True), 2)
    breakdown["P/B Ratio"] = round(normalize_score(pb, 1.5, weights["pb"], better_lower=True), 2)
    breakdown["Dividend Yield (%)"] = round(normalize_score(dividend, 2.0, weights["dividend"], better_lower=False), 2)
    breakdown["Market Cap"] = round(normalize_score(market_cap, 2e9, weights["market_cap"], better_lower=False), 2)
    breakdown["10Y Price Growth"] = round(price_growth_score, 2)
    breakdown["EPS Growth"] = round(normalize_score(eps_growth, 0.15, weights["eps_growth"], better_lower=False), 2)
    breakdown["Debt/Equity"] = round(normalize_score(de_ratio, 1.0, weights["de_ratio"], better_lower=True), 2)
    breakdown["Return on Equity"] = round(normalize_score(roe, 0.15, weights["roe"], better_lower=False), 2)
    breakdown["Current Ratio"] = round(normalize_score(current_ratio, 1.5, weights["current_ratio"], better_lower=False), 2)
    breakdown["Free Cash Flow"] = round(normalize_score(fcf, 0, weights["fcf"], better_lower=False), 2)

    total_score = int(sum(breakdown.values()))
    return total_score, breakdown, {
        "Trailing PE": info.get("trailingPE"),
        "Forward PE": info.get("forwardPE"),
        "EPS (info)": info.get("earningsPerShare"),
        "EPS (quarterly latest)": eps if eps != info.get("earningsPerShare") else "N/A",
        "Price": price,
        "Raw Free Cash Flow": fcf
    }

if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        hist = stock.history(period="10y")

        st.subheader(f"📈 {info.get('longName', ticker_input)}")
        st.write(info.get("longBusinessSummary", "No summary available."))

        score, breakdown, debug_info = calculate_score(info, hist, stock)
        st.metric("💯 Graham Score (0–100)", score)

        with st.expander("📋 Score Breakdown"):
            for k, v in breakdown.items():
                val_display = "N/A" if v == 0 else f"{v:.2f}"
                st.write(f"**{k}**: {val_display}")

        with st.expander("🧪 Debug Metrics"):
            st.json(debug_info)

        with st.expander("📊 Price History"):
            if not hist.empty:
                st.line_chart(hist["Close"])

    except Exception as e:
        st.error(f"⚠️ Error loading data for {ticker_input}: {e}")
