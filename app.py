import streamlit as st
from fpdf import FPDF
import pandas as pd
from datetime import datetime
import os

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem SPL Digital", layout="wide")

# Database Sederhana (CSV) - Bisa diganti SQL jika sudah besar
DB_FILE = "data_spl.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["ID", "Nama", "Tanggal", "Alasan", "Status", "Waktu_Approve"])
    df.to_csv(DB_FILE, index=False)

# Fungsi Generate PDF
class SPL_PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "SURAT PERINTAH LEMBUR (SPL)", ln=True, align="C")
        self.ln(5)

def create_pdf(row):
    pdf = SPL_PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Konten SPL
    pdf.cell(50, 10, f"No. SPL: SPL-{row['ID']}")
    pdf.ln(10)
    pdf.cell(50, 10, f"Nama Karyawan: {row['Nama']}")
    pdf.ln(10)
    pdf.cell(50, 10, f"Tanggal Tugas: {row['Tanggal']}")
    pdf.ln(10)
    pdf.multi_cell(0, 10, f"Alasan Lembur: {row['Alasan']}")
    
    # Bagian Tanda Tangan (Otomatis saat Approve)
    pdf.ln(20)
    pdf.cell(100, 10, "Pengaju,")
    pdf.cell(0, 10, "Pengawas (Verified),", ln=True)
    pdf.ln(15)
    pdf.cell(100, 10, f"({row['Nama']})")
    pdf.cell(0, 10, f"(Digitally Signed at {row['Waktu_Approve']})")
    
    filename = f"SPL_{row['ID']}.pdf"
    pdf.output(filename)
    return filename

# --- UI APP ---
st.title("📄 Digital Overtime System (SPL)")

tab1, tab2 = st.tabs(["Input Pengajuan", "Verifikasi Pengawas"])

with tab1:
    st.subheader("Form Input SPL")
    with st.form("form_spl"):
        nama = st.text_input("Nama Lengkap")
        tgl = st.date_input("Tanggal Lembur")
        alasan = st.text_area("Detail Pekerjaan")
        submitted = st.form_submit_button("Kirim Pengajuan")
        
        if submitted:
            df = pd.read_csv(DB_FILE)
            new_id = len(df) + 1
            new_data = {"ID": new_id, "Nama": nama, "Tanggal": tgl, "Alasan": alasan, "Status": "Pending", "Waktu_Approve": "-"}
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
            st.success(f"SPL Berhasil diajukan! ID: {new_id}")

with tab2:
    st.subheader("Daftar Menunggu Persetujuan")
    df_verif = pd.read_csv(DB_FILE)
    pending_data = df_verif[df_verif["Status"] == "Pending"]
    
    if pending_data.empty:
        st.info("Tidak ada SPL yang perlu diverifikasi.")
    else:
        for index, row in pending_data.iterrows():
            with st.expander(f"SPL # {row['ID']} - {row['Nama']}"):
                st.write(f"Detail: {row['Alasan']}")
                # Tombol 1x Klik
                if st.button("Verifikasi & Cetak PDF", key=f"btn_{row['ID']}"):
                    # Update status
                    df_verif.at[index, "Status"] = "Approved"
                    df_verif.at[index, "Waktu_Approve"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    df_verif.to_csv(DB_FILE, index=False)
                    
                    # Buat PDF
                    file_pdf = create_pdf(df_verif.loc[index])
                    
                    st.success("Tanda tangan digital berhasil ditempel!")
                    with open(file_pdf, "rb") as f:
                        st.download_button("Download PDF Sekarang", f, file_name=file_pdf)
