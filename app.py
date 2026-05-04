import streamlit as st
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem SPL Digital", layout="wide")

# Database Sederhana (CSV) - Menggunakan v3 agar tabel baru terbaca bersih
DB_FILE = "data_spl_v3.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=[
        "ID", "Nama", "NRP_Dept", "Tanggal", "Jam", "Perusahaan", "Alasan", 
        "Status", "Waktu_GL", "Waktu_SH"
    ])
    df.to_csv(DB_FILE, index=False)

# Fungsi Generate PDF Tabel (Sudah Dirapikan)
def create_pdf(row):
    pdf = FPDF()
    pdf.add_page()
    
    # Border Luar Dokumen
    pdf.rect(5, 5, 200, 287)
    
    pdf.set_font("Arial", "B", 12)
    
    # Header Logo & Nama Perusahaan
    pdf.cell(50, 20, "", border=1) 
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 10, "PT. Saptaindra Sejati\nSite Maco", border=1, align='L')
    
    # Menempelkan gambar logo (w diperbesar dari 25 menjadi 42 agar lebih besar & jelas)
    try:
        pdf.image("logo.png.png", x=9, y=11, w=42) 
    except:
        pass 
    
    pdf.ln(10)
    pdf.set_font("Arial", "BU", 14)
    pdf.cell(0, 10, "SURAT PERINTAH LEMBUR", ln=True, align="C")
    pdf.ln(5)
    
    # Body Tabel
    pdf.set_font("Arial", "", 10)
    
    # Baris 1: NAMA
    pdf.cell(40, 10, " NAMA", border=1)
    pdf.cell(150, 10, f" {row['Nama']}", border=1, ln=True)
    
    # Baris 2: NRP/DEPT
    pdf.cell(40, 10, " NRP/DEPT", border=1)
    pdf.cell(80, 10, f" {row['NRP_Dept']}", border=1)
    pdf.cell(70, 10, "", border=1, ln=True) 
    
    # Baris 3: TANGGAL & JAM
    pdf.cell(40, 10, " TANGGAL :", border=1)
    pdf.cell(80, 10, f" {row['Tanggal']}", border=1)
    pdf.cell(30, 10, " JAM :", border=1)
    pdf.cell(40, 10, f" {row['Jam']}", border=1, ln=True)
    
    # Baris 4: PERUSAHAAN (Opsi Baru)
    pdf.cell(40, 10, " PERUSAHAAN :", border=1)
    pdf.cell(150, 10, f" {row['Perusahaan']}", border=1, ln=True)
    
    # Baris 5: KETERANGAN
    pdf.cell(190, 10, " Keterangan Lembur :", border="LTR", ln=True)
    # Tambahan \n\n agar kolom keterangan lumayan luas ke bawah dan rapi
    pdf.multi_cell(190, 10, f" {row['Alasan']}\n\n", border="LBR")
    
    # Bagian Tanda Tangan
    pdf.ln(15)
    pdf.cell(95, 10, "Diketahui,", align="C")
    pdf.cell(95, 10, "Disetujui,", ln=True, align="C")
    pdf.ln(15)
    
    gl_sign = f"Digitally Signed: {row['Waktu_GL']}" if str(row['Waktu_GL']) != "nan" else "........................"
    sh_sign = f"Digitally Signed: {row['Waktu_SH']}" if str(row['Waktu_SH']) != "nan" else "........................"
    
    pdf.cell(95, 10, "__________________________", align="C", ln=0)
    pdf.cell(95, 10, "__________________________", align="C", ln=1)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(95, 5, "GL/UH", align="C")
    pdf.cell(95, 5, "Sect. Head", align="C", ln=1)
    pdf.set_font("Arial", "I", 7)
    pdf.cell(95, 5, gl_sign, align="C")
    pdf.cell(95, 5, sh_sign, align="C", ln=1)
    
    filename = f"SPL_{row['ID']}.pdf"
    pdf.output(filename)
    return filename

# --- UI APP ---
st.title("📄 SPL Digital PT. SIS (Site Maco)")

tab1, tab2, tab3 = st.tabs(["Input SPL", "Verifikasi GL/UH", "Verifikasi Sect. Head"])

# TAB 1: INPUT
with tab1:
    with st.form("form_spl"):
        col1, col2 = st.columns(2)
        nama = col1.text_input("Nama Karyawan")
        nrp = col2.text_input("NRP / DEPT")
        tgl = col1.date_input("Tanggal")
        
        # --- PERUBAHAN INPUT JAM (DROP DOWN TERPISAH) ---
        st.markdown("**Waktu Lembur:**")
        col_jam_awal, col_jam_akhir = st.columns(2)
        
        # Opsi Jam (00-23) dan Menit (00-59)
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
        # -----------------------------------------------
        
        perusahaan = st.selectbox("Nama Perusahaan", ["PT. Sapta Indrasejati", "PT. Cheisa Mandiri Utama", "PT. Borneo Mura Perkasa", "Lainnya"])
        alasan = st.text_area("Keterangan Lembur")
        submitted = st.form_submit_button("Kirim Pengajuan")
        
        if submitted:
            # Menggabungkan pilihan dropdown menjadi format teks 08:00 - 09:00
            jam_gabungan = f"{jam_a}:{menit_a} - {jam_s}:{menit_s}"
            
            df = pd.read_csv(DB_FILE, dtype=str)
            new_id = len(df) + 1
            new_data = {
                "ID": new_id, "Nama": nama, "NRP_Dept": nrp, "Tanggal": str(tgl), 
                "Jam": jam_gabungan, "Perusahaan": perusahaan, "Alasan": alasan, 
                "Status": "Pending GL", "Waktu_GL": None, "Waktu_SH": None
            }
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"SPL untuk {nama} berhasil terkirim! Waktu: {jam_gabungan}")

# TAB 2: VERIFIKASI GL
with tab2:
    df_gl = pd.read_csv(DB_FILE, dtype=str)
    
    # Antrean GL
    st.subheader("Menunggu Verifikasi Anda")
    pending_gl = df_gl[df_gl["Status"] == "Pending GL"]
    if pending_gl.empty:
        st.info("Tidak ada SPL baru.")
    else:
        for idx, row in pending_gl.iterrows():
            if st.button(f"Approve SPL #{row['ID']} ({row['Nama']})", key=f"gl_{row['ID']}"):
                df_gl.loc[idx, "Status"] = "Pending SH"
                df_gl.loc[idx, "Waktu_GL"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                df_gl.to_csv(DB_FILE, index=False)
                st.rerun()
                
    st.markdown("---")
    
    # Riwayat GL
    st.subheader("Riwayat Telah Diverifikasi (Diteruskan ke Sect. Head)")
    # Menampilkan yang sudah di-approve GL (baik yang masih pending SH maupun sudah final)
    history_gl = df_gl[(df_gl["Status"] == "Pending SH") | (df_gl["Status"] == "Final Approved")]
    if history_gl.empty:
        st.write("Belum ada riwayat persetujuan.")
    else:
        for idx, row in history_gl.iterrows():
            st.write(f"✅ **SPL #{row['ID']}** - {row['Nama']} (Disetujui pada: {row['Waktu_GL']})")

# TAB 3: VERIFIKASI SECT HEAD & DOWNLOAD
with tab3:
    df_sh = pd.read_csv(DB_FILE, dtype=str)
    
    # Antrean Section Head
    st.subheader("Menunggu Verifikasi Akhir")
    pending_sh = df_sh[df_sh["Status"] == "Pending SH"]
    if pending_sh.empty:
        st.info("Tidak ada SPL menunggu verifikasi Section Head.")
    else:
        for idx, row in pending_sh.iterrows():
            if st.button(f"Final Approve SPL #{row['ID']} ({row['Nama']})", key=f"sh_{row['ID']}"):
                df_sh.loc[idx, "Status"] = "Final Approved"
                df_sh.loc[idx, "Waktu_SH"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                df_sh.to_csv(DB_FILE, index=False)
                st.rerun()

    st.markdown("---")
    
    # Riwayat Section Head & Download
    st.subheader("Arsip Dokumen Selesai (Siap Unduh)")
    approved_sh = df_sh[df_sh["Status"] == "Final Approved"]
    if approved_sh.empty:
        st.write("Belum ada dokumen SPL yang selesai.")
    else:
        for idx, row in approved_sh.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"📄 **SPL #{row['ID']}** - {row['Nama']} (Selesai: {row['Waktu_SH']})")
            with col2:
                # Generate PDF di belakang layar saat halaman dimuat
                file_pdf = create_pdf(df_sh.loc[idx])
                with open(file_pdf, "rb") as f:
                    st.download_button("Download PDF", f, file_name=file_pdf, key=f"dl_{row['ID']}")
