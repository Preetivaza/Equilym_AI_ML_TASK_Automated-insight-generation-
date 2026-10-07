import html
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import engine as E

st.set_page_config(page_title="Auto-Analytics Engine", page_icon="📊", layout="wide")

SEV_COL = {"High": "#dc2626", "Medium": "#f59e0b", "Low": "#eab308"}
SEV_BG = {"High": "#fef2f2", "Medium": "#fffbeb", "Low": "#fefce8"}
TYPE_ICON = {"trend": "📈", "outlier": "🎯", "correlation": "🔗", "threshold_breach": "🚨"}
TYPES = ["trend", "outlier", "correlation", "threshold_breach"]

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; max-width: 1400px;}
.hero {background: linear-gradient(120deg,#4f46e5 0%,#7c3aed 55%,#06b6d4 100%);
       padding: 22px 28px; border-radius: 16px; color: #fff; margin-bottom: 18px;}
.hero h1 {margin:0; font-size: 1.9rem; color:#fff;}
.hero p {margin:4px 0 0 0; opacity:.9;}
.kpi {background:#fff; border-radius:14px; padding:14px 18px; border:1px solid #e5e7eb;
      box-shadow:0 1px 3px rgba(0,0,0,.05); border-top:4px solid var(--c);}
.kpi .v {font-size:2rem; font-weight:700; color:var(--c); line-height:1.1;}
.kpi .l {font-size:.8rem; color:#6b7280; text-transform:uppercase; letter-spacing:.05em;}
.card {background:#fff; border-radius:12px; padding:12px 16px; margin-bottom:10px;
       border:1px solid #e5e7eb; border-left:6px solid var(--c); box-shadow:0 1px 2px rgba(0,0,0,.04);}
.card .top {display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:6px;}
.badge {font-size:.72rem; font-weight:700; padding:2px 10px; border-radius:999px;
        color:var(--c); background:var(--bg);}
.tag {font-size:.72rem; padding:2px 9px; border-radius:999px; background:#eef2ff; color:#4338ca;}
.muted {color:#6b7280; font-size:.78rem;}
.card .txt {color:#1f2937; font-size:.95rem;}
.chip {display:inline-block; font-size:.78rem; background:#f3f4f6; color:#374151;
       padding:2px 9px; border-radius:6px; margin-right:6px; margin-top:6px;}
div[data-testid="stTabs"] button {font-weight:600;}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------ sidebar
st.sidebar.title("⚙️ Control Panel")
src = st.sidebar.radio("Data source", ["Sample dataset", "Upload CSV"], horizontal=True)
if src == "Upload CSV":
    up = st.sidebar.file_uploader("CSV with month, district + numeric indicators", type="csv")
    df = E.load_data(up) if up else E.load_data("data/district_data.csv")
    if not up:
        st.sidebar.caption("No file yet — using sample data.")
else:
    df = E.load_data("data/district_data.csv")
inds = E.get_indicators(df)
all_d, all_m = sorted(df.district.unique()), sorted(df.month.unique())

with st.sidebar.expander("📏 Detection thresholds", expanded=True):
    trend_thr = st.slider("Trend: |% change| ≥", 1, 50, 10, help="Default 10%")
    method = st.radio("Outlier method", ["IQR", "Z-score"], horizontal=True)
    iqr_k = st.slider("IQR multiplier (k)", 0.5, 3.0, 1.5, 0.1)
    z_thr = st.slider("Z-score threshold", 1.0, 4.0, 3.0, 0.1)
    corr_thr = st.slider("Correlation: |r| ≥", 0.30, 0.99, 0.70, 0.01)
    floor = st.slider("Breach floor (% indicators)", 0, 100, 70)
    ceiling = st.slider("Breach ceiling (count indicators)", 1, 100, 20)

with st.sidebar.expander("🔎 Filters (live)", expanded=True):
    f_dist = st.multiselect("District", all_d, default=all_d)
    f_month = st.multiselect("Month", all_m, default=all_m)
    f_ind = st.multiselect("Indicator", inds, default=inds)
    f_sev = st.multiselect("Severity", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    f_type = st.multiselect("Insight type", TYPES, default=TYPES)

# ------------------------------------------------------------------ compute
insights, corr = E.generate_insights(df, trend_thr, method, iqr_k, z_thr, corr_thr, floor, ceiling)


def keep(r):
    if r.type == "correlation":
        return all(p in f_ind for p in r.indicator.split(":"))
    return r.entity in f_dist and r.period in f_month and r.indicator in f_ind


view = insights[insights.apply(keep, axis=1)] if len(insights) else insights
view = view[view.severity.isin(f_sev) & view.type.isin(f_type)].reset_index(drop=True)
fdf = df[df.district.isin(f_dist) & df.month.isin(f_month)]

st.sidebar.markdown("---")
st.sidebar.download_button("⬇ Insights CSV", view.to_csv(index=False), "insights.csv", use_container_width=True)
st.sidebar.download_button("⬇ Insights JSON", view.to_json(orient="records", indent=2), "insights.json", use_container_width=True)
st.sidebar.download_button("⬇ Correlation matrix CSV", corr.to_csv(), "correlation_matrix.csv", use_container_width=True)

# ------------------------------------------------------------------ header + KPIs
st.markdown(f"""<div class="hero"><h1>📊 Auto-Analytics Engine</h1>
<p>Automated insight generation — trends, outliers, correlations and threshold breaches across
{df.district.nunique()} districts · {df.month.nunique()} months · {len(inds)} indicators</p></div>""",
            unsafe_allow_html=True)

kpis = [("Total insights", len(view), "#4f46e5"),
        ("High", int((view.severity == "High").sum()), SEV_COL["High"]),
        ("Medium", int((view.severity == "Medium").sum()), SEV_COL["Medium"]),
        ("Low", int((view.severity == "Low").sum()), SEV_COL["Low"]),
        ("Districts in view", len(f_dist), "#0891b2")]
for col, (label, val, c) in zip(st.columns(5), kpis):
    col.markdown(f'<div class="kpi" style="--c:{c}"><div class="v">{val}</div><div class="l">{label}</div></div>',
                 unsafe_allow_html=True)
st.write("")


def style(fig, h=340):
    fig.update_layout(template="plotly_white", height=h, margin=dict(l=10, r=10, t=40, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.2))
    return fig


def chip(r):
    if r.type == "trend":
        return f'<span class="chip">{r.metric:g} (prev {r.prev_value:g})</span><span class="chip">Δ {r.change:+.1f}%</span>'
    if r.type == "outlier":
        return f'<span class="chip">value {r.metric:g}</span><span class="chip">z = {r.change:+.1f}σ</span>'
    if r.type == "correlation":
        return f'<span class="chip">r = {r.metric:+.2f}</span>'
    return f'<span class="chip">value {r.metric:g}</span><span class="chip">gap {r.change:+.1f}</span>'


tab_ins, tab_tr, tab_out, tab_cor, tab_data = st.tabs(
    ["📋 Insights", "📈 Trends", "🎯 Outliers", "🔗 Correlation", "🧪 Data & Validation"])

# ------------------------------------------------------------------ Insights tab
with tab_ins:
    c1, c2, c3 = st.columns([1, 1, 1.3])
    sev_counts = view.severity.value_counts().reindex(["High", "Medium", "Low"], fill_value=0).reset_index()
    sev_counts.columns = ["severity", "count"]
    with c1:
        fig = px.bar(sev_counts, x="severity", y="count", color="severity", text="count",
                     color_discrete_map=SEV_COL, title="Severity counts")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style(fig), width="stretch")
    with c2:
        tc = view.type.value_counts().reset_index()
        tc.columns = ["type", "count"]
        fig = px.pie(tc, names="type", values="count", hole=.55, title="Insights by type",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(style(fig), width="stretch")
    with c3:
        if len(fdf) and f_ind:
            ind0 = f_ind[0]
            fig = px.line(fdf.sort_values("month"), x="month", y=ind0, color="district", markers=True,
                          title=f"Per-district trend · {ind0}")
            st.plotly_chart(style(fig), width="stretch")

    st.subheader("Generated insights")
    q = st.text_input("Search insights", placeholder="e.g. Mehsana, dropped, anc_coverage…",
                      label_visibility="collapsed")
    shown = view
    if q:
        shown = view[view.apply(lambda r: q.lower() in " ".join(map(str, r.values)).lower(), axis=1)]
    if shown.empty:
        st.info("No insights match the current filters / thresholds.")
    for _, r in shown.iterrows():
        c, bg = SEV_COL[r.severity], SEV_BG[r.severity]
        st.markdown(f"""<div class="card" style="--c:{c};--bg:{bg}">
<div class="top"><span class="badge">{r.severity.upper()}</span>
<span class="tag">{TYPE_ICON[r.type]} {r.type}</span>
<b>{html.escape(str(r.entity))}</b><span class="muted">· {html.escape(str(r.indicator))} · {r.period} · {r.insight_id}</span></div>
<div class="txt">{html.escape(r.explanation)}</div>{chip(r)}</div>""", unsafe_allow_html=True)
    with st.expander("View as table"):
        st.dataframe(view, width="stretch", hide_index=True)

# ------------------------------------------------------------------ Trends tab
with tab_tr:
    st.caption(f"pct_change = (current − previous) / previous × 100 · flagged when |pct_change| ≥ {trend_thr}%")
    ind = st.selectbox("Indicator", f_ind or inds, key="tr_ind")
    t = E.detect_trends(df, [ind], trend_thr)
    t = t[t.district.isin(f_dist) & t.month.isin(f_month)] if len(t) else t
    if t.empty:
        st.info("Need at least two months per district to compute trends.")
    else:
        t = t.assign(status=np.where(t.is_significant, "Significant", "Within threshold"))
        fig = px.bar(t, x="district", y="pchg", color="status", facet_col="month", text="pchg",
                     color_discrete_map={"Significant": "#dc2626", "Within threshold": "#94a3b8"},
                     labels={"pchg": "% change"}, title=f"% change vs previous month · {ind}")
        fig.add_hline(y=trend_thr, line_dash="dash", line_color="#16a34a")
        fig.add_hline(y=-trend_thr, line_dash="dash", line_color="#16a34a")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        st.plotly_chart(style(fig, 400), width="stretch")
        st.markdown("**Flagged trends**")
        st.dataframe(t[t.is_significant][["district", "indicator", "prev_month", "month", "prev_value", "value", "pchg"]]
                     .rename(columns={"pchg": "pct_change", "month": "current_month"}),
                     width="stretch", hide_index=True)
    if len(fdf):
        fig = px.line(fdf.sort_values("month"), x="month", y=ind, color="district", markers=True,
                      title=f"Per-district line chart · {ind}")
        st.plotly_chart(style(fig, 360), width="stretch")

# ------------------------------------------------------------------ Outliers tab
with tab_out:
    st.caption(f"Method: **{method}** · " + (f"k = {iqr_k}" if method == "IQR" else f"|z| ≥ {z_thr}") +
               " · computed across all districts and months for each indicator")
    ind = st.selectbox("Indicator", f_ind or inds, key="out_ind")
    o = E.detect_outliers(df, [ind], method, iqr_k, z_thr)
    keys = set(zip(o.district, o.month)) if len(o) else set()
    plot = fdf.assign(status=["Outlier" if (d, m) in keys else "Normal" for d, m in zip(fdf.district, fdf.month)])
    if len(plot):
        fig = px.strip(plot, x="month", y=ind, color="status", hover_name="district",
                       color_discrete_map={"Outlier": "#dc2626", "Normal": "#6366f1"},
                       title=f"Distribution · {ind}")
        fig.update_traces(marker=dict(size=14, line=dict(width=1, color="white")))
        fig.add_hline(y=df[ind].mean(), line_dash="dot", annotation_text=f"mean {df[ind].mean():.1f}")
        st.plotly_chart(style(fig, 400), width="stretch")
    if o.empty:
        st.success("No outliers detected for this indicator at the current threshold.")
    else:
        st.dataframe(o[["district", "indicator", "month", "value", "mean", "z"]], width="stretch", hide_index=True)

# ------------------------------------------------------------------ Correlation tab
with tab_cor:
    st.warning("⚠ **Limitation:** with only 2 months × 6 districts (12 rows) Pearson correlations are fragile. "
               "Recommended: ≥ 10 districts and ≥ 3 months. Treat results as indicative, not conclusive.")
    cols = [i for i in f_ind if i in inds]
    if len(fdf) >= 3 and len(cols) >= 2:
        cm = E.correlation_matrix(fdf, cols)
        fig = px.imshow(cm, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
                        title="Pearson correlation heatmap")
        a, b = st.columns([1.2, 1])
        with a:
            st.plotly_chart(style(fig, 420), width="stretch")
        pairs = E.flag_correlations(cm, corr_thr)
        with b:
            st.markdown(f"**Pairs with |r| ≥ {corr_thr:.2f}**")
            if not pairs:
                st.info("No pairs exceed the threshold.")
            for x, y, r in pairs:
                st.markdown(f"- `{x}` ↔ `{y}` : **r = {r:+.2f}**")
        if pairs:
            sel = st.selectbox("Inspect pair", [f"{x} vs {y}" for x, y, _ in pairs])
            x, y = sel.split(" vs ")
            fig = px.scatter(fdf, x=x, y=y, color="district", symbol="month", hover_data=["month"],
                             title=f"{x} vs {y}")
            fig.update_traces(marker=dict(size=13))
            k, c0 = np.polyfit(fdf[x], fdf[y], 1)[0], np.polyfit(fdf[x], fdf[y], 1)[1]
            xs = np.array([fdf[x].min(), fdf[x].max()])
            fig.add_trace(go.Scatter(x=xs, y=k * xs + c0, mode="lines", name="fit",
                                     line=dict(color="#6b7280", dash="dash")))
            st.plotly_chart(style(fig, 380), width="stretch")
        with st.expander("Correlation matrix (CSV format)"):
            st.dataframe(cm, width="stretch")
    else:
        st.info("Select at least 2 indicators and enough rows to compute correlations.")

# ------------------------------------------------------------------ Data tab
with tab_data:
    rep = E.validation_report(df)
    a, b = st.columns(2)
    with a:
        st.markdown("**head()**")
        st.dataframe(rep["head"], width="stretch", hide_index=True)
        st.markdown("**Missing values per column**")
        st.dataframe(rep["missing"], width="stretch")
    with b:
        st.markdown("**info()**")
        st.code(rep["info"])
    st.markdown("**Filtered dataset**")
    st.dataframe(fdf, width="stretch", hide_index=True)
    print(rep["head"]); print(rep["info"]); print(rep["missing"])
