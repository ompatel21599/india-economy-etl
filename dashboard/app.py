import os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="India Economy Dashboard", page_icon="🇮🇳",
                   layout="wide", initial_sidebar_state="collapsed")

BG_IMAGES = [
    "https://images.unsplash.com/photo-1532375810709-75b1da00537c?w=1600",
    "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1600",
    "https://images.unsplash.com/photo-1558862107-d49ef2a04d72?w=1600",
    "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=1600",
    "https://images.unsplash.com/photo-1611516491426-03025e6043c8?w=1600",
]
PALETTE = ["#FF9933","#4FC3F7","#81C784","#FFD54F","#CE93D8","#80CBC4","#F48FB1"]
DECADE_CONTEXT = {
    "1970s":"Oil shocks and socialist planning — a tightly controlled import-substitution economy with minimal FDI.",
    "1980s":"Rajiv Gandhi's partial liberalisation. Deficit-financed growth foreshadowed the 1991 balance-of-payments crisis.",
    "1990s":"Historic LPG reforms (1991) opened India to the world and planted the seeds of the IT revolution.",
    "2000s":"Golden era — 8–9% growth driven by IT-BPO exports, a youthful demographic dividend, and global liquidity.",
    "2010s":"JAM trinity, demonetisation (2016), and GST (2017) restructured India's digital economy.",
    "2020s":"COVID-19 delivered the deepest contraction on record. India rebounded as the world's fastest-growing major economy.",
}
KEY_EVENTS = {1979:"Drought & Oil Shock",1991:"LPG Reforms",
              2008:"Global Financial Crisis",2016:"Demonetisation",2020:"COVID-19"}

# ── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background-size:cover;background-position:center;background-attachment:fixed;}
div[data-testid="stMetric"]{
    background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);
    border-radius:14px;padding:18px 16px;transition:all .2s;}
div[data-testid="stMetric"]:hover{
    border-color:rgba(255,153,51,0.45);background:rgba(255,153,51,0.05);}
div[data-testid="stMetricValue"]{font-size:26px!important;color:#FF9933!important;font-weight:700!important;}
div[data-testid="stMetricLabel"]{color:#9AAAB7!important;font-size:12px!important;}
.sec-head{color:#FF9933;font-size:18px;font-weight:700;margin-bottom:3px;}
.sec-desc{color:#6B7C8E;font-size:12px;font-style:italic;margin-bottom:12px;}
.drill-panel{
    background:rgba(255,153,51,0.06);border-left:3px solid #FF9933;
    border-radius:0 10px 10px 0;padding:14px 20px;margin:8px 0 16px;
    animation:fadeIn .3s ease;}
@keyframes fadeIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
hr{border-color:rgba(255,255,255,0.06)!important;margin:22px 0!important;}
h1{color:white!important;font-weight:700!important;}
.stSelectbox label,.stMultiSelect label{color:#9AAAB7!important;font-size:12px!important;}
.stDownloadButton button{
    background:rgba(255,153,51,0.1)!important;
    border:1px solid rgba(255,153,51,0.3)!important;
    color:#FF9933!important;border-radius:8px!important;}
iframe[height="0"]{display:none!important;}
</style>""", unsafe_allow_html=True)

# ── Rotating background ────────────────────────────────────────────────────
_imgs = str(BG_IMAGES).replace("'",'"')
components.html(f"""<script>
(function(){{
    const imgs={_imgs};let idx=0;
    function go(){{
        const a=window.parent.document.querySelector('.stApp');
        if(a){{
            a.style.backgroundImage='linear-gradient(rgba(0,5,18,.83),rgba(0,5,18,.83)),url("'+imgs[idx]+'")';
            a.style.transition='background-image 1.5s ease';
            idx=(idx+1)%imgs.length;
        }}
    }}
    go();setInterval(go,9000);
}})();
</script>""", height=0)

# ── Data ───────────────────────────────────────────────────────────────────
def get_secret(key):
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key)

@st.cache_data
def load_data():
    db_user = get_secret("DB_USER")
    db_password = get_secret("DB_PASSWORD")
    db_host = get_secret("DB_HOST")
    db_port = get_secret("DB_PORT")
    db_name = get_secret("DB_NAME")

    engine = create_engine(
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require")
    df = pd.read_sql("SELECT * FROM india_economy_data ORDER BY year", engine)
    df["decade"] = (df["year"] // 10 * 10).astype(str) + "s"
    df["inf_cat"] = pd.cut(df["inflation_rate"], bins=[-999,5,10,999],
                           labels=["Low <5%","Medium 5–10%","High >10%"])
    return df

df = load_data()

# ── Session state ──────────────────────────────────────────────────────────
if "sel_year" not in st.session_state:
    st.session_state.sel_year = None

# ── Helpers ────────────────────────────────────────────────────────────────
def parse_year(ev):
    if not ev or not ev.selection or not ev.selection.points:
        return None
    pt = ev.selection.points[0]
    cd = pt.get("customdata")
    if cd is not None:
        if isinstance(cd, (list, tuple)) and len(cd) > 0:
            try: return int(cd[0])
            except: pass
        else:
            try: return int(cd)
            except: pass
    for key in ["x"]:
        val = pt.get(key)
        if val is not None:
            try: return int(val)
            except: pass
    return None

def base2d(title=""):
    return dict(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", family="Inter, sans-serif", size=11),
        title=dict(text=title, font=dict(color="white", size=13), x=0.01),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="rgba(255,255,255,.7)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="rgba(255,255,255,.7)"),
        legend=dict(bgcolor="rgba(255,255,255,0.04)", bordercolor="rgba(255,255,255,.07)", borderwidth=1),
        margin=dict(t=45, b=35, l=40, r=15),
        hoverlabel=dict(bgcolor="rgba(10,15,30,.92)", font_color="white"),
        hovermode="x unified")

def base3d(title=""):
    scene = dict(
        bgcolor="rgba(6,10,28,.75)",
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,.07)",
                   showbackground=True, backgroundcolor="rgba(0,0,0,.3)",
                   color="rgba(255,255,255,.6)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,.07)",
                   showbackground=True, backgroundcolor="rgba(0,0,0,.3)",
                   color="rgba(255,255,255,.6)"),
        zaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,.07)",
                   showbackground=True, backgroundcolor="rgba(0,0,0,.3)",
                   color="rgba(255,255,255,.6)"),
        camera=dict(eye=dict(x=1.5, y=1.4, z=0.8)))
    return dict(
        paper_bgcolor="rgba(0,0,0,0)", scene=scene,
        font=dict(color="white", family="Inter, sans-serif", size=11),
        title=dict(text=title, font=dict(color="white", size=13), x=0.01),
        margin=dict(t=45, b=5, l=5, r=5),
        hoverlabel=dict(bgcolor="rgba(10,15,30,.92)", font_color="white"))

def add_star(fig, yr, df_data, ycol):
    if yr is None: return
    rows = df_data[df_data["year"] == yr]
    if rows.empty: return
    fig.add_trace(go.Scatter(
        x=[yr], y=[rows[ycol].iloc[0]], mode="markers",
        marker=dict(size=16, color="#FFD700", symbol="star",
                    line=dict(color="white", width=2)),
        showlegend=False,
        hovertemplate=f"<b>★ {yr}</b><br>{ycol}: {rows[ycol].iloc[0]:.2f}%<extra></extra>"))

def drill_panel(year):
    if not year: return
    rows = df[df["year"] == year]
    if rows.empty: return
    r = rows.iloc[0]
    rank = int(df["gdp_growth_rate"].rank(ascending=False)[df["year"] == year].iloc[0])
    pct = round((1 - rank / len(df)) * 100)
    ctx = DECADE_CONTEXT.get(r["decade"], "")
    gdp_c = "#81C784" if r["gdp_growth_rate"] >= 6 else ("#FFD54F" if r["gdp_growth_rate"] >= 3 else "#EF5350")
    ev = KEY_EVENTS.get(year, "")
    ev_html = f'<span style="background:rgba(255,153,51,.15);color:#FF9933;border-radius:6px;padding:2px 10px;font-size:11px;margin-left:8px;">⚡ {ev}</span>' if ev else ""
    st.markdown(f"""
<div class="drill-panel">
  <b style="color:#FF9933;font-size:15px;">🔍 Year {year}</b>{ev_html}
  <div style="display:flex;gap:28px;margin:10px 0 8px;flex-wrap:wrap;">
    <div><span style="color:#6B7C8E;font-size:10px;text-transform:uppercase;letter-spacing:.5px;">GDP Growth</span><br>
         <b style="color:{gdp_c};font-size:21px;">{r['gdp_growth_rate']:.2f}%</b></div>
    <div><span style="color:#6B7C8E;font-size:10px;text-transform:uppercase;letter-spacing:.5px;">Inflation</span><br>
         <b style="color:white;font-size:21px;">{r['inflation_rate']:.2f}%</b></div>
    <div><span style="color:#6B7C8E;font-size:10px;text-transform:uppercase;letter-spacing:.5px;">FDI Inflow</span><br>
         <b style="color:#4FC3F7;font-size:21px;">{r['fdi_inflow']:.2f}%</b></div>
    <div><span style="color:#6B7C8E;font-size:10px;text-transform:uppercase;letter-spacing:.5px;">GDP Rank / 55</span><br>
         <b style="col