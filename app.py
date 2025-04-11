import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# --- KONEKSI DB ---
def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASS"],
        port=st.secrets["DB_PORT"]
    )

conn = get_connection()
cur = conn.cursor()

st.title("📦 Inventory Barang")

# --- TAMBAH BARANG ---
with st.form("form_barang"):
    st.subheader("➕ Tambah Barang")
    nama = st.text_input("Nama Barang")
    stok = st.number_input("Jumlah Stok", min_value=0, step=1)
    submitted = st.form_submit_button("Tambah Barang")

    if submitted and nama:
        tanggal = datetime.now().strftime('%Y-%m-%d')
        cur.execute("INSERT INTO barang (nama, stok, tanggal) VALUES (%s, %s, %s)",
                    (nama, stok, tanggal))
        conn.commit()
        st.success("✅ Barang berhasil ditambahkan!")
        st.experimental_rerun()

# --- TAMPILKAN TABEL ---
st.subheader("📋 Daftar Barang")

cur.execute("SELECT * FROM barang ORDER BY id DESC")
rows = cur.fetchall()
df = pd.DataFrame(rows, columns=['id', 'nama', 'stok', 'tanggal'])

# Tampilkan tombol hapus di tiap baris
for index, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([1.5, 3, 2, 3, 2])
    col1.write(row["id"])
    col2.write(row["nama"])
    col3.write(row["stok"])
    col4.write(row["tanggal"])
    if col5.button("🗑️ Hapus", key=f"hapus_{row['id']}"):
        cur.execute("DELETE FROM barang WHERE id = %s", (row["id"],))
        conn.commit()
        st.success(f"Barang ID {row['id']} dihapus.")
        st.experimental_rerun()

# --- EDIT BARANG ---
st.subheader("✏️ Edit Barang")

# Ambil daftar ID & Nama
cur.execute("SELECT id, nama FROM barang ORDER BY id")
barang_list = cur.fetchall()

if barang_list:
    barang_dict = {f"{id} - {nama}": id for id, nama in barang_list}
    selected = st.selectbox("Pilih barang yang ingin diedit", list(barang_dict.keys()))

    if selected:
        id_barang = barang_dict[selected]
        cur.execute("SELECT nama, stok FROM barang WHERE id = %s", (id_barang,))
        current_nama, current_stok = cur.fetchone()

        with st.form("form_edit"):
            new_nama = st.text_input("Nama Barang", value=current_nama)
            new_stok = st.number_input("Stok", value=current_stok, min_value=0, step=1)
            update = st.form_submit_button("💾 Simpan Perubahan")

            if update:
                cur.execute("UPDATE barang SET nama = %s, stok = %s WHERE id = %s",
                            (new_nama, new_stok, id_barang))
                conn.commit()
                st.success("✅ Data barang berhasil diperbarui!")
                st.experimental_rerun()
else:
    st.info("Belum ada data barang untuk diedit.")

# --- TUTUP DB ---
cur.close()
conn.close()
