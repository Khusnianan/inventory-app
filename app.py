import streamlit as st
import psycopg2
import pandas as pd

# Koneksi ke Railway Postgres
conn = psycopg2.connect(
    host="shuttle.proxy.rlwy.net",
    database="railway",
    user="postgres",
    password="RNCRzYyNwkvCmYnyJtJUOfrxwqWXpzjh",
    port=25419
)
cur = conn.cursor()

# Ambil data dari tabel 'barang'
cur.execute("SELECT * FROM barang;")
rows = cur.fetchall()
df = pd.DataFrame(rows, columns=['id', 'nama', 'stok', 'tanggal'])

st.title("📦 Inventory Barang")
st.dataframe(df)

cur.close()
conn.close()
