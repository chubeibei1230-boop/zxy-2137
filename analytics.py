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


ANOMALY_TAG_CONFIG = [
    ("低签到率", lambda row, t: row["签到率"] < t["low_checkin_rate"]),
    ("高退课率", lambda row, t: row["退课率"] > t["high_drop_rate"]),
    ("人数超限", lambda row, t: row["容量利用率"] > t["over_capacity_ratio"]),
    ("低消课率", lambda row, t: row["消课率"] < t.get("low_completion_rate", 0.50)),
    ("助教负载异常", lambda row, t: row.get("_ta_overloaded", False)),
]

SEVERITY_MAP = {
    "低签到率": "高",
    "高退课率": "高",
    "人数超限": "中",
    "低消课率": "中",
    "助教负载异常": "中",
}


def compute_anomaly_tags(df):
    if df.empty:
        return df
    thresholds = get_thresholds()
    df = compute_metrics(df)
    ta_load = compute_ta_load(df)
    overloaded_tas = set(ta_load[ta_load["负载标记"] == "负载过高"]["助教"].tolist()) if not ta_load.empty else set()
    df["_ta_overloaded"] = df["助教"].isin(overloaded_tas)
    all_tags = []
    all_severities = []
    for _, row in df.iterrows():
        tags = []
        for tag_name, checker in ANOMALY_TAG_CONFIG:
            try:
                if checker(row, thresholds):
                    tags.append(tag_name)
            except Exception:
                pass
        all_tags.append(tags)
        if not tags:
            all_severities.append("正常")
        elif any(SEVERITY_MAP.get(t, "低") == "高" for t in tags):
            all_severities.append("严重")
        elif any(SEVERITY_MAP.get(t, "低") == "中" for t in tags):
            all_severities.append("警告")
        else:
            all_severities.append("提示")
    df["异常标签"] = all_tags
    df["严重程度"] = all_severities
    df["是否异常"] = df["异常标签"].apply(lambda x: len(x) > 0)
    df["异常标签文本"] = df["异常标签"].apply(lambda x: "、".join(x) if x else "正常")
    df = df.drop(columns=["_ta_overloaded"])
    return df


def compute_anomaly_overview(df):
    if df.empty:
        return {
            "总课程数": 0,
            "异常课程数": 0,
            "异常课程占比": 0.0,
            "严重课程数": 0,
            "警告课程数": 0,
            "提示课程数": 0,
            "异常标签分布": {},
        }
    df = compute_anomaly_tags(df)
    anomaly_df = df[df["是否异常"]]
    tag_counter = {}
    for tags in anomaly_df["异常标签"]:
        for t in tags:
            tag_counter[t] = tag_counter.get(t, 0) + 1
    return {
        "总课程数": len(df),
        "异常课程数": int(df["是否异常"].sum()),
        "异常课程占比": round(df["是否异常"].mean(), 4),
        "严重课程数": int((df["严重程度"] == "严重").sum()),
        "警告课程数": int((df["严重程度"] == "警告").sum()),
        "提示课程数": int((df["严重程度"] == "提示").sum()),
        "异常标签分布": tag_counter,
    }


def compute_anomaly_by_dimension(df, dimension="课程名称"):
    if df.empty:
        return pd.DataFrame()
    valid_dims = {"课程名称", "场馆", "助教"}
    if dimension not in valid_dims:
        dimension = "课程名称"
    df = compute_anomaly_tags(df)
    anomaly_df = df[df["是否异常"]]
    if anomaly_df.empty:
        return pd.DataFrame(columns=[dimension, "异常次数", "异常标签汇总", "平均签到率", "平均退课率", "平均容量利用率"])
    dim_stats = anomaly_df.groupby(dimension).agg(
        异常次数=("是否异常", "sum"),
        平均签到率=("签到率", "mean"),
        平均退课率=("退课率", "mean"),
        平均容量利用率=("容量利用率", "mean"),
    ).reset_index()
    tag_agg = anomaly_df.groupby(dimension)["异常标签"].apply(
        lambda x: "、".join(sorted(set(t for tags in x for t in tags)))
    ).reset_index()
    tag_agg.columns = [dimension, "异常标签汇总"]
    result = dim_stats.merge(tag_agg, on=dimension, how="left")
    result["平均签到率"] = result["平均签到率"].round(4)
    result["平均退课率"] = result["平均退课率"].round(4)
    result["平均容量利用率"] = result["平均容量利用率"].round(4)
    return result.sort_values("异常次数", ascending=False)


def compute_anomaly_trends(df, freq="W"):
    if df.empty:
        return pd.DataFrame()
    df = compute_anomaly_tags(df)
    df["周期"] = df["日期"].dt.to_period(freq).dt.to_timestamp()
    trend = df.groupby("周期").agg(
        课程数=("课程名称", "count"),
        异常课程数=("是否异常", "sum"),
    ).reset_index()
    trend["异常率"] = np.where(
        trend["课程数"] > 0,
        (trend["异常课程数"] / trend["课程数"] * 100).round(1),
        0.0,
    )
    return trend


def compute_single_course_review(df, course_name):
    if df.empty or not course_name:
        return None
    df = compute_anomaly_tags(df)
    course_df = df[df["课程名称"] == course_name].sort_values("日期")
    if course_df.empty:
        return None
    anomaly_rows = course_df[course_df["是否异常"]]
    all_tags = []
    for tags in anomaly_rows["异常标签"]:
        all_tags.extend(tags)
    tag_counter = {}
    for t in all_tags:
        tag_counter[t] = tag_counter.get(t, 0) + 1
    top_tags = sorted(tag_counter.items(), key=lambda x: -x[1])
    venues = course_df["场馆"].unique().tolist()
    tas = course_df["助教"].unique().tolist()
    venue_df = df[df["场馆"].isin(venues)]
    venue_anomaly_rate = venue_df["是否异常"].mean() if not venue_df.empty else 0
    ta_df = df[df["助教"].isin(tas)]
    ta_anomaly_rate = ta_df["是否异常"].mean() if not ta_df.empty else 0
    overall_anomaly_rate = df["是否异常"].mean()
    conclusions = []
    if course_df["签到率"].mean() < get_thresholds()["low_checkin_rate"]:
        conclusions.append("该课程签到率持续偏低，需排查课程质量或时间安排。")
    if course_df["退课率"].mean() > get_thresholds()["high_drop_rate"]:
        conclusions.append("退课率偏高，建议审视课程内容与学员预期的匹配度。")
    if course_df["容量利用率"].mean() > get_thresholds()["over_capacity_ratio"]:
        conclusions.append("容量长期超限，建议扩容或增开平行班。")
    if venue_anomaly_rate > overall_anomaly_rate * 1.5:
        conclusions.append(f"关联场馆异常率({venue_anomaly_rate:.1%})显著高于整体({overall_anomaly_rate:.1%})，场馆可能是影响因素。")
    if ta_anomaly_rate > overall_anomaly_rate * 1.5:
        conclusions.append(f"关联助教异常率({ta_anomaly_rate:.1%})显著高于整体({overall_anomaly_rate:.1%})，助教可能是影响因素。")
    if not conclusions:
        conclusions.append("该课程各项指标整体正常，无明显异常趋势。")
    return {
        "课程名称": course_name,
        "总课时数": len(course_df),
        "异常课时数": len(anomaly_rows),
        "异常课时占比": round(len(anomaly_rows) / len(course_df), 4) if len(course_df) > 0 else 0,
        "主要异常标签": top_tags,
        "平均签到率": round(course_df["签到率"].mean(), 4),
        "平均退课率": round(course_df["退课率"].mean(), 4),
        "平均消课率": round(course_df["消课率"].mean(), 4),
        "平均容量利用率": round(course_df["容量利用率"].mean(), 4),
        "关联场馆": venues,
        "关联助教": tas,
        "场馆异常率": round(venue_anomaly_rate, 4),
        "助教异常率": round(ta_anomaly_rate, 4),
        "整体异常率": round(overall_anomaly_rate, 4),
        "结论": conclusions,
        "课程明细": course_df,
        "趋势数据": compute_anomaly_trends(course_df, freq="W"),
    }


def generate_anomaly_suggestions(df):
    if df.empty:
        return ["暂无数据，无法生成建议。"]
    df = compute_anomaly_tags(df)
    thresholds = get_thresholds()
    suggestions = []

    anomaly_count = int(df["是否异常"].sum())
    total = len(df)
    if anomaly_count == 0:
        suggestions.append("✅ 当前筛选范围内无异常课程，各项指标正常。")
        return suggestions

    anomaly_rate = anomaly_count / total
    if anomaly_rate > 0.3:
        suggestions.append(
            f"⚠️ 异常课程占比达 {anomaly_rate:.1%}，建议全面排查近期运营策略是否存在系统性问题。"
        )

    low_checkin = df[df["异常标签"].apply(lambda x: "低签到率" in x)]
    if not low_checkin.empty:
        courses = low_checkin["课程名称"].unique()[:3]
        suggestions.append(
            f"⚠️ {len(low_checkin)} 课时存在低签到率异常（涉及：{'、'.join(courses)}等），"
            f"建议核查课程时间段合理性及学员提醒机制。"
        )

    high_drop = df[df["异常标签"].apply(lambda x: "高退课率" in x)]
    if not high_drop.empty:
        courses = high_drop["课程名称"].unique()[:3]
        suggestions.append(
            f"⚠️ {len(high_drop)} 课时存在高退课率异常（涉及：{'、'.join(courses)}等），"
            f"建议调研退课原因并优化课程内容设计。"
        )

    over_cap = df[df["异常标签"].apply(lambda x: "人数超限" in x)]
    if not over_cap.empty:
        suggestions.append(
            f"⚠️ {len(over_cap)} 课时报名超出容量上限，建议及时扩容或实施报名限流。"
        )

    low_completion = df[df["异常标签"].apply(lambda x: "低消课率" in x)]
    if not low_completion.empty:
        suggestions.append(
            f"⚠️ {len(low_completion)} 课时消课率低于阈值，建议关注课程完成质量和签到后续跟踪。"
        )

    ta_anomaly = df[df["异常标签"].apply(lambda x: "助教负载异常" in x)]
    if not ta_anomaly.empty:
        tas = ta_anomaly["助教"].unique()
        suggestions.append(
            f"⚠️ 助教 {'、'.join(tas)} 存在负载异常，建议重新评估助教排班分配。"
        )

    dim_course = compute_anomaly_by_dimension(df, "课程名称")
    if not dim_course.empty and len(dim_course) > 0:
        top = dim_course.iloc[0]
        suggestions.append(
            f"💡 异常最集中课程「{top['课程名称']}」共 {int(top['异常次数'])} 次异常，建议优先复盘。"
        )

    dim_venue = compute_anomaly_by_dimension(df, "场馆")
    if not dim_venue.empty and len(dim_venue) > 0:
        top = dim_venue.iloc[0]
        suggestions.append(
            f"💡 场馆「{top['场馆']}」异常最集中（{int(top['异常次数'])} 次），建议检查场馆设施或排课密度。"
        )

    return suggestions
