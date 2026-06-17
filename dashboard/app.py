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
         <b style="color:#FFD54F;font-size:21px;">#{rank} <span style="font-size:12px;color:#9AAAB7;">({pct}th pct)</span></b></div>
  </div>
  <p style="color:#7D8FA0;font-size:12px;margin:0;line-height:1.65;">{ctx}</p>
</div>""", unsafe_allow_html=True)

def section(title, desc):
    st.markdown(f'<p class="sec-head">{title}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sec-desc">{desc}</p>', unsafe_allow_html=True)

# ── Hero parallax ──────────────────────────────────────────────────────────
components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
#hero{perspective:1200px;padding:36px 16px 16px;}
#tilt{
    transform-style:preserve-3d;transition:transform .18s ease;
    background:linear-gradient(135deg,rgba(255,153,51,.07),rgba(79,195,247,.05));
    border:1px solid rgba(255,153,51,.14);border-radius:20px;padding:34px 42px;cursor:default;}
.ht{transform:translateZ(28px);}
.htag{font-family:Inter,sans-serif;font-size:10px;letter-spacing:3px;color:#FF9933;
    text-transform:uppercase;background:rgba(255,153,51,.1);border:1px solid rgba(255,153,51,.2);
    border-radius:20px;padding:4px 14px;margin-bottom:14px;display:inline-block;}
.hh{font-family:Inter,sans-serif;font-size:26px;font-weight:700;margin:0 0 12px;
    background:linear-gradient(135deg,#FF9933,#FFD54F 45%,#4FC3F7);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hb{font-family:Inter,sans-serif;font-size:13.5px;color:#8A9BB0;line-height:1.75;
    max-width:700px;margin:0 0 20px;}
.hb b{color:#FF9933;}
.hgrid{display:flex;gap:28px;flex-wrap:wrap;}
.hstat{text-align:center;}
.hnum{font-family:Inter,sans-serif;font-size:22px;font-weight:700;}
.hlabel{font-family:Inter,sans-serif;font-size:11px;color:#6B7C8E;letter-spacing:.4px;}
</style>
<div id="hero">
  <div id="tilt">
    <div class="ht">
      <div class="htag">Data-Driven Economic Intelligence</div>
      <h2 class="hh">India's Economic Journey — 1970 to 2024</h2>
      <p class="hb">
        From a tightly controlled socialist economy to one of the world's fastest-growing powers —
        this dashboard maps <b>55 years</b> of India's macroeconomic evolution using real World Bank data,
        <b>machine learning models</b>, and interactive <b>3D visualisations</b>.
        Every chart is a chapter. Every data point, a decision that shaped a billion lives.
      </p>
      <div class="hgrid">
        <div class="hstat"><div class="hnum" style="color:#FF9933;">55</div><div class="hlabel">Years of Data</div></div>
        <div class="hstat"><div class="hnum" style="color:#4FC3F7;">3</div><div class="hlabel">Key Indicators</div></div>
        <div class="hstat"><div class="hnum" style="color:#81C784;">7+</div><div class="hlabel">ML Models</div></div>
        <div class="hstat"><div class="hnum" style="color:#FFD54F;">Live</div><div class="hlabel">World Bank API</div></div>
      </div>
    </div>
  </div>
</div>
<script>
const h=document.getElementById('hero'),t=document.getElementById('tilt');
h.addEventListener('mousemove',e=>{
    const r=h.getBoundingClientRect();
    const x=(e.clientX-r.left)/r.width-.5;
    const y=(e.clientY-r.top)/r.height-.5;
    t.style.transform='rotateY('+x*14+'deg) rotateX('+(-y*9)+'deg)';
});
h.addEventListener('mouseleave',()=>{t.style.transform='rotateY(0) rotateX(0)';});
</script>
""", height=270)

st.markdown("---")

# ── KPIs ───────────────────────────────────────────────────────────────────
k1,k2,k3,k4 = st.columns(4)
with k1:
    v=df["gdp_growth_rate"].iloc[-1]; p=df["gdp_growth_rate"].iloc[-2]
    st.metric("📈 Latest GDP Growth", f"{v:.2f}%", f"{v-p:+.2f}%")
with k2:
    v=df["inflation_rate"].iloc[-1]; p=df["inflation_rate"].iloc[-2]
    st.metric("💰 Latest Inflation", f"{v:.2f}%", f"{v-p:+.2f}%", delta_color="inverse")
with k3:
    v=df["fdi_inflow"].iloc[-1]; p=df["fdi_inflow"].iloc[-2]
    st.metric("🌍 Latest FDI Inflow", f"{v:.2f}%", f"{v-p:+.2f}%")
with k4:
    st.metric("📊 Avg GDP (55 yrs)", f"{df['gdp_growth_rate'].mean():.2f}%")

st.markdown("---")

# ── Year filter ────────────────────────────────────────────────────────────
section("📅 Filter by Year Range",
        "All charts update instantly. Click any point on any chart to drill down — all other charts highlight that year.")
yf1,yf2 = st.columns(2)
with yf1:
    start_year = st.selectbox("Start Year", sorted(df["year"].unique()), index=0)
with yf2:
    end_year = st.selectbox("End Year", sorted(df["year"].unique(), reverse=True), index=0)
if start_year > end_year:
    st.error("Start year must be ≤ end year.")
    st.stop()
df_f = df[(df["year"] >= start_year) & (df["year"] <= end_year)].copy()

sel = st.session_state.sel_year
if sel:
    c_info, c_clear = st.columns([6,1])
    with c_info:
        st.info(f"🌟 Year **{sel}** selected — highlighted across all charts below.")
    with c_clear:
        if st.button("✕ Clear"):
            st.session_state.sel_year = None
            st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# ROW 1 — Two 3D scatter charts
# ══════════════════════════════════════════════════════════════════════════
section("🌐 3D Economic Space",
        "Drag to rotate. Click any point to select a year — golden star ★ appears across all charts.")
r1c1, r1c2 = st.columns(2)

with r1c1:
    # 3D: Year × GDP × Inflation — trajectory
    sizes = [14 if y == sel else (8 if g < 0 else 6)
             for y,g in zip(df_f["year"], df_f["gdp_growth_rate"])]
    colors = ["#FFD700" if y == sel else ("#EF5350" if g < 0 else "#FF9933")
              for y,g in zip(df_f["year"], df_f["gdp_growth_rate"])]
    fig3d1 = go.Figure()
    fig3d1.add_trace(go.Scatter3d(
        x=df_f["year"], y=df_f["gdp_growth_rate"], z=df_f["inflation_rate"],
        mode="lines", line=dict(color="rgba(255,153,51,.25)", width=2),
        showlegend=False, hoverinfo="skip"))
    fig3d1.add_trace(go.Scatter3d(
        x=df_f["year"], y=df_f["gdp_growth_rate"], z=df_f["inflation_rate"],
        mode="markers",
        marker=dict(size=sizes, color=colors, line=dict(color="rgba(255,255,255,.3)", width=.5)),
        customdata=df_f[["year"]].values,
        hovertemplate="<b>Year: %{customdata[0]}</b><br>GDP: %{y:.2f}%<br>Inflation: %{z:.2f}%<extra></extra>"))
    l3d = base3d("GDP · Inflation · Year — 3D Path")
    l3d["scene"]["xaxis"]["title"] = "Year"
    l3d["scene"]["yaxis"]["title"] = "GDP Growth (%)"
    l3d["scene"]["zaxis"]["title"] = "Inflation (%)"
    fig3d1.update_layout(**l3d, height=420)
    ev1 = st.plotly_chart(fig3d1, use_container_width=True, on_select="rerun", key="c3d1")
    y1 = parse_year(ev1)
    if y1: st.session_state.sel_year = y1; st.rerun()

with r1c2:
    # 3D: GDP × FDI × Inflation — economic space
    sizes2 = [14 if y == sel else 7 for y in df_f["year"]]
    fig3d2 = go.Figure()
    fig3d2.add_trace(go.Scatter3d(
        x=df_f["gdp_growth_rate"], y=df_f["fdi_inflow"], z=df_f["inflation_rate"],
        mode="markers",
        text=[str(y) if y == sel else "" for y in df_f["year"]],
        textfont=dict(color="#FFD700", size=11),
        marker=dict(
            size=sizes2,
            color=df_f["year"].tolist(),
            colorscale="Plasma", showscale=True,
            colorbar=dict(title="Year", thickness=12, len=.6,
                          tickfont=dict(color="white", size=10),
                          title_font=dict(color="white")),
            opacity=.87, line=dict(color="rgba(255,255,255,.2)", width=.5)),
        customdata=df_f[["year"]].values,
        hovertemplate="<b>Year: %{customdata[0]}</b><br>GDP: %{x:.2f}%<br>FDI: %{y:.2f}%<br>Inflation: %{z:.2f}%<extra></extra>"))
    l3d2 = base3d("GDP · FDI · Inflation — Economic Space")
    l3d2["scene"]["xaxis"]["title"] = "GDP Growth (%)"
    l3d2["scene"]["yaxis"]["title"] = "FDI Inflow (%)"
    l3d2["scene"]["zaxis"]["title"] = "Inflation (%)"
    fig3d2.update_layout(**l3d2, height=420)
    ev2 = st.plotly_chart(fig3d2, use_container_width=True, on_select="rerun", key="c3d2")
    y2 = parse_year(ev2)
    if y2: st.session_state.sel_year = y2; st.rerun()

drill_panel(sel)
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# ROW 2 — GDP area chart + Decade 3D surface
# ══════════════════════════════════════════════════════════════════════════
section("📈 GDP Timeline & Decade Landscape",
        "Click any point on the GDP chart to drill down. The 3D surface shows decade-by-decade economic terrain.")
r2c1, r2c2 = st.columns(2)

with r2c1:
    fig_gdp = go.Figure()
    fig_gdp.add_trace(go.Scatter(
        x=df_f["year"], y=df_f["gdp_growth_rate"],
        fill="tozeroy", fillcolor="rgba(255,153,51,.09)",
        line=dict(color="#FF9933", width=2), mode="lines+markers",
        marker=dict(size=6, color="#FF9933"),
        customdata=df_f[["year"]].values,
        hovertemplate="<b>%{x}</b><br>GDP: %{y:.2f}%<extra></extra>"))
    fig_gdp.add_hline(y=0, line_dash="dash", line_color="#EF5350", line_width=1.4,
                      annotation_text="Zero Growth", annotation_font_color="#EF5350",
                      annotation_font_size=10)
    for ev_yr, ev_label in KEY_EVENTS.items():
        if start_year <= ev_yr <= end_year:
            row = df_f[df_f["year"] == ev_yr]
            if not row.empty:
                fig_gdp.add_annotation(
                    x=ev_yr, y=row["gdp_growth_rate"].iloc[0],
                    text=ev_label, showarrow=True, arrowhead=2,
                    arrowcolor="#9AAAB7", font=dict(size=9, color="#FFD700"),
                    bgcolor="rgba(0,0,0,.55)", bordercolor="rgba(255,215,0,.2)", ax=0, ay=-35)
    add_star(fig_gdp, sel, df_f, "gdp_growth_rate")
    fig_gdp.update_layout(**base2d("India GDP Growth Rate"), height=380)
    ev_gdp = st.plotly_chart(fig_gdp, use_container_width=True, on_select="rerun", key="cgdp")
    yg = parse_year(ev_gdp)
    if yg: st.session_state.sel_year = yg; st.rerun()

with r2c2:
    # 3D surface: decade landscape
    decade_list = sorted(df["decade"].unique())
    decade_map = {d: i for i, d in enumerate(decade_list)}
    years_in = sorted(range(0, 10))  # 0–9 = year within decade
    z_surface = []
    for yr_offset in years_in:
        row_vals = []
        for dec in decade_list:
            dec_start = int(dec[:-1])
            yr = dec_start + yr_offset
            match = df[df["year"] == yr]
            row_vals.append(match["gdp_growth_rate"].iloc[0] if not match.empty else 0)
        z_surface.append(row_vals)
    fig_surf = go.Figure(go.Surface(
        z=z_surface,
        x=list(range(len(decade_list))),
        y=years_in,
        colorscale=[[0,"#C62828"],[0.3,"#E65100"],[0.6,"#FFD700"],[1,"#FF9933"]],
        showscale=True,
        colorbar=dict(title="GDP %", thickness=12, len=.6,
                      tickfont=dict(color="white", size=10),
                      title_font=dict(color="white")),
        contours=dict(
            z=dict(show=True, usecolormap=True, project_z=True, highlightcolor="white")),
        hovertemplate="Decade: %{x}<br>Year offset: %{y}<br>GDP: %{z:.2f}%<extra></extra>"))
    l_surf = base3d("GDP Landscape — Decade Surface")
    l_surf["scene"]["xaxis"]["title"] = "Decade"
    l_surf["scene"]["xaxis"]["tickvals"] = list(range(len(decade_list)))
    l_surf["scene"]["xaxis"]["ticktext"] = decade_list
    l_surf["scene"]["yaxis"]["title"] = "Year in Decade"
    l_surf["scene"]["zaxis"]["title"] = "GDP Growth (%)"
    l_surf["scene"]["camera"] = dict(eye=dict(x=1.6, y=1.6, z=0.9))
    fig_surf.update_layout(**l_surf, height=380)
    st.plotly_chart(fig_surf, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# ROW 3 — Inflation + FDI (side by side, 3D scatter style)
# ══════════════════════════════════════════════════════════════════════════
section("📊 Inflation & FDI — 3D Scatter View",
        "3D view of inflation and FDI over time. Click to select a year and see it highlighted everywhere.")
r3c1, r3c2 = st.columns(2)

with r3c1:
    s3 = [14 if y == sel else 7 for y in df_f["year"]]
    fig_inf3d = go.Figure(go.Scatter3d(
        x=df_f["year"], y=df_f["inflation_rate"], z=df_f["fdi_inflow"],
        mode="markers+lines",
        line=dict(color="rgba(79,195,247,.2)", width=2),
        marker=dict(
            size=s3, color=df_f["inflation_rate"],
            colorscale=[[0,"#4FC3F7"],[0.5,"#FFD54F"],[1,"#EF5350"]],
            showscale=True,
            colorbar=dict(title="Inflation", thickness=10, len=.5,
                          tickfont=dict(color="white", size=9),
                          title_font=dict(color="white")),
            line=dict(color="rgba(255,255,255,.2)", width=.5)),
        customdata=df_f[["year"]].values,
        hovertemplate="<b>Year: %{customdata[0]}</b><br>Inflation: %{y:.2f}%<br>FDI: %{z:.2f}%<extra></extra>"))
    li = base3d("Inflation · FDI · Year — 3D")
    li["scene"]["xaxis"]["title"] = "Year"
    li["scene"]["yaxis"]["title"] = "Inflation (%)"
    li["scene"]["zaxis"]["title"] = "FDI (%)"
    fig_inf3d.update_layout(**li, height=380)
    ev3 = st.plotly_chart(fig_inf3d, use_container_width=True, on_select="rerun", key="cinf3d")
    y3 = parse_year(ev3)
    if y3: st.session_state.sel_year = y3; st.rerun()

with r3c2:
    # FDI 2D line with star
    fig_fdi = go.Figure()
    fig_fdi.add_trace(go.Scatter(
        x=df_f["year"], y=df_f["fdi_inflow"],
        mode="lines+markers",
        line=dict(color="#81C784", width=2),
        marker=dict(size=6, color="#81C784"),
        fill="tozeroy", fillcolor="rgba(129,199,132,.08)",
        customdata=df_f[["year"]].values,
        hovertemplate="<b>%{x}</b><br>FDI: %{y:.2f}%<extra></extra>"))
    add_star(fig_fdi, sel, df_f, "fdi_inflow")
    fig_fdi.update_layout(**base2d("FDI Inflow Over Time"), height=380)
    ev_fdi = st.plotly_chart(fig_fdi, use_container_width=True, on_select="rerun", key="cfdi")
    y_fdi = parse_year(ev_fdi)
    if y_fdi: st.session_state.sel_year = y_fdi; st.rerun()

drill_panel(sel)
st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# ROW 4 — Pie + Donut
# ══════════════════════════════════════════════════════════════════════════
section("🥧 Distribution Charts",
        "GDP growth share by decade and years by inflation category.")
r4c1, r4c2 = st.columns(2)

with r4c1:
    decade_pos = (df_f[df_f["gdp_growth_rate"] > 0]
                  .groupby("decade")["gdp_growth_rate"].sum().reset_index())
    decade_pos.columns = ["Decade","Total GDP Growth (%)"]
    fig_pie = go.Figure(go.Pie(
        labels=decade_pos["Decade"],
        values=decade_pos["Total GDP Growth (%)"],
        marker=dict(colors=PALETTE, line=dict(color="rgba(255,255,255,.15)", width=1.5)),
        textinfo="label+percent",
        textfont=dict(color="white", size=12),
        hovertemplate="<b>%{label}</b><br>Total GDP Growth: %{value:.1f}%<br>Share: %{percent}<extra></extra>"))
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text="GDP Growth Share by Decade", font=dict(color="white", size=13), x=0.01),
        legend=dict(font=dict(color="white"), bgcolor="rgba(255,255,255,.04)"),
        margin=dict(t=45, b=10, l=10, r=10), height=360,
        hoverlabel=dict(bgcolor="rgba(10,15,30,.92)", font_color="white"))
    st.plotly_chart(fig_pie, use_container_width=True)

with r4c2:
    inf_counts = df_f["inf_cat"].value_counts().reset_index()
    inf_counts.columns = ["Category","Count"]
    fig_donut = go.Figure(go.Pie(
        labels=inf_counts["Category"],
        values=inf_counts["Count"],
        hole=0.52,
        marker=dict(colors=["#81C784","#FFD54F","#EF5350"],
                    line=dict(color="rgba(255,255,255,.15)", width=1.5)),
        textinfo="label+percent",
        textfont=dict(color="white", size=12),
        hovertemplate="<b>%{label}</b><br>Years: %{value}<br>Share: %{percent}<extra></extra>"))
    fig_donut.add_annotation(
        text=f"{len(df_f)}<br>Years",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color="white", size=16, family="Inter, sans-serif"))
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text="Years by Inflation Category", font=dict(color="white", size=13), x=0.01),
        legend=dict(font=dict(color="white"), bgcolor="rgba(255,255,255,.04)"),
        margin=dict(t=45, b=10, l=10, r=10), height=360,
        hoverlabel=dict(bgcolor="rgba(10,15,30,.92)", font_color="white"))
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# ── Best & Worst ───────────────────────────────────────────────────────────
section("🏆 Best & Worst GDP Years",
        "India's five highest-growth years vs five deepest contractions — ranked across all 55 years.")
cb, cw = st.columns(2)
with cb:
    st.markdown("🟢 **Top 5 Growth Years**")
    best = (df.nlargest(5,"gdp_growth_rate")
              [["year","gdp_growth_rate","inflation_rate","fdi_inflow"]].reset_index(drop=True))
    best.columns = ["Year","GDP Growth (%)","Inflation (%)","FDI (%)"]
    st.dataframe(best, use_container_width=True)
with cw:
    st.markdown("🔴 **Bottom 5 Growth Years**")
    worst = (df.nsmallest(5,"gdp_growth_rate")
               [["year","gdp_growth_rate","inflation_rate","fdi_inflow"]].reset_index(drop=True))
    worst.columns = ["Year","GDP Growth (%)","Inflation (%)","FDI (%)"]
    st.dataframe(worst, use_container_width=True)

st.markdown("---")

# ── Year comparison ────────────────────────────────────────────────────────
section("🔄 Year-on-Year Comparison",
        "Pick any two years for a side-by-side delta across all three indicators.")
yy1, yy2 = st.columns(2)
with yy1:
    y1 = st.selectbox("First Year", sorted(df["year"].unique(), reverse=True), index=1, key="cmp1")
with yy2:
    y2 = st.selectbox("Second Year", sorted(df["year"].unique(), reverse=True), index=0, key="cmp2")
d1 = df[df["year"] == y1].iloc[0]
d2 = df[df["year"] == y2].iloc[0]
cm1, cm2, cm3 = st.columns(3)
with cm1:
    st.metric(f"GDP — {y1} vs {y2}", f"{d1['gdp_growth_rate']:.2f}%",
              f"{d1['gdp_growth_rate']-d2['gdp_growth_rate']:+.2f}%")
with cm2:
    st.metric(f"Inflation — {y1} vs {y2}", f"{d1['inflation_rate']:.2f}%",
              f"{d1['inflation_rate']-d2['inflation_rate']:+.2f}%", delta_color="inverse")
with cm3:
    st.metric(f"FDI — {y1} vs {y2}", f"{d1['fdi_inflow']:.2f}%",
              f"{d1['fdi_inflow']-d2['fdi_inflow']:+.2f}%")

st.markdown("---")
st.download_button("⬇️ Download Filtered Data (CSV)",
                   df_f.to_csv(index=False),
                   file_name=f"india_economy_{start_year}_{end_year}.csv",
                   mime="text/csv")
st.markdown("---")

# ── About section — 3D parallax ───────────────────────────────────────────
components.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
#ab{perspective:900px;padding:10px 0 28px;}
#ai{
    transform-style:preserve-3d;transition:transform .2s ease;
    background:linear-gradient(135deg,rgba(79,195,247,.04),rgba(255,153,51,.05));
    border:1px solid rgba(255,255,255,.07);border-radius:20px;padding:38px 46px;
    cursor:default;position:relative;overflow:hidden;}
#ai::before{
    content:'';position:absolute;inset:0;pointer-events:none;
    background:
        radial-gradient(ellipse at 15% 50%,rgba(255,153,51,.07) 0%,transparent 55%),
        radial-gradient(ellipse at 85% 50%,rgba(79,195,247,.06) 0%,transparent 55%);}
.atag{font-family:Inter,sans-serif;font-size:10px;letter-spacing:3px;color:#FF9933;
    text-transform:uppercase;background:rgba(255,153,51,.1);border:1px solid rgba(255,153,51,.2);
    border-radius:20px;padding:4px 14px;margin-bottom:16px;display:inline-block;}
.ah{font-family:Inter,sans-serif;font-size:21px;font-weight:700;color:white;margin:0 0 14px;
    transform:translateZ(18px);}
.ab2{font-family:Inter,sans-serif;font-size:13.5px;color:#8A9BB0;
    line-height:1.8;max-width:780px;margin:0 0 22px;}
.ab2 b{color:#FF9933;}
.ag{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:14px;margin-top:6px;}
.ac{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.07);
    border-radius:12px;padding:15px;transition:all .2s;}
.ac:hover{background:rgba(255,153,51,.07);border-color:rgba(255,153,51,.22);
    transform:translateY(-2px) translateZ(8px);}
.ai2{font-size:19px;margin-bottom:6px;}
.at{font-family:Inter,sans-serif;font-size:12px;font-weight:600;color:white;margin-bottom:4px;}
.ad{font-family:Inter,sans-serif;font-size:11px;color:#6B7C8E;line-height:1.5;}
</style>
<div id="ab">
  <div id="ai">
    <div class="atag">About this Dashboard</div>
    <h3 class="ah">Built at the intersection of data engineering, machine learning, and economic storytelling.</h3>
    <p class="ab2">
      This dashboard was engineered from scratch as a <b>full end-to-end ETL pipeline</b> — raw API calls
      to the <b>World Bank's open data infrastructure</b>, through Python-driven transformation scripts,
      into a <b>PostgreSQL cloud database</b>, rendered as a live 3D-interactive application accessible
      from any device on Earth.<br><br>
      The concept is simple but ambitious: <b>economic data should not live in spreadsheets</b>.
      It should breathe — react to questions, reveal hidden patterns, and tell the story of a billion
      people through numbers that mean something. Every chart here runs on <b>real World Bank data</b>.
      Every model trained on <b>55 years of truth</b>. The cross-filtering lets you click one year
      anywhere and watch <b>all six charts respond simultaneously</b>.
    </p>
    <div class="ag">
      <div class="ac"><div class="ai2">🔗</div><div class="at">Live ETL Pipeline</div>
        <div class="ad">World Bank API → Python → PostgreSQL → Dashboard. Fully automated daily refresh.</div></div>
      <div class="ac"><div class="ai2">🤖</div><div class="at">ML Models</div>
        <div class="ad">Random Forest, Gradient Boosting, OLS, Granger causality — 7+ models trained.</div></div>
      <div class="ac"><div class="ai2">🌐</div><div class="at">3D Visualisation</div>
        <div class="ad">Plotly Scatter3d and Surface charts — drag, rotate, and explore economic space.</div></div>
      <div class="ac"><div class="ai2">⚡</div><div class="at">Cross-Filtering</div>
        <div class="ad">Click any data point — all charts instantly highlight and drill down on that year.</div></div>
      <div class="ac"><div class="ai2">☁️</div><div class="at">Free Deployment</div>
        <div class="ad">Streamlit Cloud + Neon.tech PostgreSQL. Zero infrastructure cost, globally accessible.</div></div>
      <div class="ac"><div class="ai2">📂</div><div class="at">Open Source</div>
        <div class="ad">Full code on GitHub. Reproducible, extensible, Phase 2 deep learning models coming.</div></div>
    </div>
  </div>
</div>
<script>
const ab=document.getElementById('ab'),ai=document.getElementById('ai');
ab.addEventListener('mousemove',e=>{
    const r=ab.getBoundingClientRect();
    const x=(e.clientX-r.left)/r.width-.5;
    const y=(e.clientY-r.top)/r.height-.5;
    ai.style.transform='rotateY('+x*11+'deg) rotateX('+(-y*7)+'deg)';
});
ab.addEventListener('mouseleave',()=>{ai.style.transform='rotateY(0) rotateX(0)';});
</script>
""", height=560)

st.markdown("""
<div style='text-align:center;color:#374151;font-size:12px;padding:8px 0 18px;'>
  Data: World Bank API &nbsp;·&nbsp; Built with Python · PostgreSQL · Streamlit
</div>""", unsafe_allow_html=True)