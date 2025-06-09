
import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Value Investing (Graham-Dodd Score)", layout="wide")
st.title("📊 Value Investing Framework — 100 Point Score")

ticker_input = st.text_input("Enter a stock ticker (e.g. AAPL, TSLA, BP.L):")

def normalize_score(actual, target, weight, better_lower=True):
    if actual is None:
        return 0
    try:
        score = max(0, 1 - abs(actual - target) / target) if better_lower else min(1, actual / target)
        return score * weight
    except:
        return 0

def calculate_score(info, hist):
    total_score = 0
    breakdown = {}

    # Criteria weights out of 100
    weights = {
        "pe": 15,
        "pb": 10,
        "dividend": 10,
        "market_cap": 10,
        "eps_growth": 15,
        "price_growth": 10,
        "de_ratio": 10,
        "roe": 10,
        "current_ratio": 5,
        "fcf": 5
    }

    pe = info.get("trailingPE")
    pb = info.get("priceToBook")
    dividend = info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
    market_cap = info.get("marketCap", 0)
    roe = info.get("returnOnEquity", 0)
    de_ratio = info.get("debtToEquity", 0)
    current_ratio = info.get("currentRatio", 0)
    fcf = info.get("freeCashflow", 0)

    # P/E
    score_pe = normalize_score(pe, 15, weights["pe"], better_lower=True)
    breakdown["P/E Ratio"] = round(score_pe, 2)

    # P/B
    score_pb = normalize_score(pb, 1.5, weights["pb"], better_lower=True)
    breakdown["P/B Ratio"] = round(score_pb, 2)

    # Dividend Yield
    score_dividend = normalize_score(dividend, 2.0, weights["dividend"], better_lower=False)
    breakdown["Dividend Yield (%)"] = round(score_dividend, 2)

    # Market Cap (prefers > $2B)
    score_market_cap = normalize_score(market_cap, 2_000_000_000, weights["market_cap"], better_lower=False)
    breakdown["Market Cap"] = round(score_market_cap, 2)

    # 10-Year Price Growth
    price_growth_score = 0
    if not hist.empty:
        try:
            price_growth = hist["Close"].iloc[-1] / hist["Close"].iloc[0]
            price_growth_score = normalize_score(price_growth, 2.0, weights["price_growth"], better_lower=False)
        except:
            pass
    breakdown["10Y Price Growth"] = round(price_growth_score, 2)

    # EPS Growth (if available)
    eps_growth = info.get("earningsQuarterlyGrowth", 0)
    score_eps_growth = normalize_score(eps_growth, 0.15, weights["eps_growth"], better_lower=False)
    breakdown["EPS Growth"] = round(score_eps_growth, 2)

    # Debt/Equity
    score_de = normalize_score(de_ratio, 1.0, weights["de_ratio"], better_lower=True)
    breakdown["Debt/Equity"] = round(score_de, 2)

    # ROE
    score_roe = normalize_score(roe, 0.15, weights["roe"], better_lower=False)
    breakdown["Return on Equity"] = round(score_roe, 2)

    # Current Ratio
    score_current = normalize_score(current_ratio, 1.5, weights["current_ratio"], better_lower=False)
    breakdown["Current Ratio"] = round(score_current, 2)

    # Free Cash Flow (estimation)
    score_fcf = normalize_score(fcf, 0, weights["fcf"], better_lower=False)
    breakdown["Free Cash Flow"] = round(score_fcf, 2)

    total_score = sum(breakdown.values())
    return round(total_score), breakdown

if ticker_input:
    try:
        stock = yf.Ticker(ticker_input)
        info = stock.info
        hist = stock.history(period="10y")
        st.subheader(f"📈 {info.get('longName', ticker_input)}")
        st.write(info.get("longBusinessSummary", "No summary available."))

        score, details = calculate_score(info, hist)
        st.metric("💯 Value Score (0–100)", score)

        with st.expander("📋 Score Breakdown"):
            for k, v in details.items():
                st.write(f"**{k}**: {v:.2f}")

        with st.expander("📊 Price History"):
            if not hist.empty:
                st.line_chart(hist["Close"])

    except Exception as e:
        st.error(f"Error loading data: {e}")
