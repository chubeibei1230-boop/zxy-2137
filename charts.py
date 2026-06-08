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


def render_anomaly_category_chart(anomaly_overview):
    tag_dist = anomaly_overview.get("异常标签分布", {})
    if not tag_dist:
        return go.Figure()
    labels = list(tag_dist.keys())
    values = list(tag_dist.values())
    colors = {"低签到率": "#dc2626", "高退课率": "#f59e0b", "人数超限": "#8b5cf6", "低消课率": "#2563eb", "助教负载异常": "#16a34a"}
    marker_colors = [colors.get(l, "#6b7280") for l in labels]
    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=marker_colors,
        text=values,
        textposition="outside",
    )])
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="异常原因归类",
        xaxis_title="异常类型",
        yaxis_title="涉及课时数",
        height=380,
    )
    return fig


def render_anomaly_trend_chart(trend_df):
    if trend_df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=trend_df["周期"],
        y=trend_df["课程数"],
        name="总课程数",
        marker_color="#93c5fd",
    ))
    fig.add_trace(go.Bar(
        x=trend_df["周期"],
        y=trend_df["异常课程数"],
        name="异常课程数",
        marker_color="#fca5a5",
    ))
    fig.add_trace(go.Scatter(
        x=trend_df["周期"],
        y=trend_df["异常率"],
        mode="lines+markers",
        name="异常率(%)",
        yaxis="y2",
        line=dict(color="#dc2626", width=2),
    ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="异常趋势变化",
        xaxis_title="周期",
        yaxis_title="课程数",
        yaxis2=dict(title="异常率(%)", overlaying="y", side="right"),
        barmode="overlay",
        hovermode="x unified",
        height=380,
    )
    return fig


def render_anomaly_dimension_chart(dim_df, dimension="课程名称"):
    if dim_df.empty:
        return go.Figure()
    colors_map = {"课程名称": "#2563eb", "场馆": "#16a34a", "助教": "#f59e0b"}
    fig = go.Figure(data=[go.Bar(
        x=dim_df[dimension],
        y=dim_df["异常次数"],
        marker_color=colors_map.get(dimension, "#2563eb"),
        text=dim_df["异常次数"],
        textposition="outside",
    )])
    fig.update_layout(
        template=CHART_TEMPLATE,
        title=f"按{dimension}异常分布",
        xaxis_title=dimension,
        yaxis_title="异常次数",
        height=380,
    )
    return fig


def render_single_course_trend_chart(course_df):
    if course_df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=course_df["日期"],
        y=(course_df["签到率"] * 100).round(1),
        mode="lines+markers",
        name="签到率(%)",
        line=dict(color="#2563eb", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=course_df["日期"],
        y=(course_df["退课率"] * 100).round(1),
        mode="lines+markers",
        name="退课率(%)",
        line=dict(color="#dc2626", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=course_df["日期"],
        y=(course_df["消课率"] * 100).round(1),
        mode="lines+markers",
        name="消课率(%)",
        line=dict(color="#16a34a", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=course_df["日期"],
        y=(course_df["容量利用率"] * 100).round(1),
        mode="lines+markers",
        name="容量利用率(%)",
        line=dict(color="#8b5cf6", width=2, dash="dot"),
    ))
    anomaly_df = course_df[course_df["是否异常"]]
    if not anomaly_df.empty:
        fig.add_trace(go.Scatter(
            x=anomaly_df["日期"],
            y=[100] * len(anomaly_df),
            mode="markers",
            name="异常课时",
            marker=dict(color="#dc2626", size=10, symbol="x", line=dict(width=2)),
            showlegend=True,
        ))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="课程指标变化趋势",
        xaxis_title="日期",
        yaxis_title="百分比(%)",
        hovermode="x unified",
        height=400,
    )
    return fig
