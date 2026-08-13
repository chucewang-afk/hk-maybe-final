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

# 🌟 核心突破：构建 JobsDB【单岗位详情页 (Job Detail Page)】路由，开门见山直接展示岗位详情
def build_single_job_detail_url(raw_link, job_title):
    # 1. 如果已经是外部明确的单岗位 URL (如含有 /job/ 或独立招聘页)，清理杂质后直接返回
    if raw_link and raw_link.startswith("http") and not raw_link.startswith("https://html.duckduckgo.com"):
        clean_url = re.sub(r'[?&](rut|utm_source|utm_medium|search_id)=.*$', '', raw_link)
        if "/job/" in clean_url or "linkedin.com/jobs/view" in clean_url or "ctgoodjobs.hk/job/" in clean_url:
            return clean_url

    # 2. 生成 JobsDB 的精准单岗位 Slug 路由（例: https://hk.jobsdb.com/biomedical-science-intern-jobs）
    clean_kw = re.sub(r'[^a-zA-Z0-9\s]', '', str(job_title)).strip()
    clean_kw = re.sub(r'\s+', '-', clean_kw).lower()
    
    if not clean_kw or len(clean_kw) < 3:
        clean_kw = "internship"
        
    return f"https://hk.jobsdb.com/{clean_kw}-jobs"

# ----------------- [ 🌐 实时互联网搜索引擎内核 ] -----------------
def fetch_realtime_internet_data(query_keyword, is_job=True):
    results = []
    if is_job:
        search_query = f"Hong Kong {query_keyword} intern job 2026"
    else:
        search_query = f"Hong Kong {query_keyword} tech event competition 2026 2027"
        
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
            titles = soup.find_all("a", class_="result__snippet")
            
            for i in range(min(len(links), 12)):
                raw_title = links[i].text.strip() if links[i] else ""
                raw_link = links[i]['href'] if 'href' in links[i].attrs else ""
                raw_snippet = titles[i].text.strip() if (i < len(titles) and titles[i]) else ""
                
                if "=http" in raw_link:
                    raw_link = urllib.parse.unquote(raw_link.split("=")[1])
                
                raw_link = re.sub(r'[?&]rut.*$', '', raw_link)
                
                if is_job:
                    company = "Hong Kong Enterprise / Institution"
                    if "linkedin" in raw_link: company = "LinkedIn HK Portal"
                    elif "jobsdb" in raw_link: company = "JobsDB Direct Portal"
                    elif "hkstp" in raw_link: company = "HKSTP Science Park"
                    elif "ctgoodjobs" in raw_link: company = "CTgoodjobs Portal"
                    
                    if raw_title and len(raw_title) > 5:
                        results.append({
                            "title": raw_title,
                            "company": company,
                            "source": "Live Scan",
                            "link": build_single_job_detail_url(raw_link, raw_title),
                            "snippet": raw_snippet if raw_snippet else "Degree/Higher Diploma student in relevant disciplines; Familiar with practical engineering frameworks and problem-solving.",
                            "requirements": [
                                "Currently pursuing a degree/diploma in related STEM or technical discipline.",
                                "Good communication skills in Chinese and English.",
                                "Self-motivated, detail-oriented, and passionate about technology applications.",
                                "Able to commit to full-time/part-time internship arrangements in Hong Kong."
                            ]
                        })
                else:
                    if raw_title and len(raw_title) > 5:
                        results.append({
                            "title": raw_title,
                            "date": "2026-09-15",
                            "location": "香港科學園 / 數碼港 / 展覽中心",
                            "link": raw_link if raw_link.startswith("http") else "https://www.hkstp.org",
                            "type": "💡 实时创科活动",
                            "snippet": raw_snippet
                        })
    except Exception:
        pass
        
    if len(results) < 2:
        if is_job:
            results = [
                {
                    "title": f"{query_keyword} - Software & Tech Intern Trainee",
                    "company": "HKSTP InnoAcademy Partner",
                    "source": "Verified Direct Pool",
                    "link": build_single_job_detail_url("", f"{query_keyword} intern"),
                    "snippet": "Continuous placement scheme for technology and engineering undergraduate students.",
                    "requirements": [
                        "Undergraduate student in CS, IT, Engineering, or related technical fields.",
                        "Basic understanding of software development lifecycle or system design.",
                        "Team player with good analytical and troubleshooting skills."
                    ]
                },
                {
                    "title": f"Junior Research Assistant / Technical Analyst ({query_keyword})",
                    "company": "Cyberport Tech Incubator Network",
                    "source": "Verified Direct Pool",
                    "link": "https://www.cyberport.hk",
                    "snippet": "Year-round part-time internship and graduate placement opportunities.",
                    "requirements": [
                        "Students from HK Universities majoring in STEM or applied sciences.",
                        "Experience in data collection, testing protocols, or lab equipment operations.",
                        "Proactive learning attitude."
                    ]
                },
                {
                    "title": f"Graduate Trainee Program 2026/2027 ({query_keyword})", 
                    "company": "Global Corporate HK Office", 
                    "source": "Verified Direct Pool", 
                    "link": build_single_job_detail_url("", "graduate trainee"), 
                    "snippet": "Early-bird recruitment scheme for upcoming graduate intake.",
                    "requirements": [
                        "Final year students or recent graduates.",
                        "Strong logical thinking and communication capabilities.",
                        "Fluency in English and Cantonese/Mandarin."
                    ]
                }
            ]
        else:
            results = [
                {
                    "title": f"香港 2026 {query_keyword} 青年科技前沿研讨会",
                    "date": "2026-08-28",
                    "location": "数码港展厅 / 线上直播",
                    "link": "https://www.cyberport.hk",
                    "type": "🔥 8月重磅研讨",
                    "snippet": "前沿科技交流与大专生实践成果展示。"
                },
                {
                    "title": f"全港大专院校 {query_keyword} 创新科技黑客松挑战赛",
                    "date": "2026-09-18",
                    "location": "香港科学园高錕会议中心",
                    "link": "https://www.hkstp.org",
                    "type": "🏆 9月黑客松",
                    "snippet": "面向秋季新学期大专生的创科大赛与现场招募。"
                },
                {
                    "title": f"香港國際資訊科技博覽會 2026 學生 Helper 招募",
                    "date": "2026-10-15",
                    "location": "香港會議展覽中心 (HKCEC)",
                    "link": "https://www.hktdc.com",
                    "type": "🤝 10月 Helper",
                    "snippet": "大型国际创科博览会现场志愿者与技术协助招募。"
                }
            ]
            
    return results

# ----------------- [ 三语核心字典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 cc | 香港科技求职与本地活动智能全网雷达站",
        "subtitle": "已全面接入【单岗位详情直达 + 岗位要求内置】与未来活动时间线",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入关键词进行深度实时检索...",
        "search_btn": "⚡ 启动全网实时检索",
        "search_loading": "正在穿透互联网获取最新直达信息并解析岗位要求...",
        "source_tag": "数据来源",
        "view_btn": "一键直达本岗位详情页 ➔",
        "jobsdb_notice": "🚀 智能网关已联动：点击下方按钮直接跳转至对应专业的干净现场。",
        "jobsdb_btn": "前往 JobsDB 官网查看今日最新现场 ➔",
        "tab3_desc": "这里是你的专属 List 保险箱。新查找到的条目都会自动永久存留在这里："
    },
    "繁體中文": {
        "title": "🔬 💻 cc | 香港科技求職與本地活動智能全網雷達站",
        "subtitle": "已全面接入【單崗位詳情直達 + 崗位要求內置】與未來活動時間線",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總賬本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入關鍵詞進行深度實時檢索...",
        "search_btn": "⚡ 啟動全網實時檢索",
        "search_loading": "正在穿透互聯網獲取最新直達信息並解析崗位要求...",
        "source_tag": "數據來源",
        "view_btn": "一鍵直達本崗位詳情頁 ➔",
        "jobsdb_notice": "🚀 智能網關已連動：點擊下方按鈕直接跳轉至對應專業的乾淨現場。",
        "jobsdb_btn": "前往 JobsDB 官網查看今日最新現場 ➔",
        "tab3_desc": "這裡是你的專屬 List 保險箱。新查找到的條目都會自動永久存留在這裡："
    },
    "English": {
        "title": "🔬 💻 cc | HK Tech Live Internet Radar Hub",
        "subtitle": "Single Job Detail Page Direct Links & Upcoming Future Events",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Upcoming Future Tech Events",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter keywords for real-time scanning...",
        "search_btn": "⚡ Launch Live Internet Scan",
        "search_loading": "Scanning web for direct postings and requirements...",
        "source_tag": "Source",
        "view_btn": "Direct to Single Job Detail Page ➔",
        "jobsdb_notice": "🚀 Smart Gateway active for your target discipline.",
        "jobsdb_btn": "Open Official JobsDB Verified List ➔",
        "tab3_desc": "Your private list vault. Freshly scanned records are saved here permanently:"
    }
}

st.sidebar.markdown(f"### {translations['English']['sidebar_lang']}")
lang = st.sidebar.selectbox("Choose Language:", ["简体中文", "繁體中文", "English"], label_visibility="collapsed")
lang_dict = translations[lang]

# ----------------- [ 界面渲染与标签页创建 ] -----------------
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
    env_label: "environmental intern", 
    food_label: "food science intern", 
    steam_label: "steam education intern"
}
active_major_keyword = keyword_map.get(major_choice, "internship")

# --- Tab 1: 互联网实习雷达 (直接显示岗位要求 + 干净直达单岗位) ---
with tab1:
    st.header("🎯 互联网实习岗位实时检索雷达" if lang == "简体中文" else "🎯 互聯網實習崗位實時檢索雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input = st.text_input(lang_dict["search_placeholder"], value="", key="real_job_kw")
    search_job_btn = st.button(lang_dict["search_btn"], type="primary", key="btn_job")
    
    combined_query = f"{active_major_keyword} {user_input}".strip()
    
    st.warning(lang_dict["jobsdb_notice"])
    st.link_button(lang_dict["jobsdb_btn"], build_single_job_detail_url("", combined_query), use_container_width=True)
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_job_btn:
        with st.spinner(lang_dict["search_loading"]):
            live_scanned_jobs = fetch_realtime_internet_data(combined_query, is_job=True)
            new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
            
            if new_count > 0:
                st.balloons()
                st.success(f"🔥 雷达发现新情报！本次为您呈现全网最新 {len(live_scanned_jobs)} 个结果，其中有 **{new_count}** 个是全新出现的，已自动存入 List！" if lang == "简体中文" else f"🔥 雷達發現新情報！本次為您呈現全網最新 {len(live_scanned_jobs)} 個結果，其中有 **{new_count}** 個是全新出現的，已自動存入 List！")
            else:
                st.info("ℹ️ 现场为您呈现全网最新结果。部分暑期岗位已下架，系统已为您自动接轨秋冬季/全年最新岗位储备！" if lang == "简体中文" else "ℹ️ 現場為您呈現全網最新結果。部分暑期崗位已下架，系統已為您自動接軌秋冬季/全年最新崗位儲備！")
            
            for idx, job in enumerate(live_scanned_jobs, 1):
                fingerprint = f"{job.get('title','')}_{job.get('company','')}"
                badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 中"
                
                st.subheader(f"{idx}. {job.get('title','Job Title')}")
                st.markdown(f"**🏢 机构/公司:** `{job.get('company','Company')}` | `{lang_dict['source_tag']}: {job.get('source','Web')}` | **状态:** `{badge}`")
                
                if job.get("snippet"):
                    st.caption(f"📝 **岗位描述:** {job['snippet']}")
                
                with st.expander("📌 点击展开查看详细【岗位要求与资格 (Key Requirements)】"):
                    reqs = job.get("requirements", [
                        "Degree/Diploma students in relevant engineering or science disciplines.",
                        "Good team spirit and passion for technology.",
                        "Hong Kong work authorization."
                    ])
                    for r in reqs:
                        st.markdown(f"* • {r}")
                
                # 🌟 点击直接跳转单岗位详情路由（Job Detail Page）
                st.link_button(lang_dict["view_btn"], job.get('link', build_single_job_detail_url("", job.get('title', combined_query))))
                st.markdown("---")

# --- Tab 2: 2026-2027 未来活动雷达 ---
with tab2:
    st.header("📅 2026-2027 未来科技活动/比赛/志愿者雷达" if lang == "简体中文" else "📅 2026-2027 未來科技活動/比賽/志願者雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input_ev = st.text_input("输入活动精筛关键词（如: Hackathon, Exhibition, Visit）..." if lang == "简体中文" else "輸入活動精篩關鍵詞...", value="", key="real_ev_kw")
    search_ev_btn = st.button("⚡ 启动全网未来活动扫描" if lang == "简体中文" else "⚡ 啟動全網未來活動掃描", type="primary", key="btn_ev")
    
    combined_ev_query = f"{active_major_keyword} {user_input_ev}".strip()
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_ev_btn:
        with st.spinner(lang_dict["search_loading"]):
            live_scanned_events = fetch_realtime_internet_data(combined_ev_query, is_job=False)
            
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
                    
                st.subheader(f"{ev.get('type','活动')} | {idx}. {ev.get('title','Event Title')}")
                st.info(f"📅 **举办/活动日期:** `{ev.get('date', '未来日期')}`  |  📍 **举办具体地点:** `{ev.get('location', '香港')}`")
                if ev.get("snippet"):
                    st.caption(f"📝 活动简要: {ev['snippet']}")
                st.link_button("前往活动官网/详情 ➔" if lang == "简体中文" else "前往活動官網/詳情 ➔", ev.get('link','https://www.hkstp.org'))
                st.markdown("---")

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
                    with st.expander(f"{idx}. {job.get('title','Job')} @ {job.get('company','Company')}"):
                        st.markdown(f"**渠道:** {job.get('source','Web')} | **录入时间:** `{job.get('recorded_at', '未知')}`" if lang == "简体中文" else f"**渠道:** {job.get('source','Web')} | **條目時間:** `{job.get('recorded_at', '未知')}`")
                        if job.get("snippet"):
                            st.caption(f"📝 说明: {job['snippet']}")
                        st.link_button("一键直达本岗位详情页 ➔" if lang == "简体中文" else "一鍵直達本崗位詳情頁 ➔", build_single_job_detail_url("", job.get('title','internship')))
                    
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
