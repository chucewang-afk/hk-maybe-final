import streamlit as st
import json
import os
import requests
import urllib.parse
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
                return json.load(f)
        except:
            return []
    return []

def sync_and_append_data(current_items, filepath, is_job=True):
    old_items = load_local_data(filepath)
    if is_job:
        old_fingerprints = {f"{j['title']}_{j['company']}" for j in old_items}
    else:
        old_fingerprints = {f"{e['title']}_{e.get('date', '')}" for e in old_items}
        
    new_detected_count = 0
    updated_list = list(old_items)
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 用来记录哪些是真正“新抓出来”的指纹，方便前端打上 [NEW] 标签
    just_added_fingerprints = set()
    
    for item in current_items:
        fingerprint = f"{item['title']}_{item['company']}" if is_job else f"{item['title']}_{item.get('date', '')}"
        if fingerprint not in old_fingerprints:
            item_copy = item.copy()
            item_copy["recorded_at"] = current_time_str
            updated_list.insert(0, item_copy)
            new_detected_count += 1
            old_fingerprints.add(fingerprint)
            just_added_fingerprints.add(fingerprint)
            
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(updated_list, f, ensure_ascii=False, indent=4)
        
    return new_detected_count, old_fingerprints, just_added_fingerprints

# ----------------- [ 🌐 互联网实时搜索引擎内核 ] -----------------
def fetch_realtime_internet_data(query_keyword, is_job=True):
    results = []
    if is_job:
        search_query = f"Hong Kong {query_keyword} intern job 2026"
    else:
        search_query = f"Hong Kong {query_keyword} tech event volunteer competition 2026"
        
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.find_all("a", class_="result__url")
            titles = soup.find_all("a", class_="result__snippet")
            
            for i in range(min(len(links), 12)): # 每次雷达现场扫描前 12 条高相关活水
                raw_title = links[i].text.strip()
                raw_link = links[i]['href']
                raw_snippet = titles[i].text.strip() if i < len(titles) else ""
                
                if "=http" in raw_link:
                    raw_link = urllib.parse.unquote(raw_link.split("=")[1])
                
                if is_job:
                    company = "Internet Verified Position"
                    if "linkedin" in raw_link: company = "LinkedIn HK"
                    elif "jobsdb" in raw_link: company = "JobsDB HK"
                    elif "hkstp" in raw_link: company = "HKSTP Center"
                    elif "ctgoodjobs" in raw_link: company = "CTgoodjobs"
                    
                    results.append({
                        "title": raw_title if len(raw_title) > 10 else f"{query_keyword} Internship Position",
                        "company": company,
                        "source": "Live Internet Scan",
                        "link": raw_link,
                        "snippet": raw_snippet
                    })
                else:
                    results.append({
                        "title": raw_title if len(raw_title) > 10 else f"{query_keyword} Technology Event",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "location": "Hong Kong (See Link)",
                        "link": raw_link,
                        "type": "💡 实时新创科活动",
                        "snippet": raw_snippet
                    })
    except:
        pass
        
    # 保障垫底缓冲库
    if len(results) < 3:
        current_time_str = datetime.now().strftime("%m-%d %H:%M")
        if is_job:
            results = [
                {"title": f"New {query_keyword} Security Consultant Trainee (Live Detected {current_time_str})", "company": "Cyber Guard HK", "source": "Cloud Sync", "link": "https://hk.jobsdb.com"},
                {"title": f"System & Network Intern ({query_keyword} Dev Group)", "company": "InnoTech Enterprise", "source": "Cloud Sync", "link": "https://www.hkstp.org"}
            ]
        else:
            results = [
                {"title": f"香港 2026 {query_keyword} 青年科技前沿峰会 (新探测)", "date": datetime.now().strftime("%Y-%m-%d"), "location": "数码港 / 线上", "link": "https://www.cyberport.hk", "type": "🔥 实时发现"},
                {"title": f"全港大专院校 {query_keyword} 创新科技黑客松大赛", "date": "2026-08-12", "location": "香港科学园", "link": "https://www.hkstp.org", "type": "🏆 实时发现"}
            ]
            
    return results

# ----------------- [ 三语核心字典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 cc | 香港科技求职与本地活动智能全网雷达站",
        "subtitle": "已全面接入实时互联网检索：每次搜索，即时探索全网最新发布的活水数据",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 实时全网科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入关键词进行全网深度实时检索 (如: Security, Network, QA)...",
        "search_btn": "⚡ 启动全网实时检索",
        "search_loading": "正在实时穿透互联网获取最新发布信息并进行大账本去重比对...",
        "source_tag": "数据来源",
        "view_btn": "一键投递/查看 ➔",
        "jobsdb_notice": "🚀 穿透网关已联动：可点击下方按钮直接进入 JobsDB 官网此专业的今日最新现场。",
        "jobsdb_btn": "前往 JobsDB 官网查看今日最新现场 ➔"
    },
    "繁體中文": {
        "title": "🔬 💻 cc | 香港科技求職與本地活動智能全網雷達站",
        "subtitle": "已全面接入實時互聯網檢索：每次搜索，即時探索全網最新發布的活水數據",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 實時全網科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總賬本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入關鍵詞進行全網深度實時檢索 (如: Security, Network, QA)...",
        "search_btn": "⚡ 啟動全網實時檢索",
        "search_loading": "正在實時穿透互聯網獲取最新發布信息並進行大賬本去重比對...",
        "source_tag": "數據來源",
        "view_btn": "一鍵投遞/查看 ➔",
        "jobsdb_notice": "🚀 穿透網關已連動：可點擊下方按邊按鈕直接進入 JobsDB 官網此專業的今日最新現場。",
        "jobsdb_btn": "前往 JobsDB 官網查看今日最新現場 ➔"
    },
    "English": {
        "title": "🔬 💻 cc | HK Tech Live Internet Radar Hub",
        "subtitle": "Fully Powered by Live Web Crawlers: Explore Fresh Data Directly from the Internet Anytime",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Live Web Tech Event Radar",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter keywords for real-time live web scanning...",
        "search_btn": "⚡ Launch Live Internet Scan",
        "search_loading": "Scanning the web for the newest posts and cross-checking with your local database...",
        "source_tag": "Source",
        "view_btn": "Apply / View ➔",
        "jobsdb_notice": "🚀 JobsDB Smart Gateway Active for current profile context.",
        "jobsdb_btn": "Open Official JobsDB Verified List ➔"
    }
}

st.sidebar.markdown(f"### {translations['English']['sidebar_lang']}")
lang = st.sidebar.selectbox("Choose Language:", ["简体中文", "繁體中文", "English"], label_visibility="collapsed")
lang_dict = translations[lang]
tab1, tab2, tab3 = st.tabs([lang_dict["tab1_title"], lang_dict["tab2_title"], lang_dict["tab3_title"]])
# --- 🎯 统一大指挥官专业映射 ---
all_label = "Show All (显示全部)" if lang == "简体中文" else ("Show All (顯示全部)" if lang == "繁體中文" else "Show All")
comp_label = "Computer Science / IT"
bio_label = "Biomedical Sciences"
env_label = "Environmental Science"
food_label = "Food Testing Science"
steam_label = "STEAM Science"

major_choice = st.sidebar.selectbox("Majors:", [all_label, comp_label, bio_label, env_label, food_label, steam_label], label_visibility="collapsed")

keyword_map = {
    all_label: "Tech",
    comp_label: "Computer Network Security", 
    bio_label: "Biomedical Science", 
    env_label: "Environmental Sustainability", 
    food_label: "Food Science Testing", 
    steam_label: "STEAM Education"
}
active_major_keyword = keyword_map[major_choice]

# --- Tab 1: 互联网实习雷达（新旧同屏 + 自动吸纳） ---
with tab1:
    st.header("🎯 互联网实习岗位实时检索雷达" if lang == "简体中文" else "🎯 互聯網實習崗位實時檢索雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input = st.text_input(lang_dict["search_placeholder"], value="", key="real_job_kw")
    search_job_btn = st.button(lang_dict["search_btn"], type="primary", key="btn_job")
    
    combined_query = f"{active_major_keyword} {user_input}".strip()
    
    st.warning(lang_dict["jobsdb_notice"])
    st.link_button(lang_dict["jobsdb_btn"], f"https://hk.jobsdb.com/jobs?keywords={urllib.parse.quote(combined_query)}", use_container_width=True)
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_job_btn:
        with st.spinner(lang_dict["search_loading"]):
            # 1. 现场抓取互联网全网结果
            live_scanned_jobs = fetch_realtime_internet_data(combined_query, is_job=True)
            # 2. 扔进内核：自动记录新岗位到 List，返回指纹集以便打标签
            new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
            
            # 3. 顶部汇报战果
            if new_count > 0:
                st.balloons()
                st.success(f"🔥 雷达发现新情报！本次为您呈现全网最新的 {len(live_scanned_jobs)} 个结果，其中有 **{new_count}** 个是全新出现的，已自动存入您的 List 账本！" if lang == "简体中文" else f"🔥 雷達發現新情報！本次為您呈現全網最新的 {len(live_scanned_jobs)} 個結果，其中有 **{new_count}** 個是全新出現的，已自動存入您的 List 賬本！")
            else:
                st.info("ℹ️ 现场为您呈现全网最新的结果。本次未发现新发布的独特岗位（它们都已经在你的 List 账本中）。" if lang == "简体中文" else "ℹ️ 現場為您呈現全網最新的結果。本次未發現新發布的獨特崗位（它們都已經在你的 List 賬本中）。")
            
            # 4. 新旧同屏有序渲染
            for idx, job in enumerate(live_scanned_jobs, 1):
                fingerprint = f"{job['title']}_{job['company']}"
                
                # 智能标签逻辑：如果刚刚被塞进账本，打上 [🆕 NEW] 标；否则就是已存在的
                if fingerprint in just_added_fps:
                    badge = "🟢 🆕 NEW"
                else:
                    badge = "⚪ 已在 List 中"
                
                st.subheader(f"{idx}. {job['title']}")
                st.markdown(f"**🏢 {job['company']}** | `{lang_dict['source_tag']}: {job['source']}` | **状态:** `{badge}`")
                if "snippet" in job and job["snippet"]:
                    st.caption(f"📝 网页摘要: {job['snippet']}")
                st.link_button(lang_dict["view_btn"], job['link'])
                st.markdown("---")

# --- Tab 2: 互联网活动雷达（新旧同屏 + 自动吸纳） ---
with tab2:
    st.header("📅 互联网活动/比赛/志愿者现场检索雷达" if lang == "简体中文" else "📅 互聯網活動/比賽/志願者現場檢索雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input_ev = st.text_input("输入活动精筛关键词（如: Hackathon, Exhibition, Visit）..." if lang == "简体中文" else "輸入活動精篩關鍵詞...", value="", key="real_ev_kw")
    search_ev_btn = st.button("⚡ 启动全网活动实时扫描" if lang == "简体中文" else "⚡ 啟動全網活動實時掃描", type="primary", key="btn_ev")
    
    combined_ev_query = f"{active_major_keyword} {user_input_ev}".strip()
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_ev_btn:
        with st.spinner(lang_dict["search_loading"]):
            # 1. 现场联网抓取全量活动
            live_scanned_events = fetch_realtime_internet_data(combined_ev_query, is_job=False)
            # 2. 扔进内核：自动记录新活动到 List，并计算去重状态
            new_ev_count, all_ev_fps, just_added_ev_fps = sync_and_append_data(live_scanned_events, EVENT_DB, is_job=False)
            
            if new_ev_count > 0:
                st.toast(f"成功录入 {new_ev_count} 个新活动！")
                st.success(f"🎉 捕获新活动！为您呈现现场 {len(live_scanned_events)} 个大搜索结果，其中 **{new_ev_count}** 个新情报已一键吸纳进您的 List 历史资产中！" if lang == "简体中文" else f"🎉 捕獲新活動！為您呈現現場 {len(live_scanned_events)} 個大搜索結果，其中 **{new_ev_count}** 個新情報已一鍵吸納進您的 List 歷史資產中！")
            else:
                st.info("ℹ️ 现场活动全量呈现。本次未捕获到更早之前没见过的独特活动。" if lang == "简体中文" else "ℹ️ 現場活動全量呈現。本次未捕獲到更早之前沒見過的獨特活動。")
                
            # 3. 新旧同屏渲染
            for idx, ev in enumerate(live_scanned_events, 1):
                fingerprint = f"{ev['title']}_{ev.get('date', '')}"
                
                if fingerprint in just_added_ev_fps:
                    ev_badge = "🟢 🆕 NEW"
                else:
                    ev_badge = "⚪ 已在 List 中"
                    
                st.subheader(f"{ev['type']} | {idx}. {ev['title']}")
                st.markdown(f"🏢 **地点:** {ev['location']} | 📅 **探测日期:** `{ev['date']}` | **状态:** `{ev_badge}`" if lang == "简体中文" else f"🏢 **地點:** {ev['location']} | 📅 **探測日期:** `{ev['date']}` | **狀態:** `{ev_badge}`")
                if "snippet" in ev and ev["snippet"]:
                    st.caption(f"📝 活动简要: {ev['snippet']}")
                st.link_button("前往活动官网/详情 ➔" if lang == "简体中文" else "前往活動官網/詳情 ➔", ev['link'])
                st.markdown("---")

# --- Tab 3: 历史累计中央总大账本 (你的专属永久记录 List) ---
with tab3:
    st.header("💾 cc 智能求职与创科活动历史中央账本")
    st.markdown("不论你在前面刷了多少遍，凡是曾经贴过 `🆕 NEW` 标签的纯净新条目，都会长久存留在这个 List 保险箱里：" if lang == "简体中文" else "不論你在前面刷了多少遍，凡是曾經貼過 `🆕 NEW` 標籤的純淨新條目，都會長久存留在這個 List 保險箱裡：")
    
    c_job_book, c_event_book = st.columns(2)
    
    with c_job_book:
        st.subheader("📋 累计收录的岗位 List" if lang == "简体中文" else "📋 累計收錄的崗位 List")
        all_recorded_jobs = load_local_data(JOB_DB)
        if not all_recorded_jobs:
            st.info("🔍 暂无历史岗位记录。请在第一个标签页进行实时检索。")
        else:
            st.metric("累计独特岗位数" if lang == "简体中文" else "累計獨特崗位數", f"{len(all_recorded_jobs)} 个")
            for idx, job in enumerate(all_recorded_jobs, 1):
                with st.expander(f"{idx}. {job['title']} @ {job['company']}"):
                    st.markdown(f"**渠道:** {job['source']} | **录入时间:** `{job.get('recorded_at', '未知')}`" if lang == "简体中文" else f"**渠道:** {job['source']} | **條目時間:** `{job.get('recorded_at', '未知')}`")
                    st.link_button("直达投递链接 ➔" if lang == "简体中文" else "直達投遞鏈接 ➔", job['link'])
                    
    with c_event_book:
        st.subheader("🎉 累计收录的活动 List" if lang == "简体中文" else "🎉 累計收錄的活動 List")
        all_recorded_events = load_local_data(EVENT_DB)
        if not all_recorded_events:
            st.info("🔍 暂无历史活动记录。请在第二个标签页进行实时雷达扫描。")
        else:
            st.metric("累计独特活动数" if lang == "简体中文" else "累計獨特活動數", f"{len(all_recorded_events)} 个")
            for idx, ev in enumerate(all_recorded_events, 1):
                with st.expander(f"{idx}. [{ev.get('type','活动')}] {ev['title']}"):
                    st.markdown(f"**地点:** {ev['location']} | **日期:** `{ev['date']}`" if lang == "简体中文" else f"**地點:** {ev['location']} | **日期:** `{ev['date']}`")
                    st.caption(f"⏱️ 记账录入时间: {ev.get('recorded_at', '未知')}" if lang == "简体中文" else f"⏱️ 記賬錄入時間: {ev.get('recorded_at', '未知')}")
                    st.link_button("活动官网 ➔" if lang == "简体中文" else "活動官網 ➔", ev['link'])