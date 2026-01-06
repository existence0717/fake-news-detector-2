import streamlit as st
import sqlite3
import pandas as pd
import time
import altair as alt

# --- ⚙️ PAGE CONFIG ---
st.set_page_config(
    page_title="CMS Dashboard", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 🧹 CSS: UNIFORM PROFESSIONAL LOOK ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');

    .stApp {
        background-color: #f8fafc; /* Professional Light Grey */
        font-family: 'Outfit', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}

    /* HEADER & LOGO */
    .header-container {
        display: flex;
        align-items: center;
        background-color: white;
        padding: 20px 30px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        border: 1px solid #e2e8f0;
    }
    .logo-box {
        width: 48px;
        height: 48px;
        background: #7c3aed; /* UNIFORM BRAND PURPLE */
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: white;
        margin-right: 18px;
    }
    .main-title {
        font-size: 26px;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
    }
    .sub-title {
        font-size: 13px;
        color: #64748b;
        margin-top: 2px;
    }

    /* METRIC CARDS - UNIFORM COLOR */
    .metric-card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
        text-align: left;
        height: 100%;
    }
    .metric-header {
        color: #7c3aed; /* Uniform Purple Text */
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 34px;
        font-weight: 700;
        color: #1e293b;
        margin: 0;
    }

    /* CONTENT CONTAINERS */
    .content-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    div[data-testid="stDataFrame"] {border: none;}
    
    /* FOOTER */
    .footer {
        text-align: center;
        font-size: 12px;
        color: #94a3b8;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- 🔄 AUTO REFRESH ---
if 'last_update' not in st.session_state: st.session_state['last_update'] = time.time()
if time.time() - st.session_state['last_update'] > 3:
    st.session_state['last_update'] = time.time()
    st.rerun()

# --- 📥 DATA LOADING ---
def load_data():
    try:
        conn = sqlite3.connect('fake_news.db')
        df = pd.read_sql_query("SELECT * FROM content_log ORDER BY id DESC", conn)
        conn.close()
        if 'virality_vd' not in df.columns: df['virality_vd'] = 0.0
        return df
    except: return pd.DataFrame()

df = load_data()

# --- 🖥️ UI LAYOUT ---

# 1. HEADER
st.markdown("""
<div class="header-container">
    <div class="logo-box">🛡️</div>
    <div>
        <h1 class="main-title">Centre for Misinformation Surveillance</h1>
        <div class="sub-title">System Status: 🟢 Online | Connected to Edge Database (SQLite)</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. METRIC CARDS (Uniform Colors as requested)
st.markdown("###")
scanned = len(df)
fakes = len(df[df['verdict'].str.contains("FAKE|DEEPFAKE|SCAM", case=False, na=False)])
high_vel = len(df[(df['virality_vd'] > 50) | (df['views'] > 50000)])
max_reach = df['views'].max() if not df.empty else 0
reach_label = f"{max_reach/1000000:.1f}M" if max_reach > 1000000 else f"{max_reach:,.0f}"

c1, c2, c3, c4 = st.columns(4)

def card(title, value):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-header">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

with c1: card("Threats Scanned", scanned)
with c2: card("Confirmed Fakes", f"{fakes:03d}")
with c3: card("High Velocity Events", f"{high_vel:03d}")
with c4: card("Max Viral Reach", reach_label)

# 3. CHARTS
st.markdown("###")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("**Threat Classification**")
    if not df.empty:
        verdict_counts = df['verdict'].value_counts().reset_index()
        verdict_counts.columns = ['Verdict', 'Count']
        
        bar_chart = alt.Chart(verdict_counts).mark_bar(cornerRadius=5).encode(
            x=alt.X('Verdict', axis=alt.Axis(labelAngle=0, title=None, labelFont='Outfit')),
            y=alt.Y('Count', title='Volume'), # Legend added back
            color=alt.Color('Verdict', legend=None, scale=alt.Scale(scheme='purpleblue')),
            tooltip=['Verdict', 'Count']
        ).properties(height=280).configure_axis(grid=False).configure_view(strokeWidth=0)
        
        st.altair_chart(bar_chart, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("**Viral Velocity Map**")
    if not df.empty:
        line_data = df.head(50).reset_index()
        curve = alt.Chart(line_data).mark_area(
            interpolate='monotone',
            line={'color':'#7c3aed', 'strokeWidth': 3},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='rgba(124, 58, 237, 0.3)', offset=0),
                       alt.GradientStop(color='rgba(124, 58, 237, 0.0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X('index', title='Recent Scans (Time)'), # Axis Label Added
            y=alt.Y('virality_vd', title='Virality Score (R/T)'), # Axis Label Added
            tooltip=['title', 'virality_vd']
        ).properties(height=280).configure_view(strokeWidth=0)
        st.altair_chart(curve, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# 4. LIVE THREAT STREAM (With Panic Score)
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.markdown("**🚨 Live Threat Stream**")
if not df.empty:
    display_df = df[['timestamp', 'platform', 'panic_score', 'verdict', 'title', 'url']].copy()
    
    # Format Panic Score to Percentage
    display_df['panic_score'] = (display_df['panic_score'] * 100).astype(int)

    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Time", format="HH:mm"),
            "url": st.column_config.LinkColumn("Source"),
            "panic_score": st.column_config.ProgressColumn(
                "Panic %", 
                format="%d%%", 
                min_value=0, 
                max_value=100
            ),
            "verdict": st.column_config.TextColumn("Verdict"),
            "title": st.column_config.TextColumn("Headline", width="large")
        },
        hide_index=True
    )
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">CMS System v2.5 | Enterprise Edition</div>', unsafe_allow_html=True)
