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
from datetime import datetime, timedelta
import pandas_datareader.data as web
import yfinance as yf
import streamlit.components.v1 as components
from plotly.subplots import make_subplots # 👈 이 줄이 꼭 있어야 fig_dual이 작동합니다!

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

# --- Robust Initialization (Moved Here V53) ---
try:
    current_user = st.session_state.get("user_id", "csj")
    # Only initialize if logged in (double check, though code flow ensures it)
    if st.session_state["logged_in"]:
         # We need to ensure pm is in session state to persist across reruns without re-init?
         # Actually PM checks GSheets every time or we trust internal state? 
         # GSheetsConnection handles caching (ttl). 
         # But PM class instance should probably be cached or just re-inited is fine as it loads from cache.
         # Let's keep it simple: Init.
         pm = PortfolioManager(user_id=current_user) 
    else:
         st.stop() # Should be caught above
except Exception as e:
    st.error(f"CRITICAL ERROR: Failed to load Portfolio Database. {str(e)}")
    st.stop()

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

# --- MACRO INTELLIGENCE CLASS (V54) ---
class MacroThinking:
    @staticmethod
    @st.cache_data(ttl=3600)
    def get_real_interest_rate_data():
        try:
            # 1. 넉넉하게 3년치 데이터 호출
            start_date = datetime.now() - timedelta(days=1100)
            end_date = datetime.now()
            raw_data = web.DataReader(['DGS3MO', 'CPIAUCNS'], 'fred', start_date, end_date)
            
            # 2. [무결성 로직] CPI YoY 계산 (월간 데이터만 따로 추출)
            # CPI 데이터가 존재하는 행만 골라내서 월간 증감률 계산
            cpi_monthly = raw_data[['CPIAUCNS']].dropna()
            cpi_yoy = (cpi_monthly / cpi_monthly.shift(12) - 1) * 100
            cpi_yoy.columns = ['Inflation']
            
            # 3. [데이터 통합] 일간 금리 데이터프레임에 월간 Inflation 수치를 병합
            # 최신 물가 수치를 다음 발표 전까지 매일 동일하게 적용(ffill)
            df = raw_data[['DGS3MO']].rename(columns={'DGS3MO': 'US3M'})
            df = df.join(cpi_yoy).ffill()
            
            # 4. 실질금리 계산: 3M Yield - Inflation (YoY)
            df['Real_Rate'] = df['US3M'] - df['Inflation']
            
            # 최신 데이터가 누락되지 않도록 결측치 제거 후 반환
            return df[['US3M', 'Inflation', 'Real_Rate']].dropna()
            
        except Exception as e:
            st.error(f"Macro Data Error: {e}")
            return pd.DataFrame()

    @staticmethod
    @st.cache_data(ttl=3600)
    def get_treasury_yields():
        try:
            # DGS3MO, DGS1, DGS2, DGS5, DGS10, DGS30
            tickers = ['DGS3MO', 'DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS10', 'DGS20', 'DGS30']
            start = datetime.now() - timedelta(days=730)
            df = web.DataReader(tickers, 'fred', start, datetime.now())
            return df.dropna()
        except Exception as e:
            print(f"Treasury Data Error: {e}")
            return pd.DataFrame()

# Analytics Wrapper
@st.cache_data(ttl=3600)
def get_news(assets):
    return ae.get_portfolio_news(assets, limit_per_asset=15)

# 야후 파이낸스 캐싱
@st.cache_data(ttl=3600)  # 1시간 동안 가격 데이터를 메모리에 저장
def get_cached_historical_data(_ae, assets):
    """야후 파이낸스 데이터를 1시간 동안 캐싱하여 차트 오프라인 방지"""
    try:
        return _ae.fetch_historical_data(assets)
    except Exception as e:
        return pd.DataFrame()


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
    "strategic_allocation": "ALLOCATION",
    "asset_growth": "NET ASSET VALUE",
    "asset_manifest": "HOLDINGS", 
    "risk_analysis": "RISK ANALYSIS",
    "global_intel": "NEWS"
})



manual_risk = pm.get_setting('risk_inputs', {
    "roi": 0.0,
    "volatility": 0.0,
    "risk_free_rate": 4.5
})









# --- Sidebar ---
with st.sidebar:
    # [A] 최상단 정보 (ID & Logout)
    st.markdown(f'<div style="text-align: center; color: #888; font-size: 14px; margin-bottom: 20px;">ID: {st.session_state["user_id"].upper()}</div>', unsafe_allow_html=True)
    if st.button("LOGOUT", use_container_width=True, key="unique_logout_v780"):
        logout()
    st.markdown("---")

    # [B] MODULE 메뉴 출력 (최상단 배치)
    st.markdown("### MODULE")
    # 세션 상태 초기화
    if 'sidebar_menu' not in st.session_state:
        st.session_state['sidebar_menu'] = "Portfolio"

    # 1. 새로운 메뉴 리스트 정의
    menu_list = ["Portfolio", "Bitcoin Standard", "Crypto", "Macro", "Market"]

    # 2. [V1270 핵심] 세션에 저장된 메뉴가 새로운 리스트에 없으면 Portfolio로 초기화 ㅋ
    current_menu = st.session_state.get('sidebar_menu', "Portfolio")
    if current_menu not in menu_list:
        current_menu = "Portfolio"
        st.session_state['sidebar_menu'] = "Portfolio"

    # 3. 라디오 버튼 렌더링
    menu = st.radio(
        "SELECT_MODULE",
        menu_list,
        index=menu_list.index(current_menu), # 이제 에러 안 납니다 ㅋ
        label_visibility="collapsed",
        key="main_menu_radio_v780"
    )
    
    # 메뉴 변경 시 세션 갱신 및 리런
    if menu != st.session_state['sidebar_menu']:
        st.session_state['sidebar_menu'] = menu
        st.rerun()

    st.markdown("---")

    # [C] PORTFOLIO 전용 섹션 (Settings, Cash, Add Asset)
    # Portfolio 모드일 때만 아래 내용들이 나타납니다. ㅋ
    if menu == "Portfolio":
        # 1. SETTINGS (통화 설정)
        st.subheader("SETTINGS")
        curr_val = pm.get_setting("base_currency", "USD")
        new_curr = st.radio("CURRENCY", ["USD", "CAD", "KRW"], horizontal=True, key="sidebar_curr_v780")
        if new_curr != curr_val:
            pm.update_setting("base_currency", new_curr)
            st.rerun()
        
        st.markdown("---")

        # 2. CASH (현금 관리)
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
            
        st.markdown("---")

        # 3. ADD NEW ASSET (자산 추가)
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
                    curr_price = 0.0
                    info = md.get_asset_info(new_ticker)
                    if info:
                        curr_price = md.get_current_price(new_ticker)
                        if new_sector == "Technology":
                            new_sector = info.get('sector', new_sector)
                    
                    new_asset_entry = {
                        "ticker": new_ticker, "quantity": new_qty, "avg_price": new_cost,
                        "sector": new_sector, "asset_class": new_class,
                        "value_usd": 0.0, "current_price": curr_price
                    }
                    pm.add_or_update_asset(new_asset_entry)
                    pm.save_data()
                    st.toast(f"Asset Added: {new_ticker}")
                    time.sleep(0.5)
                    st.rerun()

        st.markdown("---")
    # [D] Sidebar Footer (모든 메뉴에서 공통으로 보이도록 if문 밖으로 탈출!)
    # st.sidebar를 직접 명시하여 확실하게 위치를 고정합니다.
    st.sidebar.markdown(
        """
        <div style="
            text-align: center; 
            color: #777; 
            font-size: 13px; 
            margin-top: 10px;
            margin-bottom: 30px;
            width: 100%;
            font-family: 'Courier New', Courier, monospace;
        ">
            RABBIT TERMINAL v2026.02
        </div>
        """, 
        unsafe_allow_html=True
    )








# --- MAIN EXECUTION LOGIC ---

if menu == "Macro":
    # V56: Global Macro Intelligence (Full Caption System ㅋ)
    st.title("MACRO INTELLIGENCE")
    
    # [A] TradingView Widgets (Top)
    st.markdown("---")
    st.markdown("### MARKET PULSE")
    c1, c2 = st.columns(2)
    
    # 디폴트: 현재 시점 기준 1년 전 (정확히 설정되어 있습니다! ㅋ)
    sync_start_date = datetime.now() - timedelta(days=365)
    sync_start_str = sync_start_date.strftime('%Y-%m-%d')
    
    with c1:
        try:
            fed_data = web.DataReader('FEDFUNDS', 'fred', sync_start_date, datetime.now())
            if not fed_data.empty:
                latest_fed = fed_data.dropna().iloc[-1][0]
                prev_fed = fed_data.dropna().iloc[-2][0]
                
                st.metric(label="Fed Funds Effective Rate", value=f"{latest_fed:.2f}%", 
                          delta=f"{latest_fed - prev_fed:.2f}%", delta_color="normal")
                
                fig1 = px.area(fed_data.dropna(), y='FEDFUNDS')
                fig1.update_traces(line_color='#00E676', fillcolor='rgba(0, 230, 118, 0.1)')
                fig1.update_layout(
                    height=200, margin=dict(t=10, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(showgrid=False, title=None, zeroline=False, 
                               range=[fed_data['FEDFUNDS'].min() * 0.95, fed_data['FEDFUNDS'].max() * 1.05]),
                    xaxis=dict(showgrid=False, title=None), showlegend=False)
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
                
                # [V56] Analysis Start + Source 통합 캡션 ㅋ
                actual_fed_start = fed_data.index[0].strftime('%Y-%m-%d')
                st.caption(f"Analysis Start: {actual_fed_start} | Source: Federal Reserve Bank of St. Louis (FRED)")
                
        except Exception as e:
            st.error("Fed Data Offline")
        
    with c2:
        try:
            tickers = ['WALCL', 'WTREGEN', 'RRPONTSYD']
            nl_data = web.DataReader(tickers, 'fred', sync_start_date, datetime.now())
            
            fed_assets = nl_data['WALCL'] / 1000000
            tga = nl_data['WTREGEN'] / 1000000
            rrp = nl_data['RRPONTSYD'] / 1000
            
            net_liquidity = (fed_assets - tga - rrp).dropna()
            
            if not net_liquidity.empty:
                latest_nl = net_liquidity.iloc[-1]
                prev_nl = net_liquidity.iloc[-2] if len(net_liquidity) > 1 else latest_nl
                diff = latest_nl - prev_nl
                
                st.metric(
                    label="Net Liquidity", 
                    value=f"${latest_nl:.2f}T", 
                    delta=f"{diff:.3f}T (WoW)", 
                    delta_color="normal"
                )
                
                df_plot = net_liquidity.to_frame(name='liquidity')
                fig2 = px.area(df_plot, y='liquidity')
                fig2.update_traces(line_color='#00E676', fillcolor='rgba(0, 230, 118, 0.1)')
                fig2.update_layout(
                    height=200, margin=dict(t=10, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(
                        showgrid=False, title=None, zeroline=False, 
                        range=[net_liquidity.min() * 0.99, net_liquidity.max() * 1.01]
                    ),
                    xaxis=dict(showgrid=False, title=None),
                    showlegend=False
                )
                st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
                
                # [V56] Analysis Start + Source 통합 캡션 ㅋ
                actual_nl_start = net_liquidity.index[0].strftime('%Y-%m-%d')
                st.caption(f"Analysis Start: {actual_nl_start} | Source: Federal Reserve Bank of St. Louis (FRED)")
                
        except Exception as e:
            st.error(f"Net Liquidity Stream Offline")

    st.markdown("---")




    # [B] Real Interest Rate Analysis (V82: 2-Year Default & Standard Caption ㅋ)
    st.subheader("REAL INTEREST RATE")

    # 1. 분석 기간 선택 (디폴트: 현재 시점 기준 2년 전 ㅋ)
    rr_col1, rr_col2 = st.columns([1, 2])
    with rr_col1:
        rr_default_start = datetime.now() - timedelta(days=365 * 2)
        rr_start_date = st.date_input(
            "Analysis Start Date", 
            value=rr_default_start, 
            key="real_interest_rate_date"
        )

    # 2. 데이터 로드 및 처리 (V82: 선택된 날짜 연동 ㅋ)
    @st.cache_data(ttl=3600)
    def get_real_rate_data_v82(start_date):
        try:
            # CPI 계산을 위해 시작일보다 1년 더 전부터 가져와야 함 (YoY 계산용 ㅋ)
            fetch_start = start_date - timedelta(days=365 + 30)
            raw_data = web.DataReader(['DGS3MO', 'CPIAUCNS'], 'fred', fetch_start, datetime.now())
            
            # CPI YoY 계산
            cpi_monthly = raw_data[['CPIAUCNS']].dropna()
            cpi_yoy = (cpi_monthly / cpi_monthly.shift(12) - 1) * 100
            cpi_yoy.columns = ['Inflation']
            
            # 데이터 병합 및 실질금리 계산 ㅋ
            df = raw_data[['DGS3MO']].rename(columns={'DGS3MO': 'US3M'})
            df = df.join(cpi_yoy).ffill()
            df['Real_Rate'] = df['US3M'] - df['Inflation']
            
            # 사용자가 선택한 날짜 이후 데이터만 반환 ㅋ
            return df[df.index >= pd.Timestamp(start_date)].dropna()
        except Exception as e:
            st.error(f"Real Rate Data Error: {e}")
            return pd.DataFrame()

    with st.spinner("Calculating Real Interest Rate Dynamics... ㅋ"):
        real_rate_df = get_real_rate_data_v82(rr_start_date)
    
    if not real_rate_df.empty:
        # 1. 상단 메트릭 섹션
        latest = real_rate_df.iloc[-1]
        prev = real_rate_df.iloc[-2] if len(real_rate_df) > 1 else latest
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Real Interest Rate", f"{latest['Real_Rate']:.2f}%", delta=f"{latest['Real_Rate'] - prev['Real_Rate']:.2f}%")
        m2.metric("Nominal Rate (US3M)", f"{latest['US3M']:.2f}%")
        m3.metric("Inflation (CPI YoY)", f"{latest['Inflation']:.2f}%")
        
        # 2. 차트 시각화
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=real_rate_df.index, y=real_rate_df['Real_Rate'], fill='tozeroy', mode='lines', name='Real Rate', line=dict(color='#00E676', width=2), fillcolor='rgba(0, 230, 118, 0.1)'))
        fig.add_trace(go.Scatter(x=real_rate_df.index, y=real_rate_df['Inflation'], mode='lines', name='Inflation', line=dict(color='#FF5252', width=1, dash='dot')))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=350, margin=dict(t=10, b=10, l=10, r=10), 
            xaxis=dict(gridcolor='#333'), yaxis=dict(gridcolor='#333'), 
            font=dict(color='#CCC'), legend=dict(orientation="h", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. [V82 핵심] 표준 캡션 추가 ㅋ
        actual_start_str = real_rate_df.index[0].strftime('%Y-%m-%d')
        st.caption(f"Analysis Start: {actual_start_str} | Source: Federal Reserve Bank of St. Louis (FRED)")
    else:
        st.warning("Data unavailable.")





# [C] Treasury Yield Trend (V79: 2-Year Default & Date Input ㅋ)
    st.markdown("---")
    st.subheader("U.S. TREASURY YIELD")

    # 1. 분석 기간 선택 (디폴트: 현재 시점 기준 2년 전 ㅋ)
    yield_col1, yield_col2 = st.columns([1, 2])
    with yield_col1:
        yield_default_start = datetime.now() - timedelta(days=365 * 2)
        yield_start_date = st.date_input(
            "Analysis Start Date", 
            value=yield_default_start, 
            key="treasury_yield_date"
        )

    # 2. 데이터 로드 로직 보강 ㅋ
    @st.cache_data(ttl=3600)
    def get_treasury_yields_v79(start_date):
        try:
            # 주요 만기 티커 (3M, 1Y, 2Y, 3Y, 5Y, 10Y, 20Y, 30Y)
            tickers = ['DGS3MO', 'DGS1', 'DGS2', 'DGS3', 'DGS5', 'DGS10', 'DGS20', 'DGS30']
            # 주말 데이터 유실 방지를 위해 7일 정도 더 일찍 가져옴 ㅋ
            fetch_start = start_date - timedelta(days=7)
            df = web.DataReader(tickers, 'fred', fetch_start, datetime.now())
            return df.ffill().dropna()
        except Exception as e:
            st.error(f"Treasury Data Error: {e}")
            return pd.DataFrame()

    with st.spinner("Accessing U.S. Treasury Data... ㅋ"):
        # 선택된 날짜에 맞춰 데이터 호출 ㅋ
        yields_df_raw = get_treasury_yields_v79(yield_start_date)
        # 선택한 날짜 이후로 정확히 필터링 ㅋ
        yields_df = yields_df_raw[yields_df_raw.index >= pd.Timestamp(yield_start_date)]
    
    if not yields_df.empty:
        # 1. 상단 메트릭 섹션
        latest = yields_df.iloc[-1]
        prev = yields_df.iloc[-2] if len(yields_df) > 1 else latest
        
        cols = st.columns(5)
        
        # 10Y-2Y Spread (장단기 금리차 감시 ㅋ)
        if 'DGS10' in latest and 'DGS2' in latest:
            inv_val = latest['DGS10'] - latest['DGS2']
            inv_prev = prev['DGS10'] - prev['DGS2']
            cols[0].metric("10Y-2Y Spread", f"{inv_val:.3f}%", 
                          delta=f"{inv_val - inv_prev:.3f}%", delta_color="normal")
        
        # 주요 만기별 메트릭
        keys = [('DGS3MO', '3M'), ('DGS2', '2Y'), ('DGS10', '10Y'), ('DGS30', '30Y')]
        for i, (tic, lab) in enumerate(keys):
            if tic in latest:
                cols[i+1].metric(lab, f"{latest[tic]:.2f}%", 
                                delta=f"{latest[tic]-prev[tic]:.3f}%", delta_color="normal")
            
        # 2. Yield Trend 시각화
        fig_y = go.Figure()
        neon_colors = ['#D500F9', '#7C4DFF', '#00B0FF', '#00E676']
        plot_ticks = [('DGS3MO', '3M'), ('DGS2', '2Y'), ('DGS10', '10Y'), ('DGS30', '30Y')]
        
        active_cols = [t for t, l in plot_ticks if t in yields_df.columns]
        plot_min = yields_df[active_cols].min().min() if active_cols else 0
        plot_max = yields_df[active_cols].max().max() if active_cols else 5

        for i, (tick, label) in enumerate(plot_ticks):
            if tick in yields_df.columns:
                 fig_y.add_trace(go.Scatter(
                     x=yields_df.index, y=yields_df[tick], 
                     mode='lines', name=label,
                     line=dict(width=1.8, color=neon_colors[i])
                 ))
            
        fig_y.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
            height=450, margin=dict(t=10, b=10, l=10, r=10), 
            xaxis=dict(showgrid=False, tickfont=dict(color='#888')), 
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#888'),
                zeroline=False, range=[plot_min * 0.95, plot_max * 1.05]
            ), 
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(color='#CCC')
            ),
            hovermode='x unified'
        )
        
        # [V81] 차트 출력 및 캡션 스타일 통일 ㅋ
        st.plotly_chart(fig_y, use_container_width=True, config={'displayModeBar': False})
        
        # CORPORATE BOND 섹션과 동일한 폰트/스타일 적용 ㅋ
        actual_start_str = yields_df.index[0].strftime('%Y-%m-%d')
        st.caption(f"Analysis Start: {actual_start_str} | Source: Federal Reserve Bank of St. Louis (FRED)")
    else:
        st.info("국채 금리 데이터를 스캔하는 중입니다...")





    # [D] CORPORATE BOND YIELD TRACKER (V145: FRED Data)
    st.markdown("---")
    st.subheader("U.S. CORPORATE BOND YIELDS")
    
    # 1. FRED 티커 및 스타일 설정
    bond_config = {
        "AAA Grade": {"ticker": "BAMLC0A1CAAAEY", "color": "#00E676"},   # Green
        "BBB Grade": {"ticker": "BAMLC0A4CBBBEY", "color": "#FFC107"},   # Orange/Gold
        "High Yield": {"ticker": "BAMLH0A0HYM2EY", "color": "#FF5252"}   # Red
    }
    
    # 2. 입력 도구
    bond_col1, bond_col2 = st.columns([1, 2])
    with bond_col1:
        # bond_start_date = st.date_input("Bond Analysis Start Date", value=datetime(2025, 1, 1), key="bond_start")
        bond_default_start = datetime.now() - timedelta(days=365)
        bond_start_date = st.date_input("Analysis Start Date", value=bond_default_start, key="bond_start")
    
    with bond_col2:
        selected_bonds = st.multiselect(
            "Select Bond Grades",
            options=list(bond_config.keys()),
            default=list(bond_config.keys()),
            key="bond_select"
        )
    
    # 3. 데이터 로드 및 시각화
    if selected_bonds:
        with st.spinner("Accessing FRED Bond Data..."):
            bond_tickers = [bond_config[l]["ticker"] for l in selected_bonds]
            # FRED 데이터는 pandas_datareader(web)를 사용하는 것이 가장 안정적입니다.
            try:
                bond_data = web.DataReader(bond_tickers, 'fred', bond_start_date, datetime.now())
                
                if not bond_data.empty:
                    bond_data = bond_data.ffill().dropna()
                    
                    # [레전드 순서 강제 고정]
                    priority_order = [bond_config[k]["ticker"] for k in bond_config.keys()]
                    final_order = [t for t in priority_order if t in bond_data.columns]
                    bond_data = bond_data[final_order]
                    
                    fig_bond = go.Figure()
                    
                    for ticker in bond_data.columns:
                        label = [k for k, v in bond_config.items() if v["ticker"] == ticker][0]
                        conf = bond_config[label]
                        
                        # High Yield는 더 굵게 표시하여 리스크 강조
                        line_width = 1.5 if label == "High Yield" else 1.5
                        
                        fig_bond.add_trace(go.Scatter(
                            x=bond_data.index, 
                            y=bond_data[ticker], 
                            mode='lines', 
                            name=label,
                            line=dict(width=line_width, color=conf["color"]),
                            hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"
                        ))
                    
                    fig_bond.update_layout(
                        hovermode="x unified",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=550,
                        margin=dict(t=10, b=10, l=10, r=10),
                        yaxis=dict(title="Yield (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666', ticksuffix="%"),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, traceorder="normal")
                    )
                    st.plotly_chart(fig_bond, use_container_width=True)
                    bond_actual_base = bond_data.index[0].strftime('%Y-%m-%d')
                    st.caption(f"Analysis Start: {bond_actual_base} | Source: Federal Reserve Bank of St. Louis (FRED)")
            except Exception as e:
                st.error(f"FRED Data Stream Offline: {e}")



    # [E] Macro Indicators Radar (V92: PCE % Swap & Final Tuning)
    st.markdown("---")
    st.subheader("MACRO INDICATORS RADAR")

    radar_indicators = {
        "Leading": {
            "T10Y2Y": "10Y-2Y Spread",
            "ICSA": "Initial Claims",
            "MICH": "Inflation Expectation",
            "BAMLH0A0HYM2": "High Yield Spread"
        },
        "Coincident": {
            "PAYEMS": "Nonfarm Payrolls",
            "INDPRO": "Industrial Production",
            "DPCCRV1Q225SBEA": "Personal Consumption", # % 변동률 지표로 교체
            "CMRMTSPL": "Real Manufacturing Sales"
        },
        "Lagging": {
            "UNRATE": "Unemployment Rate",
            "BUSLOANS": "Commercial Loans",
            "CP": "Corporate Profits",
            "DRCCLACBS": "Credit Card Delinquency Rate"
        }
    }

    tabs = st.tabs(list(radar_indicators.keys()))
    neon_colors = ['#D500F9', '#7C4DFF', '#00B0FF', '#00E676']

    for i, tab in enumerate(tabs):
        with tab:
            category = list(radar_indicators.keys())[i]
            cols = st.columns(4) 
            for j, (ticker, name) in enumerate(radar_indicators[category].items()):
                try:
                    # 데이터 호출 (분기별 지표 대응을 위해 900일 확보)
                    df_raw = web.get_data_fred(ticker, start=datetime.now() - timedelta(days=900)).ffill()
                    
                    if not df_raw.empty:
                        val_latest = df_raw.iloc[-1, 0]
                        val_prev = df_raw.iloc[-2, 0]
                        delta_val = val_latest - val_prev
                        
                        # --- 단위 및 출력 포맷 최적화 ---
                        # 1. 퍼센트 기반 지표 (신규 PCE 포함)
                        if "%" in name or ticker in ["T10Y2Y", "UNRATE", "MICH", "BAMLH0A0HYM2", "DRCCLACBS", "DPCCRV1Q225SBEA"]:
                            display_val = f"{val_latest:.2f}%"
                            delta_str = f"{delta_val:.2f}%"
                        # 2. 고용 지표 (Millions)
                        elif ticker == "PAYEMS":
                            display_val = f"{val_latest/1000:,.1f}M"
                            delta_str = f"{delta_val/1000:,.2f}M"
                        # 3. 달러 기반 대형 지표 (Billions)
                        elif "$B" in name:
                            div = 1000 if ticker == "CMRMTSPL" else 1
                            display_val = f"${val_latest/div:,.1f}B"
                            delta_str = f"${delta_val/div:,.2f}B"
                        else:
                            display_val = f"{val_latest:,.1f}"
                            delta_str = f"{delta_val:,.2f}"

                        with cols[j]:
                            st.metric(label=name, value=display_val, delta=delta_str, delta_color="normal")
                            
                            # 미니 차트 (더 굵고 선명하게)
                            fig_mini = px.line(df_raw.tail(15), y=df_raw.columns[0])
                            fig_mini.update_traces(line_color=neon_colors[i], width=3)
                            fig_mini.update_layout(
                                height=70, margin=dict(t=5, b=5, l=0, r=0),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False
                            )
                            st.plotly_chart(fig_mini, use_container_width=True, config={'displayModeBar': False})
                except:
                    pass

    # [V93] 매크로 섹션 최종 출처 표기
    st.caption("Source: Federal Reserve Bank of St. Louis (FRED)")

    # 매크로 섹션의 진짜 마지막 지점에서 딱 한 번 멈춥니다.
    st.stop()








# --- MARKET MODULE (V102: Absolute Size Enforcement) ---
elif menu == "Market":

    st.title("MARKET INTELLIGENCE")
    
    # [A] RELATIVE PERFORMANCE ANALYZER (V116: Bitcoin Color Fixed)
    st.markdown("---")
    st.subheader("GLOBAL INDICES PERFORMANCE")
    
    # 티커 매핑
    compare_tickers = {
        "Bitcoin": "BTC-USD",
        "Total World (VT)": "VT",
        "S&P 500": "^GSPC",
        "Nasdaq 100": "^NDX",
        "Russell 2000": "^RUT",
        "Shanghai": "000001.SS",
        "Nikkei 225": "^N225",
        "KOSPI": "^KS11",
        "India (Nifty 500)": "^CRSLDX",
        "Vietnam (VN)": "^VNINDEX",        
        "FTSE 100": "^FTSE",
        "DAX": "^GDAXI",
        "CAC 40": "^FCHI"
    }
    
    input_col1, input_col2 = st.columns([1, 2])
    with input_col1:
        default_start = datetime.now() - timedelta(days=365)
        start_date = st.date_input("Analysis Start Date", value=default_start, key="global_perf_date")
        
    with input_col2:
        selected_labels = st.multiselect(
            "Select Indices to Compare", 
            options=list(compare_tickers.keys()),
            default=["Bitcoin", "Total World (VT)", "S&P 500", "Shanghai", "Nikkei 225", "KOSPI", "FTSE 100", "DAX", "CAC 40"],
            key="global_perf_select"
        )
    
    if selected_labels:
        with st.spinner("Fetching Global Market Data..."):
            selected_tickers = [compare_tickers[l] for l in selected_labels]
            data = yf.download(selected_tickers, start=start_date)['Close']
            
            if not data.empty:
                data = data.ffill().dropna()
                if not data.empty:
                    # [V138: 레전드 순서 고정 로직]
                    # 1. 우선 순위 리스트 정의 (티커 기준)
                    priority_tickers = [compare_tickers["Bitcoin"], compare_tickers["Total World (VT)"], compare_tickers["S&P 500"]]
                    
                    # 2. 현재 데이터프레임 컬럼 중 우선 순위에 없는 나머지 티커들 추출
                    remaining_tickers = [t for t in data.columns if t not in priority_tickers]
                    
                    # 3. 전체 순서 합치기 (우선순위 + 나머지)
                    # 데이터에 실제로 존재하는 티커만 필터링하여 순서 재배치
                    final_order = [t for t in priority_tickers if t in data.columns] + remaining_tickers
                    data = data.reindex(columns=final_order)

                    # 수익률 계산
                    norm_df = (data / data.iloc[0] - 1) * 100
                    
                    fig_perf = go.Figure()
                    
                    # 이제 정렬된 데이터프레임 순서대로 루프를 돕니다.
                    for ticker in data.columns:
                        label = [k for k, v in compare_tickers.items() if v == ticker][0]
                        
                        # [핵심] 비트코인 및 주요 지수 스타일 지정
                        if label == "Bitcoin":
                            line_config = dict(width=3, color="#F7931A") 
                        elif label == "KOSPI":
                            line_config = dict(width=1.5, color="#00B0FF")
                        elif label == "S&P 500":
                            line_config = dict(width=1.5, color="#00E676") # S&P500 강조 (옵션)
                        else:
                            line_config = dict(width=1.5) 
                        
                        fig_perf.add_trace(go.Scatter(
                            x=norm_df.index, 
                            y=norm_df[ticker], 
                            mode='lines', 
                            name=label,
                            line=line_config, 
                            hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"
                        ))
                    
                    fig_perf.update_layout(
                        hovermode="x unified",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=550,
                        margin=dict(t=10, b=10, l=10, r=10),
                        yaxis=dict(title="Return (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                        # traceorder를 'normal'로 두면 add_trace한 순서대로 레전드가 나옵니다.
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, traceorder="normal")
                    )
                    st.plotly_chart(fig_perf, use_container_width=True)
                    st.caption(f"Base Date: {data.index[0].strftime('%Y-%m-%d')} (Normalized to 0%) | Source: Yahoo Finance & Global Exchange Data")




    # [B] U.S. INDEX ETF PERFORMANCE ANALYZER (V111: Date & Color Customization)
    st.markdown("---")
    st.subheader("U.S. INDEX ETF PERFORMANCE")
    
    # 1. 티커 및 커스텀 색상 매핑
    # 성진님 요청: S&P500(Green), Russell(Gold/SPY색상), Nasdaq(Orange/RUT색상)
    etf_config = {
        "S&P 500 (SPY)": {"ticker": "SPY", "color": "#00E676"},   # 초록색
        "Nasdaq 100 (QQQ)": {"ticker": "QQQ", "color": "#00B0FF"}, # 기존 러셀 색상(Orange)
        "Dow 30 (DIA)": {"ticker": "DIA", "color": "#87CEEB"},    # 스카이블루
        "Russell 2000 (IWM)": {"ticker": "IWM", "color": "#FF5252"} # 기존 S&P 색상(Gold)
    }
    
    # 2. 입력 도구 상단 배치
    etf_input_col1, etf_input_col2 = st.columns([1, 2])
    
    with etf_input_col1:
        # [수정] 디폴트 시작 날짜를 2026년 1월 1일로 고정
        etf_default_start = datetime.now() - timedelta(days=365)
        etf_start_date = st.date_input("Analysis Start Date", value=etf_default_start, key="etf_start_date_v111")
        
    with etf_input_col2:
        selected_etfs = st.multiselect(
            "Select ETFs to Compare", 
            options=list(etf_config.keys()),
            default=list(etf_config.keys()),
            key="etf_select_v111"
        )
    
    # 3. 데이터 로드 및 수익률 계산
    if selected_etfs:
        with st.spinner("Fetching ETF Market Data..."):
            target_tickers = [etf_config[l]["ticker"] for l in selected_etfs]
            etf_data = yf.download(target_tickers, start=etf_start_date)['Close']
            
            if not etf_data.empty:
                # [V140: MultiIndex 대응 및 순서 고정 로직]
                etf_data = etf_data.ffill().dropna()
                
                if not etf_data.empty:
                    # 1. 성진님이 정의한 etf_config의 티커 순서 추출
                    priority_tickers = [etf_config[k]["ticker"] for k in etf_config.keys()]
                    
                    # 2. 실제 다운로드된 데이터의 컬럼 리스트 확인
                    # MultiIndex인 경우를 대비해 columns.get_level_values를 고려한 안전한 추출
                    available_cols = etf_data.columns.tolist()
                    
                    # 3. 데이터에 존재하는 티커만 우선순위대로 필터링
                    final_order = [t for t in priority_tickers if t in available_cols]
                    
                    # 4. 순서 재배치 (여기서 오류가 주로 발생하므로 reindex 대신 직접 컬럼 슬라이싱)
                    etf_data = etf_data[final_order]
                    
                    # 수익률 계산
                    etf_norm_df = (etf_data / etf_data.iloc[0] - 1) * 100
                    
                    fig_etf = go.Figure()
                    
                    # 5. 정렬된 컬럼 순서대로 루프 실행
                    for ticker in etf_data.columns:
                        # 티커에 해당하는 라벨과 색상 매핑
                        label = [k for k, v in etf_config.items() if v["ticker"] == ticker][0]
                        line_color = etf_config[label]["color"]
                        
                        fig_etf.add_trace(go.Scatter(
                            x=etf_norm_df.index, 
                            y=etf_norm_df[ticker], 
                            mode='lines', 
                            name=label,
                            line=dict(width=1.5, color=line_color),
                            hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"
                        ))
                    
                    fig_etf.update_layout(
                        hovermode="x unified",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=550,
                        margin=dict(t=10, b=10, l=10, r=10),
                        yaxis=dict(title="Return (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                        # 트레이스 추가 순서대로 레전드 표시
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, traceorder="normal")
                    )
                    st.plotly_chart(fig_etf, use_container_width=True)
                    st.caption(f"Base Date: {etf_data.index[0].strftime('%Y-%m-%d')} (Normalized to 0%) | Source: Yahoo Finance & Global Exchange Data")





    # [C] SECTOR PERFORMANCE ANALYZER (V120: SPY Priority & Dot Style ㅋ)
    st.markdown("---")
    st.subheader("U.S. SECTOR PERFORMANCE")
    
    # 1. 섹터 ETF 및 컬러 매핑
    sector_config = {
        "S&P 500 (SPY)": {"ticker": "SPY", "color": "#FFFFFF", "width": 3, "dash": "dot"}, # [수정] 점선 스타일 추가 ㅋ
        "Tech-Expanded (IGM)": {"ticker": "IGM", "color": "#1E90FF", "width": 1.5, "dash": "solid"},
        "Software (IGV)": {"ticker": "IGV", "color": "#00FFFF", "width": 1.5, "dash": "solid"},
        "Semiconductor (SOXX)": {"ticker": "SOXX", "color": "#FF00FF", "width": 1.5, "dash": "solid"},
        "Biotech (IBB)": {"ticker": "IBB", "color": "#008000", "width": 1.5, "dash": "solid"},
        "Medical Devices (IHI)": {"ticker": "IHI", "color": "#FF0000", "width": 1.5, "dash": "solid"},
        "Genomics (IDNA)": {"ticker": "IDNA", "color": "#FFFF00", "width": 1.5, "dash": "solid"},
        "Aerospace (ITA)": {"ticker": "ITA", "color": "#FFA500", "width": 1.5, "dash": "solid"},
        "Clean Energy (POW)": {"ticker": "POW", "color": "#00FF00", "width": 1.5, "dash": "solid"},
        "Oil & Gas (IEO)": {"ticker": "IEO", "color": "#808080", "width": 1.5, "dash": "solid"},
        "Utilities (IDU)": {"ticker": "IDU", "color": "#EC83B2", "width": 1.5, "dash": "solid"},
        "Consumer Disc (IYC)": {"ticker": "IYC", "color": "#800080", "width": 1.5, "dash": "solid"},
        "Financials (IYF)": {"ticker": "IYF", "color": "#008080", "width": 1.5, "dash": "solid"},
        "Fintech (ARKF)": {"ticker": "ARKF", "color": "#FFC0CB", "width": 1.5, "dash": "solid"},
        "Industrials (IYJ)": {"ticker": "IYJ", "color": "#8B4513", "width": 1.5, "dash": "solid"},
        "Materials (IYM)": {"ticker": "IYM", "color": "#484DC4", "width": 1.5, "dash": "solid"}
    }
    
    # 2. 입력 도구 (1년 트래킹 유지 ㅋ)
    sec_in_col1, sec_in_col2 = st.columns([1, 2])
    with sec_in_col1:
        sec_default_start = datetime.now() - timedelta(days=365)
        sec_start_date = st.date_input("Analysis Start Date", value=sec_default_start, key="sec_start")
    
    with sec_in_col2:
        selected_sectors = st.multiselect(
            "Select Sectors to Compare", 
            options=list(sector_config.keys()),
            default=["S&P 500 (SPY)", "Tech-Expanded (IGM)", "Semiconductor (SOXX)", "Software (IGV)", "Materials (IYM)", "Clean Energy (POW)", "Oil & Gas (IEO)", "Aerospace (ITA)", "Genomics (IDNA)"],
            key="sec_select"
        )
    
    # 3. 데이터 로드 및 시각화
    if selected_sectors:
        with st.spinner("Scanning Sector Rotation... ㅋ"):
            sec_target_tickers = [sector_config[l]["ticker"] for l in selected_sectors]
            sec_raw_data = yf.download(sec_target_tickers, start=sec_start_date, progress=False)['Close']
            
            if not sec_raw_data.empty:
                sec_raw_data = sec_raw_data.ffill().dropna()
                
                # [V120 핵심] SPY가 가장 먼저 오도록 컬럼 순서 재배치 ㅋ
                if "SPY" in sec_raw_data.columns:
                    other_cols = [c for c in sec_raw_data.columns if c != "SPY"]
                    sec_raw_data = sec_raw_data[["SPY"] + other_cols]
                
                sec_norm_df = (sec_raw_data / sec_raw_data.iloc[0] - 1) * 100
                
                fig_sec = go.Figure()
                
                # 재배치된 순서대로 trace 추가 (레전드 순서 결정 ㅋ)
                for ticker in sec_raw_data.columns:
                    label = [k for k, v in sector_config.items() if v["ticker"] == ticker][0]
                    conf = sector_config[label]
                    
                    fig_sec.add_trace(go.Scatter(
                        x=sec_norm_df.index, 
                        y=sec_norm_df[ticker], 
                        mode='lines', 
                        name=label,
                        line=dict(
                            width=conf["width"], 
                            color=conf["color"],
                            dash=conf.get("dash", "solid") # SPY는 dot, 나머지는 solid ㅋ
                        ),
                        hovertemplate=f"<b>{label}</b>: %{{y:.2f}}%<extra></extra>"
                    ))
                
                fig_sec.update_layout(
                    hovermode="x unified",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=600,
                    margin=dict(t=10, b=10, l=10, r=10),
                    yaxis=dict(title="Return (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", y=1.02, 
                        xanchor="right", x=1,
                        traceorder="normal" # 추가한 순서(SPY 우선)대로 표시 ㅋ
                    )
                )
                st.plotly_chart(fig_sec, use_container_width=True)
                st.caption(f"Base Date: {sec_raw_data.index[0].strftime('%Y-%m-%d')} (Normalized to 0.00%) | Source: Yahoo Finance & Global Exchange Data")





    # [D] GROWTH vs VALUE ROTATION ANALYZER (V117)
    st.markdown("---")
    st.subheader("GROWTH vs VALUE")
    
    # 1. 입력 도구 (기존 스타일 유지, 2026/01/01 디폴트)
    rot_in_col1, rot_in_col2 = st.columns([1, 2])
    with rot_in_col1:
        # [수정 포인트] 2026년 고정 대신 현재로부터 365일 전으로 설정 ㅋ
        rot_default_start = datetime.now() - timedelta(days=365)
        rot_start_date = st.date_input(
            "Analysis Start Date", 
            value=rot_default_start, 
            key="rot_start"
        )
    
    # 2. 데이터 로드 (VUG, VTV)
    with st.spinner("Analyzing Style Rotation..."):
        rot_tickers = ["VUG", "VTV"]
        rot_data = yf.download(rot_tickers, start=rot_start_date)['Close']
        
        if not rot_data.empty:
            rot_data = rot_data.ffill().dropna()
            
            # 수익률 표준화 (0% 기준)
            rot_norm = (rot_data / rot_data.iloc[0] - 1) * 100
            
            # 성장주/가치주 비율 계산 (VUG / VTV)
            # 이 비율이 상승하면 성장주 우위, 하락하면 가치주 우위입니다.
            ratio = rot_data["VUG"] / rot_data["VTV"]
            ratio_norm = (ratio / ratio.iloc[0] - 1) * 100 # 비율도 변화율로 변환
            
            # 차트 생성 (수익률 비교 + 비율 변화)
            fig_rot = go.Figure()
            
            # [V119 핵심] 레전드 순서 1번: Growth/Value Ratio (화이트 강조선) ㅋ
            fig_rot.add_trace(go.Scatter(
                x=ratio_norm.index, y=ratio_norm,
                mode='lines', name="Growth/Value Ratio",
                line=dict(width=3, color="#FFFFFF", dash='dot'), # 점선 유지 ㅋ
                hovertemplate="Ratio Change: %{y:.2f}%<extra></extra>"
            ))

            # 레전드 순서 2번: 성장주 (VUG)
            fig_rot.add_trace(go.Scatter(
                x=rot_norm.index, y=rot_norm["VUG"],
                mode='lines', name="Growth (VUG)",
                line=dict(width=1.5, color="#00E5FF"),
                hovertemplate="Growth: %{y:.2f}%<extra></extra>"
            ))
            
            # 레전드 순서 3번: 가치주 (VTV)
            fig_rot.add_trace(go.Scatter(
                x=rot_norm.index, y=rot_norm["VTV"],
                mode='lines', name="Value (VTV)",
                line=dict(width=1.5, color="#FFC107"),
                hovertemplate="Value: %{y:.2f}%<extra></extra>"
            ))
            
            fig_rot.update_layout(
                hovermode="x unified",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=550,
                margin=dict(t=10, b=10, l=10, r=10),
                yaxis=dict(title="Performance / Ratio Change (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", y=1.02, 
                    xanchor="right", x=1,
                    traceorder="normal" # 코딩한 순서(Ratio -> Growth -> Value) 강제 유지 ㅋ
                )
            )
            
            st.plotly_chart(fig_rot, use_container_width=True)
            st.caption(f"Base Date: {rot_data.index[0].strftime('%Y-%m-%d')} (Normalized to 0%) | Source: Yahoo Finance & Global Exchange Data")

            # 3. 전략적 코멘트
            current_ratio = ratio_norm.iloc[-1]
            status = "성장주 우위" if current_ratio > 0 else "가치주 우위"
            st.info(f"**Insight:** 기준일 대비 **{status}** 상태입니다. (Ratio 변동률: {current_ratio:.2f}%)")




    # [F] COMMODITIES & DOLLAR INDEX RADAR (V121: Sequence Enforcement)
    st.markdown("---")
    st.subheader("COMMODITIES PERFORMANCE") 

    # 1. 딕셔너리 순서 및 스타일 업데이트
    com_config = {
        "Dollar Index (DXY)": {
            "ticker": "DX-Y.NYB", 
            "color": "#FFFFFF", 
            "width": 3, 
            "dash": "dot"  # [업데이트] 점선 스타일 추가
        },
        
        "Gold": {"ticker": "GC=F", "color": "#FFD700", "width": 1.5, "dash": "solid"},
        "Copper": {"ticker": "HG=F", "color": "#B87333", "width": 1.5, "dash": "solid"},        
        "Silver": {
            "ticker": "SI=F", 
            "color": "#1E90FF", # [업데이트] DodgerBlue (달러와 확실히 구분됨)
            "width": 1.5, 
            "dash": "solid"
        },
        "Palladium": {"ticker": "PA=F", "color": "#CED4DA", "width": 1.5, "dash": "solid"},
        "Platinum": {"ticker": "PL=F", "color": "#E5E4E2", "width": 1.5, "dash": "solid"},
        "WTI Crude": {"ticker": "CL=F", "color": "#FF4500", "width": 1.5, "dash": "solid"},
        "Brent Oil": {"ticker": "BZ=F", "color": "#8B0000", "width": 1.5, "dash": "solid"},
        "Natural Gas": {"ticker": "NG=F", "color": "#00CED1", "width": 1.5, "dash": "solid"},
    }
    
    # 2. 입력 도구 (기존과 동일)
    com_in_col1, com_in_col2 = st.columns([1, 2])
    with com_in_col1:
        # [수정 포인트] 현재 시점으로부터 365일 전으로 디폴트 설정 ㅋ
        com_default_start = datetime.now() - timedelta(days=365)
        com_start_date = st.date_input(
            "Analysis Start Date", 
            value=com_default_start, 
            key="com_start_v121"
        )
    with com_in_col2:
        selected_coms = st.multiselect(
            "Select Commodities to Compare", 
            options=list(com_config.keys()),
            default=["Dollar Index (DXY)", "Gold", "Silver", "Copper", "WTI Crude", "Natural Gas"],
            key="com_select_v121"
        )
    
    # 3. 데이터 로드 및 시각화
    if selected_coms:
        with st.spinner("Scanning Commodity Markets..."):
            com_target_tickers = [com_config[l]["ticker"] for l in selected_coms]
            com_raw_data = yf.download(com_target_tickers, start=com_start_date)['Close']
            
            if not com_raw_data.empty:
                # [핵심] 알파벳 순으로 정렬된 컬럼을 우리가 선택한 순서(com_target_tickers)대로 재배치
                com_raw_data = com_raw_data.reindex(columns=com_target_tickers)
                
                com_raw_data = com_raw_data.ffill().dropna()
                if not com_raw_data.empty:
                    com_norm_df = (com_raw_data / com_raw_data.iloc[0] - 1) * 100
                    
                    fig_com = go.Figure()
                    
                    # 이제 정렬된 데이터프레임 순서대로 루프를 돌기 때문에 레전드가 순서대로 나옵니다.
                    for ticker in com_norm_df.columns:
                        label = [k for k, v in com_config.items() if v["ticker"] == ticker][0]
                        conf = com_config[label]
                        
                        fig_com.add_trace(go.Scatter(
                            x=com_norm_df.index, 
                            y=com_norm_df[ticker], 
                            mode='lines', 
                            name=label,
                            line=dict(width=conf["width"], color=conf["color"], 
                            dash=conf.get("dash", "solid")),
                            hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"
                        ))
                    
                    fig_com.update_layout(
                        hovermode="x unified",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=550,
                        margin=dict(t=10, b=10, l=10, r=10),
                        yaxis=dict(title="Return (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_com, use_container_width=True)
                    st.caption(f"Base Date: {rot_data.index[0].strftime('%Y-%m-%d')} (Normalized to 0%) | Source: Yahoo Finance & Global Exchange Data")



    # [G] COPPER / GOLD RATIO ANALYZER (V122: The Economic Pulse)
    st.markdown("---")
    st.subheader("COPPER/GOLD RATIO")
    
    # 1. 입력 도구 (2026/01/01 디폴트)
    cgr_in_col1, cgr_in_col2 = st.columns([1, 2])
    with cgr_in_col1:
        # [수정 포인트] 현재 시점으로부터 365일 전으로 디폴트 설정 ㅋ
        cgr_default_start = datetime.now() - timedelta(days=365)
        cgr_start_date = st.date_input(
            "Analysis Start Date", 
            value=cgr_default_start, 
            key="cgr_start"
        )
    
    # 2. 데이터 로드 (Copper: HG=F, Gold: GC=F)
    with st.spinner("Calculating Economic Pulse..."):
        cgr_tickers = ["HG=F", "GC=F"]
        cgr_data = yf.download(cgr_tickers, start=cgr_start_date)['Close']
        
        if not cgr_data.empty:
            cgr_data = cgr_data.ffill().dropna()
            
            # 수익률 표준화 (0% 기준)
            cgr_norm = (cgr_data / cgr_data.iloc[0] - 1) * 100
            
            # Copper / Gold Ratio 계산
            cg_ratio = cgr_data["HG=F"] / cgr_data["GC=F"]
            cg_ratio_norm = (cg_ratio / cg_ratio.iloc[0] - 1) * 100 # 비율의 변화율
            
            # 차트 생성
            fig_cgr = go.Figure()
            
            # [V124 핵심] 레전드 순서 1번: Copper/Gold Ratio (화이트 강조 점선) ㅋ
            fig_cgr.add_trace(go.Scatter(
                x=cg_ratio_norm.index, y=cg_ratio_norm,
                mode='lines', name="Copper/Gold Ratio",
                line=dict(width=3, color="#FFFFFF", dash='dot'), # 화이트 점선 유지 ㅋ
                hovertemplate="Ratio Change: %{y:.2f}%<extra></extra>"
            ))
            
            # 레전드 순서 2번: Copper (HG=F)
            fig_cgr.add_trace(go.Scatter(
                x=cgr_norm.index, y=cgr_norm["HG=F"],
                mode='lines', name="Copper (HG=F)",
                line=dict(width=1.5, color="#B87333"),
                hovertemplate="Copper: %{y:.2f}%<extra></extra>"
            ))
            
            # 레전드 순서 3번: Gold (GC=F)
            fig_cgr.add_trace(go.Scatter(
                x=cgr_norm.index, y=cgr_norm["GC=F"],
                mode='lines', name="Gold (GC=F)",
                line=dict(width=1.5, color="#FFD700"),
                hovertemplate="Gold: %{y:.2f}%<extra></extra>"
            ))
            
            fig_cgr.update_layout(
                hovermode="x unified",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=550,
                margin=dict(t=10, b=10, l=10, r=10),
                yaxis=dict(title="Performance / Ratio Change (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(
                    orientation="h", 
                    yanchor="bottom", y=1.02, 
                    xanchor="right", x=1,
                    traceorder="normal" # 추가한 순서(Ratio 우선) 강제 적용 ㅋ
                )
            )
            
            st.plotly_chart(fig_perf_cgr if 'fig_perf_cgr' in locals() else fig_cgr, use_container_width=True)
            st.caption(f"Base Date: {cgr_data.index[0].strftime('%Y-%m-%d')} (Normalized to 0%) | Source: Yahoo Finance & Global Exchange Data")
            
            # 3. 전략적 진단
            current_cgr = cg_ratio_norm.iloc[-1]
            cgr_status = "경기 확장/인플레이션 압력" if current_cgr > 0 else "경기 둔화/디플레이션 우려"
            st.info(f"**Insight:** 기준일 대비 Copper/Gold 비율이 **{current_cgr:.2f}% { '상승' if current_cgr > 0 else '하락' }**하여, **{cgr_status}** 시그널을 보이고 있습니다.")

    st.stop()










# --- MARKET MODULE (V102: Absolute Size Enforcement) ---
elif menu == "Crypto":

    st.title("CRYPTO INTELLIGENCE")
    
    # [A] TOP 10 CRYPTO PERFORMANCE (Excl. Stablecoins)
    st.markdown("---")
    st.subheader("TOP 10 CRYPTO PERFORMANCE")
    
    # 1. 시총 상위 10개 코인 티커 매핑 (스테이블코인 제외)
    crypto_config = {
        "Bitcoin": {"ticker": "BTC-USD", "color": "#F7931A", "width": 3},   # BTC 오렌지색
        "Ethereum": {"ticker": "ETH-USD", "color": "#627EEA", "width": 1.5},  # ETH 블루
        "Solana": {"ticker": "SOL-USD", "color": "#AF52DE", "width": 1.5},
        "BNB": {"ticker": "BNB-USD", "color": "#F3BA2F", "width": 1.5},
        "XRP": {"ticker": "XRP-USD", "color": "#14F195", "width": 1.5},
        "Cardano": {"ticker": "ADA-USD", "color": "#0033AD", "width": 1.5},
        "Avalanche": {"ticker": "AVAX-USD", "color": "#E84142", "width": 1.5},
        "Dogecoin": {"ticker": "DOGE-USD", "color": "#C2A633", "width": 1.5},
        "Tron": {"ticker": "TRX-USD", "color": "#FF0013", "width": 1.5},
        "Chainlink": {"ticker": "LINK-USD", "color": "#2A5ADA", "width": 1.5}
    }
    
    # 2. 입력 도구
    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        # 비트코인 표준에 맞춰 올해 초부터를 기본값으로 설정
        crypto_default_start = datetime.now() - timedelta(days=365)
        crypto_start_date = st.date_input("Analysis Start Date", value=crypto_default_start, key="crypto_perf_date")
        
    with c_col2:
        selected_cryptos = st.multiselect(
            "Select Assets to Compare", 
            options=list(crypto_config.keys()),
            default=["Bitcoin", "Ethereum", "Solana", "BNB", "XRP", "Cardano", "Avalanche", "Dogecoin", "Tron", "Chainlink"], # 주요 코인 기본 선택
            key="crypto_perf_select"
        )
    
    # 3. 데이터 로드 및 시각화
    if selected_cryptos:
        with st.spinner("Syncing with Blockchain Data (via yfinance)..."):
            c_target_tickers = [crypto_config[l]["ticker"] for l in selected_cryptos]
            c_data = yf.download(c_target_tickers, start=crypto_start_date)['Close']
            
            if not c_data.empty:
                c_data = c_data.ffill().dropna()
                
                if not c_data.empty:
                    # [레전드 순서 고정] 정의한 crypto_config 순서대로
                    c_priority = [crypto_config[k]["ticker"] for k in crypto_config.keys()]
                    c_final_order = [t for t in c_priority if t in c_data.columns]
                    c_data = c_data[c_final_order]
                    
                    # 수익률 계산
                    c_norm_df = (c_data / c_data.iloc[0] - 1) * 100
                    
                    fig_crypto = go.Figure()
                    
                    for ticker in c_data.columns:
                        label = [k for k, v in crypto_config.items() if v["ticker"] == ticker][0]
                        conf = crypto_config[label]
                        
                        fig_crypto.add_trace(go.Scatter(
                            x=c_norm_df.index, 
                            y=c_norm_df[ticker], 
                            mode='lines', 
                            name=label,
                            line=dict(width=conf["width"], color=conf["color"]),
                            hovertemplate=f"{label}: %{{y:.2f}}%<extra></extra>"
                        ))
                    
                    fig_crypto.update_layout(
                        hovermode="x unified",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=550,
                        margin=dict(t=10, b=10, l=10, r=10),
                        yaxis=dict(title="Return (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, traceorder="normal")
                    )
                    st.plotly_chart(fig_crypto, use_container_width=True)
                    st.caption(f"Base Date: {c_data.index[0].strftime('%Y-%m-%d')} (Normalized to 0.00%) | Source: Yahoo Finance & Global Exchange Data")




    # [B] BITCOIN 217-WEEK CYCLE RADAR (V202: Clean RSI)
    st.markdown("---")
    st.subheader("BTC TECHNICAL RADAR")

    tech_col1, tech_col2 = st.columns([1, 2])
    with tech_col1:
        tech_start_date = st.date_input("Analysis Start Date", value=datetime.now() - timedelta(days=365*2), key="btc_tech_v202")

    with st.spinner("Calculating Strategic Indicators..."):
        fetch_start_long = tech_start_date - timedelta(days=365*6)
        btc_raw = yf.download("BTC-USD", start=fetch_start_long, interval='1d', progress=False)
        
        if not btc_raw.empty:
            if isinstance(btc_raw.columns, pd.MultiIndex):
                d_prices = btc_raw['Close']['BTC-USD']
            else:
                d_prices = btc_raw['Close']
                
            d_prices = d_prices.ffill().dropna()
            w_prices = d_prices.resample('W').last()

            if len(w_prices) >= 217:
                sma217w = w_prices.rolling(window=217).mean()
                ema217w = w_prices.ewm(span=217, adjust=False).mean()
                median217w = (sma217w + ema217w) / 2
                median_daily = median217w.reindex(d_prices.index).ffill()
                
                # RSI 계산 (일봉 14일)
                delta = d_prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss.replace(0, np.nan) 
                rsi = 100 - (100 / (1 + rs))
                
                mask = d_prices.index.date >= tech_start_date
                p_disp = d_prices[mask]
                m_disp = median_daily[mask]
                rsi_disp = rsi[mask].fillna(50)
                
                fig_tech = make_subplots(
                    rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.08, row_heights=[0.7, 0.3],
                    subplot_titles=("BTC", "RSI")
                )
                
                # Trace 1: BTC Price
                fig_tech.add_trace(go.Scatter(
                    x=p_disp.index, y=p_disp, name="BTC", 
                    line=dict(color="#F7931A", width=1.5)
                ), row=1, col=1)
                
                # Trace 2: 217W Median
                fig_tech.add_trace(go.Scatter(
                    x=m_disp.index, y=m_disp, name="217W Median", 
                    line=dict(color="#00E676", width=2, dash='dashdot') 
                ), row=1, col=1)
                
                # Trace 3: RSI (선만 깔끔하게 표시)
                fig_tech.add_trace(go.Scatter(
                    x=rsi_disp.index, y=rsi_disp, name="RSI", 
                    line=dict(color="#AF52DE", width=1.5)
                ), row=2, col=1)
                
                # [수정] 30, 70 기준선만 명확하게 표시
                fig_tech.add_hline(y=70, line_dash="dash", line_color="#FF5252", line_width=1, opacity=0.8, row=2, col=1)
                fig_tech.add_hline(y=30, line_dash="dash", line_color="#00E676", line_width=1, opacity=0.8, row=2, col=1)
                
                fig_tech.update_layout(
                    hovermode="x unified", height=650,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, traceorder="normal")
                )
                
                fig_tech.update_yaxes(gridcolor='rgba(255,255,255,0.05)', row=1, col=1)
                fig_tech.update_yaxes(range=[0, 100], gridcolor='rgba(255,255,255,0.05)', row=2, col=1)
                
                st.plotly_chart(fig_tech, use_container_width=True)
                
                # [추가] 실제 데이터 시작일 기준 Base Date 캡션
                tech_actual_base = p_disp.index[0].strftime('%Y-%m-%d')
                st.caption(f"Analysis Start: {tech_actual_base} | Source: Yahoo Finance & Global Exchange Data")

                # 전략적 진단
                curr_p = float(p_disp.iloc[-1])
                curr_m = float(m_disp.iloc[-1])
                curr_rsi = float(rsi_disp.iloc[-1])
                dist = ((curr_p / curr_m) - 1) * 100
                st.info(f"**Current:** BTC vs 217W Median: **{dist:.2f}%** | RSI: **{curr_rsi:.2f}**")
            else:
                st.warning("데이터가 부족합니다.")





    # [C] CRYPTO VOLATILITY & PRICE OVERLAY (V230: Legend Sorted)
    st.markdown("---")
    st.subheader("BTC VOLATILITY vs PRICE")

    vol_col1, vol_col2 = st.columns([1, 2])
    with vol_col1:
        vol_start_date = st.date_input("Analysis Start Date", value=datetime.now() - timedelta(days=365), key="vol_price_final_v230")

    with st.spinner("Analyzing BTC Pulse..."):
        fetch_start = vol_start_date - timedelta(days=60)
        btc_data = yf.download("BTC-USD", start=fetch_start, progress=False)
        
        if not btc_data.empty:
            # MultiIndex 구조 완벽 방어
            if isinstance(btc_data.columns, pd.MultiIndex):
                price_series = btc_data['Close']['BTC-USD']
            else:
                price_series = btc_data['Close']
                
            price_series = price_series.ffill().dropna()
            
            if len(price_series) > 30:
                daily_returns = price_series.pct_change().dropna()
                rolling_std = daily_returns.rolling(window=30, min_periods=20).std()
                vol_30d = rolling_std * np.sqrt(365) * 100
                
                vol_display = vol_30d[vol_30d.index.date >= vol_start_date].dropna()
                price_display = price_series[price_series.index.date >= vol_start_date].dropna()
                
                if not vol_display.empty:
                    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # [레전드 순서 1] BTC Price (Secondary Y: True)
                    fig_dual.add_trace(go.Scatter(
                        x=price_display.index, y=price_display,
                        mode='lines', name="BTC",
                        line=dict(width=1.5, color="#F7931A")
                    ), secondary_y=True)

                    # [레전드 순서 2] 30D Volatility (Secondary Y: False)
                    fig_dual.add_trace(go.Scatter(
                        x=vol_display.index, y=vol_display,
                        mode='lines', name="Volatility(30D)",
                        line=dict(width=1.5, color="#00E5FF"),
                        fill='tozeroy', fillcolor='rgba(0, 229, 255, 0.1)'
                    ), secondary_y=False)
                    
                    # avg_vol 스칼라 변환
                    raw_avg = vol_display.mean()
                    avg_vol = float(raw_avg.iloc[0]) if isinstance(raw_avg, pd.Series) else float(raw_avg)
                    
                    fig_dual.add_hline(
                        y=avg_vol, line_dash="dot", line_color="#FF5252", 
                        annotation_text=f"AVG: {avg_vol:.1f}%",
                        secondary_y=False
                    )
                    
                    fig_dual.update_layout(
                        hovermode="x unified",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=550,
                        margin=dict(t=10, b=10, l=10, r=10),
                        legend=dict(
                            orientation="h", 
                            yanchor="bottom", y=1.02, 
                            xanchor="right", x=0.95, # 통일성을 위해 1로 고정
                            traceorder="normal"
                        ),
                        yaxis=dict(title="Vol (%)", gridcolor='rgba(255,255,255,0.05)', ticksuffix="%"),
                        yaxis2=dict(title="Price (USD)", showgrid=False)
                    )
                    
                    st.plotly_chart(fig_dual, use_container_width=True)
                    
                    # [추가] 실제 데이터 시작일 기준 Base Date 캡션
                    v_actual_base = vol_display.index[0].strftime('%Y-%m-%d')
                    st.caption(f"Analysis Start: {v_actual_base} | Source: Yahoo Finance & Global Exchange Data")

                    # 인포 박스 출력
                    curr_vol = float(vol_display.iloc[-1])
                    curr_price = float(price_display.iloc[-1])
                    st.info(f"**Current:** BTC ${curr_price:,.0f} | Volatility {curr_vol:.2f}%")



    # [D] CRYPTO vs STOCK CORRELATION & PRICE (V228: Legend Sorted & White Dot)
    st.markdown("---")
    st.subheader("BTC vs U.S. STOCK CORRELATION")

    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        corr_start_date = st.date_input("Analysis Start Date", value=datetime.now() - timedelta(days=365), key="c_date_v228")
    with c_col2:
        s_bench = st.selectbox("Benchmark", ["Nasdaq 100 (^NDX)", "S&P 500 (^GSPC)"], key="s_bench_v228")
        s_ticker = "^NDX" if "Nasdaq" in s_bench else "^GSPC"

    with st.spinner("Analyzing Correlation Dynamics..."):
        c_fetch_start = corr_start_date - timedelta(days=100)
        c_raw = yf.download(["BTC-USD", s_ticker], start=c_fetch_start, progress=False)['Close']
        
        if not c_raw.empty:
            c_raw = c_raw.ffill().dropna()
            c_rets = c_raw.pct_change().dropna()
            c_series = c_rets["BTC-USD"].rolling(window=60).corr(c_rets[s_ticker]).dropna()
            
            c_common = c_series.index.intersection(c_raw.index)
            c_final = c_series.loc[c_common]
            cp_final = c_raw.loc[c_common, "BTC-USD"]
            
            c_mask = c_final.index.date >= corr_start_date
            c_disp = c_final[c_mask]
            cp_disp = cp_final[c_mask]
            
            if not c_disp.empty:
                from plotly.subplots import make_subplots
                fig_c = make_subplots(specs=[[{"secondary_y": True}]])
                
                # [레전드 순서 1] BTC Price (오렌지 실선)
                fig_c.add_trace(go.Scatter(
                    x=cp_disp.index, y=cp_disp, 
                    name="BTC", 
                    line=dict(width=1.5, color="#F7931A")
                ), secondary_y=True)

                # [레전드 순서 2] Correlation (하얀색 점선)
                fig_c.add_trace(go.Scatter(
                    x=c_disp.index, y=c_disp, 
                    name="Correlation",
                    line=dict(width=3, color="#FFFFFF", dash="dot"), # 하얀색 점선으로 변경
                    fill='tozeroy', fillcolor='rgba(255, 255, 255, 0.03)'
                ), secondary_y=False)
                
                # 기준선 (0.0)
                fig_c.add_hline(y=0, line_dash="solid", line_color="rgba(255,255,255,0.2)", secondary_y=False)
                
                # UI 레이아웃 및 우측 상단 레전드 정렬
                fig_c.update_layout(
                    hovermode="x unified", height=500,
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=10, b=10, l=10, r=10),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", y=1.02, 
                        xanchor="right", x=0.95,
                        bgcolor='rgba(0,0,0,0)',
                        traceorder="normal" # add_trace 순서대로(BTC -> Corr)
                    ),
                    yaxis=dict(title="Correlation", range=[-1.1, 1.1], gridcolor='rgba(255,255,255,0.05)'),
                    yaxis2=dict(title="BTC Price (USD)", showgrid=False)
                )
                
                st.plotly_chart(fig_c, use_container_width=True)
                
                # 전략적 해석 로직
                curr_c = float(c_disp.iloc[-1])
                curr_p = float(cp_disp.iloc[-1])
                
                if curr_c > 0.6:
                    c_status = "⚠️ 고동조화 (High Coupling): 자산 배분 효과 일시 감소"
                elif curr_c < 0.1:
                    c_status = "✅ 탈동조화 (Decoupling): 비트코인 표준 헤지 기능 강화"
                else:
                    c_status = "중립적 상관관계 (Neutral)"
                
                st.caption(f"Analysis Start: {c_disp.index[0].strftime('%Y-%m-%d')} | Source: Yahoo Finance & Global Exchange Data")
                st.info(f"**Insight:** BTC ${curr_p:,.0f} | 현재 상관계수: **{curr_c:.2f}**, {c_status}")




    # [E] BTC vs GOLD vs DXY RELATIVE STRENGTH (V160)
    st.markdown("---")
    st.subheader("DXY vs BTC vs GOLD")
    
    # 1. 입력 도구 (기본 날짜는 연초로 설정)
    bgd_col1, bgd_col2 = st.columns([1, 2])
    with bgd_col1:
        # bgd_default_start = datetime(datetime.now().year, 1, 1)
        bgd_default_start = datetime.now() - timedelta(days=365)
        bgd_start_date = st.date_input("Analysis Start Date", value=bgd_default_start, key="bgd_ratio_date")
    
    # 2. 데이터 로드 (DX-Y.NYB, BTC-USD, GC=F)
    with st.spinner("Analyzing Global Monetary Assets..."):
        # DX-Y.NYB: Dollar Index, BTC-USD: Bitcoin, GC=F: Gold
        bgd_tickers = ["DX-Y.NYB", "BTC-USD", "GC=F"]
        bgd_raw_data = yf.download(bgd_tickers, start=bgd_start_date)['Close']
        
        if not bgd_raw_data.empty:
            bgd_raw_data = bgd_raw_data.ffill().dropna()
            
            if not bgd_raw_data.empty:
                # 수익률 표준화 (0% 기준)
                bgd_norm = (bgd_raw_data / bgd_raw_data.iloc[0] - 1) * 100
                
                # 티커 변수 할당
                dxy_col = "DX-Y.NYB"
                btc_col = "BTC-USD"
                gold_col = "GC=F"
                
                # Bitcoin / Gold Ratio 계산
                bg_ratio = bgd_raw_data[btc_col] / bgd_raw_data[gold_col]
                bg_ratio_norm = (bg_ratio / bg_ratio.iloc[0] - 1) * 100
                
                # 3. 차트 생성
                fig_bgd = go.Figure()
                
                # [레전드 순서 1] Dollar Index - 초록색
                fig_bgd.add_trace(go.Scatter(
                    x=bgd_norm.index, y=bgd_norm[dxy_col],
                    mode='lines', name="US Dollar Index",
                    line=dict(width=2, color="#00FF41"), # 사령부 시그니처 그린
                    hovertemplate="DXY: %{y:.2f}%<extra></extra>"
                ))
                
                # [레전드 순서 2] Bitcoin - 오렌지색 굵은 선
                fig_bgd.add_trace(go.Scatter(
                    x=bgd_norm.index, y=bgd_norm[btc_col],
                    mode='lines', name="Bitcoin",
                    line=dict(width=1.5, color="#F7931A"),
                    hovertemplate="Bitcoin: %{y:.2f}%<extra></extra>"
                ))
                
                # [레전드 순서 3] Gold - 금색 실선
                fig_bgd.add_trace(go.Scatter(
                    x=bgd_norm.index, y=bgd_norm[gold_col],
                    mode='lines', name="Gold",
                    line=dict(width=1.5, color="#FFD700"),
                    hovertemplate="Gold: %{y:.2f}%<extra></extra>"
                ))
                
                # [레전드 순서 4] Ratio - 화이트 굵은 도트선
                fig_bgd.add_trace(go.Scatter(
                    x=bg_ratio_norm.index, y=bg_ratio_norm,
                    mode='lines', name="BTC/Gold Ratio",
                    line=dict(width=3, color="#FFFFFF", dash='dot'),
                    hovertemplate="Ratio Change: %{y:.2f}%<extra></extra>"
                ))
                
                fig_bgd.update_layout(
                    hovermode="x unified",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=550,
                    margin=dict(t=10, b=10, l=10, r=10),
                    yaxis=dict(title="Performance / Ratio Change (%)", gridcolor='rgba(255,255,255,0.05)', zerolinecolor='#666'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    legend=dict(
                        orientation="h", 
                        yanchor="bottom", y=1.02, 
                        xanchor="right", x=1,
                        traceorder="normal" # 코딩한 순서 유지
                    )
                )
                
                st.plotly_chart(fig_bgd, use_container_width=True)
                
                # 하단 캡션 추가
                st.caption(f"Base Date: {bgd_raw_data.index[0].strftime('%Y-%m-%d')} (Normalized to 0%) | Source: Yahoo Finance & Global Exchange Data")
                
                # 4. 전략적 코멘트
                current_dxy = bgd_norm[dxy_col].iloc[-1]
                current_ratio_gain = bg_ratio_norm.iloc[-1]
                st.info(f"**Insight:** 달러 인덱스는 기준일 대비 **{current_dxy:.2f}% {'강세' if current_dxy > 0 else '약세'}**이며, 금 대비 비트코인 구매력은 **{current_ratio_gain:.2f}% {'확장' if current_ratio_gain > 0 else '축소'}** 중입니다.")



    st.stop()










# --- MARKET MODULE (V103: USD/DXY Priority & Source ㅋ) ---
elif menu == "Bitcoin Standard":
    st.title("BITCOIN STANDARD a.k.a FOREX")

    # [A] BTC STANDARD: FIAT DEVALUATION (COLLECTIVE)
    st.markdown("---")
    st.subheader("BTC STANDARD: FIAT DEVALUATION")
    st.info("비트코인(BTC) 대비 각 법정화폐의 실질 구매력 변화를 추적합니다. (BTC Standard = 1.00)")

    # 1. 분석 기간 선택
    btc_col1, btc_col2 = st.columns([1, 2])
    with btc_col1:
        # 성진님의 요청에 따라 2023-01-01 유지 ㅋ
        btc_default_start = datetime(2023, 1, 1)
        btc_analysis_start = st.date_input("Analysis Start Date", value=btc_default_start, key="btc_std_global_date")

    # 2. 데이터 로드 로직 (DXY를 USD라는 이름으로 추가 ㅋ)
    fiat_tickers = {
        "USD": "DX-Y.NYB", "CAD": "CAD=X", "AUD": "AUD=X", 
        "CHF": "CHF=X", "JPY": "JPY=X", "CNY": "CNY=X", "KRW": "KRW=X"
    }

    @st.cache_data(ttl=3600)
    def get_btc_standard_final_v103(tickers_dict, start_date_str):
        combined_list = []
        try:
            btc_raw = yf.download("BTC-USD", start=start_date_str, interval='1d', progress=False)['Close']
            if btc_raw.empty: return pd.DataFrame()
            
            # [중요] unit_config 순서대로 돌아서 레전드 순서 보장 ㅋ
            for name, ticker in tickers_dict.items():
                fiat_raw = yf.download(ticker, start=start_date_str, interval='1d', progress=False)['Close']
                if not fiat_raw.empty:
                    f_series = fiat_raw[ticker] if isinstance(fiat_raw, pd.DataFrame) else fiat_raw
                    b_series = btc_raw["BTC-USD"] if isinstance(btc_raw, pd.DataFrame) else btc_raw
                    
                    if name == "USD":
                        # DXY 기반 USD 가치 역산 (지수 100 기준 보정 ㅋ)
                        # DXY가 높을수록 달러가 강하므로, 1달러로 살 수 있는 BTC는 상대적으로 많아짐 ㅋ
                        btc_per_fiat = (f_series / 100) / b_series
                    else:
                        # 일반 환율 기반 구매력 역산 ㅋ
                        btc_per_fiat = 1 / (f_series * b_series)
                    
                    btc_per_fiat.name = name
                    combined_list.append(btc_per_fiat)
            
            if combined_list:
                return pd.concat(combined_list, axis=1).ffill().dropna()
        except: pass
        return pd.DataFrame()

    btc_df = get_btc_standard_final_v103(fiat_tickers, btc_analysis_start.strftime('%Y-%m-%d'))

    if not btc_df.empty and len(btc_df) > 1:
        btc_rel_perf = (btc_df / btc_df.iloc[0] - 1) * 100
        
        # 3. 차트 생성
        fig_btc_melt = go.Figure()
        # USD: 화이트, 나머지 컬러 유지 ㅋ
        colors = {
            "USD": "#FFFFFF", "CAD": "#FF5252", "AUD": "#FFD740", 
            "CHF": "#64FFDA", "JPY": "#448AFF", "CNY": "#E040FB", "KRW": "#00E676"
        }
        
        # 설정한 순서(USD 우선)대로 Trace 추가 ㅋ
        for name in fiat_tickers.keys():
            if name in btc_rel_perf.columns:
                is_usd = (name == "USD")
                fig_btc_melt.add_trace(go.Scatter(
                    x=btc_rel_perf.index, y=btc_rel_perf[name],
                    mode='lines', name=name,
                    line=dict(
                        width=3 if is_usd else 1.5, 
                        color=colors.get(name),
                        dash='dot' if is_usd else 'solid' # USD는 점선 강조 ㅋ
                    ),
                    connectgaps=True,
                    hovertemplate=f"<b>{name}</b>: %{{y:.2f}}% (Purchasing Power)<extra></extra>"
                ))

        y_min, y_max = btc_rel_perf.min().min(), btc_rel_perf.max().max()
        y_padding = abs(y_max - y_min) * 0.15

        fig_btc_melt.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=550, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified",
            legend=dict(
                orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01, 
                bgcolor="rgba(0,0,0,0.3)", traceorder="normal"
            ),
            yaxis=dict(showgrid=True, gridcolor="#333", title="Purchasing Power Change (%)", range=[y_min - y_padding, y_max + y_padding])
        )

        st.plotly_chart(fig_btc_melt, use_container_width=True)
        
        # [V103] 캡션 업데이트: Source 추가 완료! ㅋ
        actual_start_str = btc_rel_perf.index[0].strftime('%Y-%m-%d')
        st.caption(f"Analysis Start: {actual_start_str} | Source: Yahoo Finance & Global Exchange Data")
        
        # 전략적 코멘트
        worst_fiat = btc_rel_perf.iloc[-1].idxmin()
        worst_val = btc_rel_perf.iloc[-1].min()
        st.error(f"**Worst Fiat Devaluation:** {actual_start_str} 이후 **{worst_fiat}**의 구매력은 비트코인 대비 **{worst_val:.2f}%** 하락했습니다.")




    # [B] SATOSHIS PER UNIT FIAT: THE SCARCITY TRACKER (V1245)
    st.markdown("---")
    st.subheader("SATOSHIS PER UNIT FIAT (SCARCITY)")
    st.info("각 통화 '1단위'로 구매 가능한 사토시(Sats)의 개수를 추적합니다. (USD는 달러 인덱스 기준)")

    # 1. 설정: 이름을 USD로 변경하고 단위는 1로 설정 ㅋ
    unit_config = {
        "USD": 1,      "CAD": 1,      "AUD": 1,      
        "KRW": 1000,   "JPY": 100,    "CNY": 10,     "CHF": 1       
    }

    # 2. 분석 시작일 설정
    sats_col1, sats_col2 = st.columns([1, 2])
    with sats_col1:
        sats_default_start = datetime(2023, 1, 1)
        sats_start_date = st.date_input(
            "Analysis Start Date", 
            value=sats_default_start, 
            key="sats_scarcity_date"
        )

    @st.cache_data(ttl=3600)
    def get_sats_per_fiat_data_v1245(start_date_str):
        try:
            # BTC 가격 로드
            btc_raw = yf.download("BTC-USD", start=start_date_str, interval='1d', progress=False)['Close']
            if btc_raw.empty: return pd.DataFrame()
            
            # 티커 생성 (이름은 USD지만 데이터는 DXY 티커를 가져옴 ㅋ)
            tickers = {k: (f"{k}=X" if k != "USD" else "DX-Y.NYB") for k in unit_config.keys()}
            fiat_raw = yf.download(list(tickers.values()), start=start_date_str, interval='1d', progress=False)['Close']
            
            combined_list = []
            for fiat, unit in unit_config.items():
                ticker = tickers[fiat]
                f_series = fiat_raw[ticker] if isinstance(fiat_raw, pd.DataFrame) else fiat_raw
                b_series = btc_raw["BTC-USD"] if isinstance(btc_raw, pd.DataFrame) else btc_raw
                
                # [핵심] 사토시 환산 로직 분기 ㅋ
                if fiat == "USD":
                    # DXY 지수는 100을 기준으로 달러 가치를 환산 (바닥에 붙지 않게 보정 ㅋ)
                    sats_per_unit = (f_series / 100) / b_series * 100_000_000
                else:
                    # 일반 환율 (CAD, KRW 등)은 기존 공식 유지
                    sats_per_unit = (unit / f_series) / b_series * 100_000_000
                
                sats_per_unit.name = fiat
                combined_list.append(sats_per_unit)
                
            return pd.concat(combined_list, axis=1).ffill().dropna()
        except: return pd.DataFrame()

    sats_df = get_sats_per_fiat_data_v1245(sats_start_date.strftime('%Y-%m-%d'))

    if not sats_df.empty:
        # 3. 차트 생성
        fig_sats = go.Figure()
        # USD(DXY기반): 화이트 설정 ㅋ
        colors = {
            "USD": "#FFFFFF", "CAD": "#FF5252", "AUD": "#FFD740", 
            "CHF": "#64FFDA", "JPY": "#448AFF", "CNY": "#E040FB", "KRW": "#00E676"
        }
        
        for fiat in unit_config.keys():
            if fiat in sats_df.columns:
                is_usd_base = (fiat == "USD")
                # 레전드 이름 형식: "1 USD", "1000 KRW" ㅋ
                legend_name = f"{unit_config[fiat]} {fiat}"
                
                fig_sats.add_trace(go.Scatter(
                    x=sats_df.index, y=sats_df[fiat],
                    mode='lines', 
                    name=legend_name,
                    line=dict(
                        width=3 if is_usd_base else 1.5, 
                        color=colors.get(fiat),
                        dash='dot' if is_usd_base else 'solid'
                    ),
                    hovertemplate=f"<b>{legend_name}</b>: %{{y:,.0f}} Sats<extra></extra>"
                ))

        fig_sats.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=500, margin=dict(l=10, r=10, t=20, b=40), hovermode="x unified",
            yaxis_title="Satoshi Amount (Sats)",
            legend=dict(
                orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01, 
                bgcolor="rgba(0,0,0,0.3)", traceorder="normal"
            )
        )
        # [V1246: 차트 출력 및 캡션 추가 ㅋ]
        st.plotly_chart(fig_sats, use_container_width=True)
        
        # 성진님이 찾으시던 바로 그 Base Date 캡션! ㅋ
        actual_sats_base = sats_df.index[0].strftime('%Y-%m-%d')
        st.caption(f"Analysis Start: {actual_sats_base} | Source: Yahoo Finance & Global Exchange Data")
        
        # 4. 실전 경고 리포트
        current_krw_sats = sats_df['KRW'].iloc[-1]
        st.warning(f"**Scarcity Alert:** 현재 1,000원으로 살 수 있는 비트코인은 단 **{current_krw_sats:,.0f} 사토시**뿐입니다.")
    else:
        st.info("데이터를 분석하여 사토시 단위로 변환 중입니다...")




    # [C] GLOBAL CURRENCY PERFORMANCE (V983: UI Unification ㅋ)
    st.markdown("---")
    st.subheader("GLOBAL CURRENCY PERFORMANCE")

    # 1. 대상 통화 목록
    fx_tickers = {
        "DXY": "DX-Y.NYB", "CAD": "CAD=X", "AUD": "AUD=X",
        "CHF": "CHF=X", "JPY": "JPY=X", "CNY": "CNY=X", "KRW": "KRW=X"
    }

    # 2. 분석 기간 선택 (다른 차트들과 스타일 통일! ㅋ)
    fx_perf_col1, fx_perf_col2 = st.columns([1, 2])
    with fx_perf_col1:
        # 디폴트는 성진님이 요청하신 대로 현재 기준 1년 전 ㅋ
        fx_perf_default_start = datetime.now() - timedelta(days=365)
        fx_perf_start_date = st.date_input(
            "Analysis Start Date", 
            value=fx_perf_default_start, 
            key="fx_global_perf_date"
        )

    @st.cache_data(ttl=3600)
    def get_fx_data_v983(tickers_dict, start_date_str):
        df_list = []
        # 주말/휴일을 대비해 입력받은 날짜보다 7일 더 일찍 가져와서 보정 ㅋ
        fetch_start = datetime.strptime(start_date_str, '%Y-%m-%d') - timedelta(days=7)
        
        for name, ticker in tickers_dict.items():
            try:
                raw = yf.download(ticker, start=fetch_start, interval='1d', progress=False, auto_adjust=True)
                if not raw.empty:
                    data = raw['Close']
                    if isinstance(data, pd.DataFrame):
                        data = data.iloc[:, 0]
                    
                    if name != "DXY":
                        data = 1 / data
                    
                    data.name = name
                    df_list.append(data)
            except: continue
        
        if df_list:
            combined = pd.concat(df_list, axis=1).ffill().dropna()
            # 사용자가 선택한 날짜 이후의 데이터만 정확히 필터링 ㅋ
            return combined[combined.index >= pd.Timestamp(start_date_str)]
        return pd.DataFrame()

    with st.spinner("Analyzing Global Currency Trends..."):
        # 선택된 날짜를 문자열로 변환하여 전달 ㅋ
        fx_df = get_fx_data_v983(fx_tickers, fx_perf_start_date.strftime('%Y-%m-%d'))

    # 3. 차트 렌더링
    if not fx_df.empty and len(fx_df) > 1:
        # 선택한 시작점의 첫 데이터를 0%로 기준 잡기 ㅋ
        first_valid_row = fx_df.iloc[0]
        fx_ytd_rel = (fx_df / first_valid_row - 1) * 100
        
        y_min, y_max = fx_ytd_rel.min().min(), fx_ytd_rel.max().max()
        y_padding = (y_max - y_min) * 0.2

        fig_fx = go.Figure()
        ordered_names = ["DXY", "CAD", "AUD", "CHF", "JPY", "CNY", "KRW"]
        colors = {"DXY": "#FFFFFF", "CAD": "#FF5252", "AUD": "#FFD740", "CHF": "#64FFDA", "JPY": "#448AFF", "CNY": "#E040FB", "KRW": "#00E676"}

        for name in ordered_names:
            if name in fx_ytd_rel.columns:
                fig_fx.add_trace(go.Scatter(
                    x=fx_ytd_rel.index, y=fx_ytd_rel[name],
                    mode='lines', name=name,
                    line=dict(width=3 if name=="DXY" else 1.5, dash='dot' if name=="DXY" else 'solid', color=colors[name]),
                    hovertemplate=f"<b>{name}</b>: %{{y:.2f}}%<extra></extra>"
                ))

        fig_fx.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=550, margin=dict(l=10, r=10, t=20, b=40), hovermode="x unified",
            legend=dict(orientation="h", yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0.3)"),
            yaxis=dict(showgrid=True, gridcolor="#333", title="Relative Return (%)", range=[y_min - y_padding, y_max + y_padding])
        )
        st.plotly_chart(fig_fx, use_container_width=True)
        st.caption(f"Base Date: {fx_df.index[0].strftime('%Y-%m-%d')} (Normalized to 0.00%) | Source: Yahoo Finance & Global Exchange Data")
    else:
        st.info("선택하신 기간의 데이터를 불러오는 중입니다...")



    # [D] MAJOR SPOT EXCHANGE RATES (USD BASED)
    st.markdown("---")
    st.subheader("MAJOR SPOT EXCHANGE RATES")

    # 1. 티커 및 컬러 리스트 (레전드 순서 동기화)
    spot_config = [
        {"name": "USD/CAD", "ticker": "CAD=X", "color": "#FF5252"},
        {"name": "USD/AUD", "ticker": "AUD=X", "color": "#FFD740"},
        {"name": "USD/CHF", "ticker": "CHF=X", "color": "#64FFDA"},
        {"name": "USD/JPY", "ticker": "JPY=X", "color": "#448AFF"},
        {"name": "USD/CNY", "ticker": "CNY=X", "color": "#E040FB"},
        {"name": "USD/KRW", "ticker": "KRW=X", "color": "#00E676"}
    ]

    # [V1080] 개별 차트 렌더링 루프
    for config in spot_config:
        name = config["name"]
        ticker = config["ticker"]
        color = config["color"]

        # A. 차트 제목 출력
        st.write(f"#### **{name}**")

        # B. Analysis Start Date 선택 (왼쪽 정렬을 위해 컬럼 활용 ㅋ)
        col_date, col_empty = st.columns([1, 2])
        with col_date:
            # 기본값: 1년 전 ㅋ
            default_start = datetime.now() - timedelta(days=365)
            individual_start = st.date_input(
                "Analysis Start Date", 
                value=default_start, 
                key=f"date_{name}"
            )

        # C. 데이터 로드 및 차트 생성
        try:
            # progress=False로 깔끔하게 로드 ㅋ
            raw = yf.download(ticker, start=individual_start, interval='1d', progress=False)
            if not raw.empty:
                if isinstance(raw.columns, pd.MultiIndex):
                    spot_series = raw['Close'][ticker].copy()
                else:
                    spot_series = raw['Close'].copy()
                
                # Y축 범위 최적화 ㅋ
                y_min, y_max = spot_series.min(), spot_series.max()
                padding = (y_max - y_min) * 0.15

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=spot_series.index, y=spot_series,
                    mode='lines',
                    line=dict(width=1.5, color=color),
                    fill='tozeroy',
                    fillcolor=f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, 0.05)",
                    hovertemplate=f"<b>{name}</b>: %{{y:.2f}}<extra></extra>"
                ))
                
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(
                        showgrid=True, gridcolor="rgba(255,255,255,0.05)", 
                        side="left",
                        range=[y_min - padding, y_max + padding]
                    ),
                    showlegend=False,
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # D. 하단 표준 캡션 (왼쪽 정렬) ㅋ
                actual_start_str = spot_series.index[0].strftime('%Y-%m-%d')
                st.caption(f"Analysis Start: {actual_start_str} | Source: Yahoo Finance & Global Exchange Data")
                st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.warning(f"{name} 데이터가 해당 기간에 존재하지 않습니다.")
        except Exception as e:
            st.error(f"{name} 데이터를 가져오는 중 오류가 발생했습니다.")



    # [E] GLOBAL CURRENCY HEATMAP: RELATIVE STRENGTH
    st.markdown("---")
    st.subheader("CURRENCY RELATIVE STRENGTH HEATMAP")
    st.info("왼쪽(Base) 통화가 상단(Quote) 통화 대비 얼마나 강세인지 나타냅니다. 짙은 초록색일수록 왼쪽 통화의 강세를 의미합니다.")
    hm_symbols = ["USD", "CAD", "AUD", "CHF", "JPY", "CNY", "KRW"]
    
    # [V1210] 캐시 무효화를 위해 실시간성을 더 높임 ㅋ
    @st.cache_data(ttl=300) 
    def get_heatmap_matrix_v1210(symbols):
        matrix = pd.DataFrame(index=symbols, columns=symbols)
        for base in symbols:
            for quote in symbols:
                if base == quote:
                    matrix.loc[base, quote] = 0.0
                    continue
                
                ticker = f"{base}{quote}=X"
                if base == "USD": ticker = f"{quote}=X"
                
                try:
                    # [V1210 핵심] 데이터를 1달치(1mo) 넉넉히 가져와서 결측치를 완전히 제거 ㅋ
                    raw_data = yf.download(ticker, period="1mo", interval="1d", progress=False)['Close']
                    # MultiIndex인 경우 처리 ㅋ
                    data = raw_data[ticker] if isinstance(raw_data, pd.DataFrame) else raw_data
                    series = data.dropna()
                    
                    if len(series) >= 2:
                        # [V1210 로직] 맨 마지막 날(val_now)과 
                        # 그 전날 중 값이 '다른' 날(val_prev)을 기어이 찾아냄 ㅋ
                        val_now = series.iloc[-1]
                        val_prev = val_now
                        
                        for i in range(len(series)-2, -1, -1):
                            if series.iloc[i] != val_now:
                                val_prev = series.iloc[i]
                                break
                        
                        change = ((val_now / val_prev) - 1) * 100
                        # USD 기준은 부호 반전 ㅋ
                        matrix.loc[base, quote] = change if base != "USD" else -change
                    else:
                        matrix.loc[base, quote] = 0.0
                except:
                    matrix.loc[base, quote] = 0.0
        return matrix.astype(float)

    with st.spinner("주말의 침묵을 깨고 데이터를 강제 소환 중..."):
        hm_df = get_heatmap_matrix_v1210(hm_symbols)

    if not hm_df.empty:
        import plotly.graph_objects as go

        # [V1210] 데이터가 작아도 색이 잘 보이게 범위를 0.2%로 더 조임 ㅋ
        fig_hm = go.Figure(data=go.Heatmap(
            z=hm_df.values,
            x=hm_df.columns,
            y=hm_df.index,
            colorscale='RdYlGn',
            zmin=-0.2, zmax=0.2, 
            text=np.around(hm_df.values, decimals=2),
            texttemplate="%{text}%",
            hovertemplate="Base: %{y}<br>Quote: %{x}<br>Change: %{z:.2f}%<extra></extra>"
        ))

        fig_hm.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10),
            height=500,
            xaxis=dict(side="top")
        )
        
        st.plotly_chart(fig_hm, use_container_width=True)
        st.caption(f"Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Weekend Data Forced) | Source: Yahoo Finance & Global Exchange Data")



    st.stop()












elif menu != "Portfolio":
    st.info(f"MODULE '{menu}' OFFLINE")
    st.stop()
    
# --- PORTFOLIO DASHBOARD (Existing Code) ---
# Ensure base_currency is available if skipped in sidebar
if 'base_currency' not in locals():
    base_currency = pm.get_setting("base_currency", "USD")

# --- Main Dashboard ---
st.title("PORTFOLIO MANAGER")

# 1. Header & Data Pre-processing
fx_rates, is_stale_flag = md.get_fx_rates()
raw_assets = pm.get_assets()
total_val_display, sorted_assets = process_assets(raw_assets, fx_rates, base_currency)

# --- History Calculation (기존 로직 유지) ---
real_assets = [a for a in sorted_assets if a['ticker'] != 'CASH']
total_history_display = pd.Series()

if real_assets:
    prices = get_cached_historical_data(st.session_state.ae, real_assets)
    if not prices.empty:
        prices = prices.ffill().dropna()
        portfolio_value_series = pd.Series(0.0, index=prices.index)
        for asset in real_assets:
            if asset['ticker'] in prices.columns:
                portfolio_value_series = portfolio_value_series.add(prices[asset['ticker']] * asset['quantity'], fill_value=0)
        
        total_cash_usd = next((a['value_usd'] for a in sorted_assets if a['ticker'] == 'CASH'), 0.0)
        total_history_usd = portfolio_value_series + total_cash_usd
        growth_fx = fx_rates.get(base_currency, 1.0)
        total_history_display = total_history_usd * growth_fx

# --- Metrics Calculation ---
ytd_return = 0.0
if not total_history_display.empty:
    current_year = datetime.now().year
    start_of_year = datetime(current_year, 1, 1)
    if not isinstance(total_history_display.index, pd.DatetimeIndex):
        total_history_display.index = pd.to_datetime(total_history_display.index)
    this_year_data = total_history_display[total_history_display.index >= pd.Timestamp(start_of_year)]
    current_val = total_history_display.iloc[-1]
    if not this_year_data.empty:
        start_val_ytd = this_year_data.iloc[0]
        if start_val_ytd > 0:
            ytd_return = (current_val - start_val_ytd) / start_val_ytd

# --------------------------------------------------------------------------------
# 🎯 [V700] No Arrow Minimalist & Spacing Adjustment
# --------------------------------------------------------------------------------

# m_col3(토글)과 m_spacer(여백) 사이의 비율을 조정하여 토글을 오른쪽으로 살짝 이동시킵니다.
m_col1, m_col2, m_col3, m_spacer = st.columns([1.6, 1.3, 1.2, 3.2])

with m_col3:
    st.write("") # 수직 정렬 최적화
    st.write("")
    hide_sensitive = st.toggle("Hide Data", value=False, key="privacy_filter_v700")

# 공통 스타일 정의
BASE_NEON = 'font-size: 38px; font-weight: 700; line-height: 1.1; letter-spacing: -1px;'
PURPLE_GLOW = f'{BASE_NEON} color: #D500F9; text-shadow: 0 0 10px rgba(213, 0, 249, 0.4);'

# YTD 수익률 색상 분기 (화살표 제거)
if ytd_return > 0:
    ytd_color = "#00E676"
    ytd_shadow = "rgba(0, 230, 118, 0.4)"
elif ytd_return < 0:
    ytd_color = "#FF5252"
    ytd_shadow = "rgba(255, 82, 82, 0.4)"
else:
    ytd_color = "#B0B0B0"
    ytd_shadow = "rgba(176, 176, 176, 0.2)"

YTD_NEON = f'{BASE_NEON} color: {ytd_color}; text-shadow: 0 0 10px {ytd_shadow};'
MASK_NEON = f'font-size: 38px; font-weight: 700; color: #D500F9; text-shadow: 0 0 10px rgba(213, 0, 249, 0.4); letter-spacing: 3px;'

# 마스킹 결정
if not hide_sensitive:
    val_html = f'<span style="{PURPLE_GLOW}">{total_val_display:,.2f}</span>'
    ytd_html = f'<span style="{YTD_NEON}">{ytd_return:.2%}</span>' # 🚀 화살표 삭제됨
else:
    val_html = f'<span style="{MASK_NEON}">••••••••</span>'
    ytd_html = f'<span style="{MASK_NEON}">••••</span>'

# 1. NET ASSET VALUE
with m_col1:
    st.markdown(f"""
        <div style="margin-bottom: 2px;">
            <span style="font-size: 13px; color: #B0B0B0; font-weight: 500;">NET ASSET VALUE ({base_currency})</span>
        </div>
        {val_html}
    """, unsafe_allow_html=True)

# 2. YTD Return (No Arrow)
with m_col2:
    st.markdown(f"""
        <div style="margin-bottom: 2px;">
            <span style="font-size: 13px; color: #B0B0B0; font-weight: 500;">YTD Return</span>
        </div>
        <div style="display: flex; align-items: center; height: 42px;">
            {ytd_html}
        </div>
    """, unsafe_allow_html=True)

with m_spacer:
    st.write("")

st.markdown("---")


# --------------------------------------------------------------------------------
# 1. [ALLOCATION] 자산 비중 분석 (Pie Charts)
# --------------------------------------------------------------------------------
st.header(section_labels.get("strategic_allocation", "ALLOCATION"))

# TEXT COLOR & PALETTES
PIE_TEXT_COLOR = "#FFFFFF"
PALETTE_CLASS = ['#311B92', '#4527A0', '#512DA8', '#5E35B1', '#673AB7']
PALETTE_SECTOR = ['#7B1FA2', '#8E24AA', '#9C27B0', '#AB47BC', '#BA68C8']
PALETTE_HOLDINGS = ['#6200EA', '#651FFF', '#7C4DFF', '#B388FF', '#304FFE']
COLOR_CASH = "#9E9D24"

if not raw_assets and pm.data['cash']['USD'] == 0:
    st.warning("SYSTEM EMPTY. DEPLOY ASSETS TO INITIALIZE.")
else:
    df_assets = pd.DataFrame(sorted_assets)
    chart_col1, chart_col2, chart_col3 = st.columns([1, 1, 1.2])

    with chart_col1:
        with st.container(border=True):
            st.caption("CLASS DISTRIBUTION")
            df_class = df_assets.copy()
            df_class['asset_class'] = df_class['asset_class'].replace('ETF', 'Stock')
            class_map = {'Crypto': PALETTE_CLASS[0], 'Stock': PALETTE_CLASS[1], 'Other': PALETTE_CLASS[3], 'Cash': COLOR_CASH}
            fig = px.pie(df_class, values='value_usd', names='asset_class', hole=0.5, color='asset_class', color_discrete_map=class_map)
            fig.update_traces(textinfo='percent+label', textposition='inside', textfont=dict(size=12, color=PIE_TEXT_COLOR), marker=dict(line=dict(color='#000000', width=2)))
            fig.update_layout(margin=dict(t=20, b=20, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        with st.container(border=True):
            st.caption("STOCK SECTOR DISTRIBUTION")
            df_stocks = df_assets[df_assets['asset_class'] == 'Stock']
            if not df_stocks.empty:
                fig = px.pie(df_stocks, values='value_usd', names='sector', hole=0.5, color_discrete_sequence=PALETTE_SECTOR)
                fig.update_traces(textinfo='percent+label', textposition='inside', insidetextorientation='horizontal', textfont=dict(size=12, color=PIE_TEXT_COLOR), marker=dict(line=dict(color='#000000', width=2)))
                fig.update_layout(margin=dict(t=20, b=20, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("<p style='text-align:center; color:#555; padding: 80px 0;'>NO STOCK DATA</p>", unsafe_allow_html=True)

    with chart_col3:
        with st.container(border=True):
            st.caption("TOTAL HOLDINGS")
            df_final_pie = df_assets.copy()
            df_final_pie['display_ticker'] = df_final_pie['ticker'].str.replace("-USD", "")
            holdings_colors = {t: (COLOR_CASH if t == 'CASH' else PALETTE_HOLDINGS[i % len(PALETTE_HOLDINGS)]) for i, t in enumerate(df_final_pie['display_ticker'])}
            fig = px.pie(df_final_pie, values='value_usd', names='display_ticker', hole=0.5, color='display_ticker', color_discrete_map=holdings_colors)
            fig.update_traces(textinfo='percent+label', textposition='inside', insidetextorientation='horizontal', textfont=dict(color=PIE_TEXT_COLOR), marker=dict(line=dict(color='#000000', width=2)))
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# --------------------------------------------------------------------------------
# 2. [GROWTH] 자산 성장 추세 (Growth Trend)
# --------------------------------------------------------------------------------
st.header(section_labels.get("asset_growth", "Net Asset Value"))
with st.container(border=True):
    if not total_history_display.empty:
        PURPLE_LINE = "#D500F9" 
        PURPLE_FILL = "rgba(213, 0, 249, 0.15)" 
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(x=total_history_display.index, y=total_history_display.values, fill='tozeroy', mode='lines', line=dict(color=PURPLE_LINE, width=2), fillcolor=PURPLE_FILL, name=f'Portfolio ({base_currency})'))
        fig_growth.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=30, b=10, l=10, r=10), yaxis=dict(gridcolor='#222'), xaxis=dict(gridcolor='#222'), font=dict(color='#888'), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_growth, use_container_width=True)
        st.caption(f"**Analysis Start:** {total_history_display.index[0].strftime('%Y-%m-%d')}")
    else:
        st.info("DATASTREAM OFFLINE.")

st.markdown("---")

# --------------------------------------------------------------------------------
# 3. [YTD PERFORMANCE] 연초 대비 성과 (Jan 2nd Baseline)
# --------------------------------------------------------------------------------
st.header(section_labels.get("ytd_performance", "YTD PERFORMANCE"))

with st.spinner("Analyzing 2026 Asset Performance..."):
    if 'df_assets' in locals() and not df_assets.empty:
        try:
            raw_tickers = df_assets['ticker'].dropna().unique().tolist()
            portfolio_tickers = [str(t).strip().upper() for t in raw_tickers if t not in ['KRW', 'USD', 'CAD', 'CASH', '현금']]
            if portfolio_tickers:
                fetch_start = datetime(2025, 12, 28) 
                y_data = yf.download(portfolio_tickers, start=fetch_start, progress=False)
                if not y_data.empty:
                    p_df = y_data['Close'] if 'Close' in y_data else y_data
                    p_df = p_df.ffill().dropna(how='all')
                    target_start = datetime(2026, 1, 2).date()
                    display_df = p_df.loc[p_df.index.date >= target_start]
                    if not display_df.empty:
                        base_price = display_df.iloc[0]
                        ytd_perf = (display_df / base_price - 1) * 100
                        fig_ytd = go.Figure()
                        sorted_names = sorted(ytd_perf.columns if isinstance(ytd_perf, pd.DataFrame) else [portfolio_tickers[0]], key=lambda x: "BTC" not in x)
                        for ticker in sorted_names:
                            is_btc = "BTC" in ticker
                            y_vals = ytd_perf[ticker] if isinstance(ytd_perf, pd.DataFrame) else ytd_perf
                            fig_ytd.add_trace(go.Scatter(x=ytd_perf.index, y=y_vals, name=ticker, line=dict(width=3 if is_btc else 1.5, color="#F7931A" if is_btc else None), hovertemplate=f"<b>{ticker}</b>: %{{y:.2f}}%<extra></extra>"))
                        fig_ytd.update_layout(hovermode="x unified", height=450, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(t=20, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), yaxis=dict(title="Return (%)", gridcolor='rgba(255,255,255,0.05)', ticksuffix="%"), xaxis=dict(range=[target_start, ytd_perf.index[-1]], gridcolor='rgba(255,255,255,0.05)'))
                        fig_ytd.add_hline(y=0, line_dash="solid", line_color="rgba(255,255,255,0.2)")
                        st.plotly_chart(fig_ytd, use_container_width=True)
                        st.caption(f"**Base Date:** {display_df.index[0].strftime('%Y-%m-%d')} (Normalized to 0.00%)")
                        last_p = ytd_perf.iloc[-1]
                        if isinstance(last_p, pd.Series):
                            st.info(f"YTD TOP: **{last_p.idxmax()}** ({last_p.max():+.2f}%)")
        except Exception as e:
            st.error(f"YTD 엔진 오류: {str(e)}")

st.markdown("---")

# --------------------------------------------------------------------------------
# 4. [HOLDINGS] 자산 관리 테이블 (Full Width)
# --------------------------------------------------------------------------------
col_header, col_delete = st.columns([8, 1])
with col_header:
    st.header("HOLDINGS")

if 'asset_buffer' not in st.session_state:
    st.session_state['asset_buffer'] = [a.copy() for a in sorted_assets]

table_fx_rate = fx_rates.get(base_currency, 1.0)
currency_symbol = "$" if base_currency in ["USD", "CAD"] else "₩"
display_data = []
buffer_assets = st.session_state['asset_buffer']
display_map = [] 

for i, a in enumerate(buffer_assets):
    if a['ticker'] == 'CASH': continue 
    price = a.get('current_price', 0.0)
    if price == 0: price = a.get('avg_price', 0.0)
    val_calc = price * a.get('quantity', 0.0) * table_fx_rate
    display_data.append({"DELETE": False, "TICKER": str(a.get('ticker', '')), "CLASS": str(a.get('asset_class', '')), "SECTOR": str(a.get('sector', '')), "QTY": f"{float(a.get('quantity', 0.0)):.4f}", "AVG COST": f"{float(a.get('avg_price', 0.0)):.2f}", "CURRENT PRICE": f"${float(price):,.2f}", "VALUE": f"{currency_symbol}{val_calc:,.2f}"})
    display_map.append(i)

df_display = pd.DataFrame(display_data)

def save_edits():
    state = st.session_state["holdings_editor"]
    edited_rows = state.get("edited_rows", {})
    deleted_rows = state.get("deleted_rows", [])
    added_rows = state.get("added_rows", []) 
    if not edited_rows and not deleted_rows and not added_rows: return
    buffer = st.session_state['asset_buffer']
    updates_made = False
    checkbox_deletes = [int(idx) for idx, changes in edited_rows.items() if changes.get("DELETE") is True]
    all_indices_to_delete = set(deleted_rows + checkbox_deletes)
    if all_indices_to_delete:
        rows_to_delete = sorted([display_map[i] for i in all_indices_to_delete if i < len(display_map)], reverse=True)
        for buf_idx in rows_to_delete:
            if buf_idx < len(buffer):
                buffer.pop(buf_idx)
                updates_made = True
    for idx, changes in edited_rows.items():
        if int(idx) in all_indices_to_delete: continue 
        buf_idx = display_map[int(idx)]
        asset = buffer[buf_idx]
        if "QTY" in changes: 
            try: asset['quantity'] = float(str(changes["QTY"]).replace(',', ''))
            except: pass
            updates_made = True
        if "AVG COST" in changes:
            try: asset['avg_price'] = float(str(changes["AVG COST"]).replace(',', '').replace('$', ''))
            except: pass
            updates_made = True
        if "SECTOR" in changes: asset['sector'] = str(changes["SECTOR"]).strip(); updates_made = True
        if "CLASS" in changes: asset['asset_class'] = str(changes["CLASS"]).strip(); updates_made = True
        if "TICKER" in changes: asset['ticker'] = str(changes["TICKER"]).strip().upper(); updates_made = True
    if added_rows:
        for new_row in added_rows:
            raw_ticker = new_row.get('TICKER', '').strip().upper()
            qty = 0.0; avg = 0.0
            try: qty = float(str(new_row.get('QTY', '0')).replace(',', ''))
            except: pass
            try: avg = float(str(new_row.get('AVG COST', '0')).replace('$', '').replace(',', ''))
            except: pass
            buffer.append({"ticker": raw_ticker, "quantity": qty, "avg_price": avg, "sector": "Unknown", "asset_class": "Stock", "value_usd": 0.0, "current_price": 0.0})
            updates_made = True
    if updates_made:
        valid_assets = [a for a in buffer if a.get('ticker') and a.get('ticker') != "CASH"]
        cash_asset = next((a for a in pm.data['assets'] if a['ticker'] == 'CASH'), None)
        pm.data['assets'] = valid_assets + ([cash_asset] if cash_asset else [])
        pm.save_data(); st.toast("✅ Portfolio Updated")

st.data_editor(
    df_display,
    column_config={
        "DELETE": st.column_config.CheckboxColumn("🗑️", width="small"),
        "TICKER": st.column_config.TextColumn("Ticker", width="small"), 
        "CLASS": st.column_config.TextColumn("Class", width="medium"),
        "SECTOR": st.column_config.TextColumn("Sector", width="medium"),
        "QTY": st.column_config.TextColumn("Quantity", width="small"), 
        "AVG COST": st.column_config.TextColumn("Avg Cost", width="small"), 
        "CURRENT PRICE": st.column_config.TextColumn("Price (USD)", width="medium", disabled=True), 
        "VALUE": st.column_config.TextColumn(f"Value ({base_currency})", width="medium", disabled=True) 
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
        st.subheader(section_labels.get("risk_analysis", "RISK ANALYSIS"))
        
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
        st.subheader("NEWS")
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
