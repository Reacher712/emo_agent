"""Efficacy assessment demo page."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from portal_nav import back_home

ROOT = Path(__file__).resolve().parent.parent
RECORD_FILE = ROOT / "outputs" / "efficacy_records.json"

PHQ9 = [
    "做事时提不起劲或没有兴趣",
    "感到心情低落、沮丧或绝望",
    "入睡困难、睡不安稳或睡眠过多",
    "感觉疲倦或没有活力",
    "食欲不振或吃太多",
    "觉得自己很糟，或觉得自己失败、让自己或家人失望",
    "对事情难以集中注意力",
    "动作或说话变慢，或相反地烦躁、坐立不安",
    "有不如死掉或用某种方式伤害自己的念头",
]
GAD7 = [
    "感到紧张、焦虑或急切",
    "不能停止或控制担忧",
    "对各种各样的事情担忧过多",
    "很难放松下来",
    "由于不安而难以静坐",
    "变得容易烦恼或急躁",
    "感到好像将有可怕的事情发生",
]
WHO5 = [
    "我感到愉快、心情舒畅",
    "我感到平静和放松",
    "我感到充满活力",
    "我醒来时感到清新、休息充分",
    "我的日常生活中有许多让我感兴趣的事情",
]

LIKERT_4 = ["完全没有", "好几天", "一半以上天数", "几乎每天"]
LIKERT_WHO5 = ["从未", "偶尔", "少于一半时间", "一半以上时间", "大多数时间", "所有时间"]


def load_records() -> list[dict]:
    if not RECORD_FILE.exists():
        return []
    try:
        return json.loads(RECORD_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_record(record: dict) -> None:
    RECORD_FILE.parent.mkdir(parents=True, exist_ok=True)
    records = load_records()
    records.append(record)
    RECORD_FILE.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def severity_phq(total: int) -> str:
    if total <= 4:
        return "最小或无明显抑郁相关困扰"
    if total <= 9:
        return "轻度抑郁相关困扰"
    if total <= 14:
        return "中度抑郁相关困扰"
    if total <= 19:
        return "中重度抑郁相关困扰"
    return "重度抑郁相关困扰，建议尽快寻求专业帮助"


def severity_gad(total: int) -> str:
    if total <= 4:
        return "最小或无明显焦虑相关困扰"
    if total <= 9:
        return "轻度焦虑相关困扰"
    if total <= 14:
        return "中度焦虑相关困扰"
    return "重度焦虑相关困扰，建议尽快寻求专业帮助"


def severity_who5(total: int) -> str:
    index = total * 4
    if index >= 72:
        return "近期幸福感较好"
    if index >= 52:
        return "近期幸福感中等，可继续观察"
    if index >= 29:
        return "近期幸福感偏低，建议增加支持性活动"
    return "近期幸福感较低，建议与可信任的人或专业人员沟通"


def render_scale(key: str, questions: list[str], options: list[str]) -> list[int]:
    scores = []
    for idx, question in enumerate(questions, start=1):
        st.markdown(f"**{idx}. {question}**")
        choice = st.radio(
            "选择",
            options,
            horizontal=True,
            key=f"{key}_{idx}",
            label_visibility="collapsed",
        )
        scores.append(options.index(choice))
    return scores


st.set_page_config(page_title="听山 | 疗效评估", layout="wide")
back_home()

st.title("疗效评估")
st.caption("用于演示筛查和趋势记录，不构成医学诊断。若出现自伤风险或严重不适，请及时联系专业人员或急救服务。")

phase = st.selectbox("评估阶段", ["干预前", "干预后", "随访/复测", "其他"])
tab1, tab2, tab3, tab4 = st.tabs(["PHQ-9", "GAD-7", "WHO-5", "记录"])

with tab1:
    st.subheader("PHQ-9 抑郁相关症状筛查")
    scores = render_scale("phq9", PHQ9, LIKERT_4)
    total = sum(scores)
    st.metric("总分", total)
    st.success(severity_phq(total))
    if scores[-1] > 0:
        st.error("第 9 题提示需要关注自伤相关风险。请优先联系可信任的人、学校心理中心、医院或急救服务。")
    if st.button("保存 PHQ-9 记录"):
        save_record({"time": datetime.now().isoformat(timespec="seconds"), "phase": phase, "scale": "PHQ-9", "total": total, "scores": scores})
        st.success("已保存到 outputs/efficacy_records.json")

with tab2:
    st.subheader("GAD-7 焦虑相关症状筛查")
    scores = render_scale("gad7", GAD7, LIKERT_4)
    total = sum(scores)
    st.metric("总分", total)
    st.success(severity_gad(total))
    if st.button("保存 GAD-7 记录"):
        save_record({"time": datetime.now().isoformat(timespec="seconds"), "phase": phase, "scale": "GAD-7", "total": total, "scores": scores})
        st.success("已保存到 outputs/efficacy_records.json")

with tab3:
    st.subheader("WHO-5 幸福感指数")
    scores = render_scale("who5", WHO5, LIKERT_WHO5)
    total = sum(scores)
    index = total * 4
    st.metric("指数分", index)
    st.success(severity_who5(total))
    if st.button("保存 WHO-5 记录"):
        save_record({"time": datetime.now().isoformat(timespec="seconds"), "phase": phase, "scale": "WHO-5", "total": total, "index": index, "scores": scores})
        st.success("已保存到 outputs/efficacy_records.json")

with tab4:
    records = load_records()
    if not records:
        st.info("暂无记录。完成任一量表后点击保存即可生成趋势数据。")
    else:
        df = pd.DataFrame(records)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.line_chart(df.pivot_table(index="time", columns="scale", values="total", aggfunc="last"))
