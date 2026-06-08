import streamlit as st
from auth import has_permission

DEFAULT_THRESHOLDS = {
    "low_checkin_rate": 0.60,
    "high_drop_rate": 0.15,
    "over_capacity_ratio": 1.20,
    "high_ta_load": 6,
    "low_completion_rate": 0.40,
}


def init_thresholds():
    if "thresholds" not in st.session_state:
        st.session_state.thresholds = dict(DEFAULT_THRESHOLDS)


def get_thresholds():
    return st.session_state.get("thresholds", dict(DEFAULT_THRESHOLDS))


def get_threshold(key):
    return st.session_state.thresholds.get(key, DEFAULT_THRESHOLDS.get(key))


def set_threshold(key, value):
    st.session_state.thresholds[key] = value


def render_threshold_controls():
    if not has_permission("adjust_threshold"):
        st.info("当前角色无权调整阈值参数")
        return get_thresholds()

    thresholds = get_thresholds()

    with st.expander("阈值参数设置", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            low_checkin = st.slider(
                "低签到率阈值",
                min_value=0.0,
                max_value=1.0,
                value=thresholds["low_checkin_rate"],
                step=0.05,
                format="%.0f%%",
                key="slider_low_checkin",
            )
            set_threshold("low_checkin_rate", low_checkin)

            over_capacity = st.slider(
                "人数超限倍数",
                min_value=0.5,
                max_value=3.0,
                value=thresholds["over_capacity_ratio"],
                step=0.1,
                format="%.1fx",
                key="slider_over_capacity",
            )
            set_threshold("over_capacity_ratio", over_capacity)

        with col2:
            high_drop = st.slider(
                "高退课率阈值",
                min_value=0.0,
                max_value=0.5,
                value=thresholds["high_drop_rate"],
                step=0.05,
                format="%.0f%%",
                key="slider_high_drop",
            )
            set_threshold("high_drop_rate", high_drop)

            high_ta_load = st.slider(
                "助教负载阈值（课程数）",
                min_value=1,
                max_value=15,
                value=int(thresholds["high_ta_load"]),
                step=1,
                key="slider_ta_load",
            )
            set_threshold("high_ta_load", high_ta_load)

            low_completion = st.slider(
                "低消课率阈值",
                min_value=0.0,
                max_value=1.0,
                value=thresholds.get("low_completion_rate", 0.40),
                step=0.05,
                format="%.0f%%",
                key="slider_low_completion",
            )
            set_threshold("low_completion_rate", low_completion)

        if st.button("重置为默认值"):
            st.session_state.thresholds = dict(DEFAULT_THRESHOLDS)
            st.rerun()

    return get_thresholds()
