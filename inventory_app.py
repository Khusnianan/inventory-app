import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date

# Konfigurasi koneksi database
def get_connection():
    return mysql.connector.connect(
        host="localhost",         # ganti jika bukan lokal
        user="root",              # ganti user Anda
        password="password",      # ganti password Anda
        database="inventory_db"   # nama database
    )

st.set_page_config(page_title="📦 Inventory Manager", layout="centered")
st.title("📦 Manajemen Inventory")

menu = st.sidebar.selectbox("Menu", ["📋 Daftar Barang", "➕ Tambah Barang", "📥 Transaksi Barang", "📊 Rekap Stok"])

# Fungsi tampil data
def tampil_barang():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM barang")
    data = cursor.fetchall()
    df = pd.DataFrame(data)
    st.subheader("📋 Daftar Barang")
    st.dataframe(df)
    conn.close()

# Fungsi tambah barang
def tambah_barang():
    st.subheader("➕ Tambah Barang Baru")
    kode = st.text_input("Kode Barang")
    nama = st.text_input("Nama Barang")
    kategori = st.text_input("Kategori")
    stok = st.number_input("Stok Awal", min_value=0)
    harga = st.number_input("Harga Satuan", min_value=0.0, format="%.2f")

    if st.button("Simpan Barang"):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO barang (kode, nama, kategori, stok, harga) VALUES (%s, %s, %s, %s, %s)",
                           (kode, nama, kategori, stok, harga))
            conn.commit()
            st.success("Barang berhasil ditambahkan!")
        except mysql.connector.Error as e:
            st.error(f"Gagal menambahkan: {e}")
        conn.close()

# Fungsi transaksi masuk/keluar
def transaksi_barang():
    st.subheader("📥 Input Transaksi Barang")
    jenis = st.selectbox("Jenis Transaksi", ["masuk", "keluar"])
    conn = get_connection()
    df_barang = pd.read_sql("SELECT kode, nama FROM barang", conn)
    barang = st.selectbox("Pilih Barang", df_barang["kode"] + " - " + df_barang["nama"])
    jumlah = st.number_input("Jumlah", min_value=1)
    tanggal = st.date_input("Tanggal", value=date.today())
    ket = st.text_area("Keterangan")

    if st.button("Simpan Transaksi"):
        kode_barang = barang.split(" - ")[0]
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO transaksi (kode_barang, tanggal, jenis, jumlah, keterangan) VALUES (%s, %s, %s, %s, %s)",
                           (kode_barang, tanggal, jenis, jumlah, ket))
            # Update stok
            sign = 1 if jenis == "masuk" else -1
            cursor.execute("UPDATE barang SET stok = stok + %s WHERE kode = %s", (sign * jumlah, kode_barang))
            conn.commit()
            st.success("Transaksi berhasil disimpan dan stok diperbarui!")
        except mysql.connector.Error as e:
            st.error(f"Gagal menyimpan transaksi: {e}")
        conn.close()

# Fungsi rekap
def rekap_stok():
    st.subheader("📊 Rekap Stok Barang")
    conn = get_connection()
    df = pd.read_sql("SELECT kode, nama, kategori, stok, harga FROM barang", conn)
    df["Total Nilai"] = df["stok"] * df["harga"]
    st.dataframe(df)
    st.write("💰 Total Nilai Inventory:", f"Rp {df['Total Nilai'].sum():,.2f}")
    conn.close()

# Routing menu
if menu == "📋 Daftar Barang":
    tampil_barang()
elif menu == "➕ Tambah Barang":
    tambah_barang()
elif menu == "📥 Transaksi Barang":
    transaksi_barang()\elif menu == "📊 Rekap Stok":
    rekap_stok()
