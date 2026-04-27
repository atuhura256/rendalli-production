import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from PIL import Image
import base64
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="Rendalli Production Intelligence", layout="wide", page_icon="🐟")

# Brand Colors
R_BLUE = "#014683" 
R_GOLD = "#FFD700" 
R_LIGHT = "#F1F4F8"

# --- HELPER: CIRCULAR LOGO ---
def get_circular_logo(image_path):
    try:
        img = Image.open(image_path).convert("RGBA")
        size = (300, 300)
        img = img.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        img.putalpha(mask)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except:
        return None

logo_base64 = get_circular_logo('image_e81194.png')

# --- UI STYLING ---
st.markdown(f"""
<style>
    .main {{ background-color: {R_LIGHT}; }}
    .header-container {{ display: flex; flex-direction: column; align-items: center; padding-bottom: 20px; }}
    .circular-logo {{ width: 120px; height: 120px; border-radius: 50%; border: 3px solid {R_GOLD}; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); background-color: white; }}
    div[data-testid="stMetric"] {{ background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid {R_BLUE}; }}
    section[data-testid="stSidebar"] {{ background-color: white !important; border-right: 1px solid #dfe3e8; }}
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {{ border: 1px solid #ced4da !important; border-radius: 5px !important; }}
    div[data-baseweb="select"]:focus-within > div {{ border-color: {R_BLUE} !important; }}
    .stDataFrame {{ border: 1px solid #e6e9ef; border-radius: 5px; }}
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING (Direct from Google Sheets) ---
@st.cache_data(ttl=300) 
def load_data_from_gsheets(sheet_url):
    try:
        base_url = sheet_url.split('/edit')[0]
        csv_url = f"{base_url}/export?format=csv"
        df_raw = pd.read_csv(csv_url)
        df_raw.columns = df_raw.columns.str.strip()
        df_raw['DATE'] = pd.to_datetime(df_raw['DATE'], dayfirst=True, format='mixed', errors='coerce')
        if 'CAGE/TANK' in df_raw.columns:
            df_raw['CAGE/TANK'] = df_raw['CAGE/TANK'].astype(str).str.strip()
        return df_raw.dropna(subset=['DATE', 'CAGE/TANK', 'AMOUNT'])
    except Exception as e:
        return None

GSHEET_LINK = "https://docs.google.com/spreadsheets/d/1ulkNlLKzoAZGOCF0j8oVFUkhDtGjWkhR/edit?usp=sharing"
df = load_data_from_gsheets(GSHEET_LINK)

if df is None or df.empty:
    st.error("⚠️ Connection Error: Could not retrieve data from Google Sheets.")
    st.stop()

# --- SIDEBAR CONTROLS ---
st.sidebar.markdown(f"<h3 style='color:{R_BLUE}; text-align:center;'>Control Panel</h3>", unsafe_allow_html=True)
st.sidebar.success(f"✔️ {len(df)} records synced from Cloud")

sections = sorted(list(set(str(x)[0] for x in df['CAGE/TANK'].unique() if x)))
selected_section = st.sidebar.selectbox("Select Production Section", sections)

cages = sorted([c for c in df['CAGE/TANK'].unique() if str(c).startswith(selected_section)])
selected_cage = st.sidebar.selectbox("Cage / Tank ID", cages)

st.sidebar.divider()
st.sidebar.subheader("📅 Production Timeline")
min_d, max_d = df['DATE'].min().to_pydatetime(), df['DATE'].max().to_pydatetime()
stock_date = st.sidebar.date_input("Stocking Date (DD/MM/YYYY)", min_d, format="DD/MM/YYYY")
harvest_date = st.sidebar.date_input("Harvesting Date (DD/MM/YYYY)", max_d, format="DD/MM/YYYY")

# --- HEADER ---
if logo_base64:
    st.markdown(f"""<div class="header-container"><img src="data:image/png;base64,{logo_base64}" class="circular-logo"><h2 style="margin-top:10px; color:{R_BLUE};">RENDALLI COMPANY LIMITED</h2><p style="color:#666;">Precision Aquaculture Production Management</p></div>""", unsafe_allow_html=True)

if not stock_date or not harvest_date:
    st.info("💡 Please complete the date entry in the sidebar to view analysis.")
    st.stop()

# --- PROCESSING ---
mask = (df['CAGE/TANK'] == selected_cage) & \
       (df['DATE'].dt.date >= stock_date) & \
       (df['DATE'].dt.date <= harvest_date)
f_df = df.loc[mask].sort_values('DATE')

# --- MAIN DASHBOARD LAYOUT ---
if f_df.empty:
    st.warning(f"No records found for Cage {selected_cage} in this specific date range.")
    st.info(f"Note: Data for {selected_cage} starts on {df[df['CAGE/TANK']==selected_cage]['DATE'].min().strftime('%d/%m/%Y')}")
else:
    # 1. KPI Row
    total_feed = f_df['AMOUNT'].sum()
    cycle_days = (pd.to_datetime(harvest_date) - pd.to_datetime(stock_date)).days
    avg_intake = total_feed / cycle_days if cycle_days > 0 else total_feed

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Cycle Total Feed", f"{total_feed:,.1f} Kgs")
    kpi2.metric("Cycle Duration", f"{cycle_days} Days")
    kpi3.metric("Daily Avg", f"{avg_intake:.2f} Kgs")
    
    z = np.polyfit(range(len(f_df)), f_df['AMOUNT'], 1) if len(f_df) > 5 else [0,0]
    p = np.poly1d(z)
    forecast_30 = max(0, p(len(f_df) + 15) * 30)
    kpi4.metric("30-Day Forecast", f"{forecast_30:,.0f} Kgs")

    st.markdown("---")

    # 2. Inventory & Trend
    col_breakdown, col_trend = st.columns([1, 2])
    with col_breakdown:
        st.markdown(f"#### 📦 Inventory Breakdown: {selected_cage}")
        breakdown = f_df.groupby('FEED TYPE')['AMOUNT'].sum().reset_index()
        breakdown.columns = ['Feed Type', 'Amount (Kgs)']
        st.dataframe(breakdown.style.format({'Amount (Kgs)': '{:,.1f}'}), use_container_width=True, hide_index=True)
        st.markdown(f"""<div style="background-color:{R_BLUE}; color:white; padding:10px; border-radius:5px; text-align:center;"><strong>TOTAL INVENTORY: {total_feed:,.1f} Kgs</strong></div>""", unsafe_allow_html=True)
        
        fig_pie = px.pie(breakdown, names='Feed Type', values='Amount (Kgs)', hole=0.6, color_discrete_sequence=[R_BLUE, R_GOLD, "#5B9BD5"])
        fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0), height=250)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_trend:
        st.markdown(f"#### 📈 Production Trend Analysis")
        fig_area = px.area(f_df, x='DATE', y='AMOUNT', color_discrete_sequence=[R_BLUE], template="plotly_white")
        fig_area.update_layout(xaxis_title="Timeline", yaxis_title="Daily Feed (Kgs)", height=400)
        st.plotly_chart(fig_area, use_container_width=True)

    # 3. RESTORED: Technical Profile & AI Status
    st.markdown("---")
    st.markdown(f"### 📋 Technical Profile & AI Status: {selected_cage}")
    info1, info2, info3 = st.columns(3)
    
    with info1:
        st.markdown("**Production Status**")
        farm_avg = df['AMOUNT'].mean()
        if avg_intake > (farm_avg * 1.1):
            st.success("✅ HIGH PERFORMANCE: Above farm average.")
        else:
            st.info("ℹ️ STANDARD: Consistent with farm baseline.")

    with info2:
        st.markdown("**Dominant Feed Size**")
        top_feed = breakdown.sort_values('Amount (Kgs)', ascending=False).iloc[0]['Feed Type']
        st.write(f"The primary feed used in this period is **{top_feed}**.")

    with info3:
        st.markdown("**Growth Phase Prediction**")
        slope = z[0]
        if slope > 0.05:
            st.write("📈 **Active Growth**: Fish are in a rapid intake stage.")
        else:
            st.write("⚖️ **Stable Intake**: Feed consumption is steady.")

st.markdown("<br><hr><p style='text-align: center; color: #999;'>© 2026 Rendalli Company Limited</p>", unsafe_allow_html=True)