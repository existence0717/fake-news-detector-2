import streamlit as st
import sqlite3
import pandas as pd
import time
import altair as alt
import io

# --- ⚙️ PAGE CONFIG ---
st.set_page_config(
    page_title="IICCC Dashboard", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 🧹 CSS: PROFESSIONAL UI WITH COLOR CODING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');
    .stApp { background-color: #f8fafc; font-family: 'Outfit', sans-serif; }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    
    .header-container {
        display: flex; align-items: center; background-color: white;
        padding: 20px 30px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 25px; border: 1px solid #e2e8f0;
    }
    .logo-box {
        width: 48px; height: 48px; background: #0f172a; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px; color: white; margin-right: 18px;
    }
    .main-title { font-size: 24px; font-weight: 700; color: #0f172a; margin: 0; }
    .sub-title { font-size: 13px; color: #64748b; margin-top: 2px; font-weight: 500; }
    
    .metric-card {
        background-color: white; border-radius: 12px; padding: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 1px solid #e2e8f0;
        text-align: left; height: 100%;
    }
    .metric-header {
        color: #64748b; font-size: 12px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.5px; margin-bottom: 8px;
    }
    .metric-value { font-size: 34px; font-weight: 700; color: #0f172a; margin: 0; }
    
    .content-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border: 1px solid #e2e8f0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .stTextInput input { border-radius: 12px; padding: 12px 20px; }
    div[data-testid="stDataFrame"] {border: none;}
    .footer {text-align: center; font-size: 12px; color: #94a3b8; margin-top: 30px;}
    
    /* Risk Level Badges */
    .risk-critical { background: #dc2626; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; }
    .risk-high { background: #f97316; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; }
    .risk-medium { background: #eab308; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; }
    .risk-low { background: #22c55e; color: white; padding: 4px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 📥 DATA LOADING ---
def load_data():
    try:
        import os
        if not os.path.exists('fake_news.db'):
            conn = sqlite3.connect('fake_news.db', timeout=10)
            conn.execute('PRAGMA journal_mode=WAL')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT,
                    title TEXT,
                    url TEXT UNIQUE,
                    image_url TEXT,
                    views INTEGER,
                    tags TEXT,
                    panic_score REAL,
                    verdict TEXT,
                    virality_vd REAL,
                    ai_explanation TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
        
        conn = sqlite3.connect('fake_news.db', timeout=10)
        conn.execute('PRAGMA journal_mode=WAL')
        df = pd.read_sql_query("SELECT * FROM content_log ORDER BY id DESC LIMIT 500", conn)
        conn.close()
        
        if 'virality_vd' not in df.columns: 
            df['virality_vd'] = 0.0
        if 'ai_explanation' not in df.columns:
            df['ai_explanation'] = ''
        
        return df
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# Helper function for risk level
def get_risk_level(score):
    if score >= 0.8:
        return "CRITICAL", "#dc2626"
    elif score >= 0.6:
        return "HIGH", "#f97316"
    elif score >= 0.4:
        return "MEDIUM", "#eab308"
    else:
        return "LOW", "#22c55e"

# Load data
df = load_data()
total_records = len(df)

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    # Export button
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"iiccc_threats_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    st.markdown("### 🔍 Filters")
    
    # Time filter
    hours_back = st.slider("Show last N hours", 1, 168, 24, help="Filter threats by time")
    
    # Verdict filter
    if not df.empty:
        all_verdicts = sorted(df['verdict'].unique().tolist())
        selected_verdicts = st.multiselect(
            "Verdict Type",
            options=all_verdicts,
            default=all_verdicts,
            help="Select which threat types to show"
        )
    else:
        selected_verdicts = []
    
    # Risk threshold
    min_risk = st.slider(
        "Minimum Risk Score (%)", 
        0, 100, 0,
        help="Show only threats above this risk level"
    )
    
    # Platform filter
    if not df.empty:
        all_platforms = sorted(df['platform'].unique().tolist())
        selected_platforms = st.multiselect(
            "Platform",
            options=all_platforms,
            default=all_platforms,
            help="Filter by data source"
        )
    else:
        selected_platforms = []
    
    st.markdown("---")
    
    # Statistics
    if not df.empty:
        st.markdown("### 📊 Quick Stats")
        avg_risk = df['panic_score'].mean() * 100
        st.metric("Avg Risk Score", f"{avg_risk:.1f}%")
        
        top_platform = df['platform'].value_counts().index[0]
        st.metric("Top Platform", top_platform)
        
        critical_count = len(df[df['panic_score'] >= 0.8])
        st.metric("Critical Threats", critical_count)
    
    st.markdown("---")
    st.caption(f"Total records: {total_records}")
    st.caption("IICCC v2.0")

# Apply filters
filtered_df = df.copy()

if not filtered_df.empty:
    # Time filter
    try:
        cutoff_time = pd.Timestamp.now() - pd.Timedelta(hours=hours_back)
        filtered_df['timestamp'] = pd.to_datetime(filtered_df['timestamp'])
        filtered_df = filtered_df[filtered_df['timestamp'] > cutoff_time]
    except:
        pass
    
    # Verdict filter
    if selected_verdicts:
        filtered_df = filtered_df[filtered_df['verdict'].isin(selected_verdicts)]
    
    # Risk filter
    filtered_df = filtered_df[filtered_df['panic_score'] >= (min_risk / 100)]
    
    # Platform filter
    if selected_platforms:
        filtered_df = filtered_df[filtered_df['platform'].isin(selected_platforms)]

# --- 🖥️ UI LAYOUT ---

# 1. HEADER
st.markdown("""
<div class="header-container">
    <div class="logo-box">🛡️</div>
    <div>
        <h1 class="main-title">Information Integrity Command and Control Centre</h1>
        <div class="sub-title">System Status: 🟢 OPERATIONAL | Live Intelligence Stream</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. SEARCH BAR
search_query = st.text_input(
    "", 
    placeholder="🔍 Search Intelligence Database (e.g., 'scam', 'deepfake')...", 
    label_visibility="collapsed"
)

if search_query and not filtered_df.empty:
    mask = (
        filtered_df['title'].str.contains(search_query, case=False, na=False) | 
        filtered_df['verdict'].str.contains(search_query, case=False, na=False) | 
        filtered_df['tags'].str.contains(search_query, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

# 3. METRIC CARDS
st.markdown("###")
scanned = len(filtered_df)
fakes = len(filtered_df[filtered_df['verdict'].str.contains("FAKE|DEEPFAKE|SCAM", case=False, na=False)]) if not filtered_df.empty else 0
high_vel = len(filtered_df[(filtered_df['virality_vd'] > 50) | (filtered_df['views'] > 50000)]) if not filtered_df.empty else 0
critical = len(filtered_df[filtered_df['panic_score'] >= 0.8]) if not filtered_df.empty else 0

c1, c2, c3, c4 = st.columns(4)

def card(title, value, is_danger=False):
    text_color = "#dc2626" if is_danger else "#0f172a"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-header">{title}</div>
        <div class="metric-value" style="color: {text_color}">{value}</div>
    </div>
    """, unsafe_allow_html=True)

with c1: card("Threats Scanned", scanned)
with c2: card("Confirmed Fakes", f"{fakes:03d}", is_danger=True)
with c3: card("High Velocity", f"{high_vel:03d}")
with c4: card("Critical Alerts", f"{critical:03d}", is_danger=True)

# 4. CHARTS
st.markdown("###")
col_left, col_mid, col_right = st.columns(3)

with col_left:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("**Threat Classification**")
    if not filtered_df.empty:
        verdict_counts = filtered_df['verdict'].value_counts().reset_index()
        verdict_counts.columns = ['Verdict', 'Count']
        
        pie_chart = alt.Chart(verdict_counts).mark_arc(innerRadius=50).encode(
            theta=alt.Theta('Count:Q'),
            color=alt.Color('Verdict:N', scale=alt.Scale(scheme='category20')),
            tooltip=['Verdict', 'Count']
        ).properties(height=250)
        
        st.altair_chart(pie_chart, use_container_width=True)
    else: 
        st.info("No data matches your filters.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_mid:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("**Risk Distribution**")
    if not filtered_df.empty:
        # Create risk level categories
        risk_levels = filtered_df['panic_score'].apply(
            lambda x: 'CRITICAL' if x >= 0.8 else ('HIGH' if x >= 0.6 else ('MEDIUM' if x >= 0.4 else 'LOW'))
        ).value_counts().reset_index()
        risk_levels.columns = ['Level', 'Count']
        
        bar_chart = alt.Chart(risk_levels).mark_bar(cornerRadius=5).encode(
            x=alt.X('Level', sort=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], axis=alt.Axis(title=None)),
            y=alt.Y('Count', title='Volume'),
            color=alt.Color('Level', scale=alt.Scale(
                domain=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
                range=['#dc2626', '#f97316', '#eab308', '#22c55e']
            ), legend=None),
            tooltip=['Level', 'Count']
        ).properties(height=250)
        
        st.altair_chart(bar_chart, use_container_width=True)
    else: 
        st.info("No data matches your filters.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="content-card">', unsafe_allow_html=True)
    st.markdown("**Viral Velocity Trend**")
    if not filtered_df.empty:
        line_data = filtered_df.head(50).reset_index()
        curve = alt.Chart(line_data).mark_line(
            point=True,
            color='#7c3aed',
            strokeWidth=3
        ).encode(
            x=alt.X('index', title='Recent Scans'),
            y=alt.Y('virality_vd', title='Virality'), 
            tooltip=['title', 'virality_vd']
        ).properties(height=250)
        
        st.altair_chart(curve, use_container_width=True)
    else: 
        st.info("No data matches your filters.")
    st.markdown('</div>', unsafe_allow_html=True)

# 5. LIVE THREAT STREAM WITH COLOR CODING
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.markdown("**🚨 Live Threat Stream**")

if not filtered_df.empty:
    cols = ['timestamp', 'platform', 'panic_score', 'verdict', 'views', 'title', 'url']
    if 'ai_explanation' in filtered_df.columns:
        cols.append('ai_explanation')
    display_df = filtered_df[cols].copy()
    
    # Add risk level column
    display_df['risk_level'] = display_df['panic_score'].apply(lambda x: get_risk_level(x)[0])
    
    if 'panic_score' in display_df.columns:
        display_df['panic_score'] = display_df['panic_score'].fillna(0)
        display_df['risk_pct'] = (display_df['panic_score'] * 100).astype(int)
    
    col_order = ['timestamp', 'platform', 'risk_level', 'risk_pct', 'verdict', 'views', 'title']
    if 'ai_explanation' in display_df.columns:
        col_order.append('ai_explanation')
    col_order.append('url')
    display_df = display_df[col_order]
    
    col_config = {
        "timestamp": st.column_config.DatetimeColumn("Time", format="HH:mm"),
        "platform": st.column_config.TextColumn("Platform", width="small"),
        "risk_level": st.column_config.TextColumn("Risk", width="small"),
        "risk_pct": st.column_config.ProgressColumn("Score", format="%d%%", min_value=0, max_value=100),
        "verdict": st.column_config.TextColumn("Verdict", width="medium"),
        "views": st.column_config.NumberColumn("Reach", format="%d"),
        "title": st.column_config.TextColumn("Headline", width="large"),
        "url": st.column_config.LinkColumn("Source")
    }
    if 'ai_explanation' in display_df.columns:
        col_config["ai_explanation"] = st.column_config.TextColumn("AI Reason", width="medium", help="Why the AI classified it this way")
    
    st.dataframe(
        display_df, 
        use_container_width=True,
        column_config=col_config,
        hide_index=True,
        height=400
    )
elif search_query:
    st.warning(f"No results for '{search_query}'")
elif total_records > 0:
    st.info("No data matches your filters. Try adjusting sidebar settings.")
else:
    st.info("System is scanning. First threats will appear shortly.")

st.markdown('</div>', unsafe_allow_html=True)

# 6. FOOTER
st.markdown('<div class="footer">IICCC System v2.0 | Multi-Factor Risk Analysis | Restricted Access</div>', unsafe_allow_html=True)
