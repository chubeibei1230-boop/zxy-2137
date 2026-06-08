import os
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
DEFAULT_CSV = os.path.join(DATA_DIR, "courses.csv")

REQUIRED_COLUMNS = [
    "日期", "课程名称", "场馆", "助教",
    "报名人数", "签到人数", "消课人数", "退课人数", "课程容量",
]

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def _validate_columns(df):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要列：{', '.join(missing)}")
    return True


def _normalize_df(df):
    df = df.copy()
    df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    for col in ["报名人数", "签到人数", "消课人数", "退课人数", "课程容量"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def load_data(filepath=None):
    if filepath is None:
        filepath = DEFAULT_CSV
    if not os.path.exists(filepath):
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    _validate_columns(df)
    df = _normalize_df(df)
    return df


def save_data(df, filepath=None):
    if filepath is None:
        filepath = DEFAULT_CSV
    df.to_csv(filepath, index=False, encoding="utf-8-sig")


def append_data(new_df, filepath=None):
    new_df = _normalize_df(new_df)
    existing = load_data(filepath)
    combined = pd.concat([existing, new_df], ignore_index=True)
    combined.drop_duplicates(inplace=True)
    save_data(combined, filepath)
    return combined


def init_session_data():
    if "course_data" not in st.session_state:
        st.session_state.course_data = load_data()


def get_data():
    return st.session_state.get("course_data", pd.DataFrame(columns=REQUIRED_COLUMNS))


def set_data(df):
    st.session_state.course_data = df


def filter_data(df, courses=None, date_range=None, venues=None, assistants=None):
    filtered = df.copy()
    if courses:
        filtered = filtered[filtered["课程名称"].isin(courses)]
    if date_range and len(date_range) == 2:
        start, end = date_range
        if start is not None:
            filtered = filtered[filtered["日期"] >= pd.Timestamp(start)]
        if end is not None:
            filtered = filtered[filtered["日期"] <= pd.Timestamp(end)]
    if venues:
        filtered = filtered[filtered["场馆"].isin(venues)]
    if assistants:
        filtered = filtered[filtered["助教"].isin(assistants)]
    return filtered.reset_index(drop=True)


def get_unique_values(df, column):
    if df.empty or column not in df.columns:
        return []
    return sorted(df[column].dropna().unique().tolist())
