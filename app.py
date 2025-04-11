import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# Koneksi ke Railway Postgres
conn = psycopg2.connect(
    host=st.secrets["DB_HOST"],
    database=st.secrets["DB_NAME"],
    user=st.secrets["DB_USER"],
    password=st.secrets["DB_PASS"],
    port=st.secrets["DB_PORT"]
)
cur = conn.cursor()

st.title("📦 Inventory Barang")

# Form input data baru
with st.form("form_barang"):
    nama = st.text_input("Nama Barang")
    stok = st.number_input("Jumlah Stok", min_value=0, step=1)
    submitted = st.form_submit_button("Tambah Barang")

    if submitted and nama:
        tanggal = datetime.now().strftime('%Y-%m-%d')
        cur.execute("INSERT INTO barang (nama, stok, tanggal) VALUES (%s, %s, %s)", (nama, stok, tanggal))
        conn.commit()
        st.success("Barang berhasil ditambahkan!")

# Ambil data dari tabel 'barang'
cur.execute("SELECT * FROM barang ORDER BY id DESC;")
rows = cur.fetchall()
df = pd.DataFrame(rows, columns=['id', 'nama', 'stok', 'tanggal'])

st.subheader("📋 Daftar Barang")
st.dataframe(df)

cur.close()
conn.close()
