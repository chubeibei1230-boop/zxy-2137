import streamlit as st
from auth import init_auth, render_role_selector, has_permission
from data_manager import init_session_data, get_data
from thresholds import init_thresholds, render_threshold_controls
from analytics import identify_risks, compute_overview, compute_ta_load, compute_trends, generate_suggestions
from charts import (
    render_trend_chart,
    render_enrollment_chart,
    render_ta_load_chart,
    render_risk_distribution,
    render_venue_heatmap,
)
from components import render_overview_cards, render_risk_table, render_suggestions, render_filters, render_upload_section
from report import render_export_section

st.set_page_config(
    page_title="运动课程数据分析",
    page_icon="🏃",
    layout="wide",
)

init_auth()
init_session_data()
init_thresholds()

st.title("🏃 运动课程数据分析平台")

render_role_selector()
st.sidebar.divider()

raw_df = get_data()

if has_permission("upload"):
    with st.sidebar.expander("数据管理", expanded=False):
        render_upload_section()

if raw_df.empty:
    st.warning("暂无课程数据。请通过侧栏上传 CSV 文件，或确保 data/courses.csv 存在。")
    st.stop()

filtered_df = render_filters(raw_df)

render_threshold_controls()

risk_df = identify_risks(filtered_df)
overview = compute_overview(filtered_df)
suggestions = generate_suggestions(filtered_df)

render_overview_cards(overview)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["风险分析", "趋势图表", "助教负载", "场馆热力图"])

with tab1:
    st.subheader("风险课程列表")
    render_risk_table(risk_df)
    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        fig_risk = render_risk_distribution(risk_df)
        st.plotly_chart(fig_risk, use_container_width=True)
    with col2:
        st.subheader("分析建议")
        render_suggestions(suggestions)

with tab2:
    trend_df = compute_trends(filtered_df, freq="W")
    col1, col2 = st.columns(2)
    with col1:
        fig_trend = render_trend_chart(trend_df)
        st.plotly_chart(fig_trend, use_container_width=True)
    with col2:
        fig_enroll = render_enrollment_chart(trend_df)
        st.plotly_chart(fig_enroll, use_container_width=True)

with tab3:
    ta_df = compute_ta_load(filtered_df)
    col1, col2 = st.columns([2, 1])
    with col1:
        fig_ta = render_ta_load_chart(ta_df)
        st.plotly_chart(fig_ta, use_container_width=True)
    with col2:
        st.subheader("助教负载明细")
        if not ta_df.empty:
            st.dataframe(ta_df, use_container_width=True, hide_index=True)
        else:
            st.info("暂无数据")

with tab4:
    fig_heatmap = render_venue_heatmap(filtered_df)
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()
render_export_section(filtered_df, risk_df, overview, suggestions)
