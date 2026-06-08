import pandas as pd
import numpy as np
from thresholds import get_thresholds


def compute_metrics(df):
    if df.empty:
        return df
    df = df.copy()
    df["签到率"] = np.where(
        df["报名人数"] > 0,
        df["签到人数"] / df["报名人数"],
        0.0,
    )
    df["消课率"] = np.where(
        df["报名人数"] > 0,
        df["消课人数"] / df["报名人数"],
        0.0,
    )
    df["退课率"] = np.where(
        df["报名人数"] > 0,
        df["退课人数"] / df["报名人数"],
        0.0,
    )
    df["容量利用率"] = np.where(
        df["课程容量"] > 0,
        df["报名人数"] / df["课程容量"],
        0.0,
    )
    return df


def identify_risks(df):
    if df.empty:
        return df
    thresholds = get_thresholds()
    df = compute_metrics(df)
    risks = []
    for _, row in df.iterrows():
        flags = []
        if row["签到率"] < thresholds["low_checkin_rate"]:
            flags.append("低签到率")
        if row["退课率"] > thresholds["high_drop_rate"]:
            flags.append("高退课率")
        if row["容量利用率"] > thresholds["over_capacity_ratio"]:
            flags.append("人数超限")
        risks.append("、".join(flags) if flags else "正常")
    df["风险标记"] = risks
    df["是否风险"] = df["风险标记"] != "正常"
    return df


def compute_overview(df):
    if df.empty:
        return {
            "总课程数": 0,
            "总报名人数": 0,
            "平均签到率": 0.0,
            "平均消课率": 0.0,
            "风险课程数": 0,
            "风险课程占比": 0.0,
        }
    df = identify_risks(df)
    return {
        "总课程数": len(df),
        "总报名人数": int(df["报名人数"].sum()),
        "平均签到率": round(df["签到率"].mean(), 4),
        "平均消课率": round(df["消课率"].mean(), 4),
        "风险课程数": int(df["是否风险"].sum()),
        "风险课程占比": round(df["是否风险"].mean(), 4),
    }


def compute_ta_load(df):
    if df.empty:
        return pd.DataFrame(columns=["助教", "课程数", "总报名人数", "平均签到率", "负载标记"])
    df = compute_metrics(df)
    thresholds = get_thresholds()
    ta_stats = df.groupby("助教").agg(
        课程数=("课程名称", "count"),
        总报名人数=("报名人数", "sum"),
        平均签到率=("签到率", "mean"),
    ).reset_index()
    ta_stats["平均签到率"] = ta_stats["平均签到率"].round(4)
    ta_stats["负载标记"] = ta_stats["课程数"].apply(
        lambda x: "负载过高" if x >= thresholds["high_ta_load"] else "正常"
    )
    return ta_stats.sort_values("课程数", ascending=False)


def compute_trends(df, freq="W"):
    if df.empty:
        return pd.DataFrame()
    df = compute_metrics(df)
    df["周期"] = df["日期"].dt.to_period(freq).dt.to_timestamp()
    trend = df.groupby("周期").agg(
        平均签到率=("签到率", "mean"),
        平均消课率=("消课率", "mean"),
        平均退课率=("退课率", "mean"),
        总报名人数=("报名人数", "sum"),
        课程数=("课程名称", "count"),
    ).reset_index()
    trend["平均签到率"] = (trend["平均签到率"] * 100).round(1)
    trend["平均消课率"] = (trend["平均消课率"] * 100).round(1)
    trend["平均退课率"] = (trend["平均退课率"] * 100).round(1)
    return trend


def generate_suggestions(df):
    if df.empty:
        return ["暂无数据，无法生成建议。"]
    df = identify_risks(df)
    thresholds = get_thresholds()
    suggestions = []

    low_checkin = df[df["签到率"] < thresholds["low_checkin_rate"]]
    if not low_checkin.empty:
        pct = round(len(low_checkin) / len(df) * 100, 1)
        suggestions.append(
            f"⚠️ {pct}% 的课程签到率低于 {thresholds['low_checkin_rate']:.0%}，"
            f"建议排查课程质量或时间段安排。"
        )

    high_drop = df[df["退课率"] > thresholds["high_drop_rate"]]
    if not high_drop.empty:
        pct = round(len(high_drop) / len(df) * 100, 1)
        suggestions.append(
            f"⚠️ {pct}% 的课程退课率超过 {thresholds['high_drop_rate']:.0%}，"
            f"建议关注课程内容匹配度及学员反馈。"
        )

    over_cap = df[df["容量利用率"] > thresholds["over_capacity_ratio"]]
    if not over_cap.empty:
        suggestions.append(
            f"⚠️ {len(over_cap)} 门课程报名人数超过容量的 {thresholds['over_capacity_ratio']:.1f} 倍，"
            f"建议增加课程容量或开设平行班。"
        )

    ta_stats = compute_ta_load(df)
    high_load_ta = ta_stats[ta_stats["负载标记"] == "负载过高"]
    if not high_load_ta.empty:
        names = "、".join(high_load_ta["助教"].tolist())
        suggestions.append(
            f"⚠️ 助教 {names} 负载超过 {int(thresholds['high_ta_load'])} 门课，"
            f"建议重新分配助教资源。"
        )

    if not suggestions:
        suggestions.append("✅ 当前各项指标均在合理范围内，暂无风险提示。")

    return suggestions
