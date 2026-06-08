import io
from datetime import datetime
import pandas as pd
import streamlit as st
from analytics import identify_risks, compute_overview, compute_ta_load, generate_suggestions, compute_anomaly_tags, compute_anomaly_overview, compute_anomaly_by_dimension, generate_anomaly_suggestions
from thresholds import get_thresholds


def generate_report_text(df, overview, suggestions):
    thresholds = get_thresholds()
    lines = []
    lines.append("=" * 60)
    lines.append("运动课程数据分析报告")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("一、概览统计")
    lines.append("-" * 40)
    for k, v in overview.items():
        if isinstance(v, float):
            lines.append(f"  {k}：{v:.1%}")
        else:
            lines.append(f"  {k}：{v}")
    lines.append("")
    lines.append("二、阈值参数")
    lines.append("-" * 40)
    lines.append(f"  低签到率阈值：{thresholds['low_checkin_rate']:.0%}")
    lines.append(f"  高退课率阈值：{thresholds['high_drop_rate']:.0%}")
    lines.append(f"  人数超限倍数：{thresholds['over_capacity_ratio']:.1f}x")
    lines.append(f"  助教负载阈值：{int(thresholds['high_ta_load'])} 门课")
    lines.append("")
    lines.append("三、风险课程明细")
    lines.append("-" * 40)
    risk_df = df[df["是否风险"]] if not df.empty else pd.DataFrame()
    if risk_df.empty:
        lines.append("  无风险课程")
    else:
        for _, row in risk_df.iterrows():
            lines.append(
                f"  {row.get('日期', '')} | {row.get('课程名称', '')} | "
                f"{row.get('场馆', '')} | {row.get('助教', '')} | "
                f"签到率 {row.get('签到率', 0):.1%} | {row.get('风险标记', '')}"
            )
    lines.append("")
    lines.append("四、助教负载")
    lines.append("-" * 40)
    ta_df = compute_ta_load(df)
    if ta_df.empty:
        lines.append("  无数据")
    else:
        for _, row in ta_df.iterrows():
            lines.append(
                f"  {row['助教']}：{row['课程数']} 门课 | "
                f"平均签到率 {row['平均签到率']:.1%} | {row['负载标记']}"
            )
    lines.append("")
    lines.append("五、建议")
    lines.append("-" * 40)
    for s in suggestions:
        lines.append(f"  {s}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def export_csv(df):
    if df.empty:
        return None
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)
    return output


def export_report(df, overview, suggestions):
    report_text = generate_report_text(df, overview, suggestions)
    buf = io.BytesIO()
    buf.write(report_text.encode("utf-8-sig"))
    buf.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"report_{timestamp}.txt"
    return buf, filename


def render_export_section(filtered_df, risk_df, overview, suggestions):
    from auth import has_permission
    if not has_permission("export"):
        return

    st.subheader("导出")
    col1, col2 = st.columns(2)

    with col1:
        csv_buf = export_csv(filtered_df)
        if csv_buf is not None:
            st.download_button(
                label="导出筛选数据 (CSV)",
                data=csv_buf,
                file_name=f"courses_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.caption("无数据可导出")

    with col2:
        report_buf, report_name = export_report(risk_df, overview, suggestions)
        st.download_button(
            label="导出分析报告 (TXT)",
            data=report_buf,
            file_name=report_name,
            mime="text/plain",
        )


def generate_anomaly_report_text(df, anomaly_overview, suggestions):
    thresholds = get_thresholds()
    lines = []
    lines.append("=" * 60)
    lines.append("课程异常复盘报告")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    lines.append("一、异常概览")
    lines.append("-" * 40)
    lines.append(f"  总课程数：{anomaly_overview['总课程数']}")
    lines.append(f"  异常课程数：{anomaly_overview['异常课程数']}")
    lines.append(f"  异常课程占比：{anomaly_overview['异常课程占比']:.1%}")
    lines.append(f"  严重课程数：{anomaly_overview['严重课程数']}")
    lines.append(f"  警告课程数：{anomaly_overview['警告课程数']}")
    lines.append(f"  提示课程数：{anomaly_overview['提示课程数']}")
    lines.append("")
    lines.append("二、异常标签分布")
    lines.append("-" * 40)
    tag_dist = anomaly_overview.get("异常标签分布", {})
    if tag_dist:
        for tag, count in sorted(tag_dist.items(), key=lambda x: -x[1]):
            lines.append(f"  {tag}：{count} 次")
    else:
        lines.append("  无异常标签")
    lines.append("")
    lines.append("三、阈值参数")
    lines.append("-" * 40)
    lines.append(f"  低签到率阈值：{thresholds['low_checkin_rate']:.0%}")
    lines.append(f"  高退课率阈值：{thresholds['high_drop_rate']:.0%}")
    lines.append(f"  人数超限倍数：{thresholds['over_capacity_ratio']:.1f}x")
    lines.append(f"  助教负载阈值：{int(thresholds['high_ta_load'])} 门课")
    lines.append("")
    lines.append("四、异常课程明细")
    lines.append("-" * 40)
    if not df.empty:
        anomaly_df = df[df["是否异常"]] if "是否异常" in df.columns else pd.DataFrame()
        if anomaly_df.empty:
            lines.append("  无异常课程")
        else:
            for _, row in anomaly_df.iterrows():
                lines.append(
                    f"  {row.get('日期', '')} | {row.get('课程名称', '')} | "
                    f"{row.get('场馆', '')} | {row.get('助教', '')} | "
                    f"签到率 {row.get('签到率', 0):.1%} | "
                    f"退课率 {row.get('退课率', 0):.1%} | "
                    f"{row.get('异常标签文本', '')} | {row.get('严重程度', '')}"
                )
    else:
        lines.append("  无数据")
    lines.append("")
    lines.append("五、按课程维度汇总")
    lines.append("-" * 40)
    dim_course = compute_anomaly_by_dimension(df, "课程名称") if not df.empty else pd.DataFrame()
    if dim_course.empty:
        lines.append("  无数据")
    else:
        for _, row in dim_course.iterrows():
            lines.append(
                f"  {row['课程名称']}：异常 {int(row['异常次数'])} 次 | "
                f"签到率 {row['平均签到率']:.1%} | {row['异常标签汇总']}"
            )
    lines.append("")
    lines.append("六、按场馆维度汇总")
    lines.append("-" * 40)
    dim_venue = compute_anomaly_by_dimension(df, "场馆") if not df.empty else pd.DataFrame()
    if dim_venue.empty:
        lines.append("  无数据")
    else:
        for _, row in dim_venue.iterrows():
            lines.append(
                f"  {row['场馆']}：异常 {int(row['异常次数'])} 次 | "
                f"签到率 {row['平均签到率']:.1%} | {row['异常标签汇总']}"
            )
    lines.append("")
    lines.append("七、按助教维度汇总")
    lines.append("-" * 40)
    dim_ta = compute_anomaly_by_dimension(df, "助教") if not df.empty else pd.DataFrame()
    if dim_ta.empty:
        lines.append("  无数据")
    else:
        for _, row in dim_ta.iterrows():
            lines.append(
                f"  {row['助教']}：异常 {int(row['异常次数'])} 次 | "
                f"签到率 {row['平均签到率']:.1%} | {row['异常标签汇总']}"
            )
    lines.append("")
    lines.append("八、运营建议")
    lines.append("-" * 40)
    for s in suggestions:
        lines.append(f"  {s}")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def export_anomaly_csv(df):
    if df.empty:
        return None
    anomaly_df = df[df["是否异常"]].copy() if "是否异常" in df.columns else pd.DataFrame()
    if anomaly_df.empty:
        return None
    export_cols = ["日期", "课程名称", "场馆", "助教", "报名人数", "签到人数", "消课人数", "退课人数", "课程容量",
                   "签到率", "消课率", "退课率", "容量利用率", "异常标签文本", "严重程度"]
    existing_cols = [c for c in export_cols if c in anomaly_df.columns]
    output = io.BytesIO()
    anomaly_df[existing_cols].to_csv(output, index=False, encoding="utf-8-sig")
    output.seek(0)
    return output


def export_anomaly_report(df, anomaly_overview, suggestions):
    report_text = generate_anomaly_report_text(df, anomaly_overview, suggestions)
    buf = io.BytesIO()
    buf.write(report_text.encode("utf-8-sig"))
    buf.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"anomaly_review_{timestamp}.txt"
    return buf, filename


def render_anomaly_export_section(filtered_df, anomaly_df, anomaly_overview, suggestions):
    from auth import has_permission
    if not has_permission("export"):
        return

    st.subheader("复盘导出")
    col1, col2 = st.columns(2)

    with col1:
        csv_buf = export_anomaly_csv(anomaly_df)
        if csv_buf is not None:
            st.download_button(
                label="导出异常数据 (CSV)",
                data=csv_buf,
                file_name=f"anomaly_courses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        else:
            st.caption("无异常数据可导出")

    with col2:
        report_buf, report_name = export_anomaly_report(anomaly_df, anomaly_overview, suggestions)
        st.download_button(
            label="导出复盘报告 (TXT)",
            data=report_buf,
            file_name=report_name,
            mime="text/plain",
        )
