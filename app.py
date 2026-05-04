import streamlit as st
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem SPL Digital", layout="wide")

# Setup Session State untuk Login Multi-Akun
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = "" # Menyimpan nama GL yang sedang login

# Database Sederhana (CSV) - Versi 5 (Tambah Shift dan Nama GL)
DB_FILE = "data_spl_v5.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=[
        "ID", "Nama", "NRP", "Section", "Shift", "Tanggal", "Jam", "Perusahaan", "Alasan", 
        "Status", "Waktu_GL", "Nama_GL", "Waktu_SH"
    ])
    df.to_csv(DB_FILE, index=False)

# Fungsi Generate PDF Tabel
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
    
    # Baris 1: NAMA
    pdf.cell(40, 10, " NAMA", border=1)
    pdf.cell(150, 10, f" {row['Nama']}", border=1, ln=True)
    
    # Baris 2: NRP/DEPT & SHIFT (Sejajar di atas JAM)
    pdf.cell(40, 10, " NRP/DEPT", border=1)
    pdf.cell(80, 10, f" {row['NRP']} / {row['Section']}", border=1)
    pdf.cell(30, 10, " SHIFT :", border=1)
    pdf.cell(40, 10, f" {row['Shift']}", border=1, ln=True) 
    
    # Baris 3: TANGGAL & JAM
    pdf.cell(40, 10, " TANGGAL :", border=1)
    pdf.cell(80, 10, f" {row['Tanggal']}", border=1)
    pdf.cell(30, 10, " JAM :", border=1)
    pdf.cell(40, 10, f" {row['Jam']}", border=1, ln=True)
    
    # Baris 4: PERUSAHAAN
    pdf.cell(40, 10, " PERUSAHAAN :", border=1)
    pdf.cell(150, 10, f" {row['Perusahaan']}", border=1, ln=True)
    
    # Baris 5: KETERANGAN
    pdf.cell(190, 10, " Keterangan Lembur :", border="LTR", ln=True)
    pdf.multi_cell(190, 10, f" {row['Alasan']}\n\n", border="LBR")
    
    # Bagian Tanda Tangan
    pdf.ln(15)
    pdf.cell(95, 10, "Diketahui,", align="C")
    pdf.cell(95, 10, "Disetujui,", ln=True, align="C")
    pdf.ln(15)
    
    gl_sign = f"Digitally Signed: {row['Waktu_GL']}" if str(row['Waktu_GL']) != "nan" else "........................"
    sh_sign = f"Digitally Signed: {row['Waktu_SH']}" if str(row['Waktu_SH']) != "nan" else "........................"
    
    # Menampilkan Nama GL spesifik yang login (jika ada), jika tidak tampilkan default "GL/UH"
    nama_pengawas = row['Nama_GL'] if str(row['Nama_GL']) != "nan" and row['Nama_GL'] else "GL/UH"
    
    pdf.cell(95, 10, "__________________________", align="C", ln=0)
    pdf.cell(95, 10, "__________________________", align="C", ln=1)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(95, 5, nama_pengawas, align="C") # Nama GL tercetak di sini
    pdf.cell(95, 5, "Sect. Head", align="C", ln=1)
    pdf.set_font("Arial", "I", 7)
    pdf.cell(95, 5, gl_sign, align="C")
    pdf.cell(95, 5, sh_sign, align="C", ln=1)
    
    filename = f"SPL_{row['ID']}.pdf"
    pdf.output(filename)
    return filename

# ==========================================
# KONFIGURASI AKUN GL (Bisa Ditambah Sendiri)
# ==========================================
AKUN_GL = {
    "Bapak Andi (GL 1)": "andi123",
    "Bapak Budi (GL 2)": "budi123",
    "Bapak Citra (GL 3)": "citra123"
}

# ==========================================
# HALAMAN LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 Portal SPL Digital PT. SIS</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Silakan Login")
        role = st.selectbox("Masuk Sebagai:", ["Pilih Akses...", "Karyawan (Form Input)", "GL/UH (Verifikasi 1)", "Section Head (Verifikasi 2)"])
        
        # Logika Karyawan
        if role == "Karyawan (Form Input)":
            if st.button("Masuk Form SPL"):
                st.session_state.logged_in = True
                st.session_state.role = "Karyawan"
                st.rerun()
                
        # Logika GL/UH (Multi-Akun)
        elif role == "GL/UH (Verifikasi 1)":
            nama_gl = st.selectbox("Pilih Nama Anda", list(AKUN_GL.keys()))
            password = st.text_input("Password", type="password")
            if st.button("Login GL"):
                # Cek apakah password cocok dengan nama GL yang dipilih
                if password == AKUN_GL[nama_gl]: 
                    st.session_state.logged_in = True
                    st.session_state.role = "GL/UH"
                    st.session_state.username = nama_gl
                    st.rerun()
                elif password != "":
                    st.error("Password Salah!")
                    
        # Logika Section Head
        elif role == "Section Head (Verifikasi 2)":
            password = st.text_input("Password Section Head", type="password")
            if st.button("Login Sect Head"):
                if password == "sh123": 
                    st.session_state.logged_in = True
                    st.session_state.role = "Section Head"
                    st.session_state.username = "Sect. Head"
                    st.rerun()
                elif password != "":
                    st.error("Password Salah!")

# ==========================================
# HALAMAN UTAMA (SETELAH LOGIN)
# ==========================================
else:
    col_title, col_logout = st.columns([8, 1])
    with col_title:
        # Menampilkan nama yang login di judul dashboard
        nama_user = st.session_state.username if st.session_state.username else "Karyawan"
        st.title(f"📄 Dashboard {st.session_state.role} - {nama_user}")
    with col_logout:
        st.write("") 
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.role = ""
            st.session_state.username = ""
            st.rerun()
    
    st.write("---")

    # ------------------------------------------
    # TAMPILAN KHUSUS KARYAWAN
    # ------------------------------------------
    if st.session_state.role == "Karyawan":
        st.subheader("Formulir Pengajuan Lembur")
        with st.form("form_spl"):
            col1, col2 = st.columns(2)
            nama = col1.text_input("Nama Karyawan")
            nrp = col2.text_input("NRP") 
            
            col_sec, col_per = st.columns(2)
            section = col_sec.selectbox("Section", ["Logistik"]) 
            perusahaan = col_per.selectbox("Nama Perusahaan", [
                "PT. Saptaindra Sejati", 
                "PT. Cheisa Mandiri Utama", 
                "PT. Borneo Mura Perkasa"
            ])
            
            # --- INPUT TANGGAL & SHIFT ---
            col_tgl, col_shift = st.columns(2)
            tgl = col_tgl.date_input("Tanggal")
            shift = col_shift.selectbox("Shift Lembur", ["Shift 1", "Shift 2"])
            # -----------------------------
            
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
            
            alasan = st.text_area("Keterangan Lembur")
            submitted = st.form_submit_button("Kirim Pengajuan")
            
            if submitted:
                jam_gabungan = f"{jam_a}:{menit_a} - {jam_s}:{menit_s}"
                df = pd.read_csv(DB_FILE, dtype=str)
                new_id = len(df) + 1
                new_data = {
                    "ID": new_id, "Nama": nama, "NRP": nrp, "Section": section, "Shift": shift, "Tanggal": str(tgl), 
                    "Jam": jam_gabungan, "Perusahaan": perusahaan, "Alasan": alasan, 
                    "Status": "Pending GL", "Waktu_GL": None, "Nama_GL": None, "Waktu_SH": None
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                df.to_csv(DB_FILE, index=False)
                st.success(f"SPL untuk {nama} berhasil terkirim! Waktu: {jam_gabungan}")

    # ------------------------------------------
    # TAMPILAN KHUSUS GL / UH
    # ------------------------------------------
    elif st.session_state.role == "GL/UH":
        df_gl = pd.read_csv(DB_FILE, dtype=str)
        
        st.subheader("Menunggu Verifikasi Anda")
        pending_gl = df_gl[df_gl["Status"] == "Pending GL"]
        if pending_gl.empty:
            st.info("Tidak ada SPL baru.")
        else:
            for idx, row in pending_gl.iterrows():
                # Tampilan Tombol Format: Nama & Tanggal (Shift)
                label_tombol = f"Approve: {row['Nama']} & {row['Tanggal']} ({row['Shift']})"
                if st.button(label_tombol, key=f"gl_{row['ID']}"):
                    df_gl.loc[idx, "Status"] = "Pending SH"
                    df_gl.loc[idx, "Waktu_GL"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    df_gl.loc[idx, "Nama_GL"] = st.session_state.username # Menyimpan siapa GL yang approve
                    df_gl.to_csv(DB_FILE, index=False)
                    st.rerun()
                    
        st.markdown("---")
        st.subheader("Riwayat Telah Diverifikasi (Diteruskan ke Sect. Head)")
        # Hanya melihat riwayat yang di-approve oleh GL yang sedang login
        history_gl = df_gl[((df_gl["Status"] == "Pending SH") | (df_gl["Status"] == "Final Approved")) & (df_gl["Nama_GL"] == st.session_state.username)]
        if history_gl.empty:
            st.write("Belum ada riwayat persetujuan dari Anda.")
        else:
            for idx, row in history_gl.iterrows():
                st.write(f"✅ **SPL {row['Nama']} & {row['Tanggal']}** (Disetujui pada: {row['Waktu_GL']})")

    # ------------------------------------------
    # TAMPILAN KHUSUS SECTION HEAD
    # ------------------------------------------
    elif st.session_state.role == "Section Head":
        df_sh = pd.read_csv(DB_FILE, dtype=str)
        
        st.subheader("Menunggu Verifikasi Akhir")
        pending_sh = df_sh[df_sh["Status"] == "Pending SH"]
        if pending_sh.empty:
            st.info("Tidak ada SPL menunggu verifikasi Section Head.")
        else:
            for idx, row in pending_sh.iterrows():
                # Tampilan Tombol Format: Nama & Tanggal
                label_tombol = f"Final Approve: {row['Nama']} & {row['Tanggal']} (Oleh: {row['Nama_GL']})"
                if st.button(label_tombol, key=f"sh_{row['ID']}"):
                    df_sh.loc[idx, "Status"] = "Final Approved"
                    df_sh.loc[idx, "Waktu_SH"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    df_sh.to_csv(DB_FILE, index=False)
                    st.rerun()

        st.markdown("---")
        st.subheader("Arsip Dokumen Selesai (Siap Unduh)")
        approved_sh = df_sh[df_sh["Status"] == "Final Approved"]
        if approved_sh.empty:
            st.write("Belum ada dokumen SPL yang selesai.")
        else:
            for idx, row in approved_sh.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 **SPL {row['Nama']} & {row['Tanggal']}** (Selesai: {row['Waktu_SH']})")
                with col2:
                    file_pdf = create_pdf(df_sh.loc[idx])
                    with open(file_pdf, "rb") as f:
                        st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_{row['ID']}")
