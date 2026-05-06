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

# Konfigurasi Halaman & CSS Kustom
st.set_page_config(page_title="Sistem SPL Digital", layout="wide")

st.markdown("""
<style>
/* 1. Warna Tombol & Popover Umum */
div[data-testid="stButton"] button:has(p:contains("Approve")) { background-color: #00c853 !important; color: white !important; font-weight: bold !important; }
div[data-testid="stButton"] button:has(p:contains("Tolak")) { background-color: #ff1744 !important; color: white !important; font-weight: bold !important; }
div[data-testid="stPopoverBody"] { width: 650px !important; max-width: 95vw !important; }

/* ==========================================================
   TABEL HP: AMAN, TIDAK HILANG, & UKURAN SEMPIT (650px)
   ========================================================== */
@media (max-width: 768px) {
    /* MENGUNCI HALAMAN UTAMA AGAR TIDAK GESER */
    html, body, #root, [data-testid="stAppViewContainer"], .main, .block-container {
        overflow-x: hidden !important;
        max-width: 100% !important;
    }

    /* WADAH TABEL (BISA DI-SCROLL) */
    div[data-testid="stVerticalBlock"]:has(.table-marker) {
        overflow-x: auto !important;
        max-width: 100% !important;
        display: block !important;
        -webkit-overflow-scrolling: touch !important;
        padding-bottom: 15px !important;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    /* BARIS TABEL: Dipersempit menjadi total 650px */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: 650px !important; /* <-- Ini sudah sempit dan pas di HP */
        min-width: 650px !important;
    }

    /* KOLOM TABEL: Jarak antar kolom dirapatkan */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        padding: 0 2px !important;
    }
    
    /* UKURAN KOLOM PRESISI (Total 650px) */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(1) { flex: 0 0 30px !important; }  /* NO */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(2) { flex: 0 0 75px !important; }  /* Tgl */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(3) { flex: 0 0 110px !important;} /* Nama */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(4) { flex: 0 0 50px !important; }  /* NRP */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(5) { flex: 0 0 55px !important; }  /* Shift */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(6) { flex: 0 0 50px !important; }  /* Jam Awl */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(7) { flex: 0 0 50px !important; }  /* Jam Akhir */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(8) { flex: 0 0 45px !important; }  /* View */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(9) { flex: 0 0 85px !important; }  /* Approve */
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="column"]:nth-child(10){ flex: 0 0 85px !important; } /* Tolak */

    /* KECILKAN UKURAN HURUF & TOMBOL AGAR MUAT */
    div[data-testid="stVerticalBlock"]:has(.table-marker) p,
    div[data-testid="stVerticalBlock"]:has(.table-marker) .stMarkdown {
        font-size: 12px !important;
    }
    
    div[data-testid="stVerticalBlock"]:has(.table-marker) div[data-testid="stButton"] button {
        padding: 0px 4px !important;
        font-size: 11px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SETUP SESSION STATE & ROUTING
# ==========================================
if "app_mode" not in st.session_state: st.session_state.app_mode = "landing"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = "" 

def get_wib_time(): return datetime.utcnow() + timedelta(hours=7)

# ==========================================
# KONEKSI KE GOOGLE SHEETS
# ==========================================
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_gsheets_client():
    try:
        creds_dict = json.loads(st.secrets["gcp_credentials"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Gagal memuat kredensial: {e}")
        st.stop()

def get_worksheet(sheet_name):
    client = get_gsheets_client()
    try:
        sh = client.open_by_key(SHEET_ID)
        try: return sh.worksheet(sheet_name)
        except: return sh.add_worksheet(title=sheet_name, rows="1000", cols="20")
    except Exception as e:
        st.error(f"Gagal membuka Spreadsheet: {e}")
        st.stop()

def safe_update(sheet, data, range_name="A1"):
    try: sheet.update(values=data, range_name=range_name)
    except TypeError: sheet.update(range_name, data)

# ==========================================
# DATABASE PENGGUNA & CONFIG
# ==========================================
@st.cache_data(ttl=60)
def load_users():
    sheet = get_worksheet("Users")
    data = sheet.get_all_records()
    if not data:
        default_users = {
            "Bapak Andi (GL 1)": {"password": "andi123", "failed_attempts": 0, "blocked": False, "role": "GL/UH"},
            "Bapak Budi (GL 2)": {"password": "budi123", "failed_attempts": 0, "blocked": False, "role": "GL/UH"},
            "Bapak Citra (GL 3)": {"password": "citra123", "failed_attempts": 0, "blocked": False, "role": "GL/UH"},
            "Sect. Head": {"password": "sh123", "failed_attempts": 0, "blocked": False, "role": "Section Head"},
            "Administrator": {"password": "admin123", "failed_attempts": 0, "blocked": False, "role": "Admin"}
        }
        sheet.clear()
        rows = [["Username", "Password", "Gagal", "Blocked", "Role"]]
        for k, v in default_users.items(): rows.append([k, v["password"], v["failed_attempts"], str(v["blocked"]), v["role"]])
        safe_update(sheet, rows)
        return default_users
    else:
        user_dict = {}
        for row in data:
            user_dict[str(row["Username"])] = {"password": str(row["Password"]), "failed_attempts": int(row["Gagal"]), "blocked": str(row["Blocked"]).lower() == "true", "role": str(row["Role"])}
        return user_dict

def save_users(users_data):
    sheet = get_worksheet("Users")
    sheet.clear()
    rows = [["Username", "Password", "Gagal", "Blocked", "Role"]]
    for k, v in users_data.items(): rows.append([k, v["password"], v["failed_attempts"], str(v["blocked"]), v["role"]])
    safe_update(sheet, rows)
    st.cache_data.clear()

@st.cache_data(ttl=60)
def load_config():
    sheet = get_worksheet("Config")
    data = sheet.get_all_records()
    if not data:
        default_cfg = {"status_aktif": False, "pjs_nama": ""}
        sheet.clear()
        safe_update(sheet, [["status_aktif", "pjs_nama"], [str(default_cfg["status_aktif"]), default_cfg["pjs_nama"]]])
        return default_cfg
    else:
        row = data[0]
        return {"status_aktif": str(row["status_aktif"]).lower() == "true", "pjs_nama": str(row["pjs_nama"])}

def save_config(config):
    sheet = get_worksheet("Config")
    sheet.clear()
    rows = [["status_aktif", "pjs_nama"], [str(config["status_aktif"]), config["pjs_nama"]]]
    safe_update(sheet, rows)
    st.cache_data.clear()

try:
    users_db = load_users()
    LIST_GL = [k for k, v in users_db.items() if v["role"] == "GL/UH"]
except: LIST_GL = ["Bapak Andi (GL 1)", "Bapak Budi (GL 2)", "Bapak Citra (GL 3)"]

# ==========================================
# DATABASE SPL 
# ==========================================
@st.cache_data(ttl=15)
def get_db():
    sheet = get_worksheet("Data_SPL")
    data = sheet.get_all_records()
    cols = ["ID", "Nama", "NRP", "Section", "Shift", "Tanggal", "Jam", "Perusahaan", "Alasan", "Pengawas_Tujuan", "Status", "Waktu_GL", "Nama_GL", "Waktu_SH", "Nama_SH", "Alasan_Tolak"]
    if not data:
        df = pd.DataFrame(columns=cols)
        safe_update(sheet, [cols])
        return df
    else:
        df = pd.DataFrame(data)
        for c in cols:
            if c not in df.columns: df[c] = ""
        return df.astype(str)

def save_db(df):
    sheet = get_worksheet("Data_SPL")
    sheet.clear()
    df = df.astype(str)
    data_to_save = [df.columns.values.tolist()] + df.values.tolist()
    safe_update(sheet, data_to_save)
    st.cache_data.clear()

# ==========================================
# FUNGSI PENDUKUNG
# ==========================================
def hitung_total_lembur_str(jam_str):
    if pd.notna(jam_str) and " - " in str(jam_str):
        try:
            awal, akhir = str(jam_str).split(' - ')
            wa = datetime.strptime(awal.strip(), "%H:%M")
            wk = datetime.strptime(akhir.strip(), "%H:%M")
            selisih = (wk - wa).total_seconds()
            if selisih < 0: selisih += 24 * 3600
            hours = int(selisih // 3600)
            minutes = int((selisih % 3600) // 60)
            return f"{hours:02d}:{minutes:02d}"
        except: return "-"
    return "-"

def create_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.rect(5, 5, 200, 287)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 20, "", border=1) 
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 10, "PT. Saptaindra Sejati\nSite Maco", border=1, align='L')
    try: pdf.image("logo.png.png", x=9, y=11, w=42) 
    except: pass 
    pdf.ln(10)
    pdf.set_font("Arial", "BU", 14)
    pdf.cell(0, 10, "SURAT PERINTAH LEMBUR", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 10, " NAMA", border=1)
    pdf.cell(150, 10, f" {row['Nama']}", border=1, ln=True)
    pdf.cell(40, 10, " NRP/DEPT", border=1)
    pdf.cell(70, 10, f" {row['NRP']} / {row['Section']}", border=1)
    pdf.cell(30, 10, " SHIFT :", border=1)
    pdf.cell(50, 10, f" {row['Shift']}", border=1, ln=True) 
    total_lembur = hitung_total_lembur_str(row['Jam'])
    pdf.cell(40, 10, " TANGGAL :", border=1)
    pdf.cell(70, 10, f" {row['Tanggal']}", border=1)
    pdf.cell(30, 10, " JAM :", border=1)
    pdf.cell(50, 10, f" {row['Jam']} = {total_lembur}", border=1, ln=True)
    pdf.cell(40, 10, " PERUSAHAAN :", border=1)
    pdf.cell(150, 10, f" {row['Perusahaan']}", border=1, ln=True)
    pdf.cell(190, 10, " Keterangan Lembur :", border="LTR", ln=True)
    pdf.multi_cell(190, 10, f" {row['Alasan']}\n\n", border="LBR")
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 5, "Diperintahkan Oleh,", align="C")
    pdf.cell(95, 5, "Disetujui Oleh,", ln=True, align="C")
    y_pos = pdf.get_y()
    try:
        if str(row['Waktu_GL']) != "nan" and row['Waktu_GL']: pdf.image("logo.png.png", x=35, y=y_pos + 2, w=35) 
        if str(row['Waktu_SH']) != "nan" and row['Waktu_SH']: pdf.image("logo.png.png", x=130, y=y_pos + 2, w=35)
    except: pass
    pdf.ln(18) 
    gl_sign = f"Digitally Signed: {row['Waktu_GL']}" if str(row['Waktu_GL']) != "nan" else ""
    sh_sign = f"Digitally Signed: {row['Waktu_SH']}" if str(row['Waktu_SH']) != "nan" else ""
    pdf.set_text_color(0, 0, 255)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(95, 5, gl_sign, align="C")
    pdf.cell(95, 5, sh_sign, align="C", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8) 
    nama_pengawas = row['Nama_GL'] if str(row['Nama_GL']) != "nan" and row['Nama_GL'] else "GL/UH"
    nama_sh_raw = str(row['Nama_SH']) if 'Nama_SH' in row and pd.notna(row['Nama_SH']) and str(row['Nama_SH']) != "nan" else "Haris Abi Wibowo"
    if "(PJS Section Head)" in nama_sh_raw:
        nama_sh_final = nama_sh_raw.replace(" (PJS Section Head)", "").strip()
        jabatan_sh = "PJS Section Head"
    elif "(Pjs. Sect Head)" in nama_sh_raw: 
        nama_sh_final = nama_sh_raw.replace(" (Pjs. Sect Head)", "").strip()
        jabatan_sh = "PJS Section Head"
    else:
        nama_sh_final = nama_sh_raw
        jabatan_sh = "Section Head"
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 5, "__________________________", align="C", ln=0)
    pdf.cell(95, 5, "__________________________", align="C", ln=1)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(95, 5, nama_pengawas, align="C") 
    pdf.cell(95, 5, nama_sh_final, align="C", ln=1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(95, 4, "GL / UH", align="C") 
    pdf.cell(95, 4, jabatan_sh, align="C", ln=1)
    safe_nama = "".join([c for c in str(row['Nama']) if c.isalpha() or c.isdigit() or c==' ']).strip()
    filename = f"SPL {safe_nama} {row['Tanggal']}.pdf"
    pdf.output(filename)
    return filename

def display_html_preview(row):
    total_lembur = hitung_total_lembur_str(row['Jam'])
    html_content = f"""
    <div style="background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px; color: black; font-family: Arial, sans-serif;">
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
    if username_key not in users_data: return False
    user_info = users_data[username_key]
    if user_info["blocked"]:
        st.error(f"🚨 Akun Anda ({username_key}) telah DIBLOKIR!")
        return False
    if password_input == user_info["password"]:
        user_info["failed_attempts"] = 0
        save_users(users_data)
        return True
    elif password_input != "":
        user_info["failed_attempts"] += 1
        sisa = 3 - user_info["failed_attempts"]
        if user_info["failed_attempts"] >= 3:
            user_info["blocked"] = True
            st.error(f"🚨 PERINGATAN: Sandi salah 3x. Akun {username_key} DIBLOKIR!")
        else: st.error(f"❌ Sandi Salah! Sisa percobaan Anda: {sisa} kali lagi.")
        save_users(users_data)
    return False

# ==========================================
# HALAMAN UTAMA (LANDING PAGE)
# ==========================================
if st.session_state.app_mode == "landing":
    st.markdown("<br><br><h1 style='text-align: center;'>🏢 Portal SPL Digital PT. SIS</h1>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 4, 4, 1])
    with col2:
        st.success("📝 **PORTAL KARYAWAN**")
        if st.button("Masuk ke Pembuatan Form SPL", use_container_width=True):
            st.session_state.role = "Karyawan"
            st.session_state.logged_in = True
            st.session_state.app_mode = "main"
            st.rerun()
    with col3:
        st.info("🔐 **PORTAL MANAJEMEN**")
        if st.button("Masuk Halaman Login", use_container_width=True):
            st.session_state.app_mode = "login"
            st.rerun()

# ==========================================
# HALAMAN LOGIN
# ==========================================
elif st.session_state.app_mode == "login":
    st.markdown("<br><h2 style='text-align: center;'>🔐 Login Manajemen</h2><hr>", unsafe_allow_html=True)
    if st.button("⬅️ Kembali ke Menu Utama"):
        st.session_state.app_mode = "landing"
        st.rerun()
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        role = st.selectbox("Pilih Akses Jabatan:", ["Pilih...", "GL/UH", "Section Head", "Admin"])
        if role == "GL/UH":
            nama_gl = st.selectbox("Pilih Nama Anda", LIST_GL)
            password = st.text_input("Password", type="password")
            if st.button("Login GL", use_container_width=True):
                if proses_login(nama_gl, password):
                    st.session_state.logged_in = True
                    st.session_state.role = "GL/UH"
                    st.session_state.username = nama_gl
                    st.session_state.app_mode = "main"
                    st.rerun()
        elif role == "Section Head":
            password = st.text_input("Password Section Head", type="password")
            if st.button("Login Sect Head", use_container_width=True):
                if proses_login("Haris Abi Wibowo", password):
                    st.session_state.logged_in = True
                    st.session_state.role = "Section Head"
                    st.session_state.username = "Haris Abi Wibowo"
                    st.session_state.app_mode = "main"
                    st.rerun()
        elif role == "Admin":
            password = st.text_input("Password Admin", type="password")
            if st.button("Login Admin", use_container_width=True):
                if proses_login("Administrator", password):
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.session_state.username = "Administrator"
                    st.session_state.app_mode = "main"
                    st.rerun()

# ==========================================
# HALAMAN DASHBOARD UTAMA
# ==========================================
elif st.session_state.app_mode == "main" and st.session_state.logged_in:
    if st.session_state.role != "Karyawan":
        with st.sidebar:
            with st.expander("🔑 Ganti Password", expanded=False):
                with st.form("form_ganti_pass", clear_on_submit=True):
                    pass_lama = st.text_input("Password Lama", type="password")
                    pass_baru = st.text_input("Password Baru", type="password")
                    if st.form_submit_button("Simpan Password"):
                        db_pass = load_users()
                        user_data = db_pass[st.session_state.username]
                        if pass_lama != user_data["password"]: st.error("Password lama salah!")
                        else:
                            user_data["password"] = pass_baru
                            save_users(db_pass)
                            st.success("✅ Password berhasil diperbarui!")

    col_title, col_logout = st.columns([8, 2])
    with col_title:
        if st.session_state.role == "Karyawan": st.title("📄 Pengisian Form SPL")
        else: st.title(f"📄 Dashboard {st.session_state.role}")
    with col_logout:
        st.write("") 
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.session_state.username = ""
            st.session_state.app_mode = "landing"
            st.cache_data.clear()
            st.rerun()
    st.write("---")
    
    config_del = load_config()

    # --- KARYAWAN ---
    if st.session_state.role == "Karyawan":
        with st.form("form_spl", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nama = col1.text_input("Nama Karyawan *")
            nrp = col2.text_input("NRP *") 
            col_sec, col_per = st.columns(2)
            section = col_sec.selectbox("Section", ["Logistik"]) 
            perusahaan = col_per.selectbox("Nama Perusahaan", ["PT. Saptaindra Sejati", "PT. Cheisa Mandiri Utama", "PT. Borneo Mura Perkasa"])
            col_tgl, col_shift = st.columns(2)
            tgl = col_tgl.date_input("Tanggal", value=get_wib_time().date(), disabled=True)
            shift = col_shift.selectbox("Shift Lembur", ["Shift 1", "Shift 2"])
            pengawas_tujuan = st.selectbox("Pengawas (GL) Yang Bertugas", LIST_GL)
            
            st.markdown("**Waktu Lembur:**")
            col_jam_awal, col_jam_akhir = st.columns(2)
            list_jam = [f"{i:02d}" for i in range(24)]
            list_menit = [f"{i:02d}" for i in range(60)]
            with col_jam_awal:
                c1, c2 = st.columns(2)
                jam_a = c1.selectbox("Jam Mulai", list_jam)
                menit_a = c2.selectbox("Menit Mulai", list_menit)
            with col_jam_akhir:
                c3, c4 = st.columns(2)
                jam_s = c3.selectbox("Jam Selesai", list_jam)
                menit_s = c4.selectbox("Menit Selesai", list_menit)
            
            alasan = st.text_area("Keterangan Lembur *")
            submitted = st.form_submit_button("Kirim Pengajuan Lembur")
            
            if submitted:
                if not nama.strip() or not nrp.strip() or not alasan.strip(): st.error("⚠️ GAGAL: Nama, NRP, Keterangan wajib diisi!")
                else:
                    df = get_db()
                    new_id = str(int(time.time()))
                    new_data = {
                        "ID": new_id, "Nama": nama, "NRP": nrp, "Section": section, "Shift": shift, "Tanggal": str(tgl), 
                        "Jam": f"{jam_a}:{menit_a} - {jam_s}:{menit_s}", "Perusahaan": perusahaan, "Alasan": alasan, 
                        "Pengawas_Tujuan": pengawas_tujuan, "Status": "Pending GL", "Waktu_GL": "", "Nama_GL": "", "Waktu_SH": "", "Nama_SH": "", "Alasan_Tolak": ""
                    }
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    save_db(df)
                    st.success(f"✅ BERHASIL: SPL untuk {nama} terkirim!")

    # --- GL/UH ---
    elif st.session_state.role == "GL/UH":
        df_gl = get_db()
        st.subheader("Menunggu Verifikasi Anda")
        pending_gl = df_gl[(df_gl["Status"] == "Pending GL") & (df_gl["Pengawas_Tujuan"] == st.session_state.username)]
        
        if pending_gl.empty: 
            st.info("✅ Saat ini tidak ada antrean SPL baru.")
        else:
            with st.container():
                st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
                cols = st.columns(10)
                for idx, title in enumerate(["**NO**", "**Tanggal**", "**Nama**", "**NRP**", "**Shift**", "**Jam awal**", "**jam Akhir**", "**View**", "**Approve**", "**Tolak**"]): cols[idx].markdown(title)
                st.markdown("<hr style='margin: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

                for i, (idx, row) in enumerate(pending_gl.iterrows(), 1):
                    cols = st.columns(10)
                    cols[0].write(str(i))
                    cols[1].write(row['Tanggal'])
                    cols[2].write(row['Nama'])
                    cols[3].write(row['NRP'])
                    cols[4].write(row['Shift'].replace('Shift ', ''))
                    jams = row['Jam'].split(' - ')
                    cols[5].write(jams[0] if len(jams) > 0 else "")
                    cols[6].write(jams[1] if len(jams) > 1 else "")
                    
                    with cols[7]:
                        with st.popover("👁️"): display_html_preview(row)
                    with cols[8]:
                        if st.button("Approve", key=f"gl_app_{row['ID']}"):
                            df_gl.loc[idx, "Status"] = "Pending SH"
                            df_gl.loc[idx, "Waktu_GL"] = get_wib_time().strftime("%Y-%m-%d %H:%M")
                            df_gl.loc[idx, "Nama_GL"] = st.session_state.username 
                            save_db(df_gl)
                            st.rerun()
                    with cols[9]:
                        with st.popover("Tolak"):
                            alasan_tolak = st.text_area("Masukkan Alasan:", key=f"txt_tolak_gl_{row['ID']}")
                            if st.button("Konfirmasi Tolak", key=f"gl_del_{row['ID']}"):
                                if not alasan_tolak.strip(): st.error("Alasan wajib diisi!")
                                else:
                                    df_gl.loc[idx, "Status"] = "Ditolak"
                                    df_gl.loc[idx, "Waktu_GL"] = get_wib_time().strftime("%Y-%m-%d %H:%M")
                                    df_gl.loc[idx, "Nama_GL"] = st.session_state.username 
                                    df_gl.loc[idx, "Alasan_Tolak"] = alasan_tolak
                                    save_db(df_gl)
                                    st.rerun()
                    st.markdown("<hr style='margin: 0px; opacity: 0.1;'>", unsafe_allow_html=True)
                    
        st.subheader("Riwayat Pekerjaan")
        history_gl = df_gl[((df_gl["Status"] == "Pending SH") | (df_gl["Status"] == "Final Approved") | (df_gl["Status"] == "Ditolak")) & (df_gl["Nama_GL"] == st.session_state.username)]
        if not history_gl.empty:
            for idx, row in history_gl.iterrows():
                if row['Status'] == 'Ditolak': st.error(f"❌ {row['Nama']} ({row['Tanggal']}) - Ditolak")
                else: st.write(f"✅ {row['Nama']} ({row['Tanggal']}) - {row['Status']}")

        # TUGAS PJS SH
        if config_del["status_aktif"] and config_del["pjs_nama"] == st.session_state.username:
            st.warning("👑 **TUGAS PJS SECTION HEAD**")
            pending_sh = df_gl[df_gl["Status"] == "Pending SH"]
            
            if pending_sh.empty:
                st.info("✅ Tidak ada antrean tugas verifikasi PJS untuk saat ini.")
            else:
                with st.container():
                    st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
                    cols = st.columns(10)
                    for idx, title in enumerate(["**NO**", "**Tanggal**", "**Nama**", "**NRP**", "**Shift**", "**Jam awal**", "**jam Akhir**", "**View**", "**Approve**", "**Tolak**"]): cols[idx].markdown(title)
                    st.markdown("<hr style='margin: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

                    for i, (idx, row) in enumerate(pending_sh.iterrows(), 1):
                        cols = st.columns(10)
                        cols[0].write(str(i))
                        cols[1].write(row['Tanggal'])
                        cols[2].write(row['Nama'])
                        cols[3].write(row['NRP'])
                        cols[4].write(row['Shift'].replace('Shift ', ''))
                        jams = row['Jam'].split(' - ')
                        cols[5].write(jams[0] if len(jams) > 0 else "")
                        cols[6].write(jams[1] if len(jams) > 1 else "")
                        
                        with cols[7]:
                            with st.popover("👁️"): display_html_preview(row)
                        with cols[8]:
                            if st.button("Approve", key=f"pjs_app_{row['ID']}"):
                                df_gl.loc[idx, "Status"] = "Final Approved"
                                df_gl.loc[idx, "Waktu_SH"] = get_wib_time().strftime("%Y-%m-%d %H:%M")
                                df_gl.loc[idx, "Nama_SH"] = f"{st.session_state.username} (PJS)"
                                save_db(df_gl)
                                st.rerun()
                        with cols[9]:
                            with st.popover("Tolak"):
                                alasan_pjs = st.text_area("Masukkan Alasan:", key=f"txt_tolak_pjs_{row['ID']}")
                                if st.button("Konfirmasi Tolak", key=f"pjs_del_{row['ID']}"):
                                    if not alasan_pjs.strip(): st.error("Alasan wajib diisi!")
                                    else:
                                        df_gl.loc[idx, "Status"] = "Ditolak"
                                        df_gl.loc[idx, "Waktu_SH"] = get_wib_time().strftime("%Y-%m-%d %H:%M")
                                        df_gl.loc[idx, "Nama_SH"] = f"{st.session_state.username} (PJS)"
                                        df_gl.loc[idx, "Alasan_Tolak"] = alasan_pjs
                                        save_db(df_gl)
                                        st.rerun()
                        st.markdown("<hr style='margin: 0px; opacity: 0.1;'>", unsafe_allow_html=True)
                                        
            history_pjs = df_gl[(df_gl["Status"] == "Final Approved") & (df_gl["Nama_SH"] == f"{st.session_state.username} (PJS)")]
            for idx, row in history_pjs.iterrows():
                file_pdf = create_pdf(row)
                with open(file_pdf, "rb") as f:
                    st.download_button(f"📄 Download SPL {row['Nama']}", f, file_name=file_pdf, key=f"dl_pjs_{row['ID']}")

    # --- SECTION HEAD ---
    elif st.session_state.role == "Section Head":
        with st.expander("⚙️ PENGATURAN DELEGASI", expanded=config_del["status_aktif"]):
            col_d1, col_d2 = st.columns(2)
            with col_d1: pjs_pilihan = st.selectbox("Pilih Pjs:", LIST_GL)
            with col_d2:
                if not config_del["status_aktif"]:
                    if st.button("🚀 Aktifkan Delegasi"):
                        config_del["status_aktif"] = True
                        config_del["pjs_nama"] = pjs_pilihan
                        save_config(config_del)
                        st.rerun()
                else:
                    if st.button("🛑 Cabut Delegasi"):
                        config_del["status_aktif"] = False
                        config_del["pjs_nama"] = ""
                        save_config(config_del)
                        st.rerun()
            if config_del["status_aktif"]: st.error(f"Delegasi Aktif ke: {config_del['pjs_nama']}")

        df_sh = get_db()
        st.subheader("Verifikasi Akhir (Final Approve)")
        pending_sh = df_sh[df_sh["Status"] == "Pending SH"]
        
        if pending_sh.empty: 
            st.info("✅ Belum ada antrean SPL yang masuk untuk di-Approve.")
        else:
            with st.container():
                st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
                cols = st.columns(10)
                for idx, title in enumerate(["**NO**", "**Tanggal**", "**Nama**", "**NRP**", "**Shift**", "**Jam awal**", "**jam Akhir**", "**View**", "**Approve**", "**Tolak**"]): cols[idx].markdown(title)
                st.markdown("<hr style='margin: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

                for i, (idx, row) in enumerate(pending_sh.iterrows(), 1):
                    cols = st.columns(10)
                    cols[0].write(str(i))
                    cols[1].write(row['Tanggal'])
                    cols[2].write(row['Nama'])
                    cols[3].write(row['NRP'])
                    cols[4].write(row['Shift'].replace('Shift ', ''))
                    jams = row['Jam'].split(' - ')
                    cols[5].write(jams[0] if len(jams) > 0 else "")
                    cols[6].write(jams[1] if len(jams) > 1 else "")
                    
                    with cols[7]:
                        with st.popover("👁️"): display_html_preview(row)
                    with cols[8]:
                        if st.button("Approve", key=f"sh_app_{row['ID']}"):
                            df_sh.loc[idx, "Status"] = "Final Approved"
                            df_sh.loc[idx, "Waktu_SH"] = get_wib_time().strftime("%Y-%m-%d %H:%M")
                            df_sh.loc[idx, "Nama_SH"] = "Haris Abi Wibowo"
                            save_db(df_sh)
                            st.rerun()
                    with cols[9]:
                        with st.popover("Tolak"):
                            alasan_sh = st.text_area("Masukkan Alasan:", key=f"txt_tolak_sh_{row['ID']}")
                            if st.button("Konfirmasi Tolak", key=f"sh_del_{row['ID']}"):
                                if not alasan_sh.strip(): st.error("Alasan wajib diisi!")
                                else:
                                    df_sh.loc[idx, "Status"] = "Ditolak"
                                    df_sh.loc[idx, "Waktu_SH"] = get_wib_time().strftime("%Y-%m-%d %H:%M")
                                    df_sh.loc[idx, "Nama_SH"] = "Haris Abi Wibowo"
                                    df_sh.loc[idx, "Alasan_Tolak"] = alasan_sh
                                    save_db(df_sh)
                                    st.rerun()
                    st.markdown("<hr style='margin: 0px; opacity: 0.1;'>", unsafe_allow_html=True)

        st.subheader("Arsip Dokumen Selesai")
        approved_sh = df_sh[df_sh["Status"] == "Final Approved"]
        for idx, row in approved_sh.iterrows():
            file_pdf = create_pdf(row)
            with open(file_pdf, "rb") as f:
                st.download_button(f"📄 Download SPL {row['Nama']}", f, file_name=file_pdf, key=f"dl_sh_{row['ID']}")

    # --- ADMIN ---
    elif st.session_state.role == "Admin":
        df_admin = get_db()
        st.subheader("📊 Tabel Database SPL Keseluruhan")
        
        with st.container():
            tabel_admin = df_admin[['Tanggal', 'Nama', 'NRP', 'Section', 'Shift', 'Jam', 'Status', 'Pengawas_Tujuan']].copy()
            tabel_admin.index = range(1, len(tabel_admin) + 1)
            st.dataframe(tabel_admin, use_container_width=True)
        
        st.markdown("---")
        st.subheader("🗂️ Unduh Arsip PDF Selesai")
        approved_admin = df_admin[df_admin["Status"] == "Final Approved"]
        if approved_admin.empty: st.write("Belum ada dokumen yang selesai.")
        for idx, row in approved_admin.iterrows():
            file_pdf = create_pdf(row)
            with open(file_pdf, "rb") as f:
                st.download_button(f"📄 Download SPL {row['Nama']} ({row['Tanggal']})", f, file_name=file_pdf, key=f"dl_adm_{row['ID']}")
