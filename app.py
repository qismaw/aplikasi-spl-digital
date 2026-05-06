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
/* Warna Tombol Umum */
div[data-testid="stButton"] button:has(p:contains("Approve")) { background-color: #00c853 !important; color: white !important; font-weight: bold !important; }
div[data-testid="stButton"] button:has(p:contains("Tolak")) { background-color: #ff1744 !important; color: white !important; font-weight: bold !important; }
div[data-testid="stPopoverBody"] { width: 650px !important; max-width: 95vw !important; }

/* STYLING TABEL: ANTI TUMPANG TINDIH & RAPI */
@media (max-width: 768px) {
    body, .stApp { overflow-x: hidden !important; }
}

div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) {
    background-color: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 8px !important;
    padding: 5px !important;
    margin-bottom: 20px !important;
    overflow-x: auto !important;
}

div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    min-width: 1000px !important; 
    border-bottom: 1px solid rgba(255,255,255,0.1) !important;
    padding: 12px 0px !important; 
    gap: 0px !important;
    align-items: center !important;
}

div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) div[data-testid="column"] {
    flex: 0 0 auto !important;
    padding: 0 10px !important;
}

div[data-testid="stVerticalBlock"]:has(> div.element-container .table-marker) p {
    margin-bottom: 0 !important;
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

if "app_mode" not in st.session_state: st.session_state.app_mode = "landing"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = "" 

def get_wib_time(): return datetime.utcnow() + timedelta(hours=7)

# KONEKSI GOOGLE SHEETS
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
@st.cache_resource
def get_gsheets_client():
    creds_dict = json.loads(st.secrets["gcp_credentials"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

def get_worksheet(sheet_name):
    client = get_gsheets_client()
    sh = client.open_by_key(SHEET_ID)
    try: return sh.worksheet(sheet_name)
    except: return sh.add_worksheet(title=sheet_name, rows="1000", cols="20")

def safe_update(sheet, data):
    sheet.clear()
    sheet.update("A1", data)

# DATABASE
@st.cache_data(ttl=60)
def load_users():
    sheet = get_worksheet("Users")
    data = sheet.get_all_records()
    return {str(row["Username"]): {"password": str(row["Password"]), "failed_attempts": int(row["Gagal"]), "blocked": str(row["Blocked"]).lower() == "true", "role": str(row["Role"])} for row in data}

def save_users(users_data):
    sheet = get_worksheet("Users")
    rows = [["Username", "Password", "Gagal", "Blocked", "Role"]]
    for k, v in users_data.items(): rows.append([k, v["password"], v["failed_attempts"], str(v["blocked"]), v["role"]])
    safe_update(sheet, rows)

@st.cache_data(ttl=60)
def load_config():
    sheet = get_worksheet("Config")
    data = sheet.get_all_records()
    return {"status_aktif": str(data[0]["status_aktif"]).lower() == "true", "pjs_nama": str(data[0]["pjs_nama"])} if data else {"status_aktif": False, "pjs_nama": ""}

@st.cache_data(ttl=15)
def get_db():
    sheet = get_worksheet("Data_SPL")
    data = sheet.get_all_records()
    df = pd.DataFrame(data) if data else pd.DataFrame(columns=["ID", "Nama", "NRP", "Section", "Shift", "Tanggal", "Jam", "Perusahaan", "Alasan", "Pengawas_Tujuan", "Status", "Waktu_GL", "Nama_GL", "Waktu_SH", "Nama_SH", "Alasan_Tolak"])
    return df.astype(str)

def save_db(df):
    sheet = get_worksheet("Data_SPL")
    data_to_save = [df.columns.values.tolist()] + df.values.tolist()
    safe_update(sheet, data_to_save)

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
    pdf = FPDF()
    pdf.add_page()
    pdf.rect(5, 5, 200, 287)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "SURAT PERINTAH LEMBUR - PT. Saptaindra Sejati", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.ln(5)
    for k, v in row.items(): pdf.cell(0, 8, f"{k}: {v}", ln=True)
    fn = f"SPL_{row['Nama']}_{row['Tanggal']}.pdf"
    pdf.output(fn)
    return fn

def display_html_preview(row):
    st.write(f"**Preview SPL: {row['Nama']}**")
    st.json(row)

def proses_login(username_key, password_input):
    users_data = load_users()
    if username_key not in users_data: return False
    u = users_data[username_key]
    if u["blocked"]: return False
    if str(password_input) == u["password"]:
        u["failed_attempts"] = 0
        save_users(users_data)
        return True
    return False

# ROUTING
if st.session_state.app_mode == "landing":
    st.title("🏢 Portal SPL Digital PT. SIS")
    c1, c2 = st.columns(2)
    if c1.button("📝 PORTAL KARYAWAN", use_container_width=True):
        st.session_state.role = "Karyawan"; st.session_state.logged_in = True; st.session_state.app_mode = "main"; st.rerun()
    if c2.button("🔐 PORTAL MANAJEMEN", use_container_width=True):
        st.session_state.app_mode = "login"; st.rerun()

elif st.session_state.app_mode == "login":
    st.subheader("🔐 Login Manajemen")
    if st.button("⬅️ Kembali"): st.session_state.app_mode = "landing"; st.rerun()
    role = st.selectbox("Akses:", ["Pilih...", "GL/UH", "Section Head", "Admin"])
    if role != "Pilih...":
        users_db = load_users()
        u_list = [k for k, v in users_db.items() if v["role"] == role]
        target = st.selectbox("User:", u_list)
        pwd = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True):
            if proses_login(target, pwd):
                st.session_state.logged_in = True; st.session_state.role = role; st.session_state.username = target; st.session_state.app_mode = "main"; st.rerun()

elif st.session_state.app_mode == "main" and st.session_state.logged_in:
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.session_state.app_mode = "landing"; st.rerun()
    
    # --- ADMIN ---
    if st.session_state.role == "Admin":
        st.title("📊 Database SPL Keseluruhan")
        df_admin = get_db()
        f_mode = st.radio("Pilih Filter:", ["Semua Data", "Tanggal", "Bulan", "Tahun", "Range Tanggal"], horizontal=True)
        df_f = df_admin.copy()
        
        if f_mode == "Tanggal":
            d = st.date_input("Tanggal", value=get_wib_time().date())
            df_f = df_f[df_f['Tanggal'] == str(d)]
        elif f_mode == "Bulan":
            m = st.selectbox("Bulan", ["01","02","03","04","05","06","07","08","09","10","11","12"], index=get_wib_time().month-1)
            df_f = df_f[df_f['Tanggal'].str.contains(f"-{m}-")]
        elif f_mode == "Tahun":
            y = st.selectbox("Tahun", [str(i) for i in range(2024, 2030)], index=0)
            df_f = df_f[df_f['Tanggal'].str.startswith(y)]
        elif f_mode == "Range Tanggal":
            r1, r2 = st.columns(2)
            d1 = r1.date_input("Dari", value=get_wib_time().date()-timedelta(days=7))
            d2 = r2.date_input("Sampai", value=get_wib_time().date())
            df_f = df_f[(df_f['Tanggal'] >= str(d1)) & (df_f['Tanggal'] <= str(d2))]

        # FORMAT DATA UNTUK EXCEL & LAYAR (Urutan image_874655.png)
        df_f.insert(0, 'No.', range(1, len(df_f) + 1))
        df_f['Jam Awal'] = df_f['Jam'].apply(lambda x: x.split(' - ')[0] if ' - ' in str(x) else '')
        df_f['Jam Akhir'] = df_f['Jam'].apply(lambda x: x.split(' - ')[1] if ' - ' in str(x) else '')
        df_f['Total Lembur (Jam)'] = df_f['Jam'].apply(hitung_total_lembur_str)
        
        cols_final = ['No.', 'Tanggal', 'Nama', 'NRP', 'Section', 'Shift', 'Jam Awal', 'Jam Akhir', 'Total Lembur (Jam)', 'Perusahaan', 'Alasan', 'Status', 'Pengawas_Tujuan', 'Waktu_GL', 'Nama_GL', 'Waktu_SH', 'Nama_SH', 'Alasan_Tolak']
        for c in cols_final: 
            if c not in df_f.columns: df_f[c] = ""
        df_display = df_f[cols_final]

        # DOWNLOAD EXCEL DI ATAS
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as wr: df_display.to_excel(wr, index=False)
        st.download_button("📥 Download Excel (.xlsx)", out.getvalue(), f"Rekap_{get_wib_time().strftime('%Y%m%d')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.dataframe(df_display, use_container_width=True)

    # --- GL/UH ---
    elif st.session_state.role == "GL/UH":
        st.subheader("Menunggu Verifikasi")
        df = get_db()
        pending = df[(df["Status"] == "Pending GL") & (df["Pengawas_Tujuan"] == st.session_state.username)]
        if pending.empty: st.info("Kosong.")
        else:
            st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
            for i, (idx, row) in enumerate(pending.iterrows(), 1):
                cols = st.columns(10)
                cols[0].write(str(i)); cols[1].write(row['Tanggal']); cols[2].write(row['Nama'])
                if cols[8].button("Approve", key=f"ap_{row['ID']}"):
                    df.loc[idx, ["Status", "Waktu_GL", "Nama_GL"]] = ["Pending SH", get_wib_time().strftime("%Y-%m-%d %H:%M"), st.session_state.username]
                    save_db(df); st.rerun()

    # --- SECTION HEAD ---
    elif st.session_state.role == "Section Head":
        st.subheader("Verifikasi Akhir")
        df = get_db()
        pending = df[df["Status"] == "Pending SH"]
        if pending.empty: st.info("Kosong.")
        else:
            st.markdown("<span class='table-marker'></span>", unsafe_allow_html=True)
            for i, (idx, row) in enumerate(pending.iterrows(), 1):
                cols = st.columns(10)
                cols[0].write(str(i)); cols[1].write(row['Tanggal']); cols[2].write(row['Nama'])
                if cols[8].button("Approve", key=f"sh_{row['ID']}"):
                    df.loc[idx, ["Status", "Waktu_SH", "Nama_SH"]] = ["Final Approved", get_wib_time().strftime("%Y-%m-%d %H:%M"), "Haris Abi Wibowo"]
                    save_db(df); st.rerun()

    # --- KARYAWAN ---
    elif st.session_state.role == "Karyawan":
        with st.form("f"):
            n = st.text_input("Nama"); nr = st.text_input("NRP"); s = st.selectbox("Shift", ["Shift 1", "Shift 2"])
            p = st.selectbox("Pengawas", load_users().keys())
            if st.form_submit_button("Kirim"):
                db = get_db()
                new = {"ID": str(int(time.time())), "Nama": n, "NRP": nr, "Shift": s, "Tanggal": str(get_wib_time().date()), "Status": "Pending GL", "Pengawas_Tujuan": p}
                save_db(pd.concat([db, pd.DataFrame([new])], ignore_index=True)); st.success("Terkirim")
