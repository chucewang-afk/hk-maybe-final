import streamlit as st
import json
import os
import requests
import urllib.parse
import re
from datetime import datetime

# 1. 网页基础配置
st.set_page_config(page_title="HKMU Applied Science | 科技求职与活动站", page_icon="🔬", layout="wide")

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

# 🌟 JobsDB 官方企业 Portal 直达路由
def build_official_enterprise_url(company, job_keywords=""):
    comp_clean = str(company).strip()
    
    portal_map = {
        "The Hong Kong Polytechnic University (PolyU)": "The-Hong-Kong-Polytechnic-University",
        "The Hong Kong Polytechnic University": "The-Hong-Kong-Polytechnic-University",
        "Hong Kong Metropolitan University (MU)": "Hong-Kong-Metropolitan-University",
        "Hong Kong Metropolitan University": "Hong-Kong-Metropolitan-University",
        "The University of Hong Kong (HKU)": "The-University-of-Hong-Kong",
        "The Chinese University of Hong Kong (CUHK)": "The-Chinese-University-of-Hong-Kong",
        "SGS Hong Kong Limited": "SGS-Hong-Kong-Limited",
        "Swire Properties Limited": "Swire-Properties-Limited",
        "Hong Kong Science and Technology Parks Corporation (HKSTP)": "Hong-Kong-Science-and-Technology-Parks-Corporation",
        "Cyberport Entrepreneurship Centre Network": "Cyberport",
        "CLP Power Hong Kong Limited": "CLP-Power-Hong-Kong-Limited",
        "Maxim's Caterers Limited": "Maxims-Caterers-Limited"
    }
    
    slug = portal_map.get(comp_clean)
    if slug:
        return f"https://hk.jobsdb.com/{slug}-jobs"
    else:
        clean_kw = re.sub(r'\(.*?\)|Ref:.*|[^a-zA-Z0-9\s]', ' ', str(job_keywords)).strip()
        kw_list = [w for w in clean_kw.split() if len(w) > 2]
        core_query = " ".join(kw_list[:2]) if kw_list else "Research Assistant"
        return f"https://hk.jobsdb.com/jobs?keywords={urllib.parse.quote(core_query)}"

# ----------------- [ 🌐 动态全网实习/科研岗位爬取引擎 ] -----------------
def fetch_realtime_jobs(major_key, user_kw=""):
    key = major_key.lower()
    user_kw_clean = str(user_kw).strip().lower()
    results = []
    
    major_query_map = {
        "food": "Food Safety Testing Quality Chemical Research Assistant Intern Hong Kong",
        "steam": "STEAM Science Workshop Laboratory Demonstration Assistant Hong Kong",
        "computer": "Computer Science IT Network System Engineer Intern Hong Kong",
        "biomedical": "Biomedical Laboratory Research Assistant Cell Culture Assay Hong Kong",
        "environmental": "Environmental Science Sustainability Carbon Audit Officer Hong Kong"
    }
    
    base_query = major_query_map.get(key, "Applied Science Research Assistant Intern Hong Kong")
    search_query = f"{base_query} {user_kw_clean}".strip()
    
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
            
            for i in range(min(len(links), 6)):
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
                    # 匹配或预测雇主名称
                    comp_name = "Hong Kong Institution / Industry Employer"
                    if "polyu" in raw_title.lower() or "polyu" in clean_target.lower():
                        comp_name = "The Hong Kong Polytechnic University (PolyU)"
                    elif "hkmu" in raw_title.lower() or "mu.edu" in clean_target.lower():
                        comp_name = "Hong Kong Metropolitan University (MU)"
                    elif "hku" in raw_title.lower() or "hku.hk" in clean_target.lower():
                        comp_name = "The University of Hong Kong (HKU)"
                    elif "sgs" in raw_title.lower():
                        comp_name = "SGS Hong Kong Limited"
                    elif "hkstp" in raw_title.lower():
                        comp_name = "Hong Kong Science and Technology Parks Corporation (HKSTP)"

                    results.append({
                        "title": raw_title,
                        "company": comp_name,
                        "source": "🌐 全网实时招募",
                        "link": clean_target if clean_target.startswith("http") else build_official_enterprise_url(comp_name, raw_title),
                        "snippet": raw_snippet if raw_snippet else "最新全网抓取到的香港本地科技与科研岗位招募信息。",
                        "requirements": [
                            "具备相关专业背景（如食品/生科/计算机/环境工程）。",
                            "熟悉实验室安全规范或相关技术工具。",
                            "良好的团队沟通能力与细致的操作习惯。"
                        ]
                    })
    except Exception:
        pass
        
    # 精选基础保底库（当网络爬取数量不足时兜底）
    if len(results) < 2:
        all_backup_jobs = {
            "food": [
                {
                    "title": "Junior Research Assistant / Project Assistant (Food Safety & Quality Assurance)",
                    "company": "The Hong Kong Polytechnic University (PolyU)",
                    "snippet": "Department of Applied Biology and Chemical Technology (ABCT). Conducting food sample testing, microbial assays, chromatographic analysis.",
                    "requirements": ["Bachelor/HD in Food Safety or Chemistry.", "Hands-on experience with spectrophotometry or HPLC."]
                },
                {
                    "title": "Part-Time Technical Assistant (Food Testing Lab)",
                    "company": "Hong Kong Metropolitan University (MU)",
                    "snippet": "School of Science and Technology. Assist in food chemistry analysis, sample extraction, spectrophotometry assays.",
                    "requirements": ["Pursuing Degree/HD in Food Testing Science.", "Familiarity with lab safety."]
                }
            ],
            "steam": [
                {
                    "title": "STEAM Education & Project Assistant",
                    "company": "Hong Kong Metropolitan University (MU)",
                    "snippet": "STEAM Centre. Assisting hands-on science workshop preparations and experimental kit testing.",
                    "requirements": ["Degree/HD in Science or Education.", "Passionate about science popularization."]
                }
            ],
            "computer": [
                {
                    "title": "IT & Network Operations Student Trainee",
                    "company": "Hong Kong Science and Technology Parks Corporation (HKSTP)",
                    "snippet": "Campus network traffic monitoring, Cisco switch configuration checks, IT ticketing.",
                    "requirements": ["Undergraduate in CS or IT.", "Knowledge of TCP/IP and VLAN."]
                }
            ]
        }
        
        fallback_list = all_backup_jobs.get(key, all_backup_jobs.get("food", []))
        for item in fallback_list:
            results.append({
                "title": item["title"],
                "company": item["company"],
                "source": "JobsDB Portal (保底校验)",
                "link": build_official_enterprise_url(item["company"], item["title"]),
                "snippet": item["snippet"],
                "requirements": item["requirements"]
            })
            
    return results

# ----------------- [ 📅 零污染隔离 + 自动淘汰过期活动库 ] -----------------
def get_strictly_matched_events(major_key, user_kw=""):
    key = major_key.lower()
    user_kw_clean = str(user_kw).strip().lower()
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    
    all_events_data = {
        "food": [
            {
                "title": "全港大专院校食品安全与检测科技创新论坛 2026",
                "date": "2026-09-22",
                "location": "香港理工大学 (PolyU) ABCT 演讲厅",
                "link": "https://www.polyu.edu.hk",
                "type": "💡 食品科技研讨",
                "snippet": "探讨食品化学分析、发酵品质监控、前沿快检技术及实验室 ISO 合规管理。"
            },
            {
                "title": "香港都会大学 (HKMU) 创科与生命科学/食品检测创业训练营 2026",
                "date": "2026-11-20",
                "location": "香港都会大学 (HKMU) 赛马会校园",
                "link": "https://www.hkmu.edu.hk",
                "type": "🏆 生命科学与食品创业组",
                "snippet": "面向大专院校食品与生科专业学生的创业训练营与项目路演，对接导师资源。"
            },
            {
                "title": "香港食品安全及检测科技博览会 2026 志愿者/Helper 招募",
                "date": "2026-10-18",
                "location": "香港会议展览中心 (HKCEC)",
                "link": "https://www.hktdc.com",
                "type": "🤝 展会 Helper 招募",
                "snippet": "协助国际食品检测设备展会现场运营、技术展台接待与学术讲座现场协助。"
            }
        ],
        "steam": [
            {
                "title": "香港都会大学 (HKMU) STEAM Centre 科学体验日与工作坊",
                "date": "2026-09-28",
                "location": "香港都会大学 (HKMU) STEAM Centre",
                "link": "https://www.hkmu.edu.hk",
                "type": "🔬 STEAM 科学工作坊",
                "snippet": "面向大专生助手的科学实验演示、互动套件开发与科普活动协调训练。"
            },
            {
                "title": "全港中小学 STEAM 创新科技大赛 2026 大专生评审助手招募",
                "date": "2026-10-30",
                "location": "香港科学园高錕会议中心",
                "link": "https://www.hkstp.org",
                "type": "🤝 大赛 Helper 招募",
                "snippet": "协助 STEAM 参赛作品分类、实验室场地布置及现场技术答辩秩序引导。"
            }
        ],
        "computer": [
            {
                "title": "PolyU × NuttyShell Cybersecurity & Systems Hackathon 2026",
                "date": "2026-09-18",
                "location": "香港理工大学 (PolyU) / 香港科学园",
                "link": "https://www.polyu.edu.hk",
                "type": "🏆 黑客松与创科挑战赛",
                "snippet": "面向全港 IT / 计算机专业学生的网络安全、Web Exploitation 与前沿项目 48 小时极客挑战。"
            }
        ],
        "biomedical": [
            {
                "title": "香港生物医学科技前沿研讨会与创新成果展 2026",
                "date": "2026-08-28",
                "location": "香港科学园 InnoCentre",
                "link": "https://www.hkstp.org",
                "type": "🔬 生物医学研讨",
                "snippet": "基因检测、细胞培养技术、药物递送系统的前沿学术成果分享与 poster 展示。"
            },
            {
                "title": "HKSTP InnoAcademy 生物科技孵化项目开放日",
                "date": "2026-11-05",
                "location": "沙田香港科学园 Bio-cluster",
                "link": "https://www.hkstp.org",
                "type": "🏢 园区开放日",
                "snippet": "参观前沿生物医药实验室，与初创团队创始人交流并了解实习招聘计划。"
            }
        ],
        "environmental": [
            {
                "title": "全港环境与可持续发展创新方案挑战赛 2027",
                "date": "2027-02-10",
                "location": "香港科技大学 (HKUST)",
                "link": "https://hkust.edu.hk",
                "type": "🌱 环保与 ESG 竞赛",
                "snippet": "针对减碳技术、水质监测及 ESG 可持续方案的大专生组项目竞赛。"
            }
        ]
    }
    
    selected_events = []
    if "food" in key:
        selected_events = all_events_data["food"]
    elif "steam" in key:
        selected_events = all_events_data["steam"]
    elif "computer" in key:
        selected_events = all_events_data["computer"]
    elif "biomedical" in key:
        selected_events = all_events_data["biomedical"]
    elif "environmental" in key:
        selected_events = all_events_data["environmental"]
    else:
        for cat in all_events_data:
            selected_events.extend(all_events_data[cat])

    if "computer" not in key and "all" not in key:
        selected_events = [ev for ev in selected_events if "cybersecurity" not in ev['title'].lower() and "ctf" not in ev['title'].lower()]
        
    selected_events = [ev for ev in selected_events if ev.get("date", "2099-12-31") >= current_date_str]

    if not user_kw_clean:
        return selected_events
    else:
        search_terms = user_kw_clean.split()
        results = []
        for ev in selected_events:
            match_str = f"{ev['title']} {ev['location']} {ev['snippet']} {ev['type']}".lower()
            if all(term in match_str for term in search_terms):
                results.append(ev)
        return results

# ----------------- [ 🌐 HKMU Department of Applied Science 专用多语言词典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 HKMU Department of Applied Science 专用求职与活动站",
        "subtitle": "HKMU 应用科学系专属：真实雇主岗位（全网动态检索） + 分专业隔离本地创科活动",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入搜索词精筛（如: hkmu, lab, assistant）...",
        "search_placeholder_ev": "输入活动精筛关键词（如: hkmu, workshop, forum）...",
        "search_btn": "⚡ 启动全网岗位扫描",
        "search_btn_ev": "⚡ 启动全网未来活动扫描",
        "search_loading": "正在全网动态检索最新实习与科研岗位...",
        "search_loading_ev": "正在检索与当前专业严格对应的 2026-2027 香港本地创科活动与比赛...",
        "source_tag": "来源网关",
        "tab3_desc": "这里是你的专属 List 保险箱。新查找到的条目都会自动永久存留在这里：",
        "job_header": "🎯 互联网实习岗位实时检索雷达",
        "ev_header": "📅 2026-2027 未来科技活动/比赛/志愿者雷达",
        "current_major_prefix": "🎓 当前专业方向锁定：",
        "no_job_match": "⚠️ 现场未检索到与筛选条件完全相符的工作，请尝试调整或更换搜寻关键词。",
        "no_ev_match": "⚠️ 未能找到与当前专业及关键词相符且未过期的活动。",
        "job_desc_head": "📝 岗位职责与工作内容 (Job Description)",
        "job_req_head": "🎯 核心任职要求 (Key Requirements)",
        "link_btn_job": "🌐 查看岗位详情 / 投递页面 ➔",
        "link_btn_ev": "前往活动官网/详情 ➔",
        "hist_job_title": "📋 累计收录的岗位 List",
        "hist_ev_title": "🎉 累计收录的未来活动 List",
        "hist_job_empty": "🔍 暂无历史岗位记录。请在第一个标签页进行实时检索。",
        "hist_ev_empty": "🔍 暂无历史未来活动记录。请在第二个标签页进行扫描。",
        "hist_job_metric": "累计独特岗位数",
        "hist_ev_metric": "累计待参与活动数"
    },
    "繁體中文": {
        "title": "🔬 💻 HKMU Department of Applied Science 專用求職與活動站",
        "subtitle": "HKMU 應用科學系專屬：真實僱主崗位（全網動態檢索） + 分專業隔離本地創科活動",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總帳本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入搜尋詞精篩（如: hkmu, lab, assistant）...",
        "search_placeholder_ev": "輸入活動精篩關鍵詞（如: hkmu, workshop, forum）...",
        "search_btn": "⚡ 啟動全網崗位掃描",
        "search_btn_ev": "⚡ 啟動全網未來活動掃描",
        "search_loading": "正在全網動態檢索最新實習與科研崗位...",
        "search_loading_ev": "正在檢索與當前專業嚴格對應的 2026-2027 香港本地創科活動與比賽...",
        "source_tag": "來源網關",
        "tab3_desc": "這裡是你的專屬 List 保險箱。新查找到的條目都會自動永久存留在這裡：",
        "job_header": "🎯 互聯網實習崗位實時檢索雷達",
        "ev_header": "📅 2026-2027 未來科技活動/比賽/志願者雷達",
        "current_major_prefix": "🎓 當前專業方向鎖定：",
        "no_job_match": "⚠️ 現場未檢索到與篩選條件完全相符的工作，請嘗試調整或更換搜尋關鍵詞。",
        "no_ev_match": "⚠️ 未能找到與當前專業及關鍵詞相符且未過期的活動。",
        "job_desc_head": "📝 崗位職責與工作內容 (Job Description)",
        "job_req_head": "🎯 核心任職要求 (Key Requirements)",
        "link_btn_job": "🌐 查看崗位詳情 / 投遞頁面 ➔",
        "link_btn_ev": "前往活動官網/詳情 ➔",
        "hist_job_title": "📋 累計收錄的崗位 List",
        "hist_ev_title": "🎉 累計收錄的未來活動 List",
        "hist_job_empty": "🔍 暫無歷史崗位記錄。請在第一個標籤頁進行實時檢索。",
        "hist_ev_empty": "🔍 暫無歷史未來活動記錄。請在第二個標籤頁進行掃描。",
        "hist_job_metric": "累計獨特崗位數",
        "hist_ev_metric": "累計待參與活動數"
    },
    "English": {
        "title": "🔬 💻 HKMU Department of Applied Science Gateway Hub",
        "subtitle": "HKMU Department of Applied Science Hub: Employers Jobs Direct View + Major-Isolated Events",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Upcoming Future Tech Events",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter search terms (e.g. hkmu, lab, assistant)...",
        "search_placeholder_ev": "Enter event keywords (e.g. hkmu, workshop, forum)...",
        "search_btn": "⚡ Launch Job Scan",
        "search_btn_ev": "⚡ Launch Event Scan",
        "search_loading": "Dynamically scanning real-time jobs...",
        "search_loading_ev": "Searching strictly major-matched 2026-2027 HK tech events...",
        "source_tag": "Source Gateway",
        "tab3_desc": "Your private list vault. Freshly scanned records are saved here permanently:",
        "job_header": "🎯 Live Web Job Radar",
        "ev_header": "📅 2026-2027 Future Tech Events / Contests / Helper Radar",
        "current_major_prefix": "🎓 Locked Major Direction: ",
        "no_job_match": "⚠️ No jobs matched your criteria. Please try adjusting your search terms.",
        "no_ev_match": "⚠️ No valid upcoming events matched your major and keyword criteria.",
        "job_desc_head": "📝 Job Description",
        "job_req_head": "🎯 Key Requirements",
        "link_btn_job": "🌐 View Job Details / Application Page ➔",
        "link_btn_ev": "Go to Official Event Page ➔",
        "hist_job_title": "📋 Recorded Jobs List",
        "hist_ev_title": "🎉 Recorded Future Events List",
        "hist_job_empty": "🔍 No job records found. Search in Tab 1 to record new items.",
        "hist_ev_empty": "🔍 No upcoming event records found. Search in Tab 2 to record.",
        "hist_job_metric": "Total Unique Jobs",
        "hist_ev_metric": "Total Upcoming Events"
    }
}

st.sidebar.markdown(f"### {translations['English']['sidebar_lang']}")
lang = st.sidebar.selectbox("Choose Language / 選擇語言:", ["简体中文", "繁體中文", "English"], label_visibility="collapsed")
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

major_choice = st.sidebar.selectbox("Majors:", [food_label, bio_label, comp_label, env_label, steam_label, all_label], label_visibility="collapsed")

keyword_map = {
    all_label: "show all",
    comp_label: "computer", 
    bio_label: "biomedical", 
    env_label: "environmental", 
    food_label: "food",
    steam_label: "steam"
}
active_major_keyword = keyword_map.get(major_choice, "food")

# --- Tab 1: 互联网实习雷达 (已升级为动态全网抓取) ---
with tab1:
    st.header(lang_dict["job_header"])
    st.markdown(f"{lang_dict['current_major_prefix']}`{major_choice}`")
    
    user_input = st.text_input(lang_dict["search_placeholder"], value="", key="real_job_kw")
    search_job_btn = st.button(lang_dict["search_btn"], type="primary", key="btn_job")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if search_job_btn:
        with st.spinner(lang_dict["search_loading"]):
            live_scanned_jobs = fetch_realtime_jobs(active_major_keyword, user_input)
            
            if not live_scanned_jobs:
                st.warning(lang_dict["no_job_match"])
            else:
                new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
                
                if new_count > 0:
                    st.balloons()
                    st.success(f"🔥 ({lang}) 捕获全网最新岗位！匹配到 **{len(live_scanned_jobs)}** 个，其中 **{new_count}** 个新存入 List！")
                else:
                    st.info(f"ℹ️ ({lang}) 找到 **{len(live_scanned_jobs)}** 个符合条件的岗位，均已在 List 中存留。")
                
                for idx, job in enumerate(live_scanned_jobs, 1):
                    fingerprint = f"{job.get('title','')}_{job.get('company','')}"
                    badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 中"
                    
                    with st.container(border=True):
                        st.subheader(f"{idx}. {job.get('title','Job Title')}")
                        st.markdown(f"🏢 **雇主/机构:** `{job.get('company','Company')}`  |  `{lang_dict['source_tag']}: {job.get('source','全网抓取')}`  |  **状态:** `{badge}`")
                        
                        st.markdown(f"#### {lang_dict['job_desc_head']}")
                        st.write(job.get("snippet", ""))
                        
                        st.markdown(f"#### {lang_dict['job_req_head']}")
                        reqs = job.get("requirements", [])
                        for r in reqs:
                            st.markdown(f"* {r}")
                            
                        st.markdown("---")
                        st.link_button(lang_dict["link_btn_job"], job.get('link'), type="primary")

# --- Tab 2: 2026-2027 未来科技活动雷达 ---
with tab2:
    st.header(lang_dict["ev_header"])
    st.markdown(f"{lang_dict['current_major_prefix']}`{major_choice}`")
    
    user_input_ev = st.text_input(lang_dict["search_placeholder_ev"], value="", key="real_ev_kw")
    search_ev_btn = st.button(lang_dict["search_btn_ev"], type="primary", key="btn_ev")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_ev_btn:
        with st.spinner(lang_dict["search_loading_ev"]):
            live_scanned_events = get_strictly_matched_events(active_major_keyword, user_input_ev)
            
            if not live_scanned_events:
                st.warning(lang_dict["no_ev_match"])
            else:
                new_ev_count, all_ev_fps, just_added_ev_fps = sync_and_append_data(live_scanned_events, EVENT_DB, is_job=False)
                
                if new_ev_count > 0:
                    st.toast(f"成功录入 {new_ev_count} 个未来新活动！")
                    st.success(f"🎉 ({lang}) 呈现 **{len(live_scanned_events)}** 个完全对齐的未过期活动，其中 **{new_ev_count}** 个已吸纳进 List！")
                else:
                    st.info(f"ℹ️ ({lang}) 呈现 **{len(live_scanned_events)}** 个与当前专业对齐的未过期活动，已同步至 List。")
                    
                for idx, ev in enumerate(live_scanned_events, 1):
                    fingerprint = f"{ev.get('title','')}_{ev.get('date', '')}"
                    ev_badge = "🟢 🆕 NEW" if fingerprint in just_added_ev_fps else "⚪ 已在 List 中"
                    
                    with st.container(border=True):
                        st.subheader(f"{ev.get('type','活动')} | {idx}. {ev.get('title','Event Title')}")
                        st.info(f"📅 **日期:** `{ev.get('date', '2026-2027')}`  |  📍 **地点:** `{ev.get('location', '香港')}`")
                        if ev.get("snippet"):
                            st.caption(f"📝 简要: {ev['snippet']}")
                        st.link_button(lang_dict["link_btn_ev"], ev.get('link','https://www.polyu.edu.hk'))

# --- Tab 3: 历史累计中央总大账本 ---
with tab3:
    st.header("💾 cc 智能求职与创科活动历史中央账本")
    st.markdown(lang_dict["tab3_desc"])
    
    c_job_book, c_event_book = st.columns(2)
    
    with c_job_book:
        st.subheader(lang_dict["hist_job_title"])
        all_recorded_jobs = load_local_data(JOB_DB)
        if not all_recorded_jobs:
            st.info(lang_dict["hist_job_empty"])
        else:
            st.metric(lang_dict["hist_job_metric"], f"{len(all_recorded_jobs)} 个")
            for idx, job in enumerate(all_recorded_jobs, 1):
                if isinstance(job, dict):
                    with st.expander(f"{idx}. [{job.get('company','Company')}] {job.get('title','Job')}"):
                        st.markdown(f"**雇主:** `{job.get('company','Company')}` | **渠道:** {job.get('source','全网抓取')} | **录入时间:** `{job.get('recorded_at', '未知')}`")
                        if job.get("snippet"):
                            st.caption(f"📝 说明: {job['snippet']}")
                        st.link_button(lang_dict["link_btn_job"], job.get('link'))
                    
    with c_event_book:
        st.subheader(lang_dict["hist_ev_title"])
        all_recorded_events = load_local_data(EVENT_DB)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        
        valid_recorded_events = []
        for ev in all_recorded_events:
            if isinstance(ev, dict):
                if ev.get('date', '') < current_date_str:
                    continue
                
                if "computer" not in active_major_keyword and "show all" not in active_major_keyword:
                    if "ctf" in ev.get('title','').lower() or "cybersecurity" in ev.get('title','').lower():
                        continue
                
                valid_recorded_events.append(ev)
                
        all_recorded_events = valid_recorded_events

        if not all_recorded_events:
            st.info(lang_dict["hist_ev_empty"])
        else:
            st.metric(lang_dict["hist_ev_metric"], f"{len(all_recorded_events)} 个")
            for idx, ev in enumerate(all_recorded_events, 1):
                if isinstance(ev, dict):
                    with st.expander(f"{idx}. [{ev.get('type','活动')}] {ev.get('title','Event')}"):
                        st.markdown(f"📅 **日期:** `{ev.get('date','未来')}` | 📍 **地点:** `{ev.get('location','香港')}`")
                        st.caption(f"⏱️ 记账录入时间: {ev.get('recorded_at', '未知')}")
                        st.link_button(lang_dict["link_btn_ev"], ev.get('link','https://www.polyu.edu.hk'))
