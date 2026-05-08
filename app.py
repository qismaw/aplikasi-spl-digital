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
# 💎 CSS SUPER PREMIUM: OVERTIX DARK THEME (Sesuai image_53357b.png)
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
        background: radial-gradient(circle at top, #0b1426 0%, #030612 100%) !important;
        color: white !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }

    /* 3. STYLING INPUT & DROPDOWN AGAR PUTIH TERANG */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 8px !important;
    }
    .stTextInput input::placeholder {
        color: #8292a6 !important;
        -webkit-text-fill-color: #8292a6 !important;
    }
    div[data-baseweb="select"] span { color: #ffffff !important; font-weight: 500 !important; }
    div[data-baseweb="popover"] ul { background-color: #0b1426 !important; }
    div[data-baseweb="popover"] li { color: #ffffff !important; }
    .stSelectbox label, .stTextInput label { color: #cbd5e1 !important; font-weight: 500 !important;}

    /* 4. STYLING TOMBOL CUSTOM OVERTIX */
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }
    .stButton>button:hover { transform: translateY(-2px) !important; }

    /* Tombol Karyawan (Biru Terang) */
    div[data-testid="stButton"] button:has(p:contains("Buat Form SPL")),
    div[data-testid="stButton"] button:has(p:contains("Kirim Pengajuan")) {
        background: linear-gradient(90deg, #0056D2, #0060FF) !important; color: white !important;
    }
    /* Tombol Manajemen (Ungu) */
    div[data-testid="stButton"] button:has(p:contains("Masuk Portal Approval")),
    div[data-testid="stButton"] button:has(p:contains("LOGIN")) {
        background: linear-gradient(90deg, #6431CE, #7C45F2) !important; color: white !important;
    }
    
    div[data-testid="stButton"] button:has(p:contains("Approve")) { background-color: #10b981 !important; color: white !important; }
    div[data-testid="stButton"] button:has(p:contains("Tolak")) { background-color: #ef4444 !important; color: white !important; }
    div[data-testid="stButton"] button:has(p:contains("Kembali")), div[data-testid="stButton"] button:has(p:contains("Keluar")) {
        background: rgba(255, 255, 255, 0.1) !important; color: white !important; border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }

    /* 5. TABEL DASHBOARD AGAR RAPI DI HP */
    @media (max-width: 768px) { body, .stApp { overflow-x: hidden !important; } }
    div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) {
        background-color: rgba(255,255,255,0.02) !important; border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important; padding: 10px !important; margin-bottom: 20px !important; overflow-x: auto !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) div[data-testid="stHorizontalBlock"] {
        min-width: 1000px !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; align-items: center !important; padding: 10px 0;
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
    html_content = f"""
    <div style="background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px; color: black; font-family: Arial, sans-serif;">
        <div style="border: 1px solid black; padding: 10px; margin-bottom: 10px;"><b>PT. Saptaindra Sejati<br>Site Maco</b></div>
        <h3 style="text-align: center; text-decoration: underline;">SURAT PERINTAH LEMBUR</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
            <tr><td style="border: 1px solid black; padding: 8px; width: 25%;"><b>NAMA</b></td><td style="border: 1px solid black; padding: 8px;" colspan="3">{row['Nama']}</td></tr>
            <tr><td style="border: 1px solid black; padding: 8px;"><b>NRP/DEPT</b></td><td style="border: 1px solid black; padding: 8px;">{row['NRP']} / {row['Section']}</td><td style="border: 1px solid black; padding: 8px; width: 15%;"><b>SHIFT :</b></td><td style="border: 1px solid black; padding: 8px; width: 20%;">{row['Shift']}</td></tr>
            <tr><td style="border: 1px solid black; padding: 8px;"><b>TANGGAL :</b></td><td style="border: 1px solid black; padding: 8px;">{row['Tanggal']}</td><td style="border: 1px solid black; padding: 8px;"><b>JAM :</b></td><td style="border: 1px solid black; padding: 8px;">{row['Jam']} = {hitung_total_lembur_str(row['Jam'])}</td></tr>
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
    
    # Header Logo
    st.markdown("""
    <div style="text-align: center; margin-bottom: 40px;">
        <h1 style="font-size: 55px; font-weight: 800; letter-spacing: 2px; margin-bottom: 0;">
            <span style="color: #0060FF;">✓</span> OVERTIX
        </h1>
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

    # Cards Section
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
        # Tombol dipisah agar fungsi klik Streamlit berjalan normal
        if st.button("→ Buat Form SPL", use_container_width=True):
            st.session_state.role = "Karyawan"
            st.session_state.logged_in = True
            st.session_state.app_mode = "main"
            st.rerun()

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
            st.session_state.app_mode = "login"
            st.rerun()

    st.markdown("<p style='text-align: center; color: #475569; font-size: 12px; margin-top: 60px;'>© 2026 PT. Saptaindra Sejati | Created by Qisma Rosalina Wahda</p>", unsafe_allow_html=True)

# ==========================================
# HALAMAN LOGIN MANAJEMEN
# ==========================================
elif st.session_state.app_mode == "login":
    st.write("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 25px;">
            <h1 style="font-size: 40px; font-weight: 800; margin-bottom: 0;">
                <span style="color: #0060FF;">✓</span> OVERTIX
            </h1>
            <p style="color: #8292a6; font-size: 14px;">Portal Approval Manajemen</p>
        </div>
        """, unsafe_allow_html=True)
        
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
    if st.session_state.role != "Karyawan":
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
        st.title("📄 Pengisian Form SPL" if st.session_state.role == "Karyawan" else f"📄 Dashboard {st.session_state.role}")
        if st.session_state.role != "Karyawan": st.markdown(f"**👤 Pengguna Aktif:** {st.session_state.username}")
    with col_logout:
        st.write("") 
        if st.button("🚪 Keluar / Beranda" if st.session_state.role == "Karyawan" else "🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False; st.session_state.role = ""; st.session_state.username = ""; st.session_state.app_mode = "landing"; st.cache_data.clear(); st.rerun()
    st.write("---")
    
    config_del = load_config()

    # --- KARYAWAN ---
    if st.session_state.role == "Karyawan":
        with st.form("form_spl", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nama = col1.text_input("Nama Karyawan *")
            nrp = col2.text_input("NRP *") 
            cs, cp = st.columns(2)
            section = cs.selectbox("Section", ["Logistik"]) 
            perusahaan = cp.selectbox("Nama Perusahaan", ["PT. Saptaindra Sejati", "PT. Cheisa Mandiri Utama", "PT. Borneo Mura Perkasa"])
            ct, ch = st.columns(2)
            tgl = ct.date_input("Tanggal", value=get_wib_time().date(), disabled=True)
            shift = ch.selectbox("Shift Lembur", ["Shift 1", "Shift 2"])
            pengawas_tujuan = st.selectbox("Pengawas (GL) Yang Bertugas", LIST_GL)
            
            st.markdown("**Waktu Lembur:**")
            col_jam_awal, col_jam_akhir = st.columns(2)
            list_jam = [f"{i:02d}" for i in range(24)]; list_menit = [f"{i:02d}" for i in range(60)]
            with col_jam_awal:
                c1, c2 = st.columns(2)
                jam_a = c1.selectbox("Jam Mulai", list_jam); menit_a = c2.selectbox("Menit Mulai", list_menit)
            with col_jam_akhir:
                c3, c4 = st.columns(2)
                jam_s = c3.selectbox("Jam Selesai", list_jam); menit_s = c4.selectbox("Menit Selesai", list_menit)
            
            alasan = st.text_area("Keterangan Lembur *")
            st.markdown("*Keterangan: Tanda (*) wajib diisi*")
            if st.form_submit_button("Kirim Pengajuan Lembur"):
                waktu_awal_menit = (int(jam_a) * 60) + int(menit_a)
                waktu_akhir_menit = (int(jam_s) * 60) + int(menit_s)
                if not nama.strip() or not nrp.strip() or not alasan.strip(): st.error("⚠️ GAGAL: Nama, NRP, Keterangan wajib diisi!")
                elif waktu_akhir_menit <= waktu_awal_menit: st.error("⚠️ GAGAL: Jam Akhir harus lebih besar dari Jam Awal!")
                else:
                    df = get_db()
                    new_data = {"ID": str(int(time.time())), "Nama": nama, "NRP": nrp, "Section": section, "Shift": shift, "Tanggal": str(tgl), "Jam": f"{jam_a}:{menit_a} - {jam_s}:{menit_s}", "Perusahaan": perusahaan, "Alasan": alasan, "Pengawas_Tujuan": pengawas_tujuan, "Status": "Pending GL", "Waktu_GL": "", "Nama_GL": "", "Waktu_SH": "", "Nama_SH": "", "Alasan_Tolak": ""}
                    save_db(pd.concat([df, pd.DataFrame([new_data])], ignore_index=True))
                    st.success(f"✅ BERHASIL: SPL untuk {nama} terkirim!"); time.sleep(1.5); st.rerun()

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
                                if not alasan_tolak.strip(): st.error("Alasan tidak boleh kosong!")
                                else:
                                    df_gl.loc[idx, ["Status", "Waktu_GL", "Nama_GL", "Alasan_Tolak"]] = ["Ditolak", get_wib_time().strftime("%Y-%m-%d %H:%M"), st.session_state.username, alasan_tolak]; save_db(df_gl); st.rerun()

        if config_del["status_aktif"] and config_del["pjs_nama"] == st.session_state.username:
            st.markdown("<br>", unsafe_allow_html=True)
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
                                alasan_pjs = st.text_area("Alasan Penolakan:", key=f"txt_tolak_pjs_{row['ID']}")
                                if st.button("Konfirmasi Tolak", key=f"pjs_del_{row['ID']}"):
                                    if not alasan_pjs.strip(): st.error("Alasan tidak boleh kosong!")
                                    else:
                                        df_gl.loc[idx, ["Status", "Waktu_SH", "Nama_SH", "Alasan_Tolak"]] = ["Ditolak", get_wib_time().strftime("%Y-%m-%d %H:%M"), f"{st.session_state.username} (PJS)", alasan_pjs]; save_db(df_gl); st.rerun()

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
            if config_del["status_aktif"]: st.error(f"🚨 **STATUS:** Kewenangan dialihkan kepada **{config_del['pjs_nama']}**.")
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
            st.dataframe(tabel_tampil, use_container_width=True)
            
            st.markdown("---")
            
            # --- ARSIP PDF DENGAN DAFTAR MINI (REFERENSI image_647afb.png) ---
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
                    st.error(f"❌ **SPL {row['Nama']} & {row['Tanggal']}** ➔ Ditolak oleh: **{penolak}** | **Alasan:** {row.get('Alasan_Tolak', '')}")
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
