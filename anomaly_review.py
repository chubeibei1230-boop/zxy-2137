import streamlit as st
from analytics import (
    compute_anomaly_tags,
    compute_anomaly_overview,
    compute_anomaly_by_dimension,
    compute_anomaly_trends,
    generate_anomaly_suggestions,
)
from charts import (
    render_anomaly_category_chart,
    render_anomaly_trend_chart,
    render_anomaly_dimension_chart,
)
from components import (
    render_anomaly_overview_cards,
    render_anomaly_detail_table,
    render_single_course_review,
    render_anomaly_suggestions,
    render_anomaly_filters,
)
from report import render_anomaly_export_section
from data_manager import get_unique_values


def render_anomaly_review_page(raw_df):
    st.subheader("课程异常复盘")

    st.markdown("快速定位异常课程，集中查看异常概览、原因归类、重点明细、变化趋势及运营建议。")

    filtered_df = render_anomaly_filters(raw_df)

    if filtered_df.empty:
        st.warning("当前筛选条件下无数据，请调整筛选条件。")
        return

    anomaly_df = compute_anomaly_tags(filtered_df)
    anomaly_overview = compute_anomaly_overview(filtered_df)
    suggestions = generate_anomaly_suggestions(filtered_df)

    render_anomaly_overview_cards(anomaly_overview)

    st.divider()

    view_mode = st.radio(
        "观察维度",
        options=["按课程", "按场馆", "按助教"],
        horizontal=True,
        key="anomaly_view_dim",
    )

    dim_map = {"按课程": "课程名称", "按场馆": "场馆", "按助教": "助教"}
    dimension = dim_map[view_mode]

    tab1, tab2, tab3, tab4 = st.tabs(["异常概览与归类", "重点课程明细", "变化趋势", "运营建议"])

    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            fig_cat = render_anomaly_category_chart(anomaly_overview)
            st.plotly_chart(fig_cat, use_container_width=True)
        with col2:
            dim_df = compute_anomaly_by_dimension(filtered_df, dimension)
            fig_dim = render_anomaly_dimension_chart(dim_df, dimension)
            st.plotly_chart(fig_dim, use_container_width=True)

        st.markdown(f"#### {view_mode}异常汇总")
        if not dim_df.empty:
            st.dataframe(dim_df, use_container_width=True, hide_index=True)
        else:
            st.info("当前维度下无异常汇总数据")

    with tab2:
        st.markdown("#### 异常课程明细")
        render_anomaly_detail_table(anomaly_df)

        st.divider()
        st.markdown("#### 单课程复盘")
        anomaly_courses = anomaly_df[anomaly_df["是否异常"]]["课程名称"].unique().tolist() if not anomaly_df.empty else []
        if anomaly_courses:
            selected_course = st.selectbox(
                "选择课程查看复盘",
                options=anomaly_courses,
                key="anomaly_single_course",
            )
            if selected_course:
                render_single_course_review(filtered_df, selected_course)
        else:
            st.info("当前筛选范围内无异常课程，无需单课程复盘。")

    with tab3:
        trend_df = compute_anomaly_trends(filtered_df, freq="W")
        fig_trend = render_anomaly_trend_chart(trend_df)
        st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("#### 趋势数据明细")
        if not trend_df.empty:
            display_trend = trend_df.copy()
            display_trend["周期"] = display_trend["周期"].dt.strftime("%Y-%m-%d")
            st.dataframe(display_trend, use_container_width=True, hide_index=True)
        else:
            st.info("暂无趋势数据")

    with tab4:
        st.markdown("#### 运营建议")
        render_anomaly_suggestions(suggestions)

    st.divider()
    render_anomaly_export_section(filtered_df, anomaly_df, anomaly_overview, suggestions)
