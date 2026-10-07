"""Auto-Analytics Engine: general-purpose, no hardcoded narratives.
All numbers in insights come from the data; severity is derived from the
configurable thresholds (ratio = observed magnitude / threshold)."""
import io
import numpy as np
import pandas as pd

ID_COLS = ("month", "district")
COUNT_HINTS = ("case", "count", "num", "total")   # name hints -> raw-count indicator


# ---------- Part A: load & validate ----------
def load_data(source):
    df = pd.read_csv(source)
    df["month"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m")
    return df


def get_indicators(df):
    return [c for c in df.select_dtypes("number").columns if c not in ID_COLS]


def validation_report(df):
    buf = io.StringIO()
    df.info(buf=buf)
    return {"head": df.head(), "info": buf.getvalue(),
            "missing": df.isna().sum().rename("missing_count").to_frame()}


def is_count(ind):
    return any(h in ind.lower() for h in COUNT_HINTS)


# ---------- severity (data/threshold driven) ----------
def severity_from_ratio(ratio):
    """ratio = observed magnitude / configured threshold (>=1 means breach)."""
    if ratio >= 1.5:
        return "High"
    if ratio >= 1.2:
        return "Medium"
    return "Low"


# ---------- Part B: trends ----------
def detect_trends(df, indicators, threshold=10.0):
    rows = []
    for ind in indicators:
        for dist, g in df.sort_values("month").groupby("district"):
            g = g.reset_index(drop=True)
            for i in range(1, len(g)):
                prev, cur = g.loc[i - 1, ind], g.loc[i, ind]
                if pd.isna(prev) or pd.isna(cur) or prev == 0:
                    continue
                pct = (cur - prev) / prev * 100
                rows.append(dict(district=dist, indicator=ind, month=g.loc[i, "month"],
                                 prev_month=g.loc[i - 1, "month"], prev_value=prev,
                                 value=cur, pchg=round(pct, 1),
                                 is_significant=abs(pct) >= threshold))
    return pd.DataFrame(rows)


# ---------- Part C: outliers ----------
def detect_outliers(df, indicators, method="IQR", k=1.5, z_thr=3.0):
    rows = []
    for ind in indicators:
        s = df[ind].dropna()
        mean, std = s.mean(), s.std(ddof=0)
        med = s.median()
        q1, q3 = s.quantile(.25), s.quantile(.75)
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        for _, r in df.iterrows():
            v = r[ind]
            if pd.isna(v):
                continue
            z = (v - mean) / std if std else 0.0
            if method == "IQR":
                if v > hi:
                    ratio = (v - med) / (hi - med)
                elif v < lo:
                    ratio = (med - v) / (med - lo)
                else:
                    continue
            else:
                if abs(z) < z_thr:
                    continue
                ratio = abs(z) / z_thr
            rows.append(dict(district=r["district"], indicator=ind, month=r["month"],
                             value=v, mean=round(mean, 1), z=round(z, 1),
                             direction="above" if v > mean else "below",
                             ratio=ratio, method=method))
    return pd.DataFrame(rows)


# ---------- Part D: correlations ----------
def correlation_matrix(df, indicators):
    return df[indicators].corr()


def flag_correlations(corr, thr=0.70):
    out = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = corr.loc[a, b]
            if pd.notna(r) and abs(r) >= thr:
                out.append((a, b, float(r)))
    return out


# ---------- threshold breaches ----------
def detect_breaches(df, indicators, floor=70.0, ceiling=20.0):
    """floor applies to %-type indicators, ceiling to raw-count indicators."""
    rows = []
    for ind in indicators:
        for _, r in df.iterrows():
            v = r[ind]
            if pd.isna(v):
                continue
            if is_count(ind) and v >= ceiling:
                rows.append(dict(district=r["district"], indicator=ind, month=r["month"],
                                 value=v, limit=ceiling, kind="above", ratio=v / ceiling))
            elif not is_count(ind) and v < floor and v > 0:
                rows.append(dict(district=r["district"], indicator=ind, month=r["month"],
                                 value=v, limit=floor, kind="below", ratio=floor / v))
    return pd.DataFrame(rows)


# ---------- Part E: insight generation ----------
def generate_insights(df, trend_thr=10.0, out_method="IQR", iqr_k=1.5, z_thr=3.0,
                      corr_thr=0.70, floor=70.0, ceiling=20.0):
    inds = get_indicators(df)
    rows = []

    t = detect_trends(df, inds, trend_thr)
    for _, r in t[t.is_significant].iterrows() if len(t) else []:
        verb = "rose" if r.pchg > 0 else "dropped"
        rows.append(dict(
            type="trend", indicator=r.indicator, entity=r.district, period=r.month,
            metric=r.value, prev_value=r.prev_value, change=r.pchg,
            severity=severity_from_ratio(abs(r.pchg) / trend_thr),
            explanation=(f"{r.indicator} in {r.district} {verb} by {abs(r.pchg):.1f}% "
                         f"compared to the previous period ({r.prev_month}), exceeding the "
                         f"{trend_thr:g}% significant-change threshold.")))

    o = detect_outliers(df, inds, out_method, iqr_k, z_thr)
    for _, r in o.iterrows():
        rows.append(dict(
            type="outlier", indicator=r.indicator, entity=r.district, period=r.month,
            metric=r.value, prev_value=np.nan, change=r.z,
            severity=severity_from_ratio(r.ratio),
            explanation=(f"{r.district}'s {r.indicator} of {r.value:g} is {abs(r.z):.1f}σ "
                         f"{r.direction} the overall mean ({r['mean']:g}); flagged by "
                         f"{r.method} rule, review recommended.")))

    b = detect_breaches(df, inds, floor, ceiling)
    for _, r in b.iterrows():
        word = "at/above the maximum" if r.kind == "above" else "below the minimum"
        rows.append(dict(
            type="threshold_breach", indicator=r.indicator, entity=r.district, period=r.month,
            metric=r.value, prev_value=np.nan, change=round(r.value - r.limit, 1),
            severity=severity_from_ratio(r.ratio),
            explanation=(f"{r.district}'s {r.indicator} of {r.value:g} is {word} "
                         f"acceptable limit of {r.limit:g}.")))

    corr = correlation_matrix(df, inds)
    pmin, pmax = df.month.min(), df.month.max()
    for a, c, r in flag_correlations(corr, corr_thr):
        rows.append(dict(
            type="correlation", indicator=f"{a}:{c}", entity="ALL", period=f"{pmin}..{pmax}",
            metric=round(r, 2), prev_value=np.nan, change=round(r, 2),
            severity=severity_from_ratio(abs(r) / corr_thr),
            explanation=(f"{a} and {c} show a {'negative' if r < 0 else 'positive'} correlation "
                         f"(r={r:.2f}) across {len(df)} observations; interpret cautiously "
                         f"(small sample).")))

    ins = pd.DataFrame(rows, columns=["type", "indicator", "entity", "period", "metric",
                                      "prev_value", "change", "severity", "explanation"])
    order = {"High": 0, "Medium": 1, "Low": 2}
    ins = ins.sort_values("severity", key=lambda s: s.map(order), kind="stable").reset_index(drop=True)
    ins.insert(0, "insight_id", [f"INS-{i+1:04d}" for i in range(len(ins))])
    return ins, corr
