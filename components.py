import streamlit as st
import pandas as pd
from data_manager import get_data, filter_data, get_unique_values
from analytics import compute_anomaly_tags, compute_single_course_review


def render_overview_cards(overview):
    cols = st.columns(6)
    items = [
        ("总课程数", overview["总课程数"], "📚"),
        ("总报名人数", overview["总报名人数"], "👥"),
        ("平均签到率", f"{overview['平均签到率']:.1%}", "✅"),
        ("平均消课率", f"{overview['平均消课率']:.1%}", "📝"),
        ("风险课程数", overview["风险课程数"], "⚠️"),
        ("风险占比", f"{overview['风险课程占比']:.1%}", "📊"),
    ]
    for col, (label, value, icon) in zip(cols, items):
        col.metric(label=f"{icon} {label}", value=value)


def render_risk_table(df):
    if df.empty:
        st.info("暂无数据")
        return
    risk_df = df[df["是否风险"]].copy()
    if risk_df.empty:
        st.success("当前阈值下无风险课程 🎉")
        return
    display_cols = ["日期", "课程名称", "场馆", "助教", "报名人数", "签到率", "消课率", "退课率", "容量利用率", "风险标记"]
    existing_cols = [c for c in display_cols if c in risk_df.columns]
    display_df = risk_df[existing_cols].copy()
    if "日期" in display_df.columns:
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
    for col in ["签到率", "消课率", "退课率", "容量利用率"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1%}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_suggestions(suggestions):
    for s in suggestions:
        if s.startswith("⚠️"):
            st.warning(s)
        elif s.startswith("✅"):
            st.success(s)
        else:
            st.info(s)


def render_filters(df):
    if df.empty:
        return df
    with st.expander("筛选条件", expanded=False):
        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        courses = get_unique_values(df, "课程名称")
        with col1:
            selected_courses = st.multiselect("课程名称", options=courses, default=[])

        with col2:
            if "日期" in df.columns and not df["日期"].isna().all():
                min_date = df["日期"].min().date()
                max_date = df["日期"].max().date()
                date_range = st.date_input(
                    "日期范围",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                )
            else:
                date_range = None

        venues = get_unique_values(df, "场馆")
        with col3:
            selected_venues = st.multiselect("场馆", options=venues, default=[])

        assistants = get_unique_values(df, "助教")
        with col4:
            selected_assistants = st.multiselect("助教", options=assistants, default=[])

    return filter_data(
        df,
        courses=selected_courses if selected_courses else None,
        date_range=date_range if date_range else None,
        venues=selected_venues if selected_venues else None,
        assistants=selected_assistants if selected_assistants else None,
    )


def render_upload_section():
    st.subheader("上传课程记录")
    st.caption("CSV 需包含列：日期、课程名称、场馆、助教、报名人数、签到人数、消课人数、退课人数、课程容量")
    uploaded = st.file_uploader("选择 CSV 文件", type=["csv"], key="csv_upload")
    if uploaded is not None:
        try:
            from data_manager import append_data, REQUIRED_COLUMNS, set_data
            import io
            new_df = pd.read_csv(uploaded, encoding="utf-8-sig")
            missing = [c for c in REQUIRED_COLUMNS if c not in new_df.columns]
            if missing:
                st.error(f"缺少必要列：{', '.join(missing)}")
            else:
                combined = append_data(new_df)
                set_data(combined)
                st.success(f"成功导入 {len(new_df)} 条记录！")
                st.rerun()
        except Exception as e:
            st.error(f"导入失败：{e}")


def render_anomaly_overview_cards(overview):
    cols = st.columns(5)
    items = [
        ("总课程数", overview["总课程数"], "📚"),
        ("异常课程数", overview["异常课程数"], "🚨"),
        ("异常占比", f"{overview['异常课程占比']:.1%}", "📊"),
        ("严重", overview["严重课程数"], "🔴"),
        ("警告", overview["警告课程数"], "🟡"),
    ]
    for col, (label, value, icon) in zip(cols, items):
        col.metric(label=f"{icon} {label}", value=value)


def render_anomaly_detail_table(df):
    if df.empty:
        st.info("暂无异常课程数据")
        return
    anomaly_df = df[df["是否异常"]].copy()
    if anomaly_df.empty:
        st.success("当前筛选范围内无异常课程 🎉")
        return
    display_cols = ["日期", "课程名称", "场馆", "助教", "报名人数", "签到率", "消课率", "退课率", "容量利用率", "异常标签文本", "严重程度"]
    existing_cols = [c for c in display_cols if c in anomaly_df.columns]
    display_df = anomaly_df[existing_cols].sort_values(["严重程度", "日期"], ascending=[True, False]).copy()
    if "日期" in display_df.columns:
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
    for col in ["签到率", "消课率", "退课率", "容量利用率"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1%}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_single_course_review(df, course_name):
    review = compute_single_course_review(df, course_name)
    if review is None:
        st.warning(f"未找到课程「{course_name}」的数据")
        return
    st.markdown(f"### 📋 {course_name} 复盘报告")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总课时数", review["总课时数"])
    col2.metric("异常课时数", review["异常课时数"])
    col3.metric("异常课时占比", f"{review['异常课时占比']:.1%}")
    col4.metric("平均签到率", f"{review['平均签到率']:.1%}")

    col1, col2, col3 = st.columns(3)
    col1.metric("平均退课率", f"{review['平均退课率']:.1%}")
    col2.metric("平均消课率", f"{review['平均消课率']:.1%}")
    col3.metric("平均容量利用率", f"{review['平均容量利用率']:.1%}")

    st.divider()
    st.markdown("#### 主要异常标签")
    if review["主要异常标签"]:
        for tag, count in review["主要异常标签"]:
            st.markdown(f"- **{tag}**：出现 {count} 次")
    else:
        st.info("无异常标签")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 关联场馆")
        for v in review["关联场馆"]:
            st.markdown(f"- {v}")
        st.caption(f"场馆整体异常率：{review['场馆异常率']:.1%}（整体 {review['整体异常率']:.1%}）")

    with col2:
        st.markdown("#### 关联助教")
        for t in review["关联助教"]:
            st.markdown(f"- {t}")
        st.caption(f"助教整体异常率：{review['助教异常率']:.1%}（整体 {review['整体异常率']:.1%}）")

    st.divider()
    st.markdown("#### 结论")
    for c in review["结论"]:
        st.markdown(f"- {c}")

    st.divider()
    st.markdown("#### 指标变化趋势")
    course_detail = review["课程明细"]
    if not course_detail.empty:
        from charts import render_single_course_trend_chart
        fig = render_single_course_trend_chart(course_detail)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("#### 课程逐课时明细")
    detail_df = course_detail.copy()
    display_cols = ["日期", "场馆", "助教", "报名人数", "签到率", "消课率", "退课率", "容量利用率", "异常标签文本", "严重程度"]
    existing_cols = [c for c in display_cols if c in detail_df.columns]
    display_df = detail_df[existing_cols].copy()
    if "日期" in display_df.columns:
        display_df["日期"] = display_df["日期"].dt.strftime("%Y-%m-%d")
    for col in ["签到率", "消课率", "退课率", "容量利用率"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.1%}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_anomaly_suggestions(suggestions):
    for s in suggestions:
        if s.startswith("⚠️"):
            st.warning(s)
        elif s.startswith("✅"):
            st.success(s)
        elif s.startswith("💡"):
            st.info(s)
        else:
            st.info(s)


def render_anomaly_filters(df):
    if df.empty:
        return df
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    courses = get_unique_values(df, "课程名称")
    with col1:
        selected_courses = st.multiselect("课程名称", options=courses, default=[], key="anomaly_course")

    with col2:
        if "日期" in df.columns and not df["日期"].isna().all():
            min_date = df["日期"].min().date()
            max_date = df["日期"].max().date()
            date_range = st.date_input(
                "日期范围",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="anomaly_date",
            )
        else:
            date_range = None

    venues = get_unique_values(df, "场馆")
    with col3:
        selected_venues = st.multiselect("场馆", options=venues, default=[], key="anomaly_venue")

    assistants = get_unique_values(df, "助教")
    with col4:
        selected_assistants = st.multiselect("助教", options=assistants, default=[], key="anomaly_ta")

    severity_filter = st.multiselect(
        "严重程度",
        options=["严重", "警告", "提示"],
        default=[],
        key="anomaly_severity",
    )

    filtered = filter_data(
        df,
        courses=selected_courses if selected_courses else None,
        date_range=date_range if date_range else None,
        venues=selected_venues if selected_venues else None,
        assistants=selected_assistants if selected_assistants else None,
    )
    if severity_filter:
        filtered = compute_anomaly_tags(filtered)
        filtered = filtered[filtered["严重程度"].isin(severity_filter)]
    return filtered
