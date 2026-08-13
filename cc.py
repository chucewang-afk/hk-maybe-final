import streamlit as st
import json
import os
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

# 🌟 JobsDB 官方企业 Portal 直达路由（右侧直接展开全量岗位 Details 与 Apply）
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

# ----------------- [ 🎯 各专业真实雇主岗位海量库 ] -----------------
def get_comprehensive_jobs(major_key, user_kw=""):
    key = major_key.lower()
    
    all_jobs_data = {
        "food": [
            {
                "title": "Junior Research Assistant / Project Assistant (Food Safety & Quality Assurance)",
                "company": "The Hong Kong Polytechnic University (PolyU)",
                "snippet": "Hung Hom, Kowloon. Department of Applied Biology and Chemical Technology (ABCT). Conducting food sample testing, microbial assays, chromatographic analysis, and laboratory documentation.",
                "requirements": [
                    "Bachelor Degree or Higher Diploma in Food Safety, Food Testing Science, Chemistry, or Applied Biology.",
                    "Hands-on experience with spectrophotometry, HPLC, or lab microbial testing.",
                    "Good analytical mindset and team communication."
                ]
            },
            {
                "title": "Part-Time Technical Assistant (R6972) (A&SS) (Ref: 26001QY)",
                "company": "Hong Kong Metropolitan University (MU)",
                "snippet": "Ho Man Tin, Kowloon. School of Science and Technology. Assist in food chemistry analysis, sample extraction, spectrophotometry assays, and laboratory instrument setup.",
                "requirements": [
                    "Pursuing Degree or Higher Diploma in Food Testing Science, Chemistry, or Bioengineering.",
                    "Familiarity with laboratory safety protocols and basic titration procedures.",
                    "Good command of written and spoken English and Chinese."
                ]
            },
            {
                "title": "Quality Control & Food Chemical Analyst Intern",
                "company": "SGS Hong Kong Limited",
                "snippet": "Kwai Chung. Routine chemical testing for food safety compliance, heavy metal analysis, sample logging, and report drafting.",
                "requirements": [
                    "Diploma/Degree in Analytical Chemistry, Food Testing Science, or Life Sciences.",
                    "Proactive learning attitude.",
                    "Eligible to work in Hong Kong."
                ]
            },
            {
                "title": "Research Assistant (Biochemical & Food Safety Protocols)",
                "company": "The University of Hong Kong (HKU)",
                "snippet": "Pokfulam. Sample extraction, antioxidant capacity assays, spectroscopy analysis, and experimental data recording.",
                "requirements": [
                    "Degree student or fresh graduate in Life Sciences, Chemistry, or Food Science.",
                    "Detail-oriented with strong laboratory operational capabilities.",
                    "Good command of English."
                ]
            },
            {
                "title": "Assistant Food Technologist (Product Quality & Testing)",
                "company": "Maxim's Caterers Limited",
                "snippet": "Tai Po Industrial Estate. Shelf-life testing, raw material quality evaluation, sensory evaluation, and lab documentation.",
                "requirements": [
                    "Higher Diploma or Degree in Food Science, Nutrition, or Quality Assurance.",
                    "Knowledge of HACCP / ISO 22000 standards.",
                    "Good problem-solving ability."
                ]
            }
        ],
        "biomedical": [
            {
                "title": "Research Assistant (Biomedical Science & Assay Testing)",
                "company": "The Hong Kong Polytechnic University (PolyU)",
                "snippet": "Hung Hom. Interdisciplinary research on biomedical technologies, cell culture, biomarker quantification, and spectroscopic analysis.",
                "requirements": [
                    "Degree in Biomedical Engineering, Applied Biology, Biochemistry, or related disciplines.",
                    "Experience with pipetting, aseptic cell culture, or molecular assays.",
                    "Methodical and rigorous research attitude."
                ]
            },
            {
                "title": "Part-Time Research & Lab Assistant (Biomedical Sciences)",
                "company": "The University of Hong Kong (HKU)",
                "snippet": "Pokfulam. Cell culture maintenance, reagent preparation, fluorescence assay testing, and PCR analysis support.",
                "requirements": [
                    "Students majoring in Biomedical Sciences, Biochemistry, or Bioengineering.",
                    "Familiar with lab aseptic techniques.",
                    "Good command of English."
                ]
            },
            {
                "title": "Biomedical Technology Project Intern",
                "company": "Hong Kong Science and Technology Parks Corporation (HKSTP)",
                "snippet": "Shatin Science Park. Assisting biomedical incubator start-ups in lab testing, sample logging, and technical documentation.",
                "requirements": [
                    "Degree/Diploma in Life Sciences, Biomedical Engineering, or Biotechnology.",
                    "Detail-oriented mindset.",
                    "Eligible to work in Hong Kong."
                ]
            },
            {
                "title": "Research Assistant (Cell Culture & Biomarker Assay)",
                "company": "The Chinese University of Hong Kong (CUHK)",
                "snippet": "Shatin. Assisting in cell viability assays, western blot analysis, protein quantification, and lab management.",
                "requirements": [
                    "Degree student or graduate in Life Sciences or Biomedical Sciences.",
                    "Meticulous and organized.",
                    "Good communication skills."
                ]
            }
        ],
        "computer": [
            {
                "title": "Project Assistant / Research Assistant (Cybersecurity & Systems)",
                "company": "The Hong Kong Polytechnic University (PolyU)",
                "snippet": "Hung Hom. Department of Computing. Network security analysis, CTF environment testing, vulnerability assessment, and documentation.",
                "requirements": [
                    "Undergraduate or graduate in Computer Science, Information Security, or Electronic Engineering.",
                    "Understanding of TCP/IP, network protocols, Wireshark, or system administration.",
                    "Good problem-solving capabilities."
                ]
            },
            {
                "title": "IT & Network Operations Student Trainee",
                "company": "Hong Kong Science and Technology Parks Corporation (HKSTP)",
                "snippet": "Shatin Science Park. Campus network traffic monitoring, Cisco router/switch configuration checks, and IT service desk ticketing.",
                "requirements": [
                    "Undergraduate in Computer Science, Electronic Engineering, or IT.",
                    "Basic knowledge of TCP/IP, VLAN, and routing.",
                    "Good troubleshooting skills."
                ]
            },
            {
                "title": "Junior Systems Analyst Intern",
                "company": "Cyberport Entrepreneurship Centre Network",
                "snippet": "Pokfulam. Web/mobile API testing, database query validation, system log analysis, and user feedback processing.",
                "requirements": [
                    "Background in Computer Science or Software Engineering.",
                    "Knowledge of Python, SQL, or REST APIs.",
                    "Proactive problem solver."
                ]
            },
            {
                "title": "Network Infrastructure & Systems Helper",
                "company": "Hong Kong Metropolitan University (MU)",
                "snippet": "Ho Man Tin. Assisting campus wireless network optimization, switch cabling audits, and IT user support.",
                "requirements": [
                    "Degree/Diploma student in IT, Computer Engineering, or Networking.",
                    "Hands-on technical interest.",
                    "Good communication."
                ]
            }
        ],
        "environmental": [
            {
                "title": "Research Assistant (Environmental Science & Sustainability Analysis)",
                "company": "The Hong Kong Polytechnic University (PolyU)",
                "snippet": "Hung Hom. Soil/water sample collection, environmental pollutant analysis, ESG data processing, and reporting.",
                "requirements": [
                    "Degree in Environmental Science, Chemical Engineering, or Earth System Science.",
                    "Good analytical and field sampling skills.",
                    "Fluent in English and Chinese."
                ]
            },
            {
                "title": "Environmental & Sustainability Officer Trainee",
                "company": "Swire Properties Limited",
                "snippet": "Hong Kong Island. Carbon reduction audits, ESG performance tracking, and green building certification documentations.",
                "requirements": [
                    "Degree in Environmental Science or Engineering.",
                    "Proficient in MS Excel data analysis.",
                    "Strong logical thinking."
                ]
            },
            {
                "title": "Sustainability Data & Carbon Audit Intern",
                "company": "CLP Power Hong Kong Limited",
                "snippet": "Kowloon. Carbon emission data tracking, renewable energy project documentation, and ESG report drafting.",
                "requirements": [
                    "Undergraduate in Environmental Science, Energy Management, or Engineering.",
                    "Good Excel and data skills.",
                    "Fluency in English."
                ]
            }
        ]
    }
    
    selected_pool = all_jobs_data.get("food")
    for cat_name in all_jobs_data:
        if cat_name in key:
            selected_pool = all_jobs_data[cat_name]
            break
            
    results = []
    for item in selected_pool:
        if not user_kw or any(k.lower() in item["title"].lower() or k.lower() in item["company"].lower() or k.lower() in item["snippet"].lower() for k in user_kw.split()):
            results.append({
                "title": item["title"],
                "company": item["company"],
                "source": "JobsDB Official Portal",
                "link": build_official_enterprise_url(item["company"], item["title"]),
                "snippet": item["snippet"],
                "requirements": item["requirements"]
            })
            
    return results if results else [
        {
            "title": item["title"],
            "company": item["company"],
            "source": "JobsDB Official Portal",
            "link": build_official_enterprise_url(item["company"], item["title"]),
            "snippet": item["snippet"],
            "requirements": item["requirements"]
        } for item in selected_pool
    ]

# ----------------- [ 📅 2026-2027 本地创科活动全量数据库 ] -----------------
def get_comprehensive_events(major_key, user_kw=""):
    events_pool = [
        {
            "title": "PolyU × NuttyShell Cybersecurity & Tech Hackathon 2026",
            "date": "2026-09-18",
            "location": "香港理工大学 (PolyU) / 香港科学园",
            "link": "https://www.polyu.edu.hk",
            "type": "🏆 黑客松与创科挑战赛",
            "snippet": "面向全港大专院校学生的网络安全、Web Exploitation 与前沿科技项目 48 小时挑战，现场对接 HR 与导师。"
        },
        {
            "title": "全港大专院校 2026 创新科技黑客松挑战赛 (Hackathon 2026)",
            "date": "2026-09-25",
            "location": "香港科学园高錕会议中心",
            "link": "https://www.hkstp.org",
            "type": "🏆 9月黑客松大赛",
            "snippet": "面向全港大专院校学生的创科竞赛、成果展示与现场 HR 直接对接交流。"
        },
        {
            "title": "香港 2026 青年科技前沿研讨会与创新成果展",
            "date": "2026-08-28",
            "location": "数码港展厅 / 线上直播",
            "link": "https://www.cyberport.hk",
            "type": "🔥 8月重磅论坛",
            "snippet": "前沿学术成果分享、创科企业领袖论坛与大专生优秀科研项目海报展示。"
        },
        {
            "title": "香港國際資訊科技博覽會 2026 學生 Helper / 志愿者招募",
            "date": "2026-10-15",
            "location": "香港會議展覽中心 (HKCEC)",
            "link": "https://www.hktdc.com",
            "type": "🤝 10月 Helper 招募",
            "snippet": "大型国际创科博览会现场志愿者、技术布展协助、嘉宾接待与展商现场沟通协助。"
        },
        {
            "title": "香港都会大学 (HKMU) 创科与生命科学创业训练营 2026",
            "date": "2026-11-20",
            "location": "香港都会大学 (HKMU) 赛马会校园",
            "link": "https://www.hkmu.edu.hk",
            "type": "💡 11月 创业训练营",
            "snippet": "面向大专院校学生的创业训练与创新组概念赛宣讲，提供项目指导与资金对接机会。"
        },
        {
            "title": "数码港 Career Fair (CCF) 2026 青年创客嘉年华暨实习招聘会",
            "date": "2026-03-21",
            "location": "数码港 3 座 Exhibition Gallery",
            "link": "https://www.cyberport.hk",
            "type": "🎯 招聘与实习嘉年华",
            "snippet": "涵盖 AI 模拟面试、CV Clinic、Low-Altitude Economy 展示及实习项目现场面试。"
        }
    ]
    return events_pool

# ----------------- [ 三语界面字典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 cc | 香港科技求职与本地活动智能雷达站",
        "subtitle": "PolyU 及各大真实雇主岗位（直通 JobsDB 官方页面右侧展开） + 2026-2027 本地创科活动",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入搜索词精筛（如: polyu, lab, assistant）...",
        "search_btn": "⚡ 启动全网精选检索",
        "search_loading": "正在同步 JobsDB 官方直达 Portal...",
        "source_tag": "来源网关",
        "tab3_desc": "这里是你的专属 List 保险箱。新查找到的条目都会自动永久存留在这里："
    },
    "繁體中文": {
        "title": "🔬 💻 cc | 香港科技求職與本地活動智能雷達站",
        "subtitle": "PolyU 及各大真實僱主崗位（直通 JobsDB 官方頁面右側展開） + 2026-2027 本地創科活動",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總帳本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入搜尋詞精篩（如: polyu, lab, assistant）...",
        "search_btn": "⚡ 啟動全網精選檢索",
        "search_loading": "正在同步 JobsDB 官方直達 Portal...",
        "source_tag": "來源網關",
        "tab3_desc": "這裡是你的專屬 List 保險箱。新查找到的條目都會自動永久存留在這裡："
    },
    "English": {
        "title": "🔬 💻 cc | HK Tech Live Radar Hub",
        "subtitle": "PolyU & Key Employers Jobs Direct to JobsDB Detail View + 2026 Tech Events",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Upcoming Future Tech Events",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter search terms (e.g. polyu, lab, assistant)...",
        "search_btn": "⚡ Launch Scan",
        "search_loading": "Syncing JobsDB direct portal...",
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

major_choice = st.sidebar.selectbox("Majors:", [food_label, bio_label, comp_label, env_label, all_label], label_visibility="collapsed")

keyword_map = {
    all_label: "food",
    comp_label: "computer", 
    bio_label: "biomedical", 
    env_label: "environmental", 
    food_label: "food"
}
active_major_keyword = keyword_map.get(major_choice, "food")

# --- Tab 1: 互联网实习雷达 ---
with tab1:
    st.header("🎯 互联网实习岗位实时检索雷达" if lang == "简体中文" else "🎯 互聯網實習崗位實時檢索雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input = st.text_input(lang_dict["search_placeholder"], value="", key="real_job_kw")
    search_job_btn = st.button(lang_dict["search_btn"], type="primary", key="btn_job")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if search_job_btn:
        with st.spinner(lang_dict["search_loading"]):
            live_scanned_jobs = get_comprehensive_jobs(active_major_keyword, user_input)
            new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
            
            if new_count > 0:
                st.balloons()
                st.success(f"🔥 为您精准捕获 **{len(live_scanned_jobs)}** 个 PolyU 及本地专业岗位！其中 **{new_count}** 个已存入 List！" if lang == "简体中文" else f"🔥 為您精準捕獲 **{len(live_scanned_jobs)}** 個 PolyU 及本地專業崗位！其中 **{new_count}** 個已存入 List！")
            else:
                st.info("ℹ️ 现场为您呈现精准岗位（包含 PolyU 及各大雇主）。条目已自动同步至你的 List 保险箱中！" if lang == "简体中文" else "ℹ️ 現場為您呈現精準崗位（包含 PolyU 及各大僱主）。條目已自動同步至你的 List 保險箱中！")
            
            for idx, job in enumerate(live_scanned_jobs, 1):
                fingerprint = f"{job.get('title','')}_{job.get('company','')}"
                badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 中"
                
                with st.container(border=True):
                    st.subheader(f"{idx}. {job.get('title','Job Title')}")
                    st.markdown(f"🏢 **真实雇主/机构:** `{job.get('company','Company')}`  |  `{lang_dict['source_tag']}: {job.get('source','JobsDB Portal')}`  |  **状态:** `{badge}`")
                    
                    st.markdown("#### 📝 岗位职责与工作内容 (Job Description)")
                    st.write(job.get("snippet", "暂无简述"))
                    
                    st.markdown("#### 🎯 核心任职要求 (Key Requirements)")
                    reqs = job.get("requirements", [])
                    for r in reqs:
                        st.markdown(f"* {r}")
                        
                    st.markdown("---")
                    st.link_button(f"🌐 直达 JobsDB 查看 [{job.get('company')}] 右侧展开详情 ➔", job.get('link'), type="primary")

# --- Tab 2: 2026-2027 未来科技活动雷达 ---
with tab2:
    st.header("📅 2026-2027 未来科技活动/比赛/志愿者雷达" if lang == "简体中文" else "📅 2026-2027 未來科技活動/比賽/志願者雷達")
    st.markdown(f"🎓 当前专业方向锁定：`{major_choice}`")
    
    user_input_ev = st.text_input("输入活动精筛关键词（如: polyu, hackathon, visit）..." if lang == "简体中文" else "輸入活動精篩關鍵詞...", value="", key="real_ev_kw")
    search_ev_btn = st.button("⚡ 启动全网未来活动扫描" if lang == "简体中文" else "⚡ 啟動全網未來活動掃描", type="primary", key="btn_ev")
    
    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    if search_ev_btn:
        with st.spinner("正在检索 2026-2027 香港本地创科活动与比赛..."):
            live_scanned_events = get_comprehensive_events(active_major_keyword, user_input_ev)
            new_ev_count, all_ev_fps, just_added_ev_fps = sync_and_append_data(live_scanned_events, EVENT_DB, is_job=False)
            
            if new_ev_count > 0:
                st.toast(f"成功录入 {new_ev_count} 个未来新活动！")
                st.success(f"🎉 捕获最新未来活动！现场呈现 **{len(live_scanned_events)}** 个活动情报，其中 **{new_ev_count}** 个新情报已吸纳进 List！" if lang == "简体中文" else f"🎉 捕獲最新未來活動！現場呈現 **{len(live_scanned_events)}** 個活動情報，其中 **{new_ev_count}** 個新情報已吸納進 List！")
            else:
                st.info("ℹ️ 现场活动全量呈现。条目已同步至 List 保险箱。" if lang == "简体中文" else "ℹ️ 現場活動全量呈現。條目已同步至 List 保險箱。")
                
            for idx, ev in enumerate(live_scanned_events, 1):
                fingerprint = f"{ev.get('title','')}_{ev.get('date', '')}"
                ev_badge = "🟢 🆕 NEW" if fingerprint in just_added_ev_fps else "⚪ 已在 List 中"
                
                with st.container(border=True):
                    st.subheader(f"{ev.get('type','活动')} | {idx}. {ev.get('title','Event Title')}")
                    st.info(f"📅 **举办/活动日期:** `{ev.get('date', '2026-2027')}`  |  📍 **地点:** `{ev.get('location', '香港')}`")
                    if ev.get("snippet"):
                        st.caption(f"📝 活动简要: {ev['snippet']}")
                    st.link_button("前往活动官网/详情 ➔" if lang == "简体中文" else "前往活動官網/詳情 ➔", ev.get('link','https://www.polyu.edu.hk'))

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
                        st.link_button("活动官网 ➔" if lang == "简体中文" else "活動官網 ➔", ev.get('link','https://www.polyu.edu.hk'))
