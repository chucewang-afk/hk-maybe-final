import streamlit as st
import json
import os
import requests
import urllib.parse
import re
from datetime import datetime
from bs4 import BeautifulSoup

st.set_page_config(page_title="cc | 香港科技求职与活动站", page_icon="🔬", layout="wide")

JOB_DB = "recorded_jobs.json"

# ----------------- 本地数据 -----------------
def load_local_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []

def sync_and_append_data(current_items, filepath, is_job=True):
    old_items = load_local_data(filepath)
    old_fingerprints = {f"{j.get('title','')}_{j.get('company','')}" for j in old_items if isinstance(j, dict)}
    new_detected_count = 0
    updated_list = list(old_items)
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    just_added_fingerprints = set()
    
    for item in current_items:
        if not isinstance(item, dict):
            continue
        fingerprint = f"{item.get('title','')}_{item.get('company','')}"
        if fingerprint not in old_fingerprints:
            item_copy = item.copy()
            item_copy["recorded_at"] = current_time_str
            updated_list.insert(0, item_copy)
            new_detected_count += 1
            old_fingerprints.add(fingerprint)
            just_added_fingerprints.add(fingerprint)
            
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(updated_list, f, ensure_ascii=False, indent=4)
    except Exception:
        pass
        
    return new_detected_count, old_fingerprints, just_added_fingerprints

# ----------------- 搜索引擎 -----------------
def extract_real_url_from_ddg(raw_url):
    if not raw_url or not str(raw_url).startswith("http"):
        return None
    if "uddg=" in raw_url:
        try:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
            if "uddg" in parsed and parsed["uddg"]:
                clean_target = parsed["uddg"][0]
                if clean_target.startswith("http") and "duckduckgo" not in clean_target:
                    return clean_target
        except Exception:
            pass
    if raw_url.startswith("http") and "duckduckgo.com" not in raw_url:
        return raw_url
    return None

def fetch_realtime_internet_data(query_keyword):
    results = []
    search_query = f"Hong Kong {query_keyword} intern job 2026"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.find_all("a", class_="result__url")
            titles = soup.find_all("a", class_="result__snippet")

            for i in range(min(len(links), 12)):
                raw_title = links[i].text.strip()
                raw_link = links[i]['href']
                raw_snippet = titles[i].text.strip() if (i < len(titles)) else ""
                real_direct_url = extract_real_url_from_ddg(raw_link)

                # ✅ 只保留真实岗位详情页
                if real_direct_url and ("/job/" in real_direct_url or "linkedin.com/jobs/view" in real_direct_url or "ctgoodjobs.hk/job/" in real_direct_url):
                    company = "香港科技公司"
                    if "linkedin.com/jobs/view" in real_direct_url:
                        company = "LinkedIn HK"
                    elif "jobsdb.com/job/" in real_direct_url:
                        company = "JobsDB Official"
                    elif "ctgoodjobs.hk/job/" in real_direct_url:
                        company = "CTgoodjobs"

                    results.append({
                        "title": raw_title,
                        "company": company,
                        "source": "Live Scan",
                        "link": real_direct_url,
                        "snippet": raw_snippet if raw_snippet else "暂无描述",
                        "requirements": [
                            "本科或以上学历，相关专业背景。",
                            "良好的分析与解决问题能力。",
                            "团队合作与沟通能力。",
                            "符合香港实习/工作资格。"
                        ]
                    })
    except Exception:
        pass

    return results

# ----------------- UI -----------------
st.title("🔬 💻 cc | 香港科技求职与活动站")
st.markdown("---")

tab1 = st.tabs(["🎯 实习岗位详情雷达"])[0]

with tab1:
    st.header("🎯 实习岗位详情雷达")
    user_input = st.text_input("输入关键词进行检索...", value="", key="real_job_kw")
    search_job_btn = st.button("⚡ 启动检索", type="primary", key="btn_job")

    if search_job_btn:
        with st.spinner("正在获取岗位详情..."):
            live_scanned_jobs = fetch_realtime_internet_data(user_input)
            if live_scanned_jobs:
                new_count, _, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)

                for idx, job in enumerate(live_scanned_jobs, 1):
                    fingerprint = f"{job.get('title','')}_{job.get('company','')}"
                    badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 中"

                    with st.container(border=True):
                        st.subheader(f"{idx}. {job.get('title','Job Title')}")
                        st.markdown(f"**🏢 公司:** `{job.get('company','Company')}` | 来源: `{job.get('source','Web')}` | 状态: {badge}")
                        st.markdown("#### 📝 岗位职责")
                        st.write(job.get("snippet", "暂无简述"))
                        st.markdown("#### 🎯 任职要求")
                        for r in job.get("requirements", []):
                            st.markdown(f"* {r}")
                        st.markdown("---")
                        st.link_button("🚀 查看官方岗位详情 ➔", job.get("link", "https://hk.jobsdb.com"), type="primary")
            else:
                st.warning("❌ 未找到相关岗位，请尝试更换关键词。")
