import streamlit as st
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import time
import base64
import json
import io

# Konfigurasi Halaman & CSS Kustom
st.set_page_config(page_title="Sistem SPL Digital", layout="wide")

st.markdown("""
<style>
div[data-testid="stButton"] button:has(p:contains("Approve")) {
    background-color: #00c853 !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}

div[data-testid="stButton"] button:has(p:contains("Tolak")) {
    background-color: #ff1744 !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}

div[data-testid="stPopover"] button {
    padding: 0.2rem 0.5rem !important;
}

div[data-testid="stPopoverBody"] {
    width: 650px !important;
    max-width: 90vw !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# SETUP SESSION STATE & ROUTING
# ==========================================
# app_mode mengatur halaman mana yang sedang aktif: "landing", "login", atau "main"
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "landing"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = "" 

# ==========================================
# DATABASE PENGGUNA (FITUR KEAMANAN)
# ==========================================
USER_DB_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_DB_FILE):
        default_users = {
            "Bapak Andi (GL 1)": {"password": "andi123", "failed_attempts": 0, "blocked": False, "role": "GL/UH"},
            "Bapak Budi (GL 2)": {"password": "budi123", "failed_attempts": 0, "blocked": False, "role": "GL/UH"},
            "Bapak Citra (GL 3)": {"password": "citra123", "failed_attempts": 0, "blocked": False, "role": "GL/UH"},
            "Sect. Head": {"password": "sh123", "failed_attempts": 0, "blocked": False, "role": "Section Head"},
            "Administrator": {"password": "admin123", "failed_attempts": 0, "blocked": False, "role": "Admin"}
        }
        with open(USER_DB_FILE, "w") as f:
            json.dump(default_users, f)
        return default_users
    else:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)

def save_users(users_data):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users_data, f)

users_db = load_users()
LIST_GL = [k for k, v in users_db.items() if v["role"] == "GL/UH"]

# ==========================================
# DATABASE SPL & AUTO-PATCHING
# ==========================================
DB_FILE = "data_spl_v8.csv"

def get_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=[
            "ID", "Nama", "NRP", "Section", "Shift", "Tanggal", "Jam", "Perusahaan", "Alasan", 
            "Pengawas_Tujuan", "Status", "Waktu_GL", "Nama_GL", "Waktu_SH", "Nama_SH", "Alasan_Tolak"
        ])
        df.to_csv(DB_FILE, index=False)
        return df
    else:
        df = pd.read_csv(DB_FILE, dtype=str)
        if "Alasan_Tolak" not in df.columns:
            df["Alasan_Tolak"] = ""
            df.to_csv(DB_FILE, index=False)
        return df

# File Konfigurasi Pendelegasian
CONFIG_FILE = "delegasi.json"
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"status_aktif": False, "pjs_nama": ""}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

# Fungsi Generate PDF
def create_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    pdf.rect(5, 5, 200, 287)
    pdf.set_font("Arial", "B", 12)
    
    pdf.cell(50, 20, "", border=1) 
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 10, "PT. Saptaindra Sejati\nSite Maco", border=1, align='L')
    
    try:
        pdf.image("logo.png.png", x=9, y=11, w=42) 
    except:
        pass 
    
    pdf.ln(10)
    pdf.set_font("Arial", "BU", 14)
    pdf.cell(0, 10, "SURAT PERINTAH LEMBUR", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 10, " NAMA", border=1)
    pdf.cell(150, 10, f" {row['Nama']}", border=1, ln=True)
    pdf.cell(40, 10, " NRP/DEPT", border=1)
    pdf.cell(80, 10, f" {row['NRP']} / {row['Section']}", border=1)
    pdf.cell(30, 10, " SHIFT :", border=1)
    pdf.cell(40, 10, f" {row['Shift']}", border=1, ln=True) 
    pdf.cell(40, 10, " TANGGAL :", border=1)
    pdf.cell(80, 10, f" {row['Tanggal']}", border=1)
    pdf.cell(30, 10, " JAM :", border=1)
    pdf.cell(40, 10, f" {row['Jam']}", border=1, ln=True)
    pdf.cell(40, 10, " PERUSAHAAN :", border=1)
    pdf.cell(150, 10, f" {row['Perusahaan']}", border=1, ln=True)
    pdf.cell(190, 10, " Keterangan Lembur :", border="LTR", ln=True)
    pdf.multi_cell(190, 10, f" {row['Alasan']}\n\n", border="LBR")
    
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 5, "Diketahui,", align="C")
    pdf.cell(95, 5, "Disetujui,", ln=True, align="C")
    
    y_pos = pdf.get_y()
    
    try:
        if str(row['Waktu_GL']) != "nan":
            pdf.image("logo.png.png", x=35, y=y_pos + 2, w=35) 
        if str(row['Waktu_SH']) != "nan":
            pdf.image("logo.png.png", x=130, y=y_pos + 2, w=35)
    except:
        pass
        
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
    
    filename = f"SPL_{row['ID']}.pdf"
    pdf.output(filename)
    return filename

# Fungsi Preview Digital HTML
def display_html_preview(row):
    html_content = f"""
    <div style="background-color: white; padding: 20px; border: 1px solid #ccc; border-radius: 5px; color: black; font-family: Arial, sans-serif;">
        <div style="border: 1px solid black; padding: 10px; margin-bottom: 10px;">
            <b>PT. Saptaindra Sejati<br>Site Maco</b>
        </div>
        <h3 style="text-align: center; text-decoration: underline;">SURAT PERINTAH LEMBUR</h3>
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
            <tr>
                <td style="border: 1px solid black; padding: 8px; width: 25%;"><b>NAMA</b></td>
                <td style="border: 1px solid black; padding: 8px;" colspan="3">{row['Nama']}</td>
            </tr>
            <tr>
                <td style="border: 1px solid black; padding: 8px;"><b>NRP/DEPT</b></td>
                <td style="border: 1px solid black; padding: 8px;">{row['NRP']} / {row['Section']}</td>
                <td style="border: 1px solid black; padding: 8px; width: 15%;"><b>SHIFT :</b></td>
                <td style="border: 1px solid black; padding: 8px; width: 20%;">{row['Shift']}</td>
            </tr>
            <tr>
                <td style="border: 1px solid black; padding: 8px;"><b>TANGGAL :</b></td>
                <td style="border: 1px solid black; padding: 8px;">{row['Tanggal']}</td>
                <td style="border: 1px solid black; padding: 8px;"><b>JAM :</b></td>
                <td style="border: 1px solid black; padding: 8px;">{row['Jam']}</td>
            </tr>
            <tr>
                <td style="border: 1px solid black; padding: 8px;"><b>PERUSAHAAN :</b></td>
                <td style="border: 1px solid black; padding: 8px;" colspan="3">{row['Perusahaan']}</td>
            </tr>
            <tr>
                <td style="border: 1px solid black; padding: 8px; height: 60px; vertical-align: top;" colspan="4">
                    <b>Keterangan Lembur :</b><br><br>{row['Alasan']}
                </td>
            </tr>
        </table>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)

# Fungsi Validasi Login (3x Gagal Blokir)
def proses_login(username_key, password_input):
    users_data = load_users()
    if username_key not in users_data:
        st.error("Pengguna tidak ditemukan!")
        return False
        
    user_info = users_data[username_key]
    
    if user_info["blocked"]:
        st.error(f"🚨 Akun Anda ({username_key}) telah DIBLOKIR karena 3x salah sandi. Silakan hubungi Administrator!")
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
            st.error(f"🚨 PERINGATAN: Sandi salah 3x. Akun {username_key} kini DIBLOKIR!")
        else:
            st.error(f"❌ Sandi Salah! Sisa percobaan Anda: {sisa} kali lagi.")
        
        save_users(users_data)
        return False
    return False

# ==========================================
# 1. HALAMAN UTAMA (LANDING PAGE)
# ==========================================
if st.session_state.app_mode == "landing":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🏢 Portal SPL Digital PT. SIS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; margin-bottom: 50px;'>Silakan pilih gerbang akses Anda di bawah ini:</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 4, 4, 1])
    
    with col2:
        st.success("📝 **PORTAL KARYAWAN**")
        st.write("Masuk ke sini untuk mengisi formulir lembur. Tanpa perlu *login* atau kata sandi.")
        st.write("")
        if st.button("Masuk Form Pengajuan", use_container_width=True):
            st.session_state.role = "Karyawan"
            st.session_state.logged_in = True
            st.session_state.app_mode = "main"
            st.rerun()
            
    with col3:
        st.info("🔐 **PORTAL MANAJEMEN**")
        st.write("Khusus untuk GL/UH, Section Head, dan Administrator untuk melakukan verifikasi.")
        st.write("")
        if st.button("Masuk Halaman Login", use_container_width=True):
            st.session_state.app_mode = "login"
            st.rerun()

# ==========================================
# 2. HALAMAN LOGIN MANAJEMEN
# ==========================================
elif st.session_state.app_mode == "login":
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🔐 Login Manajemen</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col_back, _ = st.columns([2, 8])
    with col_back:
        if st.button("⬅️ Kembali ke Menu Utama"):
            st.session_state.app_mode = "landing"
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        # Perhatikan: Karyawan sudah dihapus dari pilihan login ini!
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
                if proses_login("Sect. Head", password):
                    st.session_state.logged_in = True
                    st.session_state.role = "Section Head"
                    st.session_state.username = "Sect. Head"
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
# 3. HALAMAN DASHBOARD UTAMA (SETELAH MASUK)
# ==========================================
elif st.session_state.app_mode == "main" and st.session_state.logged_in:
    
    # --- FITUR SIDEBAR GANTI PASSWORD MANDIRI ---
    if st.session_state.role != "Karyawan":
        with st.sidebar:
            st.header("🔑 Ganti Password")
            st.write("Ganti sandi Anda demi keamanan.")
            with st.form("form_ganti_pass", clear_on_submit=True):
                pass_lama = st.text_input("Password Lama", type="password")
                pass_baru = st.text_input("Password Baru", type="password")
                pass_konf = st.text_input("Konfirmasi Password Baru", type="password")
                
                if st.form_submit_button("Simpan Password"):
                    db_pass = load_users()
                    user_data = db_pass[st.session_state.username]
                    
                    if pass_lama != user_data["password"]:
                        st.error("Password lama salah!")
                    elif pass_baru != pass_konf:
                        st.error("Password baru tidak cocok!")
                    elif len(pass_baru) < 4:
                        st.error("Password terlalu pendek (Min 4 karakter)!")
                    else:
                        user_data["password"] = pass_baru
                        save_users(db_pass)
                        st.success("✅ Password berhasil diperbarui!")

    col_title, col_logout = st.columns([8, 2])
    with col_title:
        if st.session_state.role == "Karyawan":
            st.title("📄 Pengisian Form SPL")
        else:
            st.title(f"📄 Dashboard {st.session_state.role} - {st.session_state.username}")
            
    with col_logout:
        st.write("") 
        # Teks tombol disesuaikan. Jika karyawan, dia hanya 'Keluar' ke beranda.
        btn_text = "🚪 Keluar / Beranda" if st.session_state.role == "Karyawan" else "🚪 Logout Akun"
        if st.button(btn_text, use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.session_state.username = ""
            st.session_state.app_mode = "landing"
            st.rerun()
    
    st.write("---")
    
    config_del = load_config()

    # ------------------------------------------
    # TAMPILAN KHUSUS KARYAWAN
    # ------------------------------------------
    if st.session_state.role == "Karyawan":
        with st.form("form_spl", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nama = col1.text_input("Nama Karyawan *")
            nrp = col2.text_input("NRP *") 
            
            col_sec, col_per = st.columns(2)
            section = col_sec.selectbox("Section", ["Logistik"]) 
            perusahaan = col_per.selectbox("Nama Perusahaan", [
                "PT. Saptaindra Sejati", "PT. Cheisa Mandiri Utama", "PT. Borneo Mura Perkasa"
            ])
            
            col_tgl, col_shift = st.columns(2)
            tgl = col_tgl.date_input("Tanggal", value=datetime.now().date(), disabled=True)
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
            st.markdown("*Keterangan: Tanda (*) wajib diisi*")
            
            submitted = st.form_submit_button("Kirim Pengajuan Lembur")
            
            if submitted:
                waktu_awal_menit = (int(jam_a) * 60) + int(menit_a)
                waktu_akhir_menit = (int(jam_s) * 60) + int(menit_s)
                
                if not nama.strip() or not nrp.strip() or not alasan.strip():
                    st.error("⚠️ GAGAL: Nama, NRP, dan Keterangan wajib diisi!")
                elif waktu_akhir_menit <= waktu_awal_menit:
                    st.error("⚠️ GAGAL: Jam Akhir harus lebih besar dari Jam Awal!")
                else:
                    jam_gabungan = f"{jam_a}:{menit_a} - {jam_s}:{menit_s}"
                    df = get_db()
                    
                    new_id = str(int(time.time()))
                    new_data = {
                        "ID": new_id, "Nama": nama, "NRP": nrp, "Section": section, "Shift": shift, "Tanggal": str(tgl), 
                        "Jam": jam_gabungan, "Perusahaan": perusahaan, "Alasan": alasan, 
                        "Pengawas_Tujuan": pengawas_tujuan, 
                        "Status": "Pending GL", "Waktu_GL": None, "Nama_GL": None, "Waktu_SH": None, "Nama_SH": None, "Alasan_Tolak": ""
                    }
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    
                    st.success(f"✅ BERHASIL: SPL untuk {nama} terkirim!")
                    time.sleep(1.5)
                    st.rerun()

    # ------------------------------------------
    # TAMPILAN KHUSUS GL / UH
    # ------------------------------------------
    elif st.session_state.role == "GL/UH":
        df_gl = get_db()
        
        # 1. TUGAS REGULER SEBAGAI GL
        st.subheader("Menunggu Verifikasi Anda (Sebagai GL/UH)")
        pending_gl = df_gl[(df_gl["Status"] == "Pending GL") & (df_gl["Pengawas_Tujuan"] == st.session_state.username)]
        
        if pending_gl.empty:
            st.info("Tidak ada SPL baru untuk Anda saat ini.")
        else:
            st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
            cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
            cols[0].markdown("**NO**")
            cols[1].markdown("**Tanggal**")
            cols[2].markdown("**Nama**")
            cols[3].markdown("**NRP**")
            cols[4].markdown("**Shift**")
            cols[5].markdown("**Jam awal**")
            cols[6].markdown("**jam Akhir**")
            cols[7].markdown("**View**")
            cols[8].markdown("**Approve**")
            cols[9].markdown("**Tolak**")
            st.markdown("<hr style='margin: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

            for i, (idx, row) in enumerate(pending_gl.iterrows(), 1):
                cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
                cols[0].write(str(i))
                try:
                    t_str = datetime.strptime(row['Tanggal'], "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    t_str = row['Tanggal']
                cols[1].write(t_str)
                cols[2].write(row['Nama'])
                cols[3].write(row['NRP'])
                cols[4].write(row['Shift'].replace('Shift ', ''))
                jams = row['Jam'].split(' - ')
                cols[5].write(jams[0] if len(jams) > 0 else "")
                cols[6].write(jams[1] if len(jams) > 1 else "")
                
                with cols[7]:
                    with st.popover("👁️"):
                        display_html_preview(row)
                with cols[8]:
                    if st.button("Approve", key=f"gl_app_{row['ID']}"):
                        df_gl.loc[idx, "Status"] = "Pending SH"
                        df_gl.loc[idx, "Waktu_GL"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        df_gl.loc[idx, "Nama_GL"] = st.session_state.username 
                        df_gl.to_csv(DB_FILE, index=False)
                        st.rerun()
                with cols[9]:
                    with st.popover("Tolak"):
                        alasan_tolak = st.text_area("Masukkan Alasan Penolakan:", key=f"txt_tolak_gl_{row['ID']}")
                        if st.button("Konfirmasi Tolak", key=f"gl_del_{row['ID']}"):
                            if not alasan_tolak.strip():
                                st.error("Alasan penolakan tidak boleh kosong!")
                            else:
                                df_gl.loc[idx, "Status"] = "Ditolak"
                                df_gl.loc[idx, "Waktu_GL"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                df_gl.loc[idx, "Nama_GL"] = st.session_state.username 
                                df_gl.loc[idx, "Alasan_Tolak"] = alasan_tolak
                                df_gl.to_csv(DB_FILE, index=False)
                                st.rerun()
                st.markdown("<hr style='margin: 0px; opacity: 0.1;'>", unsafe_allow_html=True)
                    
        st.subheader("Riwayat Pekerjaan (Sebagai GL)")
        history_gl = df_gl[((df_gl["Status"] == "Pending SH") | (df_gl["Status"] == "Final Approved") | (df_gl["Status"] == "Ditolak")) & (df_gl["Nama_GL"] == st.session_state.username)]
        if not history_gl.empty:
            for idx, row in history_gl.iterrows():
                if row['Status'] == 'Ditolak':
                    st.error(f"❌ **{row['Nama']}** - {row['Tanggal']} (Ditolak pada: {row['Waktu_GL']}) | **Alasan:** {row.get('Alasan_Tolak', '')}")
                else:
                    st.write(f"✅ **{row['Nama']}** - {row['Tanggal']} (Status saat ini: {row['Status']})")

        # 2. TUGAS DELEGASI JIKA DITUNJUK MENJADI PJS SH
        if config_del["status_aktif"] and config_del["pjs_nama"] == st.session_state.username:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.warning("👑 **TUGAS PENDELEGASIAN:** Anda saat ini bertindak sebagai **Pjs. Section Head**.")
            st.subheader("Verifikasi Akhir (Kewenangan Pjs. Section Head)")
            
            pending_sh = df_gl[df_gl["Status"] == "Pending SH"]
            if pending_sh.empty:
                st.info("Antrean Final Approve kosong.")
            else:
                st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
                cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
                cols[0].markdown("**NO**")
                cols[1].markdown("**Tanggal**")
                cols[2].markdown("**Nama**")
                cols[3].markdown("**NRP**")
                cols[4].markdown("**Shift**")
                cols[5].markdown("**Jam awal**")
                cols[6].markdown("**jam Akhir**")
                cols[7].markdown("**View**")
                cols[8].markdown("**Approve**")
                cols[9].markdown("**Tolak**")
                st.markdown("<hr style='margin: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

                for i, (idx, row) in enumerate(pending_sh.iterrows(), 1):
                    cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
                    cols[0].write(str(i))
                    try:
                        t_str = datetime.strptime(row['Tanggal'], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except:
                        t_str = row['Tanggal']
                    cols[1].write(t_str)
                    cols[2].write(row['Nama'])
                    cols[3].write(row['NRP'])
                    cols[4].write(row['Shift'].replace('Shift ', ''))
                    jams = row['Jam'].split(' - ')
                    cols[5].write(jams[0] if len(jams) > 0 else "")
                    cols[6].write(jams[1] if len(jams) > 1 else "")
                    
                    with cols[7]:
                        with st.popover("👁️"):
                            display_html_preview(row)
                    with cols[8]:
                        if st.button("Approve", key=f"pjs_app_{row['ID']}"):
                            df_gl.loc[idx, "Status"] = "Final Approved"
                            df_gl.loc[idx, "Waktu_SH"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            df_gl.loc[idx, "Nama_SH"] = f"{st.session_state.username} (PJS Section Head)"
                            df_gl.to_csv(DB_FILE, index=False)
                            st.rerun()
                    with cols[9]:
                        with st.popover("Tolak"):
                            alasan_pjs = st.text_area("Masukkan Alasan Penolakan:", key=f"txt_tolak_pjs_{row['ID']}")
                            if st.button("Konfirmasi Tolak", key=f"pjs_del_{row['ID']}"):
                                if not alasan_pjs.strip():
                                    st.error("Alasan penolakan tidak boleh kosong!")
                                else:
                                    df_gl.loc[idx, "Status"] = "Ditolak"
                                    df_gl.loc[idx, "Waktu_SH"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                    df_gl.loc[idx, "Nama_SH"] = f"{st.session_state.username} (PJS Section Head)"
                                    df_gl.loc[idx, "Alasan_Tolak"] = alasan_pjs
                                    df_gl.to_csv(DB_FILE, index=False)
                                    st.rerun()
                    st.markdown("<hr style='margin: 0px; opacity: 0.1;'>", unsafe_allow_html=True)

            st.subheader("Arsip Dokumen Selesai (Sebagai Pjs. Section Head)")
            history_pjs = df_gl[(df_gl["Status"] == "Final Approved") & (df_gl["Nama_SH"] == f"{st.session_state.username} (PJS Section Head)")]
            if history_pjs.empty:
                st.write("Belum ada dokumen SPL yang Anda selesaikan sebagai Pjs.")
            else:
                for idx, row in history_pjs.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"📄 **SPL {row['Nama']} & {row['Tanggal']}** (Disetujui pada: {row['Waktu_SH']})")
                    with col2:
                        file_pdf = create_pdf(row)
                        with open(file_pdf, "rb") as f:
                            st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_pjs_fin_{row['ID']}")

    # ------------------------------------------
    # TAMPILAN KHUSUS SECTION HEAD
    # ------------------------------------------
    elif st.session_state.role == "Section Head":
        
        with st.expander("⚙️ PENGATURAN DELEGASI CUTI / OFFSITE", expanded=config_del["status_aktif"]):
            col_d1, col_d2 = st.columns([2, 2])
            with col_d1:
                idx_default = 0
                if config_del["pjs_nama"] in LIST_GL:
                    idx_default = LIST_GL.index(config_del["pjs_nama"])
                
                pjs_pilihan = st.selectbox("Pilih Pengawas Sebagai Pejabat Sementara (Pjs):", LIST_GL, index=idx_default)
            
            with col_d2:
                st.write("") 
                st.write("") 
                if not config_del["status_aktif"]:
                    if st.button("🚀 Aktifkan Delegasi (Saya Offsite)"):
                        config_del["status_aktif"] = True
                        config_del["pjs_nama"] = pjs_pilihan
                        save_config(config_del)
                        st.rerun()
                else:
                    if st.button("🛑 Cabut Delegasi (Saya Onsite)"):
                        config_del["status_aktif"] = False
                        config_del["pjs_nama"] = ""
                        save_config(config_del)
                        st.rerun()
            
            if config_del["status_aktif"]:
                st.error(f"🚨 **STATUS:** Kewenangan Section Head saat ini sedang dibantu / dialihkan kepada **{config_del['pjs_nama']}**.")
        
        st.markdown("<hr>", unsafe_allow_html=True)

        df_sh = get_db()
        st.subheader("Verifikasi Akhir (Final Approve)")
        
        pending_sh = df_sh[df_sh["Status"] == "Pending SH"]
        if pending_sh.empty:
            st.info("Tidak ada SPL menunggu verifikasi Section Head.")
        else:
            st.markdown("<hr style='margin: 0px;'>", unsafe_allow_html=True)
            cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
            cols[0].markdown("**NO**")
            cols[1].markdown("**Tanggal**")
            cols[2].markdown("**Nama**")
            cols[3].markdown("**NRP**")
            cols[4].markdown("**Shift**")
            cols[5].markdown("**Jam awal**")
            cols[6].markdown("**jam Akhir**")
            cols[7].markdown("**View**")
            cols[8].markdown("**Approve**")
            cols[9].markdown("**Tolak**")
            st.markdown("<hr style='margin: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

            for i, (idx, row) in enumerate(pending_sh.iterrows(), 1):
                cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
                cols[0].write(str(i))
                try:
                    t_str = datetime.strptime(row['Tanggal'], "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    t_str = row['Tanggal']
                cols[1].write(t_str)
                cols[2].write(row['Nama'])
                cols[3].write(row['NRP'])
                cols[4].write(row['Shift'].replace('Shift ', ''))
                
                jams = row['Jam'].split(' - ')
                cols[5].write(jams[0] if len(jams) > 0 else "")
                cols[6].write(jams[1] if len(jams) > 1 else "")
                
                with cols[7]:
                    with st.popover("👁️"):
                        display_html_preview(row)
                            
                with cols[8]:
                    if st.button("Approve", key=f"sh_app_{row['ID']}"):
                        df_sh.loc[idx, "Status"] = "Final Approved"
                        df_sh.loc[idx, "Waktu_SH"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        df_sh.loc[idx, "Nama_SH"] = "Haris Abi Wibowo"
                        df_sh.to_csv(DB_FILE, index=False)
                        st.rerun()
                        
                with cols[9]:
                    with st.popover("Tolak"):
                        alasan_sh = st.text_area("Masukkan Alasan Penolakan:", key=f"txt_tolak_sh_{row['ID']}")
                        if st.button("Konfirmasi Tolak", key=f"sh_del_{row['ID']}"):
                            if not alasan_sh.strip():
                                st.error("Alasan penolakan tidak boleh kosong!")
                            else:
                                df_sh.loc[idx, "Status"] = "Ditolak"
                                df_sh.loc[idx, "Waktu_SH"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                df_sh.loc[idx, "Nama_SH"] = "Haris Abi Wibowo"
                                df_sh.loc[idx, "Alasan_Tolak"] = alasan_sh
                                df_sh.to_csv(DB_FILE, index=False)
                                st.rerun()
                
                st.markdown("<hr style='margin: 0px; opacity: 0.1;'>", unsafe_allow_html=True)

        st.subheader("Arsip Dokumen Selesai (Siap Unduh)")
        approved_sh = df_sh[df_sh["Status"] == "Final Approved"]
        if approved_sh.empty:
            st.write("Belum ada dokumen SPL yang selesai.")
        else:
            for idx, row in approved_sh.iterrows():
                col1, col2 = st.columns([3, 1])
                nama_tampil = str(row['Nama_SH']).replace(" (PJS Section Head)", "") if pd.notna(row['Nama_SH']) else 'Haris Abi Wibowo'
                with col1:
                    st.write(f"📄 **SPL {row['Nama']} & {row['Tanggal']}** (Disetujui Oleh: {nama_tampil})")
                with col2:
                    file_pdf = create_pdf(df_sh.loc[idx])
                    with open(file_pdf, "rb") as f:
                        st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_sh_fin_{row['ID']}")

        st.subheader("❌ Arsip Dokumen Ditolak")
        rejected_sh = df_sh[(df_sh["Status"] == "Ditolak") & (df_sh["Nama_SH"] == "Haris Abi Wibowo")]
        if rejected_sh.empty:
            st.write("Belum ada riwayat penolakan dari Anda.")
        else:
            for idx, row in rejected_sh.iterrows():
                st.error(f"❌ **SPL {row['Nama']} & {row['Tanggal']}** (Anda tolak pada: {row['Waktu_SH']}) | **Alasan:** {row.get('Alasan_Tolak', '')}")

    # ------------------------------------------
    # TAMPILAN KHUSUS ADMIN (MONITORING & EXCEL)
    # ------------------------------------------
    elif st.session_state.role == "Admin":
        df_admin_raw = get_db()
        
        st.subheader("🎛️ Filter Data SPL")
        col_f1, col_f2 = st.columns([1, 2])
        with col_f1:
            mode_filter = st.radio("Mode Filter:", ["Semua Data", "Harian (Per Tanggal)", "Bulanan (Per Bulan)"], horizontal=True)
        
        df_admin = df_admin_raw.copy()
        nama_file_excel = "Rekapan_SPL_Semua"
        
        with col_f2:
            if mode_filter == "Harian (Per Tanggal)":
                tgl_filter = st.date_input("Pilih Tanggal:", value=datetime.now().date())
                df_admin = df_admin[df_admin["Tanggal"] == str(tgl_filter)]
                nama_file_excel = f"Rekapan_SPL_{tgl_filter}"
                
            elif mode_filter == "Bulanan (Per Bulan)":
                c_bln, c_thn = st.columns(2)
                list_bulan = [f"{i:02d}" for i in range(1, 13)]
                list_tahun = [str(y) for y in range(2024, 2031)]
                bln = c_bln.selectbox("Pilih Bulan:", list_bulan, index=datetime.now().month - 1)
                thn = c_thn.selectbox("Pilih Tahun:", list_tahun, index=list_tahun.index(str(datetime.now().year)))
                
                kunci_filter = f"{thn}-{bln}"
                df_admin = df_admin[df_admin["Tanggal"].astype(str).str.startswith(kunci_filter, na=False)]
                nama_file_excel = f"Rekapan_SPL_Bulan_{kunci_filter}"
                
        st.markdown("---")
        
        if df_admin.empty:
            st.warning("⚠️ Tidak ada data SPL yang ditemukan untuk filter yang dipilih.")
        else:
            st.subheader("📊 Tabel Database SPL & Rekapan Excel")
            
            df_display = df_admin.copy()
            if "ID" in df_display.columns:
                df_display = df_display.drop(columns=["ID"])
            
            df_display['Jam Awal'] = df_display['Jam'].apply(lambda x: x.split(' - ')[0] if pd.notna(x) and ' - ' in str(x) else "")
            df_display['Jam Akhir'] = df_display['Jam'].apply(lambda x: x.split(' - ')[1] if pd.notna(x) and ' - ' in str(x) else "")
            
            def hitung_durasi(jam_str):
                try:
                    awal, akhir = jam_str.split(' - ')
                    wa = datetime.strptime(awal, "%H:%M")
                    wk = datetime.strptime(akhir, "%H:%M")
                    selisih = (wk - wa).total_seconds() / 3600
                    if selisih < 0:
                        selisih += 24
                    return round(selisih, 2)
                except:
                    return 0

            df_display['Total Lembur (Jam)'] = df_display['Jam'].apply(hitung_durasi)
            df_display = df_display.drop(columns=['Jam']) 
            
            df_display.insert(0, "No.", range(1, len(df_display) + 1))
            cols_order = ['No.', 'Tanggal', 'Nama', 'NRP', 'Section', 'Shift', 'Jam Awal', 'Jam Akhir', 'Total Lembur (Jam)', 'Perusahaan', 'Alasan', 'Status', 'Pengawas_Tujuan', 'Waktu_GL', 'Nama_GL', 'Waktu_SH', 'Nama_SH', 'Alasan_Tolak']
            cols_order = [c for c in cols_order if c in df_display.columns]
            df_display = df_display[cols_order]
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_display.to_excel(writer, index=False, sheet_name='Rekap_SPL')
            excel_data = buffer.getvalue()
            
            st.download_button(
                label="📥 Download Rekapan Excel (.xlsx)", 
                data=excel_data, 
                file_name=f"{nama_file_excel}.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.dataframe(df_display, hide_index=True)
            
            st.markdown("---")
            
            st.subheader("⏳ Tracking Dokumen Belum Selesai (Pending)")
            pending_admin = df_admin[(df_admin["Status"] != "Final Approved") & (df_admin["Status"] != "Ditolak")]
            if pending_admin.empty:
                st.success("TIDAK ADA ANTRIAN pada filter ini.")
            else:
                for idx, row in pending_admin.iterrows():
                    if row["Status"] == "Pending GL":
                        posisi = f"Menunggu Persetujuan GL/UH: {row['Pengawas_Tujuan']}"
                        st.warning(f"📌 **SPL: {row['Nama']} & {row['Tanggal']}** ➔ Saat ini posisinya di: **{posisi}**")
                    else:
                        posisi = "Menunggu Persetujuan Akhir Section Head"
                        st.info(f"📌 **SPL: {row['Nama']} & {row['Tanggal']}** ➔ Saat ini posisinya di: **{posisi}**")
            
            st.markdown("---")

            st.subheader("❌ Riwayat Pengajuan Ditolak")
            rejected_admin = df_admin[df_admin["Status"] == "Ditolak"]
            if rejected_admin.empty:
                st.write("Tidak ada pengajuan yang ditolak pada filter ini.")
            else:
                for idx, row in rejected_admin.iterrows():
                    penolak = row['Nama_SH'] if pd.notna(row['Nama_SH']) and str(row['Nama_SH']).strip() and str(row['Nama_SH']) != "nan" else row['Nama_GL']
                    alasan = row.get('Alasan_Tolak', 'Tidak ada alasan.')
                    st.error(f"❌ **SPL {row['Nama']} & {row['Tanggal']}** ➔ Ditolak oleh: **{penolak}** | **Alasan:** {alasan}")

            st.markdown("---")
            
            st.subheader("🗂️ Arsip Lengkap Dokumen PDF (Disetujui)")
            approved_admin = df_admin[df_admin["Status"] == "Final Approved"]
            if approved_admin.empty:
                st.write("Belum ada dokumen PDF yang di-generate pada filter ini.")
            else:
                for idx, row in approved_admin.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"✅ **SPL {row['Nama']} & {row['Tanggal']}**")
                    with col2:
                        file_pdf = create_pdf(row)
                        with open(file_pdf, "rb") as f:
                            st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_adm_{row['ID']}")

        # --- FITUR BUKA BLOKIR & RESET PASSWORD ---
        st.markdown("---")
        st.subheader("🔐 Manajemen Keamanan Akun")
        db_admin_users = load_users()
        
        col_ua1, col_ua2 = st.columns(2)
        with col_ua1:
            st.markdown("**Akun Terblokir (Gagal Login 3x):**")
            blocked_users = [k for k, v in db_admin_users.items() if v["blocked"]]
            
            if not blocked_users:
                st.success("Aman! Tidak ada akun yang terblokir saat ini.")
            else:
                for bu in blocked_users:
                    col_b1, col_b2 = st.columns([3, 2])
                    col_b1.error(f"🔒 {bu}")
                    if col_b2.button("Buka Blokir", key=f"unblock_{bu}"):
                        db_admin_users[bu]["blocked"] = False
                        db_admin_users[bu]["failed_attempts"] = 0
                        db_admin_users[bu]["password"] = "default123"
                        save_users(db_admin_users)
                        st.success(f"Berhasil! Akun {bu} dibuka. Sandi direset ke: default123")
                        time.sleep(2)
                        st.rerun()
                        
        with col_ua2:
            st.markdown("**Reset Sandi Pengguna ke Default:**")
            user_to_reset = st.selectbox("Pilih Pengguna:", list(db_admin_users.keys()))
            if st.button("Reset Sandi ke 'default123'"):
                db_admin_users[user_to_reset]["password"] = "default123"
                db_admin_users[user_to_reset]["failed_attempts"] = 0
                db_admin_users[user_to_reset]["blocked"] = False
                save_users(db_admin_users)
                st.success(f"✅ Sandi untuk {user_to_reset} berhasil diubah menjadi: default123")
