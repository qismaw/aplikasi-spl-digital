import streamlit as st
from fpdf import FPDF
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import json
import io
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 🛑 ID DATABASE GOOGLE SHEETS ANDA 🛑
# ==========================================
SHEET_ID = "1YV7ro3PYla3D0ZbIhNsdFwxDSh1XZmal9aO99pebG5U"

# Konfigurasi Halaman & Tab Browser
st.set_page_config(page_title="OVERTIX - SPL Digital", page_icon="⏱️", layout="wide")

# ==========================================
# 💎 CSS SUPER PREMIUM: OVERTIX DARK THEME
# ==========================================
st.markdown("""
<style>
    /* 1. HILANGKAN MENU STREAMLIT SECARA PERMANEN */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}

    /* 2. BACKGROUND APLIKASI (Dark Navy Blue) */
    .stApp {
        background-color: #151e2d !important;
        color: white !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* 3. STYLING INPUT & DROPDOWN AGAR GELAP ELEGAN */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextArea textarea, .stDateInput input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: #1c273c !important;
        border: 1px solid #2e3c54 !important;
        border-radius: 6px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
    }
    div[data-baseweb="select"] span { color: #ffffff !important; }
    div[data-baseweb="popover"] ul { background-color: #1c273c !important; }
    div[data-baseweb="popover"] li { color: #ffffff !important; }
    .stSelectbox label, .stTextInput label, .stDateInput label, .stTextArea label { 
        color: #e2e8f0 !important; font-weight: 500 !important; font-size: 14px !important;
    }

    /* 4. CUSTOM TABEL KARYAWAN (Tabel ramping, Font Besar) */
    .custom-table-container {
        background-color: #1c273c;
        border-radius: 8px;
        border: 1px solid #2e3c54;
        padding: 8px !important; /* Diperkecil agar lebih rapat */
        margin-top: 10px;
        overflow-x: auto;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 18px !important; /* UKURAN TULISAN DIPERBESAR */
    }
    .custom-table th {
        background-color: #23314a;
        color: #cbd5e1;
        text-align: center;
        padding: 4px 8px !important; /* PADDING SANGAT KECIL */
        border: 1px solid #2e3c54;
        font-weight: 700;
    }
    .custom-table td {
        background-color: #1c273c;
        color: white;
        text-align: center;
        padding: 4px 8px !important; /* PADDING SANGAT KECIL */
        border: 1px solid #2e3c54;
        white-space: nowrap;
    }

    /* 5. BOX HEADER / CARD KARYAWAN */
    .card-header {
        background-color: #1e293b;
        padding: 10px 15px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border-bottom: 1px solid #2e3c54;
        font-weight: bold;
        color: white;
        margin-bottom: 15px;
    }

    /* 6. WARNA TOMBOL */
    div[data-testid="stButton"] button {
        border-radius: 6px !important;
        font-weight: bold !important;
    }
    div[data-testid="stButton"] button:has(p:contains("Kirim Pengajuan")), 
    div[data-testid="stButton"] button:has(p:contains("LOGIN")),
    div[data-testid="stButton"] button:has(p:contains("Portal")) {
        background-color: #2563eb !important; color: white !important; border: none !important;
    }
    div[data-testid="stButton"] button:has(p:contains("Dukungan Teknis")),
    div[data-testid="stButton"] button:has(p:contains("Kembali")), div[data-testid="stButton"] button:has(p:contains("Keluar")) {
        background-color: #334155 !important; color: white !important; border: none !important;
    }
    div[data-testid="stButton"] button:has(p:contains("Approve")) { background-color: #10b981 !important; color: white !important; border:none !important;}
    div[data-testid="stButton"] button:has(p:contains("Tolak")) { background-color: #ef4444 !important; color: white !important; border:none !important;}

    /* 7. STYLING TABEL DASHBOARD ADMIN/GL AGAR RAPI & BESAR DI HP */
    @media (max-width: 768px) { body, .stApp { overflow-x: hidden !important; } }
    
    div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) {
        background-color: rgba(255,255,255,0.02) !important; 
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important; 
        padding: 5px !important; 
        margin-bottom: 20px !important; 
        overflow-x: auto !important;
    }
    
    div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) div[data-testid="stHorizontalBlock"] {
        min-width: 1000px !important; 
        border-bottom: 1px solid rgba(255,255,255,0.1) !important; 
        align-items: center !important; 
        padding: 4px 0 !important; /* Jarak baris rapat */
    }
    
    /* Memperbesar huruf di dalam tabel ke 18px */
    div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) p {
        font-size: 18px !important; 
        margin-bottom: 0 !important;
    }
    
    /* Mengecilkan tombol di dalam tabel agar baris tidak melar */
    div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) div[data-testid="stButton"] button {
        padding: 2px 10px !important;
        min-height: 32px !important;
        font-size: 14px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SETUP SESSION STATE
# ==========================================
if "app_mode" not in st.session_state: st.session_state.app_mode = "landing"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = "" 

def get_wib_time(): return datetime.utcnow() + timedelta(hours=7)

# ==========================================
# KONEKSI GOOGLE SHEETS
# ==========================================
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
@st.cache_resource
def get_gsheets_client():
    try:
        creds_dict = json.loads(st.secrets["gcp_credentials"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Kredensial Error: {e}")
        st.stop()

def get_worksheet(sheet_name):
    sh = get_gsheets_client().open_by_key(SHEET_ID)
    try: return sh.worksheet(sheet_name)
    except: return sh.add_worksheet(title=sheet_name, rows="1000", cols="20")

def safe_update(sheet, data, range_name="A1"):
    sheet.clear()
    sheet.update(range_name, data)

# ==========================================
# DATABASE & LOGIKA UTAMA
# ==========================================
@st.cache_data(ttl=60)
def load_users():
    data = get_worksheet("Users").get_all_records()
    return {str(row["Username"]): {"password": str(row["Password"]), "failed_attempts": int(row["Gagal"]), "blocked": str(row["Blocked"]).lower() == "true", "role": str(row["Role"])} for row in data}

def save_users(users_data):
    rows = [["Username", "Password", "Gagal", "Blocked", "Role"]]
    for k, v in users_data.items(): rows.append([k, v["password"], v["failed_attempts"], str(v["blocked"]), v["role"]])
    safe_update(get_worksheet("Users"), rows)
    st.cache_data.clear()

@st.cache_data(ttl=60)
def load_config():
    data = get_worksheet("Config").get_all_records()
    if not data: return {"status_aktif": False, "pjs_nama": ""}
    return {"status_aktif": str(data[0]["status_aktif"]).lower() == "true", "pjs_nama": str(data[0]["pjs_nama"])}

def save_config(config):
    safe_update(get_worksheet("Config"), [["status_aktif", "pjs_nama"], [str(config["status_aktif"]), config["pjs_nama"]]])
    st.cache_data.clear()

try: 
    users_db = load_users()
    LIST_GL = [k for k, v in users_db.items() if v["role"] == "GL/UH"]
except: LIST_GL = ["Bapak Andi (GL 1)"]

@st.cache_data(ttl=15)
def get_db():
    data = get_worksheet("Data_SPL").get_all_records()
    return pd.DataFrame(data).astype(str) if data else pd.DataFrame(columns=["ID", "Nama", "NRP", "Section", "Shift", "Tanggal", "Jam", "Perusahaan", "Alasan", "Pengawas_Tujuan", "Status", "Waktu_GL", "Nama_GL", "Waktu_SH", "Nama_SH", "Alasan_Tolak"])

def save_db(df):
    safe_update(get_worksheet("Data_SPL"), [df.columns.values.tolist()] + df.values.tolist())
    st.cache_data.clear()

def hitung_total_lembur_str(jam_str):
    if pd.notna(jam_str) and " - " in str(jam_str):
        try:
            awal, akhir = str(jam_str).split(' - ')
            wa = datetime.strptime(awal.strip(), "%H:%M")
            wk = datetime.strptime(akhir.strip(), "%H:%M")
            selisih = (wk - wa).total_seconds()
            if selisih < 0: selisih += 24 * 3600
            return f"{int(selisih // 3600):02d}:{int((selisih % 3600) // 60):02d}"
        except: return "-"
    return "-"

def create_pdf(row):
    pdf = FPDF(); pdf.add_page(); pdf.rect(5, 5, 200, 287)
    pdf.set_font("Arial", "B", 12); pdf.cell(50, 20, "", border=1) 
    pdf.set_font("Arial", "", 10); pdf.multi_cell(0, 10, "PT. Saptaindra Sejati\nSite Maco", border=1, align='L')
    pdf.ln(10); pdf.set_font("Arial", "BU", 14); pdf.cell(0, 10, "SURAT PERINTAH LEMBUR", ln=True, align="C"); pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 10, " NAMA", border=1); pdf.cell(150, 10, f" {row['Nama']}", border=1, ln=True)
    pdf.cell(40, 10, " NRP/DEPT", border=1); pdf.cell(70, 10, f" {row['NRP']} / {row['Section']}", border=1)
    pdf.cell(30, 10, " SHIFT :", border=1); pdf.cell(50, 10, f" {row['Shift']}", border=1, ln=True) 
    pdf.cell(40, 10, " TANGGAL :", border=1); pdf.cell(70, 10, f" {row['Tanggal']}", border=1)
    pdf.cell(30, 10, " JAM :", border=1); pdf.cell(50, 10, f" {row['Jam']} = {hitung_total_lembur_str(row['Jam'])}", border=1, ln=True)
    pdf.cell(40, 10, " PERUSAHAAN :", border=1); pdf.cell(150, 10, f" {row['Perusahaan']}", border=1, ln=True)
    pdf.cell(190, 10, " Keterangan Lembur :", border="LTR", ln=True); pdf.multi_cell(190, 10, f" {row['Alasan']}\n\n", border="LBR"); pdf.ln(10)
    pdf.cell(95, 5, "Diperintahkan Oleh,", align="C"); pdf.cell(95, 5, "Disetujui Oleh,", ln=True, align="C"); pdf.ln(18)
    pdf.set_text_color(0, 0, 255); pdf.set_font("Arial", "I", 8)
    pdf.cell(95, 5, f"Digitally Signed: {row['Waktu_GL']}" if str(row['Waktu_GL']) != "nan" else "", align="C")
    pdf.cell(95, 5, f"Digitally Signed: {row['Waktu_SH']}" if str(row['Waktu_SH']) != "nan" else "", align="C", ln=True)
    pdf.set_text_color(0, 0, 0); pdf.ln(8) 
    pdf.set_font("Arial", "", 10); pdf.cell(95, 5, "__________________________", align="C", ln=0); pdf.cell(95, 5, "__________________________", align="C", ln=1)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(95, 5, row['Nama_GL'] if str(row['Nama_GL']) != "nan" and row['Nama_GL'] else "GL/UH", align="C") 
    pdf.cell(95, 5, str(row['Nama_SH']).replace(" (PJS Section Head)", "") if pd.notna(row['Nama_SH']) else "Haris Abi Wibowo", align="C", ln=1)
    pdf.set_font("Arial", "", 8); pdf.cell(95, 4, "GL / UH", align="C"); pdf.cell(95, 4, "Section Head" if "(PJS" not in str(row['Nama_SH']) else "PJS Section Head", align="C", ln=1)
    safe_nama = "".join([c for c in str(row['Nama']) if c.isalpha() or c.isdigit() or c==' ']).strip()
    fn = f"SPL_{safe_nama}_{row['Tanggal']}.pdf"; pdf.output(fn); return fn

def display_html_preview(row):
    total_lembur = hitung_total_lembur_str(row['Jam'])
    html_content = f"""
    <div style="background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px; color: black; font-family: Arial, sans-serif; resize: both; overflow: auto; min-width: 300px;">
        <div style="border: 1px solid black; padding: 10px; margin-bottom: 10px;"><b>PT. Saptaindra Sejati<br>Site Maco</b></div>
        <h3 style="text-align: center; text-decoration: underline;">SURAT PERINTAH LEMBUR</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
            <tr><td style="border: 1px solid black; padding: 8px; width: 25%;"><b>NAMA</b></td><td style="border: 1px solid black; padding: 8px;" colspan="3">{row['Nama']}</td></tr>
            <tr><td style="border: 1px solid black; padding: 8px;"><b>NRP/DEPT</b></td><td style="border: 1px solid black; padding: 8px;">{row['NRP']} / {row['Section']}</td><td style="border: 1px solid black; padding: 8px; width: 15%;"><b>SHIFT :</b></td><td style="border: 1px solid black; padding: 8px; width: 20%;">{row['Shift']}</td></tr>
            <tr><td style="border: 1px solid black; padding: 8px;"><b>TANGGAL :</b></td><td style="border: 1px solid black; padding: 8px;">{row['Tanggal']}</td><td style="border: 1px solid black; padding: 8px;"><b>JAM :</b></td><td style="border: 1px solid black; padding: 8px;">{row['Jam']} = {total_lembur}</td></tr>
            <tr><td style="border: 1px solid black; padding: 8px;"><b>PERUSAHAAN :</b></td><td style="border: 1px solid black; padding: 8px;" colspan="3">{row['Perusahaan']}</td></tr>
            <tr><td style="border: 1px solid black; padding: 8px; height: 60px; vertical-align: top;" colspan="4"><b>Keterangan Lembur :</b><br><br>{row['Alasan']}</td></tr>
        </table>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

def proses_login(username_key, password_input):
    users_data = load_users()
    if username_key not in users_data: st.error("Pengguna tidak ditemukan!"); return False
    user_info = users_data[username_key]
    if user_info["blocked"]: st.error(f"🚨 Akun Anda DIBLOKIR. Hubungi Administrator!"); return False
    if str(password_input) == str(user_info["password"]):
        user_info["failed_attempts"] = 0; save_users(users_data); return True
    elif password_input != "":
        user_info["failed_attempts"] += 1
        if user_info["failed_attempts"] >= 3: user_info["blocked"] = True; st.error("🚨 PERINGATAN: Sandi salah 3x. Akun DIBLOKIR!")
        else: st.error(f"❌ Sandi Salah! Sisa percobaan: {3 - user_info['failed_attempts']}")
        save_users(users_data); return False
    return False

# ==========================================
# HALAMAN LANDING PAGE (Sesuai Desain OVERTIX)
# ==========================================
if st.session_state.app_mode == "landing":
    st.write("<br><br>", unsafe_allow_html=True)
    
    col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
    with col_img2:
        try:
            st.image("OVERTIX.png", use_container_width=True)
        except:
            st.markdown("<h1 style='text-align: center; color: white;'>✓ OVERTIX</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <p style="color: #8292a6; font-size: 14px; letter-spacing: 2px; font-weight: 600; margin-top: -10px;">
            SMART OVERTIME <span style="color: #FACC15;">EXECUTION</span> SYSTEM
        </p>
        <div style="display: flex; justify-content: center; align-items: center; margin: 15px 0;">
            <div style="height: 1px; width: 50px; background: rgba(255,255,255,0.2);"></div>
            <span style="color: #0060FF; font-weight: 600; margin: 0 15px; font-size: 13px;">PT SAPTAINDRA SEJATI</span>
            <div style="height: 1px; width: 50px; background: rgba(255,255,255,0.2);"></div>
        </div>
        <h2 style="font-size: 28px; margin-top: 30px;">Selamat Datang!</h2>
        <p style="color: #cbd5e1; font-size: 15px; max-width: 500px; margin: 0 auto;">
            Portal digital untuk pengajuan, approval, monitoring, dan dokumentasi Surat Perintah Lembur (SPL) secara terintegrasi.
        </p>
        <div style="display: flex; justify-content: center; align-items: center; margin: 40px 0 20px 0;">
            <div style="height: 1px; width: 100px; background: rgba(255,255,255,0.1);"></div>
            <span style="color: #8292a6; margin: 0 15px; font-size: 13px;">Silakan pilih portal untuk melanjutkan</span>
            <div style="height: 1px; width: 100px; background: rgba(255,255,255,0.1);"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_space1, col1, col2, col_space2 = st.columns([1, 3, 3, 1])
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(180deg, rgba(0, 96, 255, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%); border: 1px solid rgba(0, 96, 255, 0.3); border-radius: 20px; padding: 30px; text-align: center; height: 280px; display: flex; flex-direction: column; justify-content: center;">
            <div style="background: #0056D2; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; font-size: 24px;">📝</div>
            <h3 style="margin:0; font-size: 22px;">Input SPL</h3>
            <p style="color: #0060FF; font-weight: 600; font-size: 14px; margin-top: 5px; margin-bottom: 15px;">Portal Karyawan</p>
            <div style="height: 2px; width: 30px; background: #0060FF; margin: 0 auto 15px auto;"></div>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5; margin-bottom: 20px;">Masuk ke sini untuk mengisi formulir lembur. Tanpa perlu login atau kata sandi.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("→ Buat Form SPL", use_container_width=True):
            st.session_state.role = "Karyawan"; st.session_state.logged_in = True; st.session_state.app_mode = "main"; st.rerun()

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(180deg, rgba(124, 69, 242, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%); border: 1px solid rgba(124, 69, 242, 0.3); border-radius: 20px; padding: 30px; text-align: center; height: 280px; display: flex; flex-direction: column; justify-content: center;">
            <div style="background: #6431CE; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; font-size: 24px;">🛡️</div>
            <h3 style="margin:0; font-size: 22px;">Portal Approval</h3>
            <p style="color: #7C45F2; font-weight: 600; font-size: 14px; margin-top: 5px; margin-bottom: 15px;">Portal Manajemen</p>
            <div style="height: 2px; width: 30px; background: #7C45F2; margin: 0 auto 15px auto;"></div>
            <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5; margin-bottom: 20px;">Khusus untuk GL/UH, Section Head, dan Administrator untuk verifikasi & approval.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("→ Masuk Portal Approval", use_container_width=True):
            st.session_state.app_mode = "login"; st.rerun()

    st.markdown("<p style='text-align: center; color: #475569; font-size: 12px; margin-top: 60px;'>© 2026 PT. Saptaindra Sejati | Created by Qisma Rosalina Wahda</p>", unsafe_allow_html=True)

# ==========================================
# HALAMAN LOGIN MANAJEMEN
# ==========================================
elif st.session_state.app_mode == "login":
    st.write("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<div style='text-align: center; margin-bottom: 25px;'>", unsafe_allow_html=True)
        try:
            st.image("OVERTIX.png", use_container_width=True)
        except:
            st.markdown("<h1 style='color: white; font-weight: 800; font-size: 36px; letter-spacing: 1px;'>✓ OVERTIX</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #a0aabf; font-size: 15px; margin-top: -10px;'>Portal Approval Manajemen</p></div>", unsafe_allow_html=True)
        
        role = st.selectbox("Pilih Akses Jabatan:", ["Pilih...", "GL/UH", "Section Head", "Admin"])
        if role != "Pilih...":
            users_db = load_users()
            u_list = [k for k, v in users_db.items() if v["role"] == role]
            target_user = "Section Head" if role == "Section Head" else ("Administrator" if role == "Admin" else st.selectbox("Pilih User", u_list))
            pwd = st.text_input("Password", type="password")
            
            st.write("<br>", unsafe_allow_html=True)
            if st.button("LOGIN", use_container_width=True):
                if proses_login(target_user, pwd):
                    st.session_state.logged_in = True; st.session_state.role = role; st.session_state.username = target_user; st.session_state.app_mode = "main"; st.rerun()
                    
        st.write("<br>", unsafe_allow_html=True)
        if st.button("⬅️ Kembali ke Beranda", use_container_width=True):
            st.session_state.app_mode = "landing"; st.rerun()

# ==========================================
# HALAMAN DASHBOARD UTAMA
# ==========================================
elif st.session_state.app_mode == "main" and st.session_state.logged_in:
    
    # HEADER KARYAWAN (SIDE BY SIDE)
    if st.session_state.role == "Karyawan":
        st.markdown("""
        <div style='display: flex; justify-content: space-between; align-items: center; padding: 10px 0;'>
            <div>
                <h2 style='margin:0;'><span style='color: #0061ff;'>✓</span> OVERTIX</h2>
                <p style='margin:0; font-size:12px; color:#94a3b8;'>Smart Overtime Execution System</p>
            </div>
            <div style='display: flex; align-items: center;'>
                <span style='margin-right: 15px;'>🔔</span>
                <span>👤 PT. Saptaindra Sejati ▾</span>
            </div>
        </div>
        <h3 style='margin-top: 20px; border-bottom: 1px solid #2e3c54; padding-bottom: 10px;'>Sistem SPL Digital - Portal Karyawan</h3>
        <p style='color: #64748b;'><span style='color: #60a5fa; border-bottom: 2px solid #60a5fa; padding-bottom: 5px;'>SPL Karyawan</span> &nbsp;&nbsp;&nbsp; Nav Menu</p>
        <br>
        """, unsafe_allow_html=True)
    else:
        # Header Admin / GL / SH
        with st.sidebar:
            st.markdown("### ⚙️ Pengaturan Akun")
            with st.expander("🔑 Ganti Password", expanded=False):
                with st.form("form_ganti_pass", clear_on_submit=True):
                    pass_lama = st.text_input("Password Lama", type="password")
                    pass_baru = st.text_input("Password Baru", type="password")
                    pass_konf = st.text_input("Konfirmasi Baru", type="password")
                    if st.form_submit_button("Simpan"):
                        db_pass = load_users(); user_data = db_pass[st.session_state.username]
                        if str(pass_lama) != str(user_data["password"]): st.error("Password lama salah!")
                        elif pass_baru != pass_konf: st.error("Password baru tidak cocok!")
                        elif len(pass_baru) < 4: st.error("Password terlalu pendek (Min 4)!")
                        else:
                            user_data["password"] = pass_baru; save_users(db_pass); st.success("✅ Diperbarui!")

        col_title, col_logout = st.columns([8, 2])
        with col_title:
            st.title(f"📄 Dashboard {st.session_state.role}")
            st.markdown(f"**👤 Pengguna Aktif:** {st.session_state.username}")
        with col_logout:
            st.write("") 
            if st.button("🚪 Logout Akun", use_container_width=True):
                st.session_state.logged_in = False; st.session_state.role = ""; st.session_state.username = ""; st.session_state.app_mode = "landing"; st.cache_data.clear(); st.rerun()
        st.write("---")

    config_del = load_config()

    # --- KARYAWAN (TAMPILAN SIDE-BY-SIDE SEPERTI GAMBAR) ---
    if st.session_state.role == "Karyawan":
        col_form, col_table = st.columns([1, 1.3]) # Pembagian rasio layar
        
        # SISI KIRI: FORM PENGISIAN
        with col_form:
            st.markdown("<div class='card-header'>PENGISIAN FORM SPL</div>", unsafe_allow_html=True)
            with st.container(border=True):
                with st.form("form_spl", clear_on_submit=True):
                    nama = st.text_input("Name")
                    
                    c_nrp, c_sec = st.columns(2)
                    nrp = c_nrp.text_input("NRP") 
                    section = c_sec.selectbox("Section", ["Production", "Logistik", "Maintenance"]) 
                    
                    perusahaan = "PT. Saptaindra Sejati"
                    shift = "Shift 1"
                    pengawas_tujuan = "Bapak Andi (GL 1)"
                    
                    c_tgl, c_jam = st.columns(2)
                    tgl = c_tgl.date_input("Tanggal", value=get_wib_time().date())
                    jam_input = c_jam.text_input("Jam Lembur", placeholder="Contoh: 17:00 - 21:00")
                    
                    alasan = st.text_area("Keterangan Lembur", placeholder="Contoh: Pusat Bantuan", height=100)
                    
                    c_btn1, c_btn2 = st.columns(2)
                    submitted = c_btn1.form_submit_button("Kirim Pengajuan Lembur", use_container_width=True)
                    dukungan = c_btn2.form_submit_button("Dukungan Teknis", use_container_width=True)
                    
                    if submitted:
                        if not nama.strip() or not nrp.strip() or not jam_input.strip() or not alasan.strip(): 
                            st.error("⚠️ GAGAL: Semua kolom wajib diisi!")
                        elif " - " not in jam_input:
                            st.error("⚠️ GAGAL: Format Jam Lembur salah, contoh: 17:00 - 21:00")
                        else:
                            df = get_db()
                            new_data = {
                                "ID": str(int(time.time())), "Nama": nama, "NRP": nrp, "Section": section, "Shift": shift, "Tanggal": str(tgl), 
                                "Jam": jam_input, "Perusahaan": perusahaan, "Alasan": alasan, 
                                "Pengawas_Tujuan": pengawas_tujuan, 
                                "Status": "Pending GL", "Waktu_GL": "", "Nama_GL": "", "Waktu_SH": "", "Nama_SH": "", "Alasan_Tolak": ""
                            }
                            save_db(pd.concat([df, pd.DataFrame([new_data])], ignore_index=True))
                            st.success(f"✅ BERHASIL: SPL terkirim!")
                            time.sleep(1); st.rerun()

        # SISI KANAN: DAFTAR PENGAJUAN (HTML TABLE CUSTOM - KECIL/RAPAT, TULISAN BESAR)
        with col_table:
            st.markdown("<div class='card-header'>DAFTAR PENGAJUAN LEMBUR SAYA</div>", unsafe_allow_html=True)
            
            df = get_db()
            if df.empty:
                st.info("Belum ada riwayat pengajuan lembur.")
            else:
                df_karyawan = df.tail(10).copy()
                df_karyawan = df_karyawan.reset_index(drop=True)
                
                html_table = "<div class='custom-table-container'><table class='custom-table'>"
                html_table += "<tr><th>NO.</th><th>NAMA</th><th>NRP</th><th>SECTION</th><th>TANGGAL</th><th>JAM<br>LEMBUR</th><th>STATUS</th><th>PENGAWAS<br>TUJUAN</th></tr>"
                
                for i, row in df_karyawan.iterrows():
                    status_text = str(row['Status']).upper()
                    if "FINAL" in status_text: status_col = "<span style='color:#10b981; font-weight:bold;'>FINAL<br>APPROVED</span>"
                    elif "DITOLAK" in status_text: status_col = "<span style='color:#ef4444; font-weight:bold;'>DITOLAK</span>"
                    else: status_col = f"<span style='color:#facc15; font-weight:bold;'>{status_text.replace(' ', '<br>')}</span>"
                    
                    html_table += f"<tr>"
                    html_table += f"<td>{i+1}.</td><td>{row['Nama']}</td><td>{row['NRP']}</td><td>{row['Section']}</td>"
                    try: tgl_str = datetime.strptime(row['Tanggal'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except: tgl_str = row['Tanggal']
                    html_table += f"<td>{tgl_str}</td>"
                    
                    jam_arr = str(row['Jam']).split(" - ")
                    jam_html = f"{jam_arr[0]} -<br>{jam_arr[1]}" if len(jam_arr)==2 else row['Jam']
                    
                    html_table += f"<td>{jam_html}</td><td>{status_col}</td>"
                    peng_tujuan = str(row['Pengawas_Tujuan']).replace(' (GL 1)','<br>(GL 1)')
                    html_table += f"<td>{peng_tujuan}</td></tr>"
                    
                html_table += "</table></div>"
                st.markdown(html_table, unsafe_allow_html=True)
                
        st.write("<br><hr>", unsafe_allow_html=True)
        col_out1, col_out2 = st.columns([8, 2])
        if col_out2.button("🚪 Keluar ke Beranda", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.role = ""; st.session_state.app_mode = "landing"; st.rerun()

    # --- GL/UH ---
    elif st.session_state.role == "GL/UH":
        df_gl = get_db()
        st.subheader("Menunggu Verifikasi Anda (Sebagai GL/UH)")
        pending_gl = df_gl[(df_gl["Status"] == "Pending GL") & (df_gl["Pengawas_Tujuan"] == st.session_state.username)]
        
        if pending_gl.empty: st.info("Tidak ada SPL baru untuk Anda saat ini.")
        else:
            with st.container():
                st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
                for i, (idx, row) in enumerate(pending_gl.iterrows(), 1):
                    cols = st.columns([0.5, 1, 2, 1, 1, 1.5, 1.5, 1, 1, 1])
                    if i == 1:
                        for idx_t, title in enumerate(["**NO**", "**Tanggal**", "**Nama**", "**NRP**", "**Shift**", "**Jam awal**", "**jam Akhir**", "**View**", "**Approve**", "**Tolak**"]): cols[idx_t].markdown(title)
                        cols = st.columns([0.5, 1, 2, 1, 1, 1.5, 1.5, 1, 1, 1])
                    cols[0].write(str(i)); cols[1].write(row['Tanggal']); cols[2].write(row['Nama'])
                    cols[3].write(row['NRP']); cols[4].write(row['Shift'].replace('Shift ', ''))
                    jams = row['Jam'].split(' - '); cols[5].write(jams[0] if len(jams) > 0 else ""); cols[6].write(jams[1] if len(jams) > 1 else "")
                    with cols[7]:
                        with st.popover("👁️"): display_html_preview(row)
                    with cols[8]:
                        if st.button("Approve", key=f"gl_app_{row['ID']}"):
                            df_gl.loc[idx, ["Status", "Waktu_GL", "Nama_GL"]] = ["Pending SH", get_wib_time().strftime("%Y-%m-%d %H:%M"), st.session_state.username]; save_db(df_gl); st.rerun()
                    with cols[9]:
                        with st.popover("Tolak"):
                            alasan_tolak = st.text_area("Masukkan Alasan Penolakan:", key=f"txt_tolak_gl_{row['ID']}")
                            if st.button("Konfirmasi Tolak", key=f"gl_del_{row['ID']}"):
                                if not alasan_tolak.strip(): st.error("Alasan penolakan tidak boleh kosong!")
                                else:
                                    df_gl.loc[idx, ["Status", "Waktu_GL", "Nama_GL", "Alasan_Tolak"]] = ["Ditolak", get_wib_time().strftime("%Y-%m-%d %H:%M"), st.session_state.username, alasan_tolak]; save_db(df_gl); st.rerun()

        # ---> BAGIAN YANG SEMPAT HILANG (RIWAYAT GL) <---
        st.subheader("Riwayat Pekerjaan (Sebagai GL)")
        history_gl = df_gl[((df_gl["Status"] == "Pending SH") | (df_gl["Status"] == "Final Approved") | (df_gl["Status"] == "Ditolak")) & (df_gl["Nama_GL"] == st.session_state.username)]
        if not history_gl.empty:
            for idx, row in history_gl.iterrows():
                if row['Status'] == 'Ditolak': st.error(f"❌ **{row['Nama']}** - {row['Tanggal']} (Ditolak pada: {row['Waktu_GL']}) | **Alasan:** {row.get('Alasan_Tolak', '')}")
                else: st.write(f"✅ **{row['Nama']}** - {row['Tanggal']} (Status saat ini: {row['Status']})")
        # ------------------------------------------------

        if config_del["status_aktif"] and config_del["pjs_nama"] == st.session_state.username:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.warning("👑 **TUGAS PENDELEGASIAN:** Anda saat ini bertindak sebagai **Pjs. Section Head**.")
            st.subheader("Verifikasi Akhir (Kewenangan Pjs. Section Head)")
            pending_sh = df_gl[df_gl["Status"] == "Pending SH"]
            if pending_sh.empty: st.info("Antrean Final Approve kosong.")
            else:
                with st.container():
                    st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
                    for i, (idx, row) in enumerate(pending_sh.iterrows(), 1):
                        cols = st.columns([0.5, 1, 2, 1, 1, 1.5, 1.5, 1, 1, 1])
                        if i == 1:
                            for idx_t, title in enumerate(["**NO**", "**Tanggal**", "**Nama**", "**NRP**", "**Shift**", "**Jam awal**", "**jam Akhir**", "**View**", "**Approve**", "**Tolak**"]): cols[idx_t].markdown(title)
                            cols = st.columns([0.5, 1, 2, 1, 1, 1.5, 1.5, 1, 1, 1])
                        cols[0].write(str(i)); cols[1].write(row['Tanggal']); cols[2].write(row['Nama'])
                        cols[3].write(row['NRP']); cols[4].write(row['Shift'].replace('Shift ', ''))
                        jams = row['Jam'].split(' - '); cols[5].write(jams[0] if len(jams) > 0 else ""); cols[6].write(jams[1] if len(jams) > 1 else "")
                        with cols[7]:
                            with st.popover("👁️"): display_html_preview(row)
                        with cols[8]:
                            if st.button("Approve", key=f"pjs_app_{row['ID']}"):
                                df_gl.loc[idx, ["Status", "Waktu_SH", "Nama_SH"]] = ["Final Approved", get_wib_time().strftime("%Y-%m-%d %H:%M"), f"{st.session_state.username} (PJS)"]; save_db(df_gl); st.rerun()
                        with cols[9]:
                            with st.popover("Tolak"):
                                alasan_pjs = st.text_area("Masukkan Alasan Penolakan:", key=f"txt_tolak_pjs_{row['ID']}")
                                if st.button("Konfirmasi Tolak", key=f"pjs_del_{row['ID']}"):
                                    if not alasan_pjs.strip(): st.error("Alasan penolakan tidak boleh kosong!")
                                    else:
                                        df_gl.loc[idx, ["Status", "Waktu_SH", "Nama_SH", "Alasan_Tolak"]] = ["Ditolak", get_wib_time().strftime("%Y-%m-%d %H:%M"), f"{st.session_state.username} (PJS)", alasan_pjs]; save_db(df_gl); st.rerun()

            st.subheader("Arsip Dokumen Selesai (Sebagai Pjs. Section Head)")
            history_pjs = df_gl[(df_gl["Status"] == "Final Approved") & (df_gl["Nama_SH"] == f"{st.session_state.username} (PJS Section Head)")]
            if history_pjs.empty: st.write("Belum ada dokumen SPL yang Anda selesaikan sebagai Pjs.")
            else:
                for idx, row in history_pjs.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1: st.write(f"📄 **SPL {row['Nama']} & {row['Tanggal']}** (Disetujui pada: {row['Waktu_SH']})")
                    with col2:
                        file_pdf = create_pdf(row)
                        with open(file_pdf, "rb") as f: st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_pjs_fin_{row['ID']}")

    # --- SECTION HEAD ---
    elif st.session_state.role == "Section Head":
        with st.expander("⚙️ PENGATURAN DELEGASI CUTI / OFFSITE", expanded=config_del["status_aktif"]):
            col_d1, col_d2 = st.columns([2, 2])
            with col_d1:
                idx_default = LIST_GL.index(config_del["pjs_nama"]) if config_del["pjs_nama"] in LIST_GL else 0
                pjs_pilihan = st.selectbox("Pilih Pengawas Sebagai Pejabat Sementara (Pjs):", LIST_GL, index=idx_default)
            with col_d2:
                st.write("") ; st.write("") 
                if not config_del["status_aktif"]:
                    if st.button("🚀 Aktifkan Delegasi (Saya Offsite)"): config_del["status_aktif"] = True; config_del["pjs_nama"] = pjs_pilihan; save_config(config_del); st.rerun()
                else:
                    if st.button("🛑 Cabut Delegasi (Saya Onsite)"): config_del["status_aktif"] = False; config_del["pjs_nama"] = ""; save_config(config_del); st.rerun()
            if config_del["status_aktif"]: st.error(f"🚨 **STATUS:** Kewenangan Section Head saat ini dialihkan kepada **{config_del['pjs_nama']}**.")
        st.markdown("<hr>", unsafe_allow_html=True)

        df_sh = get_db()
        st.subheader("Verifikasi Akhir (Final Approve)")
        pending_sh = df_sh[df_sh["Status"] == "Pending SH"]
        if pending_sh.empty: st.info("Tidak ada SPL menunggu verifikasi Section Head.")
        else:
            with st.container():
                st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
                for i, (idx, row) in enumerate(pending_sh.iterrows(), 1):
                    cols = st.columns([0.5, 1, 2, 1, 1, 1.5, 1.5, 1, 1, 1])
                    if i == 1:
                        for idx_t, title in enumerate(["**NO**", "**Tanggal**", "**Nama**", "**NRP**", "**Shift**", "**Jam awal**", "**jam Akhir**", "**View**", "**Approve**", "**Tolak**"]): cols[idx_t].markdown(title)
                        cols = st.columns([0.5, 1, 2, 1, 1, 1.5, 1.5, 1, 1, 1])
                    cols[0].write(str(i)); cols[1].write(row['Tanggal']); cols[2].write(row['Nama'])
                    cols[3].write(row['NRP']); cols[4].write(row['Shift'].replace('Shift ', ''))
                    jams = row['Jam'].split(' - '); cols[5].write(jams[0] if len(jams) > 0 else ""); cols[6].write(jams[1] if len(jams) > 1 else "")
                    with cols[7]:
                        with st.popover("👁️"): display_html_preview(row)
                    with cols[8]:
                        if st.button("Approve", key=f"sh_app_{row['ID']}"):
                            df_sh.loc[idx, ["Status", "Waktu_SH", "Nama_SH"]] = ["Final Approved", get_wib_time().strftime("%Y-%m-%d %H:%M"), "Haris Abi Wibowo"]; save_db(df_sh); st.rerun()
                    with cols[9]:
                        with st.popover("Tolak"):
                            alasan_sh = st.text_area("Alasan Penolakan:", key=f"txt_tolak_sh_{row['ID']}")
                            if st.button("Konfirmasi Tolak", key=f"sh_del_{row['ID']}"):
                                if not alasan_sh.strip(): st.error("Wajib diisi!")
                                else:
                                    df_sh.loc[idx, ["Status", "Waktu_SH", "Nama_SH", "Alasan_Tolak"]] = ["Ditolak", get_wib_time().strftime("%Y-%m-%d %H:%M"), "Haris Abi Wibowo", alasan_sh]; save_db(df_sh); st.rerun()

        st.subheader("Arsip Dokumen Selesai (Siap Unduh)")
        approved_sh = df_sh[df_sh["Status"] == "Final Approved"]
        if approved_sh.empty: st.write("Belum ada dokumen SPL yang selesai.")
        else:
            for idx, row in approved_sh.iterrows():
                col1, col2 = st.columns([3, 1])
                nama_tampil = str(row['Nama_SH']).replace(" (PJS Section Head)", "") if pd.notna(row['Nama_SH']) else 'Haris Abi Wibowo'
                with col1: st.write(f"📄 **SPL {row['Nama']} & {row['Tanggal']}** (Disetujui Oleh: {nama_tampil})")
                with col2:
                    file_pdf = create_pdf(row)
                    with open(file_pdf, "rb") as f: st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_sh_fin_{row['ID']}")

        st.subheader("❌ Arsip Dokumen Ditolak")
        rejected_sh = df_sh[(df_sh["Status"] == "Ditolak") & (df_sh["Nama_SH"] == "Haris Abi Wibowo")]
        if rejected_sh.empty: st.write("Belum ada riwayat penolakan dari Anda.")
        else:
            for idx, row in rejected_sh.iterrows():
                st.error(f"❌ **SPL {row['Nama']} & {row['Tanggal']}** (Anda tolak pada: {row['Waktu_SH']}) | **Alasan:** {row.get('Alasan_Tolak', '')}")

    # --- ADMIN ---
    elif st.session_state.role == "Admin":
        df_admin_raw = get_db()
        st.subheader("🎛️ Filter Data SPL")
        
        mode_filter = st.radio("Pilih Mode Filter:", ["Semua Data", "Tanggal", "Bulan", "Tahun", "Range Tanggal"], horizontal=True)
        df_admin = df_admin_raw.copy()
        nama_file_excel = "Rekapan_SPL_Semua"
        
        if mode_filter == "Tanggal":
            tgl_filter = st.date_input("Pilih Tanggal:", value=get_wib_time().date())
            df_admin = df_admin[df_admin["Tanggal"] == str(tgl_filter)]
            nama_file_excel = f"Rekapan_SPL_{tgl_filter}"
        elif mode_filter == "Bulan":
            list_bulan = [f"{i:02d}" for i in range(1, 13)]
            bln = st.selectbox("Pilih Bulan:", list_bulan, index=get_wib_time().month - 1)
            df_admin = df_admin[df_admin["Tanggal"].str.contains(f"-{bln}-")]
            nama_file_excel = f"Rekapan_SPL_Bulan_{bln}"
        elif mode_filter == "Tahun":
            list_tahun = [str(y) for y in range(2024, 2031)]
            thn = st.selectbox("Pilih Tahun:", list_tahun, index=list_tahun.index(str(get_wib_time().year)) if str(get_wib_time().year) in list_tahun else 0)
            df_admin = df_admin[df_admin["Tanggal"].str.startswith(thn)]
            nama_file_excel = f"Rekapan_SPL_Tahun_{thn}"
        elif mode_filter == "Range Tanggal":
            r1, r2 = st.columns(2)
            d_mulai = r1.date_input("Mulai:", value=get_wib_time().date()-timedelta(days=7))
            d_akhir = r2.date_input("Sampai:", value=get_wib_time().date())
            df_admin = df_admin[(df_admin['Tanggal'] >= str(d_mulai)) & (df_admin['Tanggal'] <= str(d_akhir))]
            nama_file_excel = f"Rekapan_SPL_{d_mulai}_to_{d_akhir}"
            
        st.markdown("---")
        
        if df_admin.empty: 
            st.warning("⚠️ Tidak ada data SPL yang ditemukan untuk filter yang dipilih.")
        else:
            st.subheader("📊 Tabel Database SPL & Rekapan Excel")
            
            # --- EXCEL (.XLSX) ---
            df_display = df_admin.copy()
            df_display['Jam Awal'] = df_display['Jam'].apply(lambda x: x.split(' - ')[0] if pd.notna(x) and ' - ' in str(x) else "")
            df_display['Jam Akhir'] = df_display['Jam'].apply(lambda x: x.split(' - ')[1] if pd.notna(x) and ' - ' in str(x) else "")
            
            def hitung_durasi(jam_str):
                try:
                    awal, akhir = jam_str.split(' - ')
                    wa = datetime.strptime(awal.strip(), "%H:%M")
                    wk = datetime.strptime(akhir.strip(), "%H:%M")
                    selisih = (wk - wa).total_seconds() / 3600
                    if selisih < 0: selisih += 24
                    return round(selisih, 2)
                except: return 0

            df_display['Total Lembur (Jam)'] = df_display['Jam'].apply(hitung_durasi)
            df_display.insert(0, "No.", range(1, len(df_display) + 1))
            cols_order = ['No.', 'Tanggal', 'Nama', 'NRP', 'Section', 'Shift', 'Jam Awal', 'Jam Akhir', 'Total Lembur (Jam)', 'Perusahaan', 'Alasan', 'Status', 'Pengawas_Tujuan', 'Waktu_GL', 'Nama_GL', 'Waktu_SH', 'Nama_SH', 'Alasan_Tolak']
            cols_order = [c for c in cols_order if c in df_display.columns]
            df_excel = df_display[cols_order]
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_excel.to_excel(writer, index=False, sheet_name='Rekap_SPL')
            st.download_button("📥 Download Tabel di Bawah (Format .xlsx)", data=buffer.getvalue(), file_name=f"{nama_file_excel}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            # --- TAMPILAN DASHBOARD ---
            tabel_tampil = df_admin[['Tanggal', 'Nama', 'NRP', 'Section', 'Shift', 'Jam', 'Status', 'Pengawas_Tujuan']].copy()
            tabel_tampil.index = range(1, len(tabel_tampil) + 1)
            
            st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
            st.dataframe(tabel_tampil, use_container_width=True)
            
            st.markdown("---")
            
            # --- ARSIP PDF DENGAN DAFTAR MINI ---
            st.subheader("🗂️ Arsip Dokumen PDF (Siap Unduh)")
            approved_admin = df_admin[df_admin["Status"] == "Final Approved"]
            if approved_admin.empty: st.write("Belum ada dokumen PDF yang di-generate pada filter ini.")
            else:
                for idx, row in approved_admin.iterrows():
                    c_pdf1, c_pdf2, c_pdf3 = st.columns([1, 4, 2])
                    c_pdf1.write(f"📅 {row['Tanggal']}")
                    c_pdf2.write(f"👤 **{row['Nama']}** (NRP: {row['NRP']})")
                    file_pdf = create_pdf(row)
                    with open(file_pdf, "rb") as f: c_pdf3.download_button("⬇️ Download PDF", f, file_name=file_pdf, key=f"dl_adm_fin_{row['ID']}", use_container_width=True)
                    st.markdown("<hr style='margin: 0px; opacity: 0.1;'>", unsafe_allow_html=True)

            st.markdown("---")
            
            # --- TRACKING ---
            st.subheader("⏳ Tracking Dokumen Belum Selesai (Pending)")
            pending_admin = df_admin[(df_admin["Status"] != "Final Approved") & (df_admin["Status"] != "Ditolak")]
            if pending_admin.empty: st.success("TIDAK ADA ANTRIAN pada filter ini.")
            else:
                for idx, row in pending_admin.iterrows():
                    if row["Status"] == "Pending GL": st.warning(f"📌 **SPL: {row['Nama']} & {row['Tanggal']}** ➔ Saat ini posisinya di: **Menunggu Persetujuan GL/UH: {row['Pengawas_Tujuan']}**")
                    else: st.info(f"📌 **SPL: {row['Nama']} & {row['Tanggal']}** ➔ Saat ini posisinya di: **Menunggu Persetujuan Akhir Section Head**")
            st.markdown("---")

            # --- DITOLAK ---
            st.subheader("❌ Riwayat Pengajuan Ditolak")
            rejected_admin = df_admin[df_admin["Status"] == "Ditolak"]
            if rejected_admin.empty: st.write("Tidak ada pengajuan yang ditolak pada filter ini.")
            else:
                for idx, row in rejected_admin.iterrows():
                    penolak = row['Nama_SH'] if pd.notna(row['Nama_SH']) and str(row['Nama_SH']).strip() and str(row['Nama_SH']) != "nan" else row['Nama_GL']
                    alasan = row.get('Alasan_Tolak', 'Tidak ada alasan.')
                    st.error(f"❌ **SPL {row['Nama']} & {row['Tanggal']}** ➔ Ditolak oleh: **{penolak}** | **Alasan:** {alasan}")
            st.markdown("---")
            
        # --- MANAJEMEN AKUN ---
        st.subheader("🔐 Manajemen Keamanan Akun")
        db_admin_users = load_users()
        col_ua1, col_ua2 = st.columns(2)
        with col_ua1:
            st.markdown("**Akun Terblokir (Gagal Login 3x):**")
            blocked_users = [k for k, v in db_admin_users.items() if v["blocked"]]
            if not blocked_users: st.success("Aman! Tidak ada akun yang terblokir saat ini.")
            else:
                for bu in blocked_users:
                    col_b1, col_b2 = st.columns([3, 2])
                    col_b1.error(f"🔒 {bu}")
                    if col_b2.button("Buka Blokir", key=f"unblock_{bu}"):
                        db_admin_users[bu]["blocked"] = False; db_admin_users[bu]["failed_attempts"] = 0; db_admin_users[bu]["password"] = "default123"; save_users(db_admin_users); st.success(f"Berhasil! Akun {bu} dibuka. Sandi direset ke: default123"); time.sleep(2); st.rerun()
                        
        with col_ua2:
            st.markdown("**Reset Sandi Pengguna ke Default:**")
            user_to_reset = st.selectbox("Pilih Pengguna:", list(db_admin_users.keys()))
            if st.button("Reset Sandi ke 'default123'"):
                db_admin_users[user_to_reset]["password"] = "default123"; db_admin_users[user_to_reset]["failed_attempts"] = 0; db_admin_users[user_to_reset]["blocked"] = False; save_users(db_admin_users); st.success(f"✅ Sandi untuk {user_to_reset} berhasil diubah menjadi: default123")
