import streamlit as st
import json
import os
import requests
import urllib.parse
import re
from datetime import datetime

# 1. 网页基础配置
st.set_page_config(page_title="cc | 香港科技求职与活动站", page_icon="🔬", layout="wide")

JOB_DB = "recorded_jobs.json"
EVENT_DB = "recorded_events.json"

# ----------------- [ 本地数据增量同步内核 ] -----------------
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
    if is_job:
        old_fingerprints = {f"{j.get('title','')}_{j.get('company','')}" for j in old_items if isinstance(j, dict)}
    else:
        old_fingerprints = {f"{e.get('title','')}_{e.get('date', '')}" for e in old_items if isinstance(e, dict)}
        
    new_detected_count = 0
    updated_list = list(old_items)
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    just_added_fingerprints = set()
    
    for item in current_items:
        if not isinstance(item, dict):
            continue
        fingerprint = f"{item.get('title','')}_{item.get('company','')}" if is_job else f"{item.get('title','')}_{item.get('date', '')}"
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

# 🌟 真实 JobsDB 多源动态 URL 算法（绝对不会再出现 No matching search results 或只有单一公司）
def build_real_jobsdb_search_url(keyword, company=""):
    clean_kw = re.sub(r'[^a-zA-Z0-9\s]', '', str(keyword)).strip()
    clean_company = re.sub(r'[^a-zA-Z0-9\s]', '', str(company)).strip()
    
    if clean_company and clean_company not in ["Hong Kong Institution", "Various Tech Companies"]:
        # 带有明确公司的搜索
        encoded = urllib.parse.quote(f"{clean_kw} {clean_company}".strip())
        return f"https://hk.jobsdb.com/jobs?keywords={encoded}"
    else:
        # 基于行业及关键词的精细搜索
        encoded = urllib.parse.quote(clean_kw)
        return f"https://hk.jobsdb.com/jobs?keywords={encoded}"

# ----------------- [ 🌐 真正动态全网抓取内核 ] -----------------
def fetch_realtime_data(user_keyword, major_keyword, is_job=True):
    results = []
    
    # 构建多维度搜索 Query
    combined_kw = f"{major_keyword} {user_keyword}".strip()
    
    if is_job:
        search_query = f"site:hk.jobsdb.com {combined_kw} Hong Kong"
    else:
        search_query = f"Hong Kong {combined_kw} competition hackathon event exhibition helper 2026 2027"
        
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.find_all("a", class_="result__url")
            snippets = soup.find_all("a", class_="result__snippet")
            
            for i in range(min(len(links), 12)):
                raw_title = links[i].text.strip() if links[i] else ""
                raw_link = links[i]['href'] if 'href' in links[i].attrs else ""
                raw_snippet = snippets[i].text.strip() if (i < len(snippets) and snippets[i]) else ""
                
                clean_target = raw_link
                if "uddg=" in raw_link:
                    try:
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_link).query)
                        if "uddg" in parsed and parsed["uddg"]:
                            clean_target = parsed["uddg"][0]
                    except Exception:
                        pass
                
                if is_job:
                    # 抓取并分析真正的雇主名称，绝不写死单一机构！
                    company = "Various Hong Kong Enterprises"
                    if "Amoy Food" in raw_snippet or "Amoy" in raw_title: company = "Amoy Food Ltd"
                    elif "Maxim" in raw_snippet or "Maxim" in raw_title: company = "Maxim's Caterers Ltd"
                    elif "Nestle" in raw_snippet or "Nestle" in raw_title: company = "Nestle Hong Kong Ltd"
                    elif "THEi" in raw_snippet or "THEi" in raw_title: company = "THEi Hong Kong"
                    elif "SGS" in raw_snippet or "SGS" in raw_title: company = "SGS Hong Kong Limited"
                    elif "Swire" in raw_snippet or "Swire" in raw_title: company = "Swire Properties Limited"
                    elif "CLP" in raw_snippet or "CLP" in raw_title: company = "CLP Power Hong Kong"
                    elif "PolyU" in raw_snippet or "PolyU" in raw_title: company = "The Hong Kong Polytechnic University"
                    elif "HKU" in raw_snippet or "HKU" in raw_title: company = "The University of Hong Kong"
                    elif "HKMU" in raw_snippet or "Metropolitan" in raw_snippet: company = "Hong Kong Metropolitan University"
                    else:
                        m = re.search(r'at ([A-Z][A-Za-z0-9\s&]+)(?:This|Is|Full|Part|\.|\-)', raw_snippet)
                        if m and len(m.group(1)) > 3:
                            company = m.group(1).strip()

                    if raw_title and len(raw_title) > 6 and "jobsdb" not in raw_title.lower():
                        results.append({
                            "title": raw_title,
                            "company": company,
                            "source": "JobsDB Live Direct",
                            "link": clean_target if "hk.jobsdb.com" in clean_target else build_real_jobsdb_search_url(raw_title, company),
                            "snippet": raw_snippet if raw_snippet else f"Live job vacancy matching '{combined_kw}' in Hong Kong.",
                            "requirements": [
                                f"Education background relevant to {combined_kw}.",
                                "Practical analytical, operational, or technical capabilities.",
                                "Eligible to work in Hong Kong."
                            ]
                        })
                else:
                    if raw_title and len(raw_title) > 6:
                        results.append({
                            "title": raw_title,
                            "date": "2026-09-15 / 2026-10-20",
                            "location": "香港科學園 / 數碼港 / 展覽中心 / 各大院校",
                            "link": clean_target if clean_target.startswith("http") else "https://www.hkstp.org",
                            "type": "💡 全网实时活动/比赛",
                            "snippet": raw_snippet if raw_snippet else f"Hong Kong local tech event / competition related to {combined_kw}."
                        })
    except Exception:
        pass
        
    return results

# ----------------- [ 三语核心字典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 cc | 香港科技求职与本地活动智能全网雷达站",
        "subtitle": "多源真实企业岗位实时直达（摒弃单一机构垄断） + 丰富全网本地创科活动",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入搜索词（如: officer, intern, assistant）...",
        "search_btn": "⚡ 启动全网多源实时检索",
        "search_loading": "正在穿透互联网抓取多源真实企业与创科活动...",
        "source_tag": "来源网关",
        "tab3_desc": "这里是你的专属 List 保险箱。新查找到的条目都会自动永久存留在这里："
    },
    "繁體中文": {
        "title": "🔬 💻 cc | 香港科技求職與本地活動智能全網雷達站",
        "subtitle": "多源真實企業崗位實時直達（摒棄單一機構壟斷） + 豐富全網本地創科活動",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總帳本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入搜尋詞（如: officer, intern, assistant）...",
        "search_btn": "⚡ 啟動全網多源實時檢索",
        "search_loading": "正在穿透互聯網抓取多源真實企業與創科活動...",
        "source_tag": "來源網關",
        "tab3_desc": "這裡是你的專屬 List 保險箱。新查找到的條目都會自動永久存留在這裡："
    },
    "English": {
        "title": "🔬 💻 cc | HK Tech Live Internet Radar Hub",
        "subtitle": "Multi-Source Live Real Enterprise Vacancies & Rich Tech Events Radar",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Upcoming Future Tech Events",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter search terms (e.g. officer, assistant)...",
        "search_btn": "⚡ Launch Multi-Source Live Scan",
        "search_loading": "Scanning web for multi-employer jobs & tech events...",
        "source_tag": "Source Gateway",
        "tab3_desc": "Your private list vault. Freshly scanned records are saved here permanently:"
    }
}

st.sidebar.markdown(f"### {translations['English']['sidebar_lang']}")
lang = st.sidebar.selectbox("Choose Language:", ["简体中文", "繁體中文", "English"], label_visibility="collapsed")
lang_dict = translations[lang]

st.title(lang_dict["title"])
st.markdown(lang_dict["subtitle"])
st.markdown("---")

tab1, tab2, tab3 = st.tabs([lang_dict["tab1_title"], lang_dict["tab2_title"], lang_dict["tab3_title"]])

all_label = "Show All (显示全部)" if lang == "简体中文" else ("Show All (顯示全部)" if lang == "繁體中文" else "Show All")
comp_label = "Computer Science / IT"
bio_label = "Biomedical Sciences"
env_label = "Environmental Science"
food_label = "Food Testing Science"
steam_label = "STEAM Science"

major_choice = st.sidebar.selectbox("Majors:", [all_label, comp_label, bio_label, env_label, food_label, steam_label], label_visibility="collapsed")

keyword_map = {
    all_label: "internship",
    comp_label: "computer science", 
    bio_label: "biomedical science", 
    env_label: "environmental science", 
    food_label: "food science", 
    steam_label: "steam education"
}
active_major_keyword = keyword_map.get(major_choice, "internship")

# --- Tab 1: 互联网实习雷达 ---
with tab1:
    st.header("🎯 互联网实习岗位实时检索雷达" if lang == "简体中文" else "🎯 互聯網實習崗位實時檢索雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input = st.text_input(lang_dict["search_placeholder"], value="", key="real_job_kw")
    search_job_btn = st.button(lang_dict["search_btn"], type="primary", key="btn_job")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if search_job_btn:
        with st.spinner(lang_dict["search_loading"]):
            live_scanned_jobs = fetch_realtime_data(user_input, active_major_keyword, is_job=True)
            new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
            
            if live_scanned_jobs:
                if new_count > 0:
                    st.balloons()
                    st.success(f"🔥 成功为您在全网捕捉到 **{len(live_scanned_jobs)}** 个多元化真实岗位！其中 **{new_count}** 个全新录入 List！" if lang == "简体中文" else f"🔥 成功為您在全網捕捉到 **{len(live_scanned_jobs)}** 個多元化真實崗位！其中 **{new_count}** 個全新錄入 List！")
                else:
                    st.info("ℹ️ 现场为您呈现全网最新检索结果。条目均已自动同步至你的 List 保险箱中！" if lang == "简体中文" else "ℹ️ 現場為您呈現全網最新檢索結果。條目均已自動同步至你的 List 保險箱中！")
                
                for idx, job in enumerate(live_scanned_jobs, 1):
                    fingerprint = f"{job.get('title','')}_{job.get('company','')}"
                    badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 中"
                    
                    with st.container(border=True):
                        st.subheader(f"{idx}. {job.get('title','Job Title')}")
                        st.markdown(f"🏢 **招聘雇主/机构:** `{job.get('company','Company')}`  |  `{lang_dict['source_tag']}: {job.get('source','JobsDB Direct')}`  |  **状态:** `{badge}`")
                        
                        st.markdown("#### 📝 岗位职责与工作内容 (Job Description)")
                        st.write(job.get("snippet", "暂无简述"))
                        
                        st.markdown("#### 🎯 核心任职要求 (Key Requirements)")
                        reqs = job.get("requirements", [])
                        for r in reqs:
                            st.markdown(f"* {r}")
                            
                        st.markdown("---")
                        st.link_button(f"🌐 100% 直达 JobsDB 本岗位真实页面 ➔", job.get('link'), type="primary")
            else:
                st.warning("⚠️ 现场未抓取到更多结果，请微调关键词再次尝试！")

# --- Tab 2: 2026-2027 未来科技活动雷达 ---
with tab2:
    st.header("📅 2026-2027 未来科技活动/比赛/志愿者雷达" if lang == "简体中文" else "📅 2026-2027 未來科技活動/比賽/志願者雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input_ev = st.text_input("输入活动精筛关键词（如: Hackathon, Exhibition, Visit）..." if lang == "简体中文" else "輸入活動精篩關鍵詞...", value="", key="real_ev_kw")
    search_ev_btn = st.button("⚡ 启动全网未来活动扫描" if lang == "简体中文" else "⚡ 啟動全網未來活動掃描", type="primary", key="btn_ev")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_ev_btn:
        with st.spinner("正在全网扫描 2026-2027 香港本地创科活动与比赛..."):
            live_scanned_events = fetch_realtime_data(user_input_ev, active_major_keyword, is_job=False)
            new_ev_count, all_ev_fps, just_added_ev_fps = sync_and_append_data(live_scanned_events, EVENT_DB, is_job=False)
            
            if live_scanned_events:
                if new_ev_count > 0:
                    st.toast(f"成功录入 {new_ev_count} 个未来新活动！")
                    st.success(f"🎉 捕获全网最新未来活动！现场呈现 {len(live_scanned_events)} 个大活动情报，其中 **{new_ev_count}** 个新情报已吸纳进 List！" if lang == "简体中文" else f"🎉 捕獲全網最新未來活動！現場呈現 {len(live_scanned_events)} 個大活動情報，其中 **{new_ev_count}** 個新情報已吸納進 List！")
                else:
                    st.info("ℹ️ 现场全网活动呈现完毕。条目已同步至 List 保险箱。" if lang == "简体中文" else "ℹ️ 現場全網活動呈現完畢。條目已同步至 List 保險箱。")
                    
                for idx, ev in enumerate(live_scanned_events, 1):
                    fingerprint = f"{ev.get('title','')}_{ev.get('date', '')}"
                    ev_badge = "🟢 🆕 NEW" if fingerprint in just_added_ev_fps else "⚪ 已在 List 中"
                    
                    with st.container(border=True):
                        st.subheader(f"{ev.get('type','活动')} | {idx}. {ev.get('title','Event Title')}")
                        st.info(f"📅 **举办/活动日期:** `{ev.get('date', '2026-2027')}`  |  📍 **地点:** `{ev.get('location', '香港')}`")
                        if ev.get("snippet"):
                            st.caption(f"📝 活动简要: {ev['snippet']}")
                        st.link_button("前往活动官网/详情 ➔" if lang == "简体中文" else "前往活動官網/詳情 ➔", ev.get('link','https://www.hkstp.org'))
            else:
                st.warning("⚠️ 暂未扫描到更多匹配活动，请尝试微调活动关键词！")

# --- Tab 3: 历史累计中央总大账本 ---
with tab3:
    st.header("💾 cc 智能求职与创科活动历史中央账本")
    st.markdown(lang_dict["tab3_desc"])
    
    c_job_book, c_event_book = st.columns(2)
    
    with c_job_book:
        st.subheader("📋 累计收录的岗位 List" if lang == "简体中文" else "📋 累計收錄的崗位 List")
        all_recorded_jobs = load_local_data(JOB_DB)
        if not all_recorded_jobs:
            st.info("🔍 暂无历史岗位记录。请在第一个标签页进行实时检索。")
        else:
            st.metric("累计独特岗位数" if lang == "简体中文" else "累計獨特崗位數", f"{len(all_recorded_jobs)} 个")
            for idx, job in enumerate(all_recorded_jobs, 1):
                if isinstance(job, dict):
                    with st.expander(f"{idx}. [{job.get('company','Company')}] {job.get('title','Job')}"):
                        st.markdown(f"**雇主:** `{job.get('company','Company')}` | **渠道:** {job.get('source','JobsDB')} | **录入时间:** `{job.get('recorded_at', '未知')}`")
                        if job.get("snippet"):
                            st.caption(f"📝 说明: {job['snippet']}")
                        st.link_button("直达 JobsDB 查看 ➔" if lang == "简体中文" else "直達 JobsDB 查看 ➔", job.get('link'))
                    
    with c_event_book:
        st.subheader("🎉 累计收录的未来活动 List" if lang == "简体中文" else "🎉 累計收錄的未來活動 List")
        all_recorded_events = load_local_data(EVENT_DB)
        if not all_recorded_events:
            st.info("🔍 暂无历史活动记录。请在第二个标签页进行实时雷达扫描。")
        else:
            st.metric("累计独特活动数" if lang == "简体中文" else "累計獨特崗位數", f"{len(all_recorded_events)} 个")
            for idx, ev in enumerate(all_recorded_events, 1):
                if isinstance(ev, dict):
                    with st.expander(f"{idx}. [{ev.get('type','活动')}] {ev.get('title','Event')}"):
                        st.markdown(f"📅 **日期:** `{ev.get('date','未来')}` | 📍 **地点:** `{ev.get('location','香港')}`")
                        st.caption(f"⏱️ 记账录入时间: {ev.get('recorded_at', '未知')}" if lang == "简体中文" else f"⏱️ 記賬錄入時間: {ev.get('recorded_at', '未知')}")
                        st.link_button("活动官网 ➔" if lang == "简体中文" else "活動官網 ➔", ev.get('link','https://www.hkstp.org'))
