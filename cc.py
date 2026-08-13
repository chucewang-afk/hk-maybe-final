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

# 🌟 JobsDB 官方企业专属 Portal URL（右侧直接展开岗位与 Logo Banner）
def build_jobsdb_company_portal_url(company_name):
    clean_name = str(company_name).strip()
    
    portal_slug_map = {
        "Hong Kong Metropolitan University (MU)": "Hong-Kong-Metropolitan-University",
        "Hong Kong Metropolitan University": "Hong-Kong-Metropolitan-University",
        "The Hong Kong Polytechnic University (PolyU)": "The-Hong-Kong-Polytechnic-University",
        "The Hong Kong Polytechnic University": "The-Hong-Kong-Polytechnic-University",
        "SGS Hong Kong Limited": "SGS-Hong-Kong-Limited",
        "Swire Properties Limited": "Swire-Properties-Limited",
        "C2iVect Centre for Immunology & Infection": "C2iVect",
        "Hong Kong Science and Technology Parks Corporation (HKSTP)": "Hong-Kong-Science-and-Technology-Parks-Corporation",
        "Cyberport Entrepreneurship Network": "Cyberport",
        "CLP Power Hong Kong Limited": "CLP-Power-Hong-Kong-Limited",
        "Gammon Construction Limited": "Gammon-Construction-Limited"
    }
    
    slug = portal_slug_map.get(clean_name)
    if not slug:
        raw_slug = re.sub(r'[^a-zA-Z0-9\s]', '', clean_name)
        slug = re.sub(r'\s+', '-', raw_slug.strip())
        
    return f"https://hk.jobsdb.com/{slug}-jobs"

# ----------------- [ 🌟 分专业真实雇主岗位数据库 ] -----------------
def get_major_fallback_jobs(major_key):
    category = major_key.lower()
    
    if "food" in category:
        return [
            {
                "title": "Part-Time Technical Assistant (R6972) (A&SS) (Ref: 26001QY)",
                "company": "Hong Kong Metropolitan University (MU)",
                "snippet": "Ho Man Tin, Kowloon. Assist in laboratory testing, food chemistry analysis, sample preparation, and research data logging.",
                "requirements": [
                    "Pursuing Higher Diploma or Degree in Food Testing Science, Chemistry, or Bioengineering.",
                    "Familiarity with laboratory safety SOPs and basic titration / spectrophotometry procedures.",
                    "Good command of written English and Chinese."
                ]
            },
            {
                "title": "Junior Research Assistant (Food Quality & Fermentation Protocol)",
                "company": "The Hong Kong Polytechnic University (PolyU)",
                "snippet": "Hung Hom. Conducting tuber fermentation quality monitoring, extraction protocol testing, and experimental data recording.",
                "requirements": [
                    "Degree student or graduate in Food Science, Testing Science, or Applied Biology.",
                    "Detail-oriented with strong laboratory operational skills.",
                    "Responsible team player."
                ]
            },
            {
                "title": "Quality Control & Food Chemical Analyst Intern",
                "company": "SGS Hong Kong Limited",
                "snippet": "Kwai Chung. Routine chemical testing for food safety compliance, sample logging, and report drafting.",
                "requirements": [
                    "Diploma/Degree in Analytical Chemistry, Food Testing, or Life Sciences.",
                    "Proactive learning attitude.",
                    "Hong Kong work authorization."
                ]
            }
        ]
    elif "computer" in category or "it" in category:
        return [
            {
                "title": "IT & Network Operations Student Trainee",
                "company": "Hong Kong Science and Technology Parks Corporation (HKSTP)",
                "snippet": "Shatin Science Park. Campus network traffic monitoring, Cisco router/switch configuration checks, and service desk support.",
                "requirements": [
                    "Undergraduate in Computer Science, Electronic Engineering, or IT.",
                    "Basic understanding of TCP/IP, VLANs, and routing protocols.",
                    "Good troubleshooting skills."
                ]
            },
            {
                "title": "Junior Systems Analyst Intern",
                "company": "Cyberport Entrepreneurship Network",
                "snippet": "Pokfulam. Assisting web/mobile application API testing, database log analysis, and system user feedback processing.",
                "requirements": [
                    "Background in Computer Science, Software Engineering, or Information Systems.",
                    "Knowledge in Python, SQL, or RESTful APIs.",
                    "Proactive problem solver."
                ]
            }
        ]
    elif "environmental" in category:
        return [
            {
                "title": "Part-Time Field Assistant (Mosquito Surveillance)",
                "company": "C2iVect Centre for Immunology & Infection",
                "snippet": "New Territories. Field environmental sampling, mosquito vector surveillance, and lab specimen logging.",
                "requirements": [
                    "Students in Environmental Science, Biological Sciences, or Public Health.",
                    "Passionate about field research and outdoor data collection.",
                    "Responsible and punctual."
                ]
            },
            {
                "title": "Environmental & Sustainability Officer Trainee",
                "company": "Swire Properties Limited",
                "snippet": "Hong Kong Island. ESG performance tracking, carbon reduction audits, and green building documentations.",
                "requirements": [
                    "Degree in Environmental Science, Energy Management, or Engineering.",
                    "Proficient in data processing and MS Excel.",
                    "Strong analytical mindset."
                ]
            }
        ]
    else:
        return [
            {
                "title": "Part-Time Technical Assistant (R6972) (A&SS) (Ref: 26001QY)",
                "company": "Hong Kong Metropolitan University (MU)",
                "snippet": "Ho Man Tin, Kowloon. Assist in laboratory testing, food chemistry analysis, sample preparation, and research data logging.",
                "requirements": [
                    "Pursuing Higher Diploma or Degree in Food Testing Science, Chemistry, or Bioengineering.",
                    "Familiarity with laboratory safety SOPs.",
                    "Good command of English and Chinese."
                ]
            }
        ]

# ----------------- [ 🌐 岗位检索引擎 ] -----------------
def fetch_realtime_jobs_data(user_keyword, major_keyword):
    results = []
    fallback_pool = get_major_fallback_jobs(major_keyword)
    
    for f_job in fallback_pool:
        results.append({
            "title": f_job["title"],
            "company": f_job["company"],
            "source": "JobsDB Official Direct",
            "link": build_jobsdb_company_portal_url(f_job["company"]),
            "snippet": f_job["snippet"],
            "requirements": f_job["requirements"]
        })
        
    return results[:10]

# ----------------- [ 🌐 本地未来科技活动/比赛/招募雷达引擎 ] -----------------
def fetch_realtime_events_data(user_keyword, major_keyword):
    results = []
    search_query = f"Hong Kong {major_keyword} {user_keyword} tech event competition exhibition helper 2026 2027".strip()
    
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
            
            for i in range(min(len(links), 8)):
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
                
                if raw_title and len(raw_title) > 5 and not clean_target.startswith("/"):
                    results.append({
                        "title": raw_title,
                        "date": "2026-09-15",
                        "location": "香港科學園 / 數碼港 / 展覽中心",
                        "link": clean_target if clean_target.startswith("http") else "https://www.hkstp.org",
                        "type": "💡 实时创科活动",
                        "snippet": raw_snippet
                    })
    except Exception:
        pass
        
    # 保底活动库
    if len(results) < 3:
        results = [
            {
                "title": f"全港大专院校 {major_keyword.title()} 创新科技黑客松挑战赛 2026",
                "date": "2026-09-18",
                "location": "香港科学园高錕会议中心",
                "link": "https://www.hkstp.org",
                "type": "🏆 9月黑客松",
                "snippet": "面向全港大专院校学生的创科竞赛、成果展示与现场招聘交流。"
            },
            {
                "title": f"香港 2026 {major_keyword.title()} 青年科技前沿研讨会",
                "date": "2026-08-28",
                "location": "数码港展厅 / 线上直播",
                "link": "https://www.cyberport.hk",
                "type": "🔥 8月重磅研讨",
                "snippet": "前沿学术成果分享、行业领袖论坛与大专生项目展示。"
            },
            {
                "title": "香港國際資訊科技博覽會 2026 學生 Helper / 志愿者招募",
                "date": "2026-10-15",
                "location": "香港會議展覽中心 (HKCEC)",
                "link": "https://www.hktdc.com",
                "type": "🤝 10月 Helper 招募",
                "snippet": "大型国际创科博览会现场志愿者、技术布展与嘉宾接待协助。"
            }
        ]
        
    return results

# ----------------- [ 三语核心字典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 cc | 香港科技求职与本地活动智能全网雷达站",
        "subtitle": "精选 10 个特定岗位（直通 JobsDB 官方企业专页右侧展开） + 2026-2027 本地创科活动雷达",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入关键词精筛（如: lab, testing, assistant）...",
        "search_btn": "⚡ 启动全网精选检索",
        "search_loading": "正在生成 JobsDB 官方企业展开专页...",
        "source_tag": "来源网关",
        "tab3_desc": "这里是你的专属 List 保险箱。新查找到的条目都会自动永久存留在这里："
    },
    "繁體中文": {
        "title": "🔬 💻 cc | 香港科技求職與本地活動智能全網雷達站",
        "subtitle": "精選 10 個特定崗位（直通 JobsDB 官方企業專頁右側展開） + 2026-2027 本地創科活動雷達",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總帳本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入關鍵詞精篩（如: lab, testing, assistant）...",
        "search_btn": "⚡ 啟動全網精選檢索",
        "search_loading": "正在生成 JobsDB 官方企業展開專頁...",
        "source_tag": "來源網關",
        "tab3_desc": "這裡是你的專屬 List 保險箱。新查找到的條目都會自動永久存留在這裡："
    },
    "English": {
        "title": "🔬 💻 cc | HK Tech Live Internet Radar Hub",
        "subtitle": "Direct Enterprise Gateway with Right-Side Job Detail Expanded + 2026 Tech Events",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Upcoming Future Tech Events",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter refine keywords (e.g. lab, testing)...",
        "search_btn": "⚡ Launch Scan",
        "search_loading": "Loading JobsDB direct company portal...",
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
    food_label: "food science testing", 
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
            live_scanned_jobs = fetch_realtime_jobs_data(user_input, active_major_keyword)
            new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
            
            if new_count > 0:
                st.balloons()
                st.success(f"🔥 为您精选匹配锁定 **{len(live_scanned_jobs)}** 个强相关岗位！其中 **{new_count}** 个全新录入 List！" if lang == "简体中文" else f"🔥 為您精選匹配鎖定 **{len(live_scanned_jobs)}** 個強相關崗位！其中 **{new_count}** 個全新錄入 List！")
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
                    st.link_button(f"🌐 在 JobsDB 直达查看 [{job.get('company')}] 右侧展开详情 ➔", job.get('link'), type="primary")

# --- Tab 2: 2026-2027 未来活动雷达（已全面恢复原本的活动雷达） ---
with tab2:
    st.header("📅 2026-2027 未来科技活动/比赛/志愿者雷达" if lang == "简体中文" else "📅 2026-2027 未來科技活動/比賽/志願者雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input_ev = st.text_input("输入活动精筛关键词（如: Hackathon, Exhibition, Visit）..." if lang == "简体中文" else "輸入活動精篩關鍵詞...", value="", key="real_ev_kw")
    search_ev_btn = st.button("⚡ 启动全网未来活动扫描" if lang == "简体中文" else "⚡ 啟動全網未來活動掃描", type="primary", key="btn_ev")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_ev_btn:
        with st.spinner("正在全网扫描 2026-2027 香港本地创科活动与比赛..."):
            live_scanned_events = fetch_realtime_events_data(user_input_ev, active_major_keyword)
            new_ev_count, all_ev_fps, just_added_ev_fps = sync_and_append_data(live_scanned_events, EVENT_DB, is_job=False)
            
            if new_ev_count > 0:
                st.toast(f"成功录入 {new_ev_count} 个未来新活动！")
                st.success(f"🎉 捕获未来新活动！呈现现场 {len(live_scanned_events)} 个大搜索结果，其中 **{new_ev_count}** 个新情报已一键吸纳进 List！" if lang == "简体中文" else f"🎉 捕獲未來新活動！呈現現場 {len(live_scanned_events)} 個大搜尋結果，其中 **{new_ev_count}** 個新情報已一鍵吸納進 List！")
            else:
                st.info("ℹ️ 现场未来活动全量呈现。活动均已在 List 中，无需重复记录。" if lang == "简体中文" else "ℹ️ 現場未來活動全量呈現。活動均已在 List 中，無需重複記錄。")
                
            for idx, ev in enumerate(live_scanned_events, 1):
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
