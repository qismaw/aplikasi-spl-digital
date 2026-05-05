import streamlit as st
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os
import time

# Konfigurasi Halaman & CSS Kustom untuk Warna Tombol
st.set_page_config(page_title="Sistem SPL Digital", layout="wide")

st.markdown("""
<style>
/* Desain Tombol Approve (Hijau) */
div[data-testid="stButton"] button:has(p:contains("Approve")) {
    background-color: #00c853 !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}

/* Desain Tombol Tolak (Merah) */
div[data-testid="stButton"] button:has(p:contains("Tolak")) {
    background-color: #ff1744 !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}

/* Menyesuaikan tombol popover mata agar rapi */
div[data-testid="stPopover"] button {
    padding: 0.2rem 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Setup Session State untuk Login Multi-Akun
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = ""
    st.session_state.username = "" 

# ==========================================
# KONFIGURASI AKUN PENGGUNA
# ==========================================
AKUN_GL = {
    "Bapak Andi (GL 1)": "andi123",
    "Bapak Budi (GL 2)": "budi123",
    "Bapak Citra (GL 3)": "citra123"
}

# Database Sederhana (CSV)
DB_FILE = "data_spl_v7.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=[
        "ID", "Nama", "NRP", "Section", "Shift", "Tanggal", "Jam", "Perusahaan", "Alasan", 
        "Pengawas_Tujuan", "Status", "Waktu_GL", "Nama_GL", "Waktu_SH"
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
    nama_sh = "Haris Abi Wibowo"
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 5, "__________________________", align="C", ln=0)
    pdf.cell(95, 5, "__________________________", align="C", ln=1)
    
    pdf.set_font("Arial", "B", 9)
    pdf.cell(95, 5, nama_pengawas, align="C") 
    pdf.cell(95, 5, nama_sh, align="C", ln=1)
    
    filename = f"SPL_{row['ID']}.pdf"
    pdf.output(filename)
    return filename

# ==========================================
# HALAMAN LOGIN
# ==========================================
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>🔐 Portal SPL Digital PT. SIS</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Silakan Login")
        role = st.selectbox("Masuk Sebagai:", [
            "Pilih Akses...", "Karyawan (Form Input)", "GL/UH (Verifikasi 1)", 
            "Section Head (Verifikasi 2)", "Admin (Monitoring & Rekapan)"
        ])
        
        if role == "Karyawan (Form Input)":
            if st.button("Masuk Form SPL"):
                st.session_state.logged_in = True
                st.session_state.role = "Karyawan"
                st.rerun()
                
        elif role == "GL/UH (Verifikasi 1)":
            nama_gl = st.selectbox("Pilih Nama Anda", list(AKUN_GL.keys()))
            password = st.text_input("Password", type="password")
            if st.button("Login GL"):
                if password == AKUN_GL[nama_gl]: 
                    st.session_state.logged_in = True
                    st.session_state.role = "GL/UH"
                    st.session_state.username = nama_gl
                    st.rerun()
                elif password != "":
                    st.error("Password Salah!")
                    
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
                    
        elif role == "Admin (Monitoring & Rekapan)":
            password = st.text_input("Password Admin", type="password")
            if st.button("Login Admin"):
                if password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.role = "Admin"
                    st.session_state.username = "Administrator"
                    st.rerun()
                elif password != "":
                    st.error("Password Salah!")

# ==========================================
# HALAMAN UTAMA (SETELAH LOGIN)
# ==========================================
else:
    col_title, col_logout = st.columns([8, 1])
    with col_title:
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
            
            pengawas_tujuan = st.selectbox("Pengawas (GL) Yang Bertugas", list(AKUN_GL.keys()))
            
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
            submitted = st.form_submit_button("Kirim Pengajuan")
            
            if submitted:
                waktu_awal_menit = (int(jam_a) * 60) + int(menit_a)
                waktu_akhir_menit = (int(jam_s) * 60) + int(menit_s)
                
                if not nama.strip() or not nrp.strip() or not alasan.strip():
                    st.error("⚠️ PENGIRIMAN GAGAL: Harap pastikan Nama, NRP, dan Keterangan Lembur sudah diisi semua!")
                elif waktu_akhir_menit <= waktu_awal_menit:
                    st.error("⚠️ PENGIRIMAN GAGAL: Jam Akhir tidak boleh lebih kecil atau sama dengan Jam Awal!")
                else:
                    jam_gabungan = f"{jam_a}:{menit_a} - {jam_s}:{menit_s}"
                    df = pd.read_csv(DB_FILE, dtype=str)
                    new_id = str(int(time.time())) 
                    new_data = {
                        "ID": new_id, "Nama": nama, "NRP": nrp, "Section": section, "Shift": shift, "Tanggal": str(tgl), 
                        "Jam": jam_gabungan, "Perusahaan": perusahaan, "Alasan": alasan, 
                        "Pengawas_Tujuan": pengawas_tujuan, 
                        "Status": "Pending GL", "Waktu_GL": None, "Nama_GL": None, "Waktu_SH": None
                    }
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    df.to_csv(DB_FILE, index=False)
                    st.success(f"SPL berhasil terkirim ke {pengawas_tujuan}! Waktu: {jam_gabungan}")

    # ------------------------------------------
    # TAMPILAN KHUSUS GL / UH
    # ------------------------------------------
    elif st.session_state.role == "GL/UH":
        df_gl = pd.read_csv(DB_FILE, dtype=str)
        st.subheader("Menunggu Verifikasi Anda")
        pending_gl = df_gl[(df_gl["Status"] == "Pending GL") & (df_gl["Pengawas_Tujuan"] == st.session_state.username)]
        
        if pending_gl.empty:
            st.info("Tidak ada SPL baru untuk Anda saat ini.")
        else:
            st.markdown("<hr style='margin: 0px; padding: 0px;'>", unsafe_allow_html=True)
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
            cols[9].markdown("**Tolak/Hapus**")
            st.markdown("<hr style='margin: 0px; padding: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

            for i, (idx, row) in enumerate(pending_gl.iterrows(), 1):
                cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
                cols[0].write(str(i))
                
                try:
                    t_obj = datetime.strptime(row['Tanggal'], "%Y-%m-%d")
                    t_str = t_obj.strftime("%d/%m/%Y")
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
                        st.write(f"**Perusahaan:** {row['Perusahaan']}")
                        st.write(f"**Alasan:** {row['Alasan']}")
                        file_pdf = create_pdf(row)
                        with open(file_pdf, "rb") as f:
                            st.download_button("📄 Draft PDF", f, file_name=f"Draft_{file_pdf}", key=f"dl_gl_{row['ID']}")
                            
                with cols[8]:
                    if st.button("Approve", key=f"app_{row['ID']}"):
                        df_gl.loc[idx, "Status"] = "Pending SH"
                        df_gl.loc[idx, "Waktu_GL"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        df_gl.loc[idx, "Nama_GL"] = st.session_state.username 
                        df_gl.to_csv(DB_FILE, index=False)
                        st.rerun()
                        
                with cols[9]:
                    if st.button("Tolak", key=f"del_{row['ID']}"):
                        df_gl = df_gl.drop(idx)
                        df_gl.to_csv(DB_FILE, index=False)
                        st.rerun()
                
                st.markdown("<hr style='margin: 0px; padding: 0px; opacity: 0.1;'>", unsafe_allow_html=True)
                    
        st.subheader("Riwayat Telah Diverifikasi")
        history_gl = df_gl[((df_gl["Status"] == "Pending SH") | (df_gl["Status"] == "Final Approved")) & (df_gl["Nama_GL"] == st.session_state.username)]
        if history_gl.empty:
            st.write("Belum ada riwayat persetujuan dari Anda.")
        else:
            for idx, row in history_gl.iterrows():
                st.write(f"✅ **SPL {row['Nama']} & {row['Tanggal']}** (Disetujui: {row['Waktu_GL']})")

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
            st.markdown("<hr style='margin: 0px; padding: 0px;'>", unsafe_allow_html=True)
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
            cols[9].markdown("**Tolak/Hapus**")
            st.markdown("<hr style='margin: 0px; padding: 0px; margin-bottom: 10px;'>", unsafe_allow_html=True)

            for i, (idx, row) in enumerate(pending_sh.iterrows(), 1):
                cols = st.columns([0.6, 1.5, 2.5, 1.5, 0.8, 1.2, 1.2, 1.0, 1.2, 1.2])
                cols[0].write(str(i))
                
                try:
                    t_obj = datetime.strptime(row['Tanggal'], "%Y-%m-%d")
                    t_str = t_obj.strftime("%d/%m/%Y")
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
                        st.write(f"**Di-Approve Oleh GL:** {row['Nama_GL']}")
                        st.write(f"**Perusahaan:** {row['Perusahaan']}")
                        st.write(f"**Keterangan:** {row['Alasan']}")
                        file_pdf = create_pdf(row)
                        with open(file_pdf, "rb") as f:
                            st.download_button("📄 Draft PDF", f, file_name=f"Draft_{file_pdf}", key=f"dl_sh_{row['ID']}")
                            
                with cols[8]:
                    if st.button("Approve", key=f"sh_app_{row['ID']}"):
                        df_sh.loc[idx, "Status"] = "Final Approved"
                        df_sh.loc[idx, "Waktu_SH"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        df_sh.to_csv(DB_FILE, index=False)
                        st.rerun()
                        
                with cols[9]:
                    if st.button("Tolak", key=f"sh_del_{row['ID']}"):
                        df_sh = df_sh.drop(idx)
                        df_sh.to_csv(DB_FILE, index=False)
                        st.rerun()
                
                st.markdown("<hr style='margin: 0px; padding: 0px; opacity: 0.1;'>", unsafe_allow_html=True)

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
                        st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_sh_fin_{row['ID']}")

    # ------------------------------------------
    # TAMPILAN KHUSUS ADMIN (MONITORING & EXCEL)
    # ------------------------------------------
    elif st.session_state.role == "Admin":
        df_admin = pd.read_csv(DB_FILE, dtype=str)
        
        st.subheader("📊 Tabel Database Seluruh SPL")
        
        df_display = df_admin.copy()
        if "ID" in df_display.columns:
            df_display = df_display.drop(columns=["ID"])
            
        df_display.insert(0, "No.", range(1, len(df_display) + 1))
        
        csv_data = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Rekapan Format Excel (CSV)", 
            data=csv_data, 
            file_name="Rekapan_SPL_Maco.csv", 
            mime="text/csv"
        )
        
        st.dataframe(df_display, hide_index=True)
        
        st.markdown("---")
        
        st.subheader("⏳ Tracking Dokumen Belum Selesai (Pending)")
        pending_admin = df_admin[df_admin["Status"] != "Final Approved"]
        if pending_admin.empty:
            st.success("TIDAK ADA ANTRIAN. Seluruh pengajuan lembur sudah disetujui.")
        else:
            for idx, row in pending_admin.iterrows():
                if row["Status"] == "Pending GL":
                    posisi = f"Menunggu Persetujuan GL/UH: {row['Pengawas_Tujuan']}"
                    st.warning(f"📌 **SPL: {row['Nama']} & {row['Tanggal']}** ➔ Saat ini posisinya di: **{posisi}**")
                else:
                    posisi = "Menunggu Persetujuan Akhir Section Head"
                    st.info(f"📌 **SPL: {row['Nama']} & {row['Tanggal']}** ➔ Saat ini posisinya di: **{posisi}**")
                    
        st.markdown("---")
        
        st.subheader("🗂️ Arsip Lengkap Dokumen PDF")
        approved_admin = df_admin[df_admin["Status"] == "Final Approved"]
        if approved_admin.empty:
            st.write("Belum ada dokumen PDF yang di-generate.")
        else:
            for idx, row in approved_admin.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"✅ **SPL {row['Nama']} & {row['Tanggal']}**")
                with col2:
                    file_pdf = create_pdf(df_admin.loc[idx])
                    with open(file_pdf, "rb") as f:
                        st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_adm_{row['ID']}")
