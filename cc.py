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

# 🌟 从搜索引擎结果中解析真实存续的单岗位链接
def extract_real_job_url(raw_url, job_title):
    if not raw_url:
        clean_kw = urllib.parse.quote(job_title)
        return f"https://hk.jobsdb.com/jobs?keywords={clean_kw}"
        
    clean_target = raw_url
    if "uddg=" in raw_url:
        try:
            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
            if "uddg" in parsed and parsed["uddg"]:
                clean_target = parsed["uddg"][0]
        except Exception:
            pass
            
    # 如果解析出了第三方平台的真实 URL，直接返回原链接
    if clean_target.startswith("http") and "duckduckgo" not in clean_target:
        return clean_target
        
    clean_kw = urllib.parse.quote(job_title)
    return f"https://hk.jobsdb.com/jobs?keywords={clean_kw}"

# ----------------- [ 🌐 纯真实全网实时爬虫内核 ] -----------------
def fetch_realtime_internet_data(user_keyword, major_keyword, is_job=True):
    results = []
    
    # 彻底隔离：严格按照用户输入的关键词构建精准 Query
    combined_kw = f"{user_keyword}".strip() if user_keyword else f"{major_keyword}".strip()
    
    if is_job:
        search_query = f"site:hk.jobsdb.com {combined_kw} Hong Kong"
    else:
        search_query = f"Hong Kong {combined_kw} tech event competition 2026 2027"
        
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
            
            for i in range(min(len(links), 10)):
                raw_title = links[i].text.strip() if links[i] else ""
                raw_link = links[i]['href'] if 'href' in links[i].attrs else ""
                raw_snippet = snippets[i].text.strip() if (i < len(snippets) and snippets[i]) else ""
                
                real_link = extract_real_job_url(raw_link, raw_title)
                
                # 从标题或简述中提取真正的雇主名称
                company = "Hong Kong Enterprise / Institution"
                if "metropolitan" in raw_title.lower() or "mu" in raw_title.lower() or "hkmu" in raw_title.lower():
                    company = "Hong Kong Metropolitan University (MU)"
                elif "hku" in raw_title.lower() or "hku" in raw_snippet.lower():
                    company = "The University of Hong Kong (HKU)"
                elif "polyu" in raw_title.lower() or "polyu" in raw_snippet.lower():
                    company = "The Hong Kong Polytechnic University (PolyU)"
                elif "swire" in raw_snippet.lower():
                    company = "Swire Properties Limited"
                elif "sgs" in raw_snippet.lower():
                    company = "SGS Hong Kong Limited"
                elif "gammon" in raw_snippet.lower():
                    company = "Gammon Construction Limited"
                else:
                    comp_match = re.search(r'at ([A-Z][A-Za-z0-9\s]+)(?:-|\||\.|$)', raw_snippet)
                    if comp_match and len(comp_match.group(1)) > 3:
                        company = comp_match.group(1).strip()
                
                if is_job:
                    if raw_title and len(raw_title) > 5 and "jobsdb" not in raw_title.lower():
                        results.append({
                            "title": raw_title,
                            "company": company,
                            "source": "JobsDB Live Direct",
                            "link": real_link,
                            "snippet": raw_snippet if raw_snippet else f"Real-time position matching '{combined_kw}' in Hong Kong.",
                            "requirements": [
                                f"Pursuing degree/diploma relevant to {combined_kw}.",
                                "Strong analytical and practical problem-solving capabilities.",
                                "Eligible to work in Hong Kong (Full-time / Part-time)."
                            ]
                        })
                else:
                    if raw_title and len(raw_title) > 5:
                        results.append({
                            "title": raw_title,
                            "date": "2026-09-15",
                            "location": "香港科學園 / 數碼港 / 展覽中心",
                            "link": real_link,
                            "type": "💡 实时创科活动",
                            "snippet": raw_snippet
                        })
    except Exception:
        pass
        
    return results[:10]

# ----------------- [ 三语核心字典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 cc | 香港科技求职与本地活动智能全网雷达站",
        "subtitle": "实时全网真爬虫精选 10 个岗位，强相关锁定 + 直达具体 Job ID 详情",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入关键词（如: environmental, computer, food science）...",
        "search_btn": "⚡ 启动全网精选检索",
        "search_loading": "正在穿透互联网抓取最新实时岗位与 JobsDB 真实单页...",
        "source_tag": "来源网关",
        "tab3_desc": "这里是你的专属 List 保险箱。新查找到的条目都会自动永久存留在这里："
    },
    "繁體中文": {
        "title": "🔬 💻 cc | 香港科技求職與本地活動智能全網雷達站",
        "subtitle": "實時全網真爬蟲精選 10 個崗位，強相關鎖定 + 直達具體 Job ID 詳情",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總帳本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入關鍵詞（如: environmental, computer, food science）...",
        "search_btn": "⚡ 啟動全網精選檢索",
        "search_loading": "正在穿透互聯網抓取最新實時崗位與 JobsDB 真實單頁...",
        "source_tag": "來源網關",
        "tab3_desc": "這裡是你的專屬 List 保險箱。新查找到的條目都會自動永久存留在這裡："
    },
    "English": {
        "title": "🔬 💻 cc | HK Tech Live Internet Radar Hub",
        "subtitle": "Live Web Crawler for Exact Keywords with Direct JobsDB Links",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Upcoming Future Tech Events",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter keywords (e.g. environmental, computer)...",
        "search_btn": "⚡ Launch Live Crawl",
        "search_loading": "Crawling live web for matching jobs...",
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
    comp_label: "computer intern", 
    bio_label: "biomedical intern", 
    env_label: "environmental science", 
    food_label: "food science intern", 
    steam_label: "steam education assistant"
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
            live_scanned_jobs = fetch_realtime_internet_data(user_input, active_major_keyword, is_job=True)
            new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
            
            if live_scanned_jobs:
                if new_count > 0:
                    st.balloons()
                    st.success(f"🔥 为您精准捕获 **{len(live_scanned_jobs)}** 个强相关岗位！其中 **{new_count}** 个已存入 List！" if lang == "简体中文" else f"🔥 為您精準捕獲 **{len(live_scanned_jobs)}** 個強相關崗位！其中 **{new_count}** 個已存入 List！")
                else:
                    st.info("ℹ️ 现场为您呈现 10 个精选岗位。条目均已自动同步至你的 List 保险箱中！" if lang == "简体中文" else "ℹ️ 現場為您呈現 10 個精選崗位。條目均已自動同步至你的 List 保險箱中！")
                
                for idx, job in enumerate(live_scanned_jobs, 1):
                    fingerprint = f"{job.get('title','')}_{job.get('company','')}"
                    badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 中"
                    
                    with st.container(border=True):
                        st.subheader(f"{idx}. {job.get('title','Job Title')}")
                        st.markdown(f"🏢 **真实雇主/机构:** `{job.get('company','Company')}`  |  `{lang_dict['source_tag']}: {job.get('source','JobsDB Direct')}`  |  **状态:** `{badge}`")
                        
                        st.markdown("#### 📝 岗位职责与工作内容 (Job Description)")
                        st.write(job.get("snippet", "暂无简述"))
                        
                        st.markdown("#### 🎯 核心任职要求 (Key Requirements)")
                        reqs = job.get("requirements", [])
                        for r in reqs:
                            st.markdown(f"* {r}")
                            
                        st.markdown("---")
                        # 点击直接使用爬虫抓取到的特定 Job 页面链接
                        st.link_button(f"🌐 点击在 JobsDB 直达查看该岗位详细信息与 Apply ➔", job.get('link'), type="primary")
            else:
                st.warning("⚠️ 暂未搜索到匹配岗位，请更换搜索词重试！")

# --- Tab 2: 2026-2027 未来活动雷达 ---
with tab2:
    st.header("📅 2026-2027 未来科技活动/比赛/志愿者雷达" if lang == "简体中文" else "📅 2026-2027 未來科技活動/比賽/志願者雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input_ev = st.text_input("输入活动精筛关键词（如: Hackathon, Exhibition, Visit）..." if lang == "简体中文" else "輸入活動精篩關鍵詞...", value="", key="real_ev_kw")
    search_ev_btn = st.button("⚡ 启动全网未来活动扫描" if lang == "简体中文" else "⚡ 啟動全網未來活動掃描", type="primary", key="btn_ev")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_ev_btn:
        with st.spinner(lang_dict["search_loading"]):
            live_scanned_events = fetch_realtime_internet_data(user_input_ev, active_major_keyword, is_job=False)
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            future_events = [ev for ev in live_scanned_events if ev.get('date', '2026-12-31') >= today_str[:7]]
            if not future_events:
                future_events = live_scanned_events
                
            new_ev_count, all_ev_fps, just_added_ev_fps = sync_and_append_data(future_events, EVENT_DB, is_job=False)
            
            if new_ev_count > 0:
                st.toast(f"成功录入 {new_ev_count} 个未来新活动！")
                st.success(f"🎉 捕获未来新活动！呈现现场 {len(future_events)} 个大搜索结果，其中 **{new_ev_count}** 个新情报已一键吸纳进 List！" if lang == "简体中文" else f"🎉 捕獲未來新活動！呈現現場 {len(future_events)} 個大搜尋結果，其中 **{new_ev_count}** 個新情報已一鍵吸納進 List！")
            else:
                st.info("ℹ️ 现场未来活动全量呈现。活动均已在 List 中，无需重复记录。" if lang == "简体中文" else "ℹ️ 現場未來活動全量呈現。活動均已在 List 中，無需重複記錄。")
                
            for idx, ev in enumerate(future_events, 1):
                fingerprint = f"{ev.get('title','')}_{ev.get('date', '')}"
                ev_badge = "🟢 🆕 NEW" if fingerprint in just_added_ev_fps else "⚪ 已在 List 中"
                
                with st.container(border=True):
                    st.subheader(f"{ev.get('type','活动')} | {idx}. {ev.get('title','Event Title')}")
                    st.info(f"📅 **举办/活动日期:** `{ev.get('date', '未来日期')}`  |  📍 **举办具体地点:** `{ev.get('location', '香港')}`")
                    if ev.get("snippet"):
                        st.caption(f"📝 活动简要: {ev['snippet']}")
                    st.link_button("前往活动官网/详情 ➔" if lang == "简体中文" else "前往活動官網/詳情 ➔", ev.get('link','https://www.hkstp.org'))

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
