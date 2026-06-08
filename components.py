import streamlit as st
import pandas as pd
from data_manager import get_data, filter_data, get_unique_values


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
