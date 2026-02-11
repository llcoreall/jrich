import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from portfolio_manager import PortfolioManager
from market_data import MarketData
from analytics_engine import AnalyticsEngine
import time
import os
import numpy as np
from datetime import datetime

# --- Setup ---
st.set_page_config(page_title="Portfolio Manager", layout="wide", page_icon=None, initial_sidebar_state="collapsed")

# --- Authentication Logic ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

def login_page():
    # Login Page Style
    st.markdown("""
    <style>
        .stApp { background-color: #000000; }
        .login-box {
            max-width: 400px;
            margin: 100px auto;
            padding: 40px;
            border: 1px solid #333;
            background-color: #111;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 0 20px rgba(0,0,0,0.8);
        }
        .login-title {
            color: #D500F9;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 30px;
            text-shadow: 0 0 10px rgba(213, 0, 249, 0.4);
        }
        div[data-testid="stForm"] {
            border: 1px solid #222;
            background-color: #0a0a0a;
            padding: 30px;
            border-radius: 8px;
            width: 100%;
            max-width: 400px;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #D500F9; margin-bottom: 10px;'>PORTFOLIO MANAGER</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666; font-size: 12px; margin-bottom: 30px;'>ACCESS GRANT REQUIRED</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("ID")
            password = st.text_input("ACCESS CODE", type="password")
            
            submitted = st.form_submit_button("AUTHENTICATE", use_container_width=True)
            
            if submitted:
                # V50: Security Hardening (st.secrets)
                authenticated = False
                
                try:
                    # Check against secrets
                    if "passwords" in st.secrets:
                        # Direct lookup or section lookup
                        stored_pass = st.secrets["passwords"].get(username)
                        if stored_pass and password == stored_pass:
                            authenticated = True
                    else:
                        st.error("CONFIGURATION ERROR: 'passwords' section missing in secrets.")
                        return
                except FileNotFoundError:
                        st.error("SECURITY ERROR: secrets.toml not found. Deployment requires configuration.")
                        return
                except Exception as e:
                     # Fallback for dev/local if secrets are totally missing (though we created them)
                     # or specific error handling
                     st.error(f"AUTHENTICATION ERROR: {str(e)}")
                     return
                
                if authenticated:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = username
                    st.toast(f"ACCESS GRANTED: WELCOME COMMANDER {username.upper()}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: INVALID CREDENTIALS")

if not st.session_state["logged_in"]:
    login_page()
    st.stop() # Prevents running the rest of the app

# --- LOGGED IN DASHBOARD BELOW ---

# Add Logout Button in Sidebar (Will be rendered later but added to session logic)
def logout():
    st.session_state["logged_in"] = False
    st.session_state["user_id"] = None
    st.rerun()

# --- Custom CSS for Dystopian UI & Mobile Optimization (V42) ---
st.markdown("""
<meta name="theme-color" content="#050505">
<style>
    /* Main Background - Deepest Void */
    .stApp {
        background-color: #050505; /* Near Black */
        color: #E0E0E0;
    }
    
    /* V42: Mobile Optimization (iPhone 15 Pro & Others) */
    @media only screen and (max-width: 768px) {
        /* Adjust padding for Dynamic Island & Bottom Swipe Bar */
        .main .block-container {
            padding-top: 60px !important;    /* Safe Area Top */
            padding-bottom: 80px !important; /* Safe Area Bottom */
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        /* Increase Touch Targets */
        button {
            min-height: 48px !important;
            min-width: 48px !important;
        }
        
        /* V48: Fix Tab Overflow/Alignment on Mobile */
        .stTabs [data-baseweb="tab"] {
            min-height: 44px !important;
            padding: 4px 10px !important; /* Reduced padding */
            font-size: 14px !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            max-width: 120px !important; /* Prevent expansion */
            flex: 0 0 auto !important; /* Ensure they don't shrink weirdly */
        }
        
        /* Ensure horizontal scroll for tables */
        [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }
        
        /* Stack columns on very small screens */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 auto !important;
            min-width: 100% !important;
        }
        
        /* V44: Force Dark Mode on Mobile Tables & Buttons */
        [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
            background-color: #121212 !important;
            color: white !important;
        }
        div[data-testid="stDataFrame"] > div, div[data-testid="stDataEditor"] > div {
            background-color: #121212 !important;
            color: white !important;
        }
        
        /* Force Buttons Dark */
        .stButton > button {
            background-color: #1F1F1F !important;
            color: #E0E0E0 !important;
            border: 1px solid #333 !important;
        }
    }
    
    /* V46: Reverted Aggressive Table CSS (Caused Rendering Issue) */
    /* We will rely on config.toml for Dark Mode */
    
    /* Global Button Style */
    
    /* Global Button Style */
    .stButton > button {
        background-color: #1F1F1F;
        color: #E0E0E0;
        border: 1px solid #333;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #D500F9;
        color: #D500F9;
    }

    /* Metrics - Electric Violet */
    div[data-testid="stMetricValue"] {
        color: #D500F9 !important; 
        text-shadow: 0 0 10px rgba(213, 0, 249, 0.4);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        background-color: #1F1F1F;
        color: #9E9E9E;
        border: 1px solid #333;
        padding: 10px 16px; /* Larger tap area */
    }
    .stTabs [aria-selected="true"] {
        background-color: #050505;
        color: #D500F9 !important;
        border-bottom: 2px solid #D500F9;
        border-top: 1px solid #D500F9;
    }
    
    /* Inputs */
    .stNumberInput label, .stTextInput label, .stSelectbox label {
        color: #FFFFFF !important; /* V45: Force Labels White for Login/Mobile */
    }
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #121212 !important;
        color: #FFF !important;
        border: 1px solid #333 !important;
        min-height: 44px; /* Touch friendly */
    }

    /* News Items */
    .news-item {
        margin-bottom: 6px;
        padding-bottom: 6px;
        border-bottom: 1px solid #222;
    }
    .news-title {
        font-size: 13px;
        font-weight: 600;
        color: #EEE;
        margin-bottom: 2px;
        line-height: 1.3;
    }
    .news-meta {
        font-size: 10px;
        color: #777;
    }
    .news-link {
        font-size: 10px;
        color: #AA00FF; /* Deep Purple Link */
        text-decoration: none;
    }
    .news-link:hover {
        color: #D500F9;
        text-decoration: underline;
    }
    
    /* V37: Metric Pill Styles */
    .metric-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 16px;
        margin-left: 10px;
    }
    .pill-negative {
        background-color: #3e1f1f; /* Dark Red Background */
        color: #ff6b6b; /* Soft Red Text */
        border: 1px solid #ff6b6b;
    }
    .pill-positive {
        background-color: #1f3e26; /* Dark Green Background */
        color: #69f0ae; /* Soft Green Text */
        border: 1px solid #69f0ae;
    }
</style>
""", unsafe_allow_html=True)

# --- Robust Initialization (Fix Persistence) ---
try:
    # V43: Load User specific data
    current_user = st.session_state.get("user_id", "csj") # Fallback to csj if somehow None
    pm = PortfolioManager(user_id=current_user) 
except Exception as e:
    st.error(f"CRITICAL ERROR: Failed to load Portfolio Database. {str(e)}")
    st.stop()

# Cache heavy agents if possible, but MarketData needs fresh prices usually
if 'md' not in st.session_state:
    st.session_state.md = MarketData()
if 'ae' not in st.session_state:
    st.session_state.ae = AnalyticsEngine()

md = st.session_state.md
ae = st.session_state.ae

# Analytics Wrapper
@st.cache_data(ttl=3600)
def get_news(assets):
    return ae.get_portfolio_news(assets, limit_per_asset=15)

# Helper: Process Assets
def process_assets(assets, rates, base_currency):
    total_val = 0.0
    processed_assets = []
    
    for asset in assets:
        price = md.get_current_price(asset['ticker'])
        if price == 0:
            price = asset.get('avg_price', 0.0) 
        
        val_usd = price * asset['quantity']
        total_val += val_usd
        
        asset['current_price'] = price
        asset['value_usd'] = val_usd
        processed_assets.append(asset)
    
    # Cash
    cash_data = pm.data.get('cash', {})
    total_cash_usd = 0.0
    total_cash_usd += cash_data.get('USD', 0.0)
    total_cash_usd += cash_data.get('CAD', 0.0) / rates.get('CAD', 1.35)
    total_cash_usd += cash_data.get('KRW', 0.0) / rates.get('KRW', 1300.0)
    
    total_val += total_cash_usd
    
    if total_cash_usd > 1:
        processed_assets.append({
            'ticker': 'CASH',
            'quantity': 1,
            'current_price': total_cash_usd,
            'value_usd': total_cash_usd,
            'sector': 'Liquidity',
            'asset_class': 'Cash'
        })

    # Sort
    def asset_rank(a):
        ac = a.get('asset_class', 'Other')
        if ac == 'Crypto': return 0
        if ac == 'Stock': return 1
        if ac == 'ETF': return 2
        if ac == 'Index': return 3
        if ac == 'Future': return 4
        if ac == 'Cash': return 99
        return 50 # Other
    
    # Sort by Rank -> Sector -> Value (Desc)
    processed_assets.sort(key=lambda x: (asset_rank(x), x.get('sector', 'Unknown'), -x['value_usd']))
    
    display_total = total_val
    if base_currency != 'USD':
        display_total = total_val * rates.get(base_currency, 1.0)
        
    return display_total, processed_assets

# --- Get Settings ---
section_labels = pm.get_setting('section_labels', {
    "strategic_allocation": "Allocation",
    "asset_growth": "Growth",
    "asset_manifest": "Holdings", 
    "risk_analysis": "Risk Analysis",
    "global_intel": "Global Intel"
})



manual_risk = pm.get_setting('risk_inputs', {
    "roi": 0.0,
    "volatility": 0.0,
    "risk_free_rate": 4.5
})

# --- Sidebar ---
with st.sidebar:
    st.caption(f"OPERATOR: {st.session_state['user_id'].upper()}")
    if st.button("LOGOUT", use_container_width=True):
        logout()
        
    st.title("SETTINGS")
    
    base_currency = st.radio("CURRENCY", ["USD", "CAD", "KRW"], horizontal=True)
    pm.update_setting("base_currency", base_currency)
    


    st.markdown("---")
    
    st.subheader("CASH")
    cash_data = pm.data.get('cash', {'USD':0.0, 'CAD':0.0, 'KRW':0.0})
    
    c1, c2 = st.columns(2)
    with c1:
        usd_in = st.number_input("USD", value=cash_data.get('USD', 0.0), key="cash_usd")
        if usd_in != cash_data.get('USD', 0.0):
            pm.update_cash('USD', usd_in)
            st.rerun()
    with c2:
        cad_in = st.number_input("CAD", value=cash_data.get('CAD', 0.0), key="cash_cad")
        if cad_in != cash_data.get('CAD', 0.0):
            pm.update_cash('CAD', cad_in)
            st.rerun()
    krw_in = st.number_input("KRW", value=cash_data.get('KRW', 0.0), key="cash_krw", step=1000.0)
    if krw_in != cash_data.get('KRW', 0.0):
        pm.update_cash('KRW', krw_in)
        st.rerun()
        
    if krw_in != cash_data.get('KRW', 0.0):
        pm.update_cash('KRW', krw_in)
        st.rerun()
        
    st.markdown("---")

    # V52: Add Asset Moved to Sidebar (Under Cash)
    with st.expander("➕ Add New Asset", expanded=False):
        with st.form("add_asset_form_sidebar"):
            new_ticker = st.text_input("Ticker Symbol").upper()
            
            c_qty, c_cost = st.columns(2)
            with c_qty:
                new_qty = st.number_input("Qty", min_value=0.0, format="%.4f")
            with c_cost:
                new_cost = st.number_input("Avg Cost", min_value=0.0, format="%.2f")
            
            new_class = st.selectbox("Class", ["Stock", "Crypto", "ETF", "Bond", "Cash", "Other"])
            new_sector = st.text_input("Sector", value="Technology")
            
            submitted_add = st.form_submit_button("ADD", use_container_width=True)
            
            if submitted_add and new_ticker:
                # Auto-fetch price if 0
                curr_price = 0.0
                if new_ticker:
                    info = md.get_asset_info(new_ticker)
                    if info:
                        curr_price = md.get_current_price(new_ticker)
                        if new_sector == "Technology": # Only override default if meaningful
                            new_sector = info.get('sector', new_sector)
                
                new_asset_entry = {
                    "ticker": new_ticker,
                    "quantity": new_qty,
                    "avg_price": new_cost,
                    "sector": new_sector,
                    "asset_class": new_class,
                    "value_usd": 0.0, 
                    "current_price": curr_price
                }
                
                # Direct save via PM (bypass buffer for sidebar add, or append to buffer if needed for immediate view)
                # Ideally, we update PM and rerun, which refreshes everything.
                pm.add_or_update_asset(new_asset_entry)
                pm.save_data()
                
                st.toast(f"Asset Added: {new_ticker}")
                time.sleep(0.5)
                st.rerun()

    st.markdown("---")
    with st.expander("Override Protocols"):
        new_labels = section_labels.copy()
        for key, val in section_labels.items():
            new_labels[key] = st.text_input(f"{key}", value=val)
        if st.button("UPDATE PROTOCOLS"):
            pm.update_setting('section_labels', new_labels)
            st.rerun()

# --- Main Dashboard ---
st.title("PORTFOLIO MANAGER")

# 1. Header & Data Pre-processing
fx_rates, is_stale_flag = md.get_fx_rates()
raw_assets = pm.get_assets()
total_val_display, sorted_assets = process_assets(raw_assets, fx_rates, base_currency)

# --- History Calculation (Lifted for Header Metrics) ---
real_assets = [a for a in sorted_assets if a['ticker'] != 'CASH']
total_history_display = pd.Series()

if real_assets:
    prices = st.session_state.ae.fetch_historical_data(real_assets)
    if not prices.empty:
        prices = prices.ffill().dropna()
        portfolio_value_series = pd.Series(0.0, index=prices.index)
        for asset in real_assets:
            if asset['ticker'] in prices.columns:
                portfolio_value_series = portfolio_value_series.add(prices[asset['ticker']] * asset['quantity'], fill_value=0)
        
        total_cash_usd = next((a['value_usd'] for a in sorted_assets if a['ticker'] == 'CASH'), 0.0)
        total_history_usd = portfolio_value_series + total_cash_usd
        
        # V35: Apply Currency Conversion
        growth_fx = fx_rates.get(base_currency, 1.0)
        total_history_display = total_history_usd * growth_fx

# --- Metrics Calculation ---
ytd_return = 0.0
cagr = 0.0

if not total_history_display.empty:
    # YTD
    current_year = datetime.now().year
    start_of_year = datetime(current_year, 1, 1)
    
    # Filter for dates >= Jan 1. 
    # Logic: Find first available date in this year. 
    # If history starts after Jan 1, use first date.
    
    # Ensure index is datetime
    if not isinstance(total_history_display.index, pd.DatetimeIndex):
        total_history_display.index = pd.to_datetime(total_history_display.index)
        
    this_year_data = total_history_display[total_history_display.index >= pd.Timestamp(start_of_year)]
    
    current_val = total_history_display.iloc[-1]
    
    if not this_year_data.empty:
        start_val_ytd = this_year_data.iloc[0]
        if start_val_ytd > 0:
            ytd_return = (current_val - start_val_ytd) / start_val_ytd
    else:
        # Fallback if no data in current year (e.g. Jan 1 morning?) or history ends before Jan 1
        pass 

    # CAGR (REMOVED V37)
    
# Header Layout
# Header Layout (Unified HTML for V39)
val_html = f"{total_val_display:,.2f}"

pill_html = ""
if ytd_return != 0:
    pill_class = "pill-positive" if ytd_return > 0 else "pill-negative"
    arrow = "↑" if ytd_return > 0 else "↓"
    # No indentation to avoid code block
    pill_html = f'<div class="metric-pill {pill_class}"><span>{arrow} {ytd_return:.2%}</span></div>'
else:
    pill_html = '<span style="color: #555;">—</span>'

st.markdown(f"""
<div style="display: flex; gap: 30px; align-items: flex-start;">
    <div>
        <div style="margin-bottom: 2px;">
            <span style="font-size: 14px; color: #B0B0B0; font-weight: 500;">NET ASSETS ({base_currency})</span>
        </div>
        <span style="font-size: 42px; font-weight: 700; color: #D500F9; text-shadow: 0 0 10px rgba(213, 0, 249, 0.4); line-height: 1;">
            {val_html}
        </span>
    </div>
    <div>
        <div style="margin-bottom: 2px;">
            <span style="font-size: 14px; color: #B0B0B0; font-weight: 500; padding-left: 10px;">YTD Return</span>
        </div>
        <div style="display: flex; align-items: center; height: 42px;">
            {pill_html}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# 2. SWAPPED: Growth Chart First
st.subheader(section_labels.get("asset_growth", "Growth"))
with st.container(border=True):
    if not total_history_display.empty:
        PURPLE_LINE = "#D500F9" 
        PURPLE_FILL = "rgba(213, 0, 249, 0.15)" 
        
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(
            x=total_history_display.index, 
            y=total_history_display.values, 
            fill='tozeroy',
            mode='lines',
            line=dict(color=PURPLE_LINE, width=2), 
            fillcolor=PURPLE_FILL, 
            name=f'Portfolio ({base_currency})'
        ))
        fig_growth.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, b=10, l=10, r=10),
            yaxis=dict(gridcolor='#222'),
            xaxis=dict(gridcolor='#222'),
            font=dict(color='#888'),
            height=350, # V42: Fixed height for mobile fitting
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        if not real_assets:
             st.info("NO ASSETS TRACKED.")
        else:
             st.info("DATASTREAM OFFLINE.")

st.markdown("---")

# 3. SWAPPED: Allocation (Pie Charts) Second
st.subheader(section_labels.get("strategic_allocation", "Allocation"))

# TEXT COLOR: WHITE (High Luminance)
PIE_TEXT_COLOR = "#FFFFFF"

# COLOR PALETTES
PALETTE_CLASS = ['#311B92', '#4527A0', '#512DA8', '#5E35B1', '#673AB7']
PALETTE_SECTOR = ['#7B1FA2', '#8E24AA', '#9C27B0', '#AB47BC', '#BA68C8']
PALETTE_HOLDINGS = ['#6200EA', '#651FFF', '#7C4DFF', '#B388FF', '#304FFE']

if not raw_assets and pm.data['cash']['USD'] == 0:
    st.warning("SYSTEM EMPTY. DEPLOY ASSETS TO INITIALIZE.")
else:
    df_assets = pd.DataFrame(sorted_assets)
    
    # Resized Columns to balance Holdings Chart (Feedback V25)
    # Holdings was too big at 1.4, user wants it reduced slightly and others increased.
    # V42: On mobile these will stack via CSS, but for desktop we keep this ratio.
    chart_col1, chart_col2, chart_col3 = st.columns([1, 1, 1.2])
    
    # Define Distinct Cash Color (Toned Down Lime - Feedback V26)
    COLOR_CASH = "#9E9D24" # Lime 800 (Darker/Muted)

    # Pie Chart 1
    with chart_col1:
        with st.container(border=True):
            st.caption("CLASS DISTRIBUTION")
            
            # Custom Color Map for Class Distribution
            # We map specific classes to the Palette, and Cash to our custom color
            # V34: Merge ETF into Stock
            df_class = df_assets.copy()
            df_class['asset_class'] = df_class['asset_class'].replace('ETF', 'Stock')
            
            class_map = {
                'Crypto': PALETTE_CLASS[0],
                'Stock': PALETTE_CLASS[1], # Now includes ETFs
                'Other': PALETTE_CLASS[3],
                'Cash': COLOR_CASH 
            }
            
            fig = px.pie(df_class, values='value_usd', names='asset_class', hole=0.5,
                         color='asset_class', color_discrete_map=class_map)
                         
            # V41: Clean Tooltip & Dystopian Styling
            fig.update_traces(
                textinfo='percent+label', 
                textposition='inside', # V42: Force inside for mobile safety
                textfont=dict(size=12, color=PIE_TEXT_COLOR),
                marker=dict(line=dict(color='#000000', width=2)),
                hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"
            )
            fig.update_layout(
                margin=dict(t=20, b=20, l=10, r=10), 
                paper_bgcolor='rgba(0,0,0,0)', 
                showlegend=False, # V42: Hide Legend (labels inside is sufficient and cleaner)
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    bordercolor="rgba(0, 0, 0, 0.8)", 
                    font=dict(color="white")
                )
            )
            st.plotly_chart(fig, use_container_width=True)

    # Pie Chart 2
    with chart_col2:
        with st.container(border=True):
            st.caption("SECTOR ALLOCATION")
            df_stocks = df_assets[df_assets['asset_class'] == 'Stock']
            if not df_stocks.empty:
                fig = px.pie(df_stocks, values='value_usd', names='sector', hole=0.5,
                             color_discrete_sequence=PALETTE_SECTOR)
                # Text Inside + Horizontal
                # V41: Clean Tooltip & Dystopian Styling
                fig.update_traces(
                    textinfo='percent+label', 
                    textposition='inside', 
                    insidetextorientation='horizontal',
                    textfont=dict(size=12, color=PIE_TEXT_COLOR),
                    marker=dict(line=dict(color='#000000', width=2)),
                    hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"
                )
                fig.update_layout(
                    margin=dict(t=20, b=20, l=10, r=10), 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    showlegend=False,
                    hoverlabel=dict(
                        bgcolor="rgba(0, 0, 0, 0.8)",
                        bordercolor="rgba(0, 0, 0, 0.8)", 
                        font=dict(color="white")
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("<p style='text-align:center; color:#555; padding: 80px 0;'>NO STOCK DATA</p>", unsafe_allow_html=True)

    # Pie Chart 3 (Expanded)
    with chart_col3:
        with st.container(border=True):
            st.caption("HOLDINGS") 
            
            # Grouping Logic for "Etc" (< 1%)
            total_portfolio_val = df_assets['value_usd'].sum()
            if total_portfolio_val > 0:
                df_chart = df_assets.copy()
                df_chart['ratio'] = df_chart['value_usd'] / total_portfolio_val
                
                # Separate Small vs Large
                mask_small = df_chart['ratio'] < 0.01
                df_small = df_chart[mask_small]
                df_large = df_chart[~mask_small].copy()
                
                if not df_small.empty:
                    etc_val = df_small['value_usd'].sum()
                    # Create generic Etc row
                    etc_row = pd.DataFrame([{
                        'ticker': 'Etc.',
                        'value_usd': etc_val,
                        'asset_class': 'Other',
                        'sector': 'Other'
                    }])
                    df_large = pd.concat([df_large, etc_row], ignore_index=True)
                
                df_final_pie = df_large
            else:
                df_final_pie = df_assets

            # Assign colors dynamically
            # V47: Strip -USD
            df_final_pie['display_ticker'] = df_final_pie['ticker'].str.replace("-USD", "")

            holdings_colors = {}
            # Re-generate tickers list from the aggregared DF
            pie_tickers = df_final_pie['ticker'].tolist()
            display_tickers = df_final_pie['display_ticker'].tolist()
            
            # Helper to cycle through palette
            def get_color(i):
                return PALETTE_HOLDINGS[i % len(PALETTE_HOLDINGS)]
                
            for i, t in enumerate(pie_tickers):
                d_t = display_tickers[i]
                if t == 'CASH':
                    holdings_colors[d_t] = COLOR_CASH 
                elif t == 'Etc.':
                    holdings_colors[d_t] = "#757575" # Grey for Etc
                else:
                    # Try to maintain original color consistency if possible, but simple cycle is fine
                    holdings_colors[d_t] = get_color(i)
            
            fig = px.pie(df_final_pie, values='value_usd', names='display_ticker', hole=0.5,
                         color='display_ticker', color_discrete_map=holdings_colors)
            
            pull = [0.1 if v == df_final_pie['value_usd'].max() else 0 for v in df_final_pie['value_usd']]
            text_s = [18 if v == df_final_pie['value_usd'].max() else 11 for v in df_final_pie['value_usd']]
            
            # V41: Clean Tooltip & Dystopian Styling
            fig.update_traces(
                textinfo='percent+label', 
                textposition='inside', # V42: Force inside for mobile safety
                insidetextorientation='horizontal',
                textfont=dict(color=PIE_TEXT_COLOR), 
                texttemplate="%{label}<br>%{percent}",
                pull=pull,
                marker=dict(line=dict(color='#000000', width=2)),
                hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"
            )
            
            fig.data[0].textfont.size = text_s
            
            # Margins kept generous for labels
            fig.update_layout(
                margin=dict(t=20, b=20, l=20, r=20), # V42: Reduced margins
                paper_bgcolor='rgba(0,0,0,0)', 
                showlegend=False,
                hoverlabel=dict(
                    bgcolor="rgba(0, 0, 0, 0.8)",
                    bordercolor="rgba(0, 0, 0, 0.8)", 
                    font=dict(color="white")
                )
            )
            st.plotly_chart(fig, use_container_width=True)
           # --------------------------------------------------------------------------------
    # ASSET TABLE (Feedback V25-V29)
    # --------------------------------------------------------------------------------
    with st.container(border=True):
        col_header, col_delete = st.columns([8, 1])
        with col_header:
            st.subheader("Holdings")
            
        # Initialize Local Asset Buffer if not present
        if 'asset_buffer' not in st.session_state:
            # Deep copy to prevent reference issues
            st.session_state['asset_buffer'] = [a.copy() for a in sorted_assets]

        # Prepare data for editor from BUFFER
        # STRATEGY: Use buffer as source of truth for the Editor to allow partial edits/adds to persist.
        
        # Currency Conversion for Table
        table_fx_rate = fx_rates.get(base_currency, 1.0)
        currency_symbol = "$" if base_currency in ["USD", "CAD"] else "₩"
        
        display_data = []
        # Filter CASH from buffer for display (unless we want to edit cash?)
        # Logic: Cash is managed automatically or via specific input. Let's hide CASH row from table editing.
        buffer_assets = st.session_state['asset_buffer']
        
        display_map = [] # List of buffer indices
        
        for i, a in enumerate(buffer_assets):
            if a['ticker'] == 'CASH': continue 
            
            # Convert Value
            val_in_base = float(a.get('value_usd', 0.0)) * table_fx_rate
            
            price = a.get('current_price', 0.0)
            if price == 0: price = a.get('avg_price', 0.0)
            
            val_calc = price * a.get('quantity', 0.0) * table_fx_rate
            
            display_data.append({
                "DELETE": False, # V49: Explicit Delete Checkbox for Mobile
                "TICKER": str(a.get('ticker', '')),
                "CLASS": str(a.get('asset_class', '')),
                "SECTOR": str(a.get('sector', '')),
                "QTY": f"{float(a.get('quantity', 0.0)):.4f}", 
                "AVG COST": f"{float(a.get('avg_price', 0.0)):.2f}", 
                "CURRENT PRICE": f"${float(price):,.2f}", 
                "VALUE": f"{currency_symbol}{val_calc:,.2f}" 
            })
            display_map.append(i)
        
        df_display = pd.DataFrame(display_data)
        
        # --------------------------------------------------------------------------------
        # EDITING LOGIC V8 (Buffer + Native Delete + Checkbox Delete)
        # --------------------------------------------------------------------------------

        # Helper to process edits
        def save_edits():
            state = st.session_state["holdings_editor"]
            edited_rows = state.get("edited_rows", {})
            deleted_rows = state.get("deleted_rows", [])
            added_rows = state.get("added_rows", []) 
            
            if not edited_rows and not deleted_rows and not added_rows:
                return

            print(f"DEBUG: Callback triggered. Changes: {state}")
            
            buffer = st.session_state['asset_buffer']
            updates_made = False
            
            # 0. IDENTIFY CHECKBOX DELETES (V49)
            checkbox_deletes = []
            for idx, changes in edited_rows.items():
                if changes.get("DELETE") is True:
                    # User checked the Delete box
                    checkbox_deletes.append(int(idx))
            
            # Combine with native deletes
            # Use set to avoid duplicates if user somehow did both
            all_indices_to_delete = set(deleted_rows + checkbox_deletes)
            
            # 1. EXECUTE DELETES
            if all_indices_to_delete:
                rows_to_delete = sorted([display_map[i] for i in all_indices_to_delete if i < len(display_map)], reverse=True)
                for buf_idx in rows_to_delete:
                    if buf_idx < len(buffer):
                        removed = buffer.pop(buf_idx)
                        print(f"DEBUG: Removed {removed.get('ticker')} via Delete Logic.")
                        updates_made = True
            
            # 2. HANDLE EDITS (Edits to existing rows)
            # Strategy: Skip rows that were just deleted.
            
            for idx, changes in edited_rows.items():
                if int(idx) in all_indices_to_delete: continue 
                
                if idx < len(display_map):
                    buf_idx = display_map[idx]
                    if buf_idx < len(buffer): # Safety check
                        asset = buffer[buf_idx]
                        
                        # Note: 'DELETE' change might be in 'changes' but false (uncheck?)
                        # If it was True, we already handled it. If False, nothing to do.
                        
                        if "QTY" in changes:
                            try: asset['quantity'] = float(str(changes["QTY"]).replace(',', ''))
                            except: pass
                            updates_made = True
                        
                        if "AVG COST" in changes:
                            try: asset['avg_price'] = float(str(changes["AVG COST"]).replace(',', '').replace('$', ''))
                            except: pass
                            updates_made = True

                        if "SECTOR" in changes:
                            asset['sector'] = str(changes["SECTOR"]).strip()
                            updates_made = True
                            
                        if "CLASS" in changes:
                            asset['asset_class'] = str(changes["CLASS"]).strip()
                            updates_made = True
                        
                        if "TICKER" in changes:
                            asset['ticker'] = str(changes["TICKER"]).strip().upper()
                            updates_made = True
            
            # 3. HANDLE ADDS
            if added_rows:
                for new_row in added_rows:
                    raw_ticker = new_row.get('TICKER', '').strip().upper()
                    
                    # Manual Override Check (If user typed in Class/Sector on Add row?)
                    # Streamlit Add Row usually gives default values unless columns are required/defaulted.
                    # We will Auto-Populate but allow overwrite if they edit it immediately after.
                    
                    final_class = "Stock"
                    final_sector = "Unknown"
                    curr_price = 0.0
                    
                    if raw_ticker:
                        info = md.get_asset_info(raw_ticker)
                        if info:
                            final_class = info.get('asset_class', 'Stock')
                            final_sector = info.get('sector', 'Unknown')
                            curr_price = md.get_current_price(raw_ticker)
                    
                    # If user provided input in params (unlikely for new row unless typed), use it.
                    if new_row.get('CLASS'): final_class = new_row.get('CLASS')
                    if new_row.get('SECTOR'): final_sector = new_row.get('SECTOR')
                    
                    try: qty = float(str(new_row.get('QTY', '0')).replace(',', ''))
                    except: qty = 0.0
                    try: avg = float(str(new_row.get('AVG COST', '0')).replace('$', '').replace(',', ''))
                    except: avg = 0.0
                    
                    new_asset = {
                        "ticker": raw_ticker,
                        "quantity": qty,
                        "avg_price": avg,
                        "sector": final_sector,
                        "asset_class": final_class,
                        "value_usd": 0.0, 
                        "current_price": curr_price
                    }
                    buffer.append(new_asset)
                    print(f"DEBUG: Added new row to buffer. Ticker: {raw_ticker}")
                    updates_made = True

            if updates_made:
                valid_assets = [a for a in buffer if a.get('ticker') and a.get('ticker') != "CASH"]
                cash_asset = next((a for a in pm.data['assets'] if a['ticker'] == 'CASH'), None)
                final_pm_assets = valid_assets
                if cash_asset:
                    final_pm_assets.append(cash_asset)
                
                pm.data['assets'] = final_pm_assets
                pm.save_data()
                st.toast("✅ Portfolio Updated")

        # Configure Column Config
        st.data_editor(
            df_display,
            column_config={
                "DELETE": st.column_config.CheckboxColumn("🗑️", help="Select to delete", default=False, width="small"),
                "TICKER": st.column_config.TextColumn("Ticker", disabled=False), 
                "CLASS": st.column_config.TextColumn("Class", disabled=False), # Editable V31
                "SECTOR": st.column_config.TextColumn("Sector", disabled=False), # Editable V31
                "QTY": st.column_config.TextColumn("Quantity", disabled=False), 
                "AVG COST": st.column_config.TextColumn("Avg Cost", disabled=False), 
                "CURRENT PRICE": st.column_config.TextColumn("Price (USD)", disabled=True), 
                "VALUE": st.column_config.TextColumn(f"Value ({base_currency})", disabled=True) 
            },
            hide_index=True,
            use_container_width=True,
            key="holdings_editor",
            on_change=save_edits,
            num_rows="dynamic" 
        )

st.markdown("---")

# 4. Intelligence
st.header("INTELLIGENCE GRID")

r1, r2 = st.columns([1, 1])
SYNC_HEIGHT = 460 

with r1:
    # Risk Analysis (Auto-Weighted)
    # --------------------------------------------------------------------------------
    with st.container(border=True, height=SYNC_HEIGHT):
        st.subheader(section_labels.get("risk_analysis", "Risk Analysis"))
        
        # 1. BENCHMARKS
        RISK_BENCHMARKS = {
            "Crypto": {"roi": 0.70, "vol": 0.60},
            "Stock":  {"roi": 0.12, "vol": 0.20},
            "Bond":   {"roi": 0.04, "vol": 0.08},
            "Cash":   {"roi": 0.035, "vol": 0.00},
            "Other":  {"roi": 0.05, "vol": 0.10} # Default fallback
        }
        RF_RATE = 0.035 # Fixed 3.5%
        
        # 2. CALCULATE WEIGHTS
        # We need total value excluding cash? No, Cash is an asset class.
        # 'processed_assets (sorted_assets)' includes CASH entry if applicable.
        
        # Map asset class from our data to benchmarks
        # Our data uses: "Stock", "Crypto", "ETF", "Other", "Cash"
        # Map ETF -> Stock? or Other? Let's map ETF -> Stock for now or add ETF benchmark.
        # User only specified: Crypto, Stock, Bond, Cash.
        # We will map ETF -> Stock.
        
        class_mapping = {
            "Crypto": "Crypto",
            "Stock": "Stock",
            "ETF": "Stock", # Assumed
            "Cash": "Cash",
            "Liquidity": "Cash",
            "Bond": "Bond"
        }
        
        total_p_value = sum(a['value_usd'] for a in sorted_assets)
        weighted_roi = 0.0
        weighted_vol = 0.0
        
        composition = {"Crypto": 0.0, "Stock": 0.0, "Bond": 0.0, "Cash": 0.0}
        
        if total_p_value > 0:
            for asset in sorted_assets:
                ac = asset.get('asset_class', 'Other')
                val = asset['value_usd']
                weight = val / total_p_value
                
                # Resolving Benchmark Key
                bench_key = class_mapping.get(ac, "Other")
                if bench_key not in RISK_BENCHMARKS: bench_key = "Other"
                
                # Aggregate for Display
                if bench_key in composition:
                    composition[bench_key] += weight
                
                # Weighted Sum
                metrics = RISK_BENCHMARKS[bench_key]
                weighted_roi += metrics['roi'] * weight
                weighted_vol += metrics['vol'] * weight
        
        # 3. SHARPE CALCULATION
        # Sharpe = (Rp - Rf) / Op
        if weighted_vol > 0:
            sharpe_auto = (weighted_roi - RF_RATE) / weighted_vol
        else:
            sharpe_auto = 0.0
            
        # 4. RENDER GAUGE
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = sharpe_auto,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "SHARPE RATIO"},
            gauge = {
                'axis': {'range': [-1, 4], 'tickwidth': 1, 'tickcolor': "#FFF"},
                'bar': {'color': "#FFF"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "#444",
                'steps': [
                    {'range': [-1, 0], 'color': "#311B92"}, 
                    {'range': [0, 1], 'color': "#512DA8"},
                    {'range': [1, 2], 'color': "#7B1FA2"},
                    {'range': [2, 4], 'color': "#D500F9"}
                ],
                'threshold': {
                    'line': {'color': "#FFF", 'width': 4},
                    'thickness': 0.75,
                    'value': sharpe_auto
                }
            }
        ))
        fig_gauge.update_layout(height=180, margin=dict(t=50, b=0, l=30, r=40), paper_bgcolor='rgba(0,0,0,0)', font={'color': "#FFF"})
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # 5. COMPOSITION SUMMARY
        st.divider()
        st.caption(f"STRATEGIC PROFILE (RF: {RF_RATE*100:.2f}%)")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CRYPTO", f"{composition['Crypto']*100:.1f}%", help="ROI: 70% | Vol: 60%")
        c2.metric("STOCK", f"{composition['Stock']*100:.1f}%", help="ROI: 12% | Vol: 20%")
        c3.metric("BOND", f"{composition['Bond']*100:.1f}%", help="ROI: 4% | Vol: 8%")
        c4.metric("CASH", f"{composition['Cash']*100:.1f}%", help="ROI: 3.5% | Vol: 0%")
        
        st.caption(f"Est. ROI: {weighted_roi*100:.1f}% | Est. Volatility: {weighted_vol*100:.1f}%")

with r2:
    with st.container(border=True, height=SYNC_HEIGHT):
        st.subheader(section_labels.get("global_intel", "Global Intel"))
        news_items = get_news(raw_assets)
        
        if news_items:
            news_by_ticker = {}
            for n in news_items:
                t = n['ticker']
                if t not in news_by_ticker: news_by_ticker[t] = []
                news_by_ticker[t].append(n)
            
            all_tickers = [a['ticker'] for a in sorted_assets if a['ticker'] != 'CASH']
            if not all_tickers: all_tickers = ["General"]
            
            tab_names = []
            seen = {}
            for t in all_tickers:
                # V47: Strip -USD
                d_t = t.replace("-USD", "")
                if d_t in seen:
                    seen[d_t] += 1
                    tab_names.append(f"{d_t} ({seen[d_t]})")
                else:
                    seen[d_t] = 1
                    tab_names.append(d_t)
            
            tabs = st.tabs(tab_names)
            
            for i, t in enumerate(all_tickers):
                with tabs[i]:
                    page_key = f"news_page_{t}_{i}" 
                    if page_key not in st.session_state: st.session_state[page_key] = 0
                    
                    page = st.session_state[page_key]
                    items_per_page = 5 
                    
                    if t == "General":
                         current_ticker_news = news_items 
                    else:
                         current_ticker_news = news_by_ticker.get(t, [])

                    total_items = len(current_ticker_news)
                    start_idx = page * items_per_page
                    end_idx = start_idx + items_per_page
                    display_items = current_ticker_news[start_idx:end_idx]
                    
                    div_space_height = SYNC_HEIGHT - 220 
                    with st.container(height=div_space_height, border=False):
                        if display_items:
                            for item in display_items:
                                pub_time = item.get('providerPublishTime', 0)
                                date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(pub_time)) if isinstance(pub_time, int) else str(pub_time)
                                st.markdown(f"""
                                <div class="news-item">
                                    <div class="news-title">{item['title']}</div>
                                    <div class="news-meta">
                                        {date_str} • <a href="{item.get('link', '#')}" class="news-link" target="_blank">ACCESS DATA</a>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.caption("NO SIGNAL.")
                    
                    f_col1, f_mid, f_col2 = st.columns([1, 2, 1])
                    with f_col1:
                        if page > 0:
                            if st.button("<< PREV", key=f"prev_{page_key}", use_container_width=True):
                                st.session_state[page_key] -= 1
                                st.rerun()     
                    with f_col2:
                         if end_idx < total_items:
                            if st.button("NEXT >>", key=f"next_{page_key}", use_container_width=True):
                                st.session_state[page_key] += 1
                                st.rerun()
        else:
            st.info("NO INTEL DETECTED.")
