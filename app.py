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
st.set_page_config(page_title="OVERTIX - SPL Digital", layout="wide")

# ==========================================
# CSS SAKTI: OVERTIX DARK BLUE THEME (Sesuai Gambar)
# ==========================================
st.markdown("""
<style>
/* 1. HILANGKAN MENU DEVELOPER & GITHUB SECARA PERMANEN */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
header {visibility: hidden !important;}
.stDeployButton {display: none !important;}
[data-testid="stToolbar"] {display: none !important; visibility: hidden !important;}
[data-testid="stHeader"] {display: none !important; visibility: hidden !important;}

/* 2. TEMA BACKGROUND APLIKASI (Dark Blue / #151e2d) */
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

/* 4. CUSTOM TABEL KARYAWAN (Tabel kecil/rapat, Font Besar) */
.custom-table-container {
    background-color: #1c273c;
    border-radius: 8px;
    border: 1px solid #2e3c54;
    padding: 15px;
    margin-top: 10px;
    overflow-x: auto;
}
.custom-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 15px !important; /* UKURAN FONT DIPERBESAR */
}
.custom-table th {
    background-color: #23314a;
    color: #cbd5e1;
    text-align: center;
    padding: 6px 10px !important; /* PADDING DIPERKECIL AGAR RAPAT */
    border: 1px solid #2e3c54;
    font-weight: 600;
}
.custom-table td {
    background-color: #1c273c;
    color: white;
    text-align: center;
    padding: 6px 10px !important; /* PADDING DIPERKECIL AGAR RAPAT */
    border: 1px solid #2e3c54;
    white-space: nowrap;
}

/* 5. BOX HEADER / CARD */
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
/* Tombol Kirim / Utama */
div[data-testid="stButton"] button:has(p:contains("Kirim Pengajuan")), 
div[data-testid="stButton"] button:has(p:contains("LOGIN")),
div[data-testid="stButton"] button:has(p:contains("Portal")) {
    background-color: #2563eb !important; color: white !important; border: none !important;
}
/* Tombol Dukungan Teknis / Secondary */
div[data-testid="stButton"] button:has(p:contains("Dukungan Teknis")),
div[data-testid="stButton"] button:has(p:contains("Kembali")) {
    background-color: #334155 !important; color: white !important; border: none !important;
}

/* Styling Tabel Admin Bawaan */
div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) {
    background-color: #1c273c !important; border: 1px solid #2e3c54 !important;
    border-radius: 8px !important; padding: 5px !important; margin-bottom: 20px !important; overflow-x: auto !important;
}
div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) div[data-testid="stHorizontalBlock"] {
    display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
    min-width: 1000px !important; border-bottom: 1px solid #2e3c54 !important;
    padding: 10px 0px !important; gap: 0px !important; align-items: center !important;
}
div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) div[data-testid="column"] {
    flex: 0 0 auto !important; padding: 0 10px !important;
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
    creds_dict = json.loads(st.secrets["gcp_credentials"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

def get_worksheet(sheet_name):
    sh = get_gsheets_client().open_by_key(SHEET_ID)
    try: return sh.worksheet(sheet_name)
    except: return sh.add_worksheet(title=sheet_name, rows="1000", cols="20")

def safe_update(sheet, data, range_name="A1"):
    try: sheet.update(values=data, range_name=range_name)
    except TypeError: sheet.update(range_name, data)

# ==========================================
# DATABASE PENGGUNA & SPL
# ==========================================
@st.cache_data(ttl=60)
def load_users():
    data = get_worksheet("Users").get_all_records()
    if not data: return {}
    return {str(row["Username"]): {"password": str(row["Password"]), "failed_attempts": int(row["Gagal"]), "blocked": str(row["Blocked"]).lower() == "true", "role": str(row["Role"])} for row in data}

def save_users(users_data):
    sheet = get_worksheet("Users"); sheet.clear()
    rows = [["Username", "Password", "Gagal", "Blocked", "Role"]]
    for k, v in users_data.items(): rows.append([k, v["password"], v["failed_attempts"], str(v["blocked"]), v["role"]])
    safe_update(sheet, rows); st.cache_data.clear()

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
    cols = ["ID", "Nama", "NRP", "Section", "Shift", "Tanggal", "Jam", "Perusahaan", "Alasan", "Pengawas_Tujuan", "Status", "Waktu_GL", "Nama_GL", "Waktu_SH", "Nama_SH", "Alasan_Tolak"]
    if not data:
        df = pd.DataFrame(columns=cols); safe_update(get_worksheet("Data_SPL"), [cols]); return df
    df = pd.DataFrame(data)
    for c in cols:
        if c not in df.columns: df[c] = ""
    return df.astype(str)

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
    pdf.cell(95, 5, "Diperintahkan Oleh,", align="C"); pdf.cell(95, 5, "Disetujui Oleh,", ln=True, align="C")
    pdf.ln(18); pdf.set_text_color(0, 0, 255); pdf.set_font("Arial", "I", 8)
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
    if username_key not in users_data: st.error("Pengguna tidak ditemukan!"); return False
    user_info = users_data[username_key]
    if user_info["blocked"]: st.error(f"🚨 Akun Anda ({username_key}) telah DIBLOKIR. Hubungi Administrator!"); return False
    if str(password_input) == str(user_info["password"]):
        user_info["failed_attempts"] = 0; save_users(users_data); return True
    elif password_input != "":
        user_info["failed_attempts"] += 1
        sisa = 3 - user_info["failed_attempts"]
        if user_info["failed_attempts"] >= 3:
            user_info["blocked"] = True; st.error(f"🚨 PERINGATAN: Sandi salah 3x. Akun {username_key} DIBLOKIR!")
        else: st.error(f"❌ Sandi Salah! Sisa percobaan Anda: {sisa} kali lagi.")
        save_users(users_data); return False
    return False

# ==========================================
# HALAMAN UTAMA (LANDING PAGE)
# ==========================================
if st.session_state.app_mode == "landing":
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #0061ff;'><span style='color:white;'>✓</span> OVERTIX</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8; letter-spacing: 2px; margin-top:-15px;'>SMART OVERTIME EXECUTION SYSTEM</p>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: gray; margin-bottom: 40px; margin-top: 30px;'>Silakan pilih gerbang akses Anda di bawah ini:</p>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 3, 3, 1])
    with col2:
        st.markdown("<div style='background-color:#1c273c; padding:20px; border-radius:10px; border:1px solid #2e3c54; text-align:center;'>", unsafe_allow_html=True)
        st.write("📝 **PORTAL KARYAWAN**")
        st.write("Masuk ke sini untuk mengisi formulir lembur. Tanpa login.")
        if st.button("Masuk Portal Karyawan", use_container_width=True):
            st.session_state.role = "Karyawan"; st.session_state.logged_in = True; st.session_state.app_mode = "main"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div style='background-color:#1c273c; padding:20px; border-radius:10px; border:1px solid #2e3c54; text-align:center;'>", unsafe_allow_html=True)
        st.write("🔐 **PORTAL MANAJEMEN**")
        st.write("Khusus GL/UH, Section Head, dan Administrator.")
        if st.button("Masuk Halaman Login", use_container_width=True):
            st.session_state.app_mode = "login"; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# HALAMAN LOGIN MANAJEMEN
# ==========================================
elif st.session_state.app_mode == "login":
    st.write("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🔐 Login Manajemen</h2><hr style='border-color:#2e3c54;'>", unsafe_allow_html=True)
    
    col_back, _ = st.columns([2, 8])
    with col_back:
        if st.button("⬅️ Kembali"): st.session_state.app_mode = "landing"; st.rerun()
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        role = st.selectbox("Pilih Akses Jabatan:", ["Pilih...", "GL/UH", "Section Head", "Admin"])
        if role != "Pilih...":
            users_db = load_users()
            u_list = [k for k, v in users_db.items() if v["role"] == role]
            target_user = "Section Head" if role == "Section Head" else ("Administrator" if role == "Admin" else st.selectbox("Pilih User", u_list))
            pwd = st.text_input("Password", type="password")
            
            if st.button("LOGIN", use_container_width=True):
                if proses_login(target_user, pwd):
                    st.session_state.logged_in = True; st.session_state.role = role; st.session_state.username = target_user; st.session_state.app_mode = "main"; st.rerun()

# ==========================================
# HALAMAN DASHBOARD UTAMA
# ==========================================
elif st.session_state.app_mode == "main" and st.session_state.logged_in:
    
    # KARYAWAN HEADER (Kustom seperti gambar referensi)
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
        # Header Admin / Manajemen
        col_title, col_logout = st.columns([8, 2])
        with col_title: st.title(f"📄 Dashboard {st.session_state.role} - {st.session_state.username}")
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
            with st.container(border=True): # Menggunakan border bawaan Streamlit
                with st.form("form_spl", clear_on_submit=True):
                    nama = st.text_input("Name")
                    
                    c_nrp, c_sec = st.columns(2)
                    nrp = c_nrp.text_input("NRP") 
                    section = c_sec.selectbox("Section", ["Production", "Logistik", "Maintenance"]) 
                    
                    # Kolom tambahan yang disembunyikan agar sesuai layout namun data tetap lengkap
                    perusahaan = "PT. Saptaindra Sejati"
                    shift = "Shift 1"
                    pengawas_tujuan = "Bapak Andi (GL 1)"
                    
                    c_tgl, c_jam = st.columns(2)
                    tgl = c_tgl.date_input("Tanggal", value=get_wib_time().date())
                    # Kita satukan jam menjadi format teks agar mirip dengan mockup "17:00 - 21:00"
                    jam_input = c_jam.text_input("Jam Lembur", placeholder="Contoh: 17:00 - 21:00")
                    
                    alasan = st.text_area("Keterangan Lembur", placeholder="Contoh: Pusat Bantuan", height=100)
                    
                    c_btn1, c_btn2 = st.columns(2)
                    submitted = c_btn1.form_submit_button("Kirim Pengajuan Lembur", use_container_width=True)
                    dukungan = c_btn2.form_submit_button("Dukungan Teknis", use_container_width=True)
                    
                    if submitted:
                        if not nama.strip() or not nrp.strip() or not jam_input.strip() or not alasan.strip(): 
                            st.error("⚠️ GAGAL: Semua kolom wajib diisi dengan benar!")
                        elif " - " not in jam_input:
                            st.error("⚠️ GAGAL: Format Jam Lembur harus menggunakan tanda hubung, contoh: 17:00 - 21:00")
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
                            time.sleep(1)
                            st.rerun()
                            
                    if dukungan:
                        st.info("Fitur Dukungan Teknis belum tersedia pada versi ini.")

        # SISI KANAN: DAFTAR PENGAJUAN (HTML TABLE CUSTOM - KECIL/RAPAT, TULISAN BESAR)
        with col_table:
            st.markdown("<div class='card-header'>DAFTAR PENGAJUAN LEMBUR SAYA</div>", unsafe_allow_html=True)
            
            df = get_db()
            if df.empty:
                st.info("Belum ada riwayat pengajuan lembur.")
            else:
                # Ambil 10 data terakhir saja agar tidak terlalu panjang ke bawah
                df_karyawan = df.tail(10).copy()
                df_karyawan = df_karyawan.reset_index(drop=True)
                
                # Buat HTML String untuk tabel kustom
                html_table = "<div class='custom-table-container'><table class='custom-table'>"
                html_table += "<tr><th>NO.</th><th>NAMA</th><th>NRP</th><th>SECTION</th><th>TANGGAL</th><th>JAM<br>LEMBUR</th><th>STATUS</th><th>PENGAWAS<br>TUJUAN</th></tr>"
                
                for i, row in df_karyawan.iterrows():
                    status_text = str(row['Status']).upper()
                    # Warnai status untuk estetika
                    if "FINAL" in status_text: status_col = "<span style='color:#10b981; font-weight:bold;'>FINAL<br>APPROVED</span>"
                    elif "DITOLAK" in status_text: status_col = "<span style='color:#ef4444; font-weight:bold;'>DITOLAK</span>"
                    else: status_col = f"<span style='color:#facc15; font-weight:bold;'>{status_text.replace(' ', '<br>')}</span>"
                    
                    html_table += f"<tr>"
                    html_table += f"<td>{i+1}.</td>"
                    html_table += f"<td>{row['Nama']}</td>"
                    html_table += f"<td>{row['NRP']}</td>"
                    html_table += f"<td>{row['Section']}</td>"
                    
                    try: tgl_str = datetime.strptime(row['Tanggal'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except: tgl_str = row['Tanggal']
                    html_table += f"<td>{tgl_str}</td>"
                    
                    # Pecah jam lembur menjadi dua baris agar tidak memakan tempat ke samping
                    jam_arr = str(row['Jam']).split(" - ")
                    jam_html = f"{jam_arr[0]} -<br>{jam_arr[1]}" if len(jam_arr)==2 else row['Jam']
                    
                    html_table += f"<td>{jam_html}</td>"
                    html_table += f"<td>{status_col}</td>"
                    
                    peng_tujuan = str(row['Pengawas_Tujuan']).replace(' (GL 1)','<br>(GL 1)')
                    html_table += f"<td>{peng_tujuan}</td>"
                    html_table += "</tr>"
                    
                html_table += "</table></div>"
                
                st.markdown(html_table, unsafe_allow_html=True)
                
        # Tombol Log Out untuk karyawan
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
