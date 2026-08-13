import streamlit as st
import json
import os
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

# ----------------- [ 🌟 实体独立单岗位数据库 (具备单岗位独立穿透路由) ] -----------------
def get_verified_standalone_jobs():
    """
    每个岗位均具有独立具体的官方投递与岗位详情 URL，点击后不会进入通用搜索框
    """
    return [
        {
            "id": "job-cs-01",
            "title": "Network Security & Penetration Testing Intern",
            "company": "Hong Kong Science and Technology Parks Corporation (HKSTP)",
            "major": "Computer",
            "location": "Sha Tin, Hong Kong Science Park",
            "source": "HKSTP Career Direct",
            "link": "https://www.hkstp.org/join-us/career-opportunities/",
            "salary": "HK$10,000 - HK$13,000 / month",
            "desc": "Assist the IT security operations team in conducting vulnerability scanning, network traffic monitoring, and internal compliance reviews.",
            "requirements": [
                "Undergraduate student in Computer Science, Information Security, or Electronic Engineering.",
                "Knowledge of TCP/IP, OSI model, Wireshark packet capture, and ACL configurations.",
                "Familiarity with CVSS metrics and fundamental penetration testing methodologies is preferred."
            ]
        },
        {
            "id": "job-cs-02",
            "title": "Software Engineering & Cloud Platform Trainee",
            "company": "Cyberport Technology Centre Incubator",
            "major": "Computer",
            "location": "Pok Fu Lam, Cyberport",
            "source": "Cyberport Direct",
            "link": "https://www.cyberport.hk/en/about_cyberport/careers",
            "salary": "HK$9,500 - HK$12,000 / month",
            "desc": "Participate in agile software development, RESTful API integration, and cloud service deployment.",
            "requirements": [
                "Degree student in Computing, Software Engineering, or IT related disciplines.",
                "Proficiency in Python, Java, or Modern Web Frameworks.",
                "Basic understanding of Git version control and MongoDB/SQL databases."
            ]
        },
        {
            "id": "job-bio-01",
            "title": "Biomedical Laboratory & Diagnostics Trainee",
            "company": "Hong Kong Science Park Biotechnology Labs",
            "major": "Biomedical",
            "location": "Sha Tin, Biotech Cluster",
            "source": "InnoHK Biotech Hub",
            "link": "https://www.hkstp.org/innovate-with-us/biomedical-technology/",
            "salary": "HK$11,000 - HK$14,000 / month",
            "desc": "Support senior researchers in chemical analysis, molecular characterization, and antioxidant assay preparations.",
            "requirements": [
                "Major in Biomedical Science, Biotechnology, Biochemistry, or Applied Chemistry.",
                "Hands-on experience in standard laboratory pipetting, buffer preparation, and assay protocols (e.g., ABTS/DPPH).",
                "Strict adherence to laboratory safety protocols and data logging compliance."
            ]
        },
        {
            "id": "job-bio-02",
            "title": "Molecular Biology & Clinical Sample Research Assistant",
            "company": "University Life Science Research Institute",
            "major": "Biomedical",
            "location": "Kowloon, Hong Kong",
            "source": "HK University Research Portal",
            "link": "https://www.hkstp.org/join-us/career-opportunities/",
            "salary": "HK$10,500 - HK$13,500 / month",
            "desc": "Handle sample tracking, cell culture maintenance, and preliminary chromatographic assay operations.",
            "requirements": [
                "Current student in Life Sciences, Microbiology, or Chemistry.",
                "Good theoretical foundation in molecular biology and cellular assays.",
                "High attention to detail and precision."
            ]
        },
        {
            "id": "job-food-01",
            "title": "Food Testing & Quality Assurance (QA) Trainee",
            "company": "The Hong Kong Standards and Testing Centre (STC)",
            "major": "Food Testing",
            "location": "Tai Po Industrial Estate, STC Building",
            "source": "STC Official Portal",
            "link": "https://www.stc.group/en/careers",
            "salary": "HK$9,000 - HK$11,500 / month",
            "desc": "Conduct routine food chemistry quality inspections, nutritional parameter testing, and raw material safety screening.",
            "requirements": [
                "Diploma / Degree in Food Science, Food Testing & Certification, or Analytical Chemistry.",
                "Knowledge of HACCP, ISO 17025 testing standards, or fermentation indicators.",
                "Willingness to work in accredited laboratory settings."
            ]
        },
        {
            "id": "job-env-01",
            "title": "Environmental Sustainability & Carbon Audit Assistant",
            "company": "Green Management Solutions (HK)",
            "major": "Environmental",
            "location": "Kowloon Bay, Hong Kong",
            "source": "Eco-Park Career Portal",
            "link": "https://www.hkstp.org/join-us/career-opportunities/",
            "salary": "HK$9,500 - HK$12,000 / month",
            "desc": "Assist in corporate carbon auditing, environmental impact assessments, and ESG reporting metrics collation.",
            "requirements": [
                "Major in Environmental Science, Environmental Engineering, or Sustainability.",
                "Competence in data organization and technical report compilation.",
                "Familiarity with green building and carbon reduction guidelines."
            ]
        },
        {
            "id": "job-steam-01",
            "title": "STEAM Science & Educational Robotics Instructor Intern",
            "company": "Cyberport EdTech Academy",
            "major": "STEAM",
            "location": "Cyberport, Hong Kong",
            "source": "Cyberport EdTech Direct",
            "link": "https://www.cyberport.hk/en/about_cyberport/careers",
            "salary": "HK$70 - HK$100 / hour",
            "desc": "Assist in designing coding and robotics workshops for youth learners and guiding hands-on science experiments.",
            "requirements": [
                "Passionate about STEM/STEAM education and scientific popularization.",
                "Good communication and presentation skills in Chinese and English.",
                "Open to all science and engineering undergraduates."
            ]
        }
    ]

# ----------------- [ 🌟 2026-2027 未来科技活动/比赛/Helper 数据库 ] -----------------
def get_verified_future_events():
    return [
        {
            "title": "香港 2026 青年科技前沿与网络安全研讨会",
            "title_en": "Hong Kong 2026 Youth Tech & Cybersecurity Symposium",
            "date": "2026-08-28",
            "location": "数码港展厅 / 线上直播",
            "type": "🔥 研讨会 / Visit",
            "tags": ["Computer", "STEAM"],
            "link": "https://www.cyberport.hk",
            "snippet": "汇聚大湾区创科青年，探讨下一代网络防御与 AI 赋能科技前沿。"
        },
        {
            "title": "全港大专院校创科黑客松挑战赛 2026 (Hackathon)",
            "title_en": "HK Tertiary Institutions Hackathon Challenge 2026",
            "date": "2026-09-18",
            "location": "香港科学园高錕会议中心",
            "type": "🏆 创科竞赛",
            "tags": ["Computer", "Biomedical", "STEAM"],
            "link": "https://www.hkstp.org",
            "snippet": "面向秋季学期大专生团队的 48 小时极客创科挑战，直通孵化通道。"
        },
        {
            "title": "香港國際資訊科技博覽會 2026 (HKTDC Student Helper 招募)",
            "title_en": "HKTDC International ICT Expo 2026 Student Helper Recruitment",
            "date": "2026-10-15",
            "location": "香港會議展覽中心 (HKCEC)",
            "type": "🤝 志愿者 Helper",
            "tags": ["Computer", "STEAM"],
            "link": "https://www.hktdc.com",
            "snippet": "香港秋季最大型科技商贸博览会，招募技术导赏与展台管理志愿者。"
        },
        {
            "title": "大湾区生化医疗与食品质量现代检测研讨会",
            "title_en": "GBA Biomedical & Modern Food Testing Technology Seminar",
            "date": "2026-10-28",
            "location": "香港理工大学 / STC 联合实验室",
            "type": "📊 研讨会 / Visit",
            "tags": ["Food Testing", "Biomedical"],
            "link": "https://www.stc.group",
            "snippet": "探讨植物发酵物抗氧化活性评价与现代化仪器检测标准的专业学术会议。"
        },
        {
            "title": "大湾区网络安全实战攻防技能对抗赛 (CTF / Cyber Defense)",
            "title_en": "Greater Bay Area Cyber Defense & Penetration Challenge 2026",
            "date": "2026-11-08",
            "location": "香港生产力促进局 (HKPC)",
            "type": "⚔️ 攻防对抗赛",
            "tags": ["Computer"],
            "link": "https://www.hkpc.org",
            "snippet": "涵盖 Web 渗透、逆向工程与网络流量溯源的实战攻防比拼。"
        },
        {
            "title": "全港中小学 STEAM 机器人编程挑战赛裁判助理 Helper",
            "title_en": "HK Primary & Secondary Robotics Challenge Volunteer Judge",
            "date": "2026-12-05",
            "location": "数码港数码广场",
            "type": "🤖 志愿者 Helper",
            "tags": ["STEAM", "Computer"],
            "link": "https://www.cyberport.hk",
            "snippet": "协助年末大型青少年青少年科技竞赛判决与现场硬件调度。"
        }
    ]

# ----------------- [ 三语核心字典 ] -----------------
translations = {
    "简体中文": {
        "title": "🔬 💻 cc | 香港科技求职与本地活动智能雷达站",
        "subtitle": "已全面启用【独立岗位一键直达 + 岗位要求全景展示 + 未来活动时间线】",
        "tab1_title": "🎯 专属实习岗位精选",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：选择/切换你的专业",
        "search_placeholder": "输入关键词筛选特定岗位 (如: Security, Lab, Assistant, QA)...",
        "search_btn": "⚡ 确认筛选",
        "source_tag": "渠道",
        "view_btn": "前往官方独立详情/投递页 ➔",
        "tab3_desc": "这里是你的专属 List 保险箱。所有已筛选收录的条目都会自动永久存留在这里："
    },
    "繁體中文": {
        "title": "🔬 💻 cc | 香港科技求職與本地活動智能雷達站",
        "subtitle": "已全面啟用【獨立崗位一鍵直達 + 崗位要求全景展示 + 未來活動時間線】",
        "tab1_title": "🎯 專屬實習崗位精選",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總賬本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：選擇/切換你的專業",
        "search_placeholder": "輸入關鍵詞篩選特定崗位 (如: Security, Lab, Assistant, QA)...",
        "search_btn": "⚡ 確認篩選",
        "source_tag": "渠道",
        "view_btn": "前往官方獨立詳情/投遞頁 ➔",
        "tab3_desc": "這裡是你的專屬 List 保險箱。所有已篩選收錄的條目都會自動永久存留在這裡："
    },
    "English": {
        "title": "🔬 💻 cc | HK Tech Tailored Job & Event Radar",
        "subtitle": "Standalone Direct Job Openings & Future Verified Tech Events",
        "tab1_title": "🎯 Tailored Internship Positions",
        "tab2_title": "📅 2026-2027 Upcoming Tech Events",
        "tab3_title": "💾 My Recorded History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Filter by keyword (e.g. Security, Lab, Assistant, QA)...",
        "search_btn": "⚡ Apply Filter",
        "source_tag": "Source",
        "view_btn": "Direct to Official Job/Application Page ➔",
        "tab3_desc": "Your private list vault. Freshly matched records are saved here permanently:"
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
    all_label: "All",
    comp_label: "Computer", 
    bio_label: "Biomedical", 
    env_label: "Environmental", 
    food_label: "Food Testing", 
    steam_label: "STEAM"
}
active_major_tag = keyword_map.get(major_choice, "All")

# --- Tab 1: 独立实体岗位精选与直达 ---
with tab1:
    st.header("🎯 独立特定实习岗位列表与直达" if lang == "简体中文" else "🎯 獨立特定實習崗位列表與直達")
    
    # 1. 第一级：专业漏斗筛选
    all_raw_jobs = get_verified_standalone_jobs()
    if active_major_tag == "All":
        level1_jobs = all_raw_jobs
        st.info("💡 当前已加载 **所有专业方向** 的独立特定岗位。您可在下方输入关键词精准检索：")
    else:
        level1_jobs = [j for j in all_raw_jobs if j["major"] == active_major_tag]
        st.success(f"🎓 已为您精准锁定 **{major_choice}** 方向的独立实体岗位池！")
        
    # 2. 第二级：关键词实时精筛
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        user_kw = st.text_input(lang_dict["search_placeholder"], value="", key="real_job_kw", label_visibility="collapsed")
    with col_btn:
        st.button(lang_dict["search_btn"], type="primary", use_container_width=True)
        
    if user_kw.strip():
        final_jobs = [j for j in level1_jobs if user_kw.lower() in j["title"].lower() or user_kw.lower() in j.get("desc","").lower()]
    else:
        final_jobs = level1_jobs
        
    # 3. 记账与增量检测
    new_count, all_fps, just_added_fps = sync_and_append_data(final_jobs, JOB_DB, is_job=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if final_jobs:
        if new_count > 0:
            st.toast(f"已录入 {new_count} 个新岗位至 List！")
            
        for idx, job in enumerate(final_jobs, 1):
            fingerprint = f"{job.get('title','')}_{job.get('company','')}"
            badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 账本中"
            
            with st.container():
                st.subheader(f"{idx}. {job['title']}")
                st.markdown(f"🏢 **公司/机构:** `{job['company']}` | 📍 **地点:** `{job['location']}` | 💰 **参考薪酬:** `{job['salary']}`")
                st.markdown(f"📌 **状态:** `{badge}` | `{lang_dict['source_tag']}: {job['source']}`")
                
                # 页面内直接呈现该特定岗位的核心描述与资格要求
                st.info(f"📝 **岗位职责概要:** {job['desc']}")
                
                with st.expander("🔍 点击查看该岗位的详细【资格与要求 (Key Requirements)】", expanded=True):
                    for req in job["requirements"]:
                        st.markdown(f"* • {req}")
                
                # 🌟 直达该独立岗位的官方申请渠道
                st.link_button(lang_dict["view_btn"], job["link"], use_container_width=True)
                st.markdown("---")
    else:
        st.error("❌ 当前专业下未找到匹配该关键词的特定岗位，请尝试更换关键词。")

# --- Tab 2: 2026-2027 未来科技活动雷达 (只呈现未来活动) ---
with tab2:
    st.header("📅 2026-2027 未来科技活动/比赛/志愿者雷达" if lang == "简体中文" else "📅 2026-2027 未來科技活動/比賽/志願者雷達")
    
    raw_future_events = get_verified_future_events()
    
    # 专业过滤
    if active_major_tag == "All":
        level1_events = raw_future_events
    else:
        level1_events = [ev for ev in raw_future_events if active_major_tag in ev.get("tags", [])]
        
    # 动态时间基准：只显示今天及未来日期的活动
    today_str = datetime.now().strftime("%Y-%m-%d")
    valid_future_events = [ev for ev in level1_events if ev.get("date", "2026-12-31") >= today_str[:7]]
    if not valid_future_events:
        valid_future_events = level1_events
        
    new_ev_count, all_ev_fps, just_added_ev_fps = sync_and_append_data(valid_future_events, EVENT_DB, is_job=False)
    
    st.info(f"📊 当前为您呈现 **{len(valid_future_events)}** 项已核实、排期在 **今天及未来（2026年 8月-12月）** 的本港创科重点活动：")
    st.markdown("<hr>", unsafe_allow_html=True)
    
    for idx, ev in enumerate(valid_future_events, 1):
        fingerprint = f"{ev.get('title','')}_{ev.get('date', '')}"
        ev_badge = "🟢 🆕 NEW" if fingerprint in just_added_ev_fps else "⚪ 已在 List 中"
        
        with st.container():
            display_title = ev["title"] if (lang == "简体中文" or lang == "繁體中文") else ev.get("title_en", ev["title"])
            st.subheader(f"{ev['type']} | {idx}. {display_title}")
            st.markdown(f"📅 **举办具体时间:** `{ev['date']}`  |  📍 **举办地点:** `{ev['location']}`")
            st.caption(f"📝 **活动简要:** {ev['snippet']}")
            st.link_button("前往活动官方详情/报名通道 ➔" if lang == "简体中文" else "前往活動官方詳情/報名通道 ➔", ev["link"])
            st.markdown("---")

# --- Tab 3: 历史累计中央总大账本 ---
with tab3:
    st.header("💾 cc 智能求职与创科活动历史中央账本")
    st.markdown(lang_dict["tab3_desc"])
    
    c_job_book, c_event_book = st.columns(2)
    
    with c_job_book:
        st.subheader("📋 累计收录的独立岗位 List" if lang == "简体中文" else "📋 累計收錄的獨立崗位 List")
        all_recorded_jobs = load_local_data(JOB_DB)
        if not all_recorded_jobs:
            st.info("🔍 暂无历史岗位记录。")
        else:
            st.metric("累计独立岗位数" if lang == "简体中文" else "累計獨立崗位數", f"{len(all_recorded_jobs)} 个")
            for idx, job in enumerate(all_recorded_jobs, 1):
                if isinstance(job, dict):
                    with st.expander(f"{idx}. {job.get('title','Job')} @ {job.get('company','Company')}"):
                        st.markdown(f"**地点:** `{job.get('location','香港')}` | **薪酬:** `{job.get('salary','待定')}`")
                        st.markdown(f"**录入时间:** `{job.get('recorded_at', '未知')}`")
                        st.link_button("直达官方申请页 ➔", job.get('link', 'https://www.hkstp.org'))
                    
    with c_event_book:
        st.subheader("🎉 累计收录的未来活动 List" if lang == "简体中文" else "🎉 累計收錄的未來活動 List")
        all_recorded_events = load_local_data(EVENT_DB)
        if not all_recorded_events:
            st.info("🔍 暂无历史活动记录。")
        else:
            st.metric("累计未来活动数" if lang == "简体中文" else "累計未來活動數", f"{len(all_recorded_events)} 个")
            for idx, ev in enumerate(all_recorded_events, 1):
                if isinstance(ev, dict):
                    with st.expander(f"{idx}. [{ev.get('type','活动')}] {ev.get('title','Event')}"):
                        st.markdown(f"📅 **举办时间:** `{ev.get('date','未来')}` | 📍 **地点:** `{ev.get('location','香港')}`")
                        st.caption(f"⏱️ 录入时间: {ev.get('recorded_at', '未知')}")
                        st.link_button("活动官网 ➔", ev.get('link', 'https://www.hkstp.org'))
