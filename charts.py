import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from thresholds import get_thresholds


CHART_TEMPLATE = "plotly_white"


def render_trend_chart(trend_df):
    if trend_df.empty:
        return go.Figure()
    thresholds = get_thresholds()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=trend_df["周期"],
        y=trend_df["平均签到率"],
        mode="lines+markers",
        name="平均签到率(%)",
        line=dict(color="#2563eb", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["周期"],
        y=trend_df["平均消课率"],
        mode="lines+markers",
        name="平均消课率(%)",
        line=dict(color="#16a34a", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["周期"],
        y=trend_df["平均退课率"],
        mode="lines+markers",
        name="平均退课率(%)",
        line=dict(color="#dc2626", width=2),
    ))
    fig.add_hline(
        y=thresholds["low_checkin_rate"] * 100,
        line_dash="dash",
        line_color="#2563eb",
        annotation_text=f"低签到率阈值 {thresholds['low_checkin_rate']:.0%}",
    )
    fig.add_hline(
        y=thresholds["high_drop_rate"] * 100,
        line_dash="dash",
        line_color="#dc2626",
        annotation_text=f"高退课率阈值 {thresholds['high_drop_rate']:.0%}",
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="签到率 / 消课率 / 退课率 周趋势",
        xaxis_title="周期",
        yaxis_title="百分比(%)",
        hovermode="x unified",
        height=400,
    )
    return fig


def render_enrollment_chart(trend_df):
    if trend_df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=trend_df["周期"],
        y=trend_df["总报名人数"],
        name="总报名人数",
        marker_color="#8b5cf6",
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["周期"],
        y=trend_df["课程数"],
        mode="lines+markers",
        name="课程数",
        yaxis="y2",
        line=dict(color="#f59e0b", width=2),
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="报名人数与课程数趋势",
        xaxis_title="周期",
        yaxis_title="报名人数",
        yaxis2=dict(title="课程数", overlaying="y", side="right"),
        hovermode="x unified",
        height=400,
    )
    return fig


def render_ta_load_chart(ta_df):
    if ta_df.empty:
        return go.Figure()
    thresholds = get_thresholds()
    colors = ta_df["负载标记"].map({"正常": "#16a34a", "负载过高": "#dc2626"})
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=ta_df["助教"],
        y=ta_df["课程数"],
        marker_color=colors,
        name="课程数",
    ))
    fig.add_hline(
        y=thresholds["high_ta_load"],
        line_dash="dash",
        line_color="#dc2626",
        annotation_text=f"负载阈值 {int(thresholds['high_ta_load'])}",
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="助教课程负载分布",
        xaxis_title="助教",
        yaxis_title="课程数",
        height=400,
    )
    return fig


def render_risk_distribution(df):
    if df.empty:
        return go.Figure()
    risk_counts = df["风险标记"].value_counts()
    fig = go.Figure(data=[go.Pie(
        labels=risk_counts.index,
        values=risk_counts.values,
        hole=0.4,
        marker=dict(
            line=dict(color="white", width=2),
        ),
    )])
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="风险分布",
        height=400,
    )
    return fig


def render_venue_heatmap(df):
    if df.empty:
        return go.Figure()
    from analytics import compute_metrics
    df = compute_metrics(df)
    pivot = df.pivot_table(
        values="签到率",
        index="场馆",
        columns=df["日期"].dt.date,
        aggfunc="mean",
    )
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[str(c) for c in pivot.columns],
        y=pivot.index.tolist(),
        colorscale="RdYlGn",
        zmin=0,
        zmax=1,
        text=[[f"{v:.1%}" if not pd.isna(v) else "" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        colorbar=dict(title="签到率"),
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="场馆签到率热力图",
        xaxis_title="日期",
        yaxis_title="场馆",
        height=max(300, len(pivot.index) * 40 + 100),
    )
    return fig
