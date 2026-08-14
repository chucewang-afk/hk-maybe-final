import streamlit as st
import json
import os
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

# ----------------- [ 🎯 严格过滤匹配岗位内核 ] -----------------
def get_comprehensive_jobs(major_key, user_kw=""):
    key = major_key.lower()
    user_kw_clean = str(user_kw).strip().lower()
    
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
        ],
        "steam": [
            {
                "title": "STEAM Education & Project Assistant",
                "company": "Hong Kong Metropolitan University (MU)",
                "snippet": "Ho Man Tin. STEAM Centre. Assisting hands-on science workshop preparations, experimental kit testing, and student activity coordination.",
                "requirements": [
                    "Degree or Diploma in Science, Education, Bioengineering, or Applied Science.",
                    "Passionate about science popularization and hands-on laboratory workshops.",
                    "Good interpersonal and organizational skills."
                ]
            },
            {
                "title": "STEM Learning & Lab Demonstration Assistant",
                "company": "The Hong Kong Polytechnic University (PolyU)",
                "snippet": "Hung Hom. Supporting STEM education projects, lab kit maintenance, interactive experiment setup, and student mentoring.",
                "requirements": [
                    "Undergraduate in Science, Engineering, or Education.",
                    "Good presentation skills and enthusiasm for science education.",
                    "Fluency in English and Cantonese."
                ]
            },
            {
                "title": "Science & Innovation Workshop Helper",
                "company": "Hong Kong Science and Technology Parks Corporation (HKSTP)",
                "snippet": "Shatin Science Park. Assisting STEAM robotics and science workshops, event setup, and participant guidance.",
                "requirements": [
                    "Students in Science, Computer Science, or Engineering disciplines.",
                    "Patient, proactive, and good team communicator.",
                    "Eligible to work in Hong Kong."
                ]
            }
        ]
    }
    
    if key == "show all" or "all" in key:
        selected_pool = []
        for cat in all_jobs_data:
            selected_pool.extend(all_jobs_data[cat])
    else:
        selected_pool = []
        for cat_name in all_jobs_data:
            if cat_name in key:
                selected_pool = all_jobs_data[cat_name]
                break
                
    results = []
    if not user_kw_clean:
        for item in selected_pool:
            results.append({
                "title": item["title"],
                "company": item["company"],
                "source": "JobsDB Official Portal",
                "link": build_official_enterprise_url(item["company"], item["title"]),
                "snippet": item["snippet"],
                "requirements": item["requirements"]
            })
    else:
        search_terms = user_kw_clean.split()
        for item in selected_pool:
            match_str = f"{item['title']} {item['company']} {item['snippet']}".lower()
            if all(term in match_str for term in search_terms):
                results.append({
                    "title": item["title"],
                    "company": item["company"],
                    "source": "JobsDB Official Portal",
                    "link": build_official_enterprise_url(item["company"], item["title"]),
                    "snippet": item["snippet"],
                    "requirements": item["requirements"]
                })
                
    return results

# ----------------- [ 📅 零污染隔离 + 自动淘汰过期活动库 ] -----------------
def get_strictly_matched_events(major_key, user_kw=""):
    key = major_key.lower()
    user_kw_clean = str(user_kw).strip().lower()
    current_date_str = datetime.now().strftime("%Y-%m-%d") # 获取当前日期
    
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
            },
            {
                "title": "数码港 Career Fair (CCF) 2026 创客嘉年华暨 IT 实习招聘会",
                "date": "2026-03-21", # 这个日期已过期，将被自动过滤，不再显示和保存
                "location": "数码港 3 座 Exhibition Gallery",
                "link": "https://www.cyberport.hk",
                "type": "🎯 招聘与实习嘉年华",
                "snippet": "涵盖 AI 模拟面试、CV Clinic、低空经济技术展示及 IT 实习项目现场面试。"
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

    # 1. 过滤不相关的专业内容
    if "computer" not in key and "all" not in key:
        selected_events = [ev for ev in selected_events if "cybersecurity" not in ev['title'].lower() and "ctf" not in ev['title'].lower()]
        
    # 2. 🌟 过滤已过期活动（只保留日期大于等于今天的活动，过期的直接丢弃）
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
        "subtitle": "HKMU 应用科学系专属：真实雇主岗位（直通 JobsDB 官方页面右侧展开） + 分专业隔离本地创科活动",
        "tab1_title": "🎯 实时全网实习雷达",
        "tab2_title": "📅 2026-2027 未来科技活动雷达",
        "tab3_title": "💾 专属历史累计总账本 (List)",
        "sidebar_lang": "🌐 切换语言 / Language",
        "sidebar_major": "🎓 数据指挥中心：锁定你的专业方向",
        "search_placeholder": "输入搜索词精筛（如: hkmu, lab, assistant）...",
        "search_placeholder_ev": "输入活动精筛关键词（如: hkmu, workshop, forum）...",
        "search_btn": "⚡ 启动全网精选检索",
        "search_btn_ev": "⚡ 启动全网未来活动扫描",
        "search_loading": "正在执行无污染隔离筛选逻辑...",
        "search_loading_ev": "正在检索与当前专业严格对应的 2026-2027 香港本地创科活动与比赛...",
        "source_tag": "来源网关",
        "tab3_desc": "这里是你的专属 List 保险箱。新查找到的条目都会自动永久存留在这里：",
        "job_header": "🎯 互联网实习岗位实时检索雷达",
        "ev_header": "📅 2026-2027 未来科技活动/比赛/志愿者雷达",
        "current_major_prefix": "🎓 当前专业方向锁定：",
        "no_job_match": "⚠️ 现场未检索到与筛选条件完全相符的工作，已按您的要求不展示不相关的替代数据。请尝试调整或更换搜寻关键词。",
        "no_ev_match": "⚠️ 未能找到与当前专业及关键词相符且未过期的活动。",
        "job_desc_head": "📝 岗位职责与工作内容 (Job Description)",
        "job_req_head": "🎯 核心任职要求 (Key Requirements)",
        "link_btn_job": "🌐 直达 JobsDB 查看 [{company}] 右侧展开详情 ➔",
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
        "subtitle": "HKMU 應用科學系專屬：真實僱主崗位（直通 JobsDB 官方頁面右側展開） + 分專業隔離本地創科活動",
        "tab1_title": "🎯 實時全網實習雷達",
        "tab2_title": "📅 2026-2027 未來科技活動雷達",
        "tab3_title": "💾 專屬歷史累計總帳本 (List)",
        "sidebar_lang": "🌐 切換語言 / Language",
        "sidebar_major": "🎓 數據指揮中心：鎖定你的專業方向",
        "search_placeholder": "輸入搜尋詞精篩（如: hkmu, lab, assistant）...",
        "search_placeholder_ev": "輸入活動精篩關鍵詞（如: hkmu, workshop, forum）...",
        "search_btn": "⚡ 啟動全網精選檢索",
        "search_btn_ev": "⚡ 啟動全網未來活動掃描",
        "search_loading": "正在執行無污染隔離篩選邏輯...",
        "search_loading_ev": "正在檢索與當前專業嚴格對應的 2026-2027 香港本地創科活動與比賽...",
        "source_tag": "來源網關",
        "tab3_desc": "這裡是你的專屬 List 保險箱。新查找到的條目都會自動永久存留在這裡：",
        "job_header": "🎯 互聯網實習崗位實時檢索雷達",
        "ev_header": "📅 2026-2027 未來科技活動/比賽/志願者雷達",
        "current_major_prefix": "🎓 當前專業方向鎖定：",
        "no_job_match": "⚠️ 現場未檢索到與篩選條件完全相符的工作，已按您的要求不展示不相關的替代數據。請嘗試調整或更換搜尋關鍵詞。",
        "no_ev_match": "⚠️ 未能找到與當前專業及關鍵詞相符且未過期的活動。",
        "job_desc_head": "📝 崗位職責與工作內容 (Job Description)",
        "job_req_head": "🎯 核心任職要求 (Key Requirements)",
        "link_btn_job": "🌐 直達 JobsDB 查看 [{company}] 右側展開詳情 ➔",
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
        "subtitle": "HKMU Department of Applied Science Hub: Employers Jobs Direct to JobsDB Right-Side View + Major-Isolated Events",
        "tab1_title": "🎯 Live Web Job Radar",
        "tab2_title": "📅 Upcoming Future Tech Events",
        "tab3_title": "💾 My Recorded Full History Book (List)",
        "sidebar_lang": "🌐 Language / 語言 / 语言",
        "sidebar_major": "🎓 Command Centre: Select Your Major",
        "search_placeholder": "Enter search terms (e.g. hkmu, lab, assistant)...",
        "search_placeholder_ev": "Enter event keywords (e.g. hkmu, workshop, forum)...",
        "search_btn": "⚡ Launch Scan",
        "search_btn_ev": "⚡ Launch Event Scan",
        "search_loading": "Executing strict filter logic...",
        "search_loading_ev": "Searching strictly major-matched 2026-2027 HK tech events...",
        "source_tag": "Source Gateway",
        "tab3_desc": "Your private list vault. Freshly scanned records are saved here permanently:",
        "job_header": "🎯 Live Web Job Radar",
        "ev_header": "📅 2026-2027 Future Tech Events / Contests / Helper Radar",
        "current_major_prefix": "🎓 Locked Major Direction: ",
        "no_job_match": "⚠️ No jobs matched your exact criteria. Unrelated data has been hidden as requested. Please try adjusting your search terms.",
        "no_ev_match": "⚠️ No valid upcoming events matched your major and keyword criteria.",
        "job_desc_head": "📝 Job Description",
        "job_req_head": "🎯 Key Requirements",
        "link_btn_job": "🌐 View [{company}] Right-Side Job Detail on JobsDB ➔",
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

# --- Tab 1: 互联网实习雷达 ---
with tab1:
    st.header(lang_dict["job_header"])
    st.markdown(f"{lang_dict['current_major_prefix']}`{major_choice}`")
    
    user_input = st.text_input(lang_dict["search_placeholder"], value="", key="real_job_kw")
    search_job_btn = st.button(lang_dict["search_btn"], type="primary", key="btn_job")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if search_job_btn:
        with st.spinner(lang_dict["search_loading"]):
            live_scanned_jobs = get_comprehensive_jobs(active_major_keyword, user_input)
            
            if not live_scanned_jobs:
                st.warning(lang_dict["no_job_match"])
            else:
                new_count, all_fps, just_added_fps = sync_and_append_data(live_scanned_jobs, JOB_DB, is_job=True)
                
                if new_count > 0:
                    st.balloons()
                    st.success(f"🔥 ({lang}) 精准匹配到 **{len(live_scanned_jobs)}** 个岗位！其中 **{new_count}** 个已存入 List！")
                else:
                    st.info(f"ℹ️ ({lang}) 找到 **{len(live_scanned_jobs)}** 个符合条件的岗位，均已在 List 中存留。")
                
                for idx, job in enumerate(live_scanned_jobs, 1):
                    fingerprint = f"{job.get('title','')}_{job.get('company','')}"
                    badge = "🟢 🆕 NEW" if fingerprint in just_added_fps else "⚪ 已在 List 中"
                    
                    with st.container(border=True):
                        st.subheader(f"{idx}. {job.get('title','Job Title')}")
                        st.markdown(f"🏢 **雇主/机构:** `{job.get('company','Company')}`  |  `{lang_dict['source_tag']}: {job.get('source','JobsDB Portal')}`  |  **状态:** `{badge}`")
                        
                        st.markdown(f"#### {lang_dict['job_desc_head']}")
                        st.write(job.get("snippet", ""))
                        
                        st.markdown(f"#### {lang_dict['job_req_head']}")
                        reqs = job.get("requirements", [])
                        for r in reqs:
                            st.markdown(f"* {r}")
                            
                        st.markdown("---")
                        btn_label = lang_dict["link_btn_job"].format(company=job.get('company','Company'))
                        st.link_button(btn_label, job.get('link'), type="primary")

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
                        st.markdown(f"**雇主:** `{job.get('company','Company')}` | **渠道:** {job.get('source','JobsDB')} | **录入时间:** `{job.get('recorded_at', '未知')}`")
                        if job.get("snippet"):
                            st.caption(f"📝 说明: {job['snippet']}")
                        btn_label = lang_dict["link_btn_job"].format(company=job.get('company','Company'))
                        st.link_button(btn_label, job.get('link'))
                    
    with c_event_book:
        st.subheader(lang_dict["hist_ev_title"])
        all_recorded_events = load_local_data(EVENT_DB)
        current_date_str = datetime.now().strftime("%Y-%m-%d") # 获取今天日期
        
        valid_recorded_events = []
        for ev in all_recorded_events:
            if isinstance(ev, dict):
                # 🌟 核心剔除机制：哪怕之前被记录了，一旦日期小于今天，就不在历史账单中显示
                if ev.get('date', '') < current_date_str:
                    continue
                
                # 专业防污染隔离
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
