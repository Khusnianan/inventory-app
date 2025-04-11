import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# --- Config & Styling ---
st.set_page_config(page_title="Inventory App", page_icon="📦", layout="wide")

# --- Koneksi DB ---
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

# --- Login ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        cur.execute("SELECT role FROM users WHERE username=%s AND password=%s", (username, password))
        result = cur.fetchone()
        if result:
            st.session_state.logged_in = True
            st.session_state.role = result[0]
            st.rerun()
        else:
            st.error("❌ Username/password salah.")
    st.stop()

# --- Sidebar ---
menu = st.sidebar.radio("📂 Menu", ["Dashboard", "Transaksi In", "Transaksi Out", "Manajemen Stok"])
st.sidebar.markdown(f"**👤 Role:** `{st.session_state.role}`")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- Dashboard ---
if menu == "Dashboard":
    st.title("📦 Dashboard Inventory")
    if st.session_state.role == "admin":
        with st.expander("📝 Registrasi User"):
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "user"])
            if st.button("Buat Akun"):
                try:
                    cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                                (new_user, new_pass, new_role))
                    conn.commit()
                    st.success("✅ Akun berhasil dibuat.")
                    st.rerun()
                except:
                    conn.rollback()
                    st.error("❌ Username sudah ada.")

# --- Transaksi In ---
if menu == "Transaksi In":
    st.title("📥 Transaksi Masuk")
    nama_barang = st.text_input("Nama Barang Baru / Lama")
    jumlah = st.number_input("Jumlah Masuk", min_value=1, step=1)
    if st.button("💾 Simpan Transaksi Masuk"):
        # Cek apakah barang sudah ada
        cur.execute("SELECT id FROM barang WHERE LOWER(nama) = LOWER(%s)", (nama_barang,))
        barang = cur.fetchone()

        if barang:
            barang_id = barang[0]
        else:
            cur.execute("INSERT INTO barang (nama, stok, tanggal) VALUES (%s, %s, %s)",
                        (nama_barang, 0, datetime.now()))
            conn.commit()
            cur.execute("SELECT id FROM barang WHERE nama = %s", (nama_barang,))
            barang_id = cur.fetchone()[0]

        cur.execute("INSERT INTO transaksi (tipe, barang_id, jumlah) VALUES ('in', %s, %s)",
                    (barang_id, jumlah))
        cur.execute("UPDATE barang SET stok = stok + %s WHERE id = %s", (jumlah, barang_id))
        conn.commit()
        st.success("✅ Transaksi masuk berhasil disimpan.")
        st.rerun()

# --- Transaksi Out ---
if menu == "Transaksi Out":
    st.title("📤 Transaksi Keluar")
    cur.execute("SELECT id, nama, stok FROM barang ORDER BY nama")
    barang_list = cur.fetchall()
    barang_dict = {f"{nama} (stok: {stok})": (id, stok) for id, nama, stok in barang_list}
    selected = st.selectbox("Pilih Barang", list(barang_dict.keys()))
    jumlah = st.number_input("Jumlah Keluar", min_value=1, step=1)
    if st.button("📤 Simpan Transaksi Keluar"):
        barang_id, stok_tersedia = barang_dict[selected]
        if jumlah > stok_tersedia:
            st.error("❌ Stok tidak cukup.")
        else:
            cur.execute("INSERT INTO transaksi (tipe, barang_id, jumlah) VALUES ('out', %s, %s)",
                        (barang_id, jumlah))
            cur.execute("UPDATE barang SET stok = stok - %s WHERE id = %s", (jumlah, barang_id))
            conn.commit()
            st.success("✅ Transaksi keluar disimpan.")
            st.rerun()

# --- Manajemen Stok ---
if menu == "Manajemen Stok":
    st.title("📦 Manajemen Stok")
    cur.execute("SELECT * FROM barang ORDER BY id")
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["id", "nama", "stok", "tanggal"])

    for _, row in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 3, 1])
        col1.write(row["id"])
        col2.write(row["nama"])
        col3.write(row["stok"])
        col4.write(str(row["tanggal"].date()))

        # Ikon Edit dan Hapus (admin only)
        if st.session_state.role == "admin":
            edit_key = f"edit_{row['id']}"
            delete_key = f"delete_{row['id']}"

            if col5.button("✏️", key=edit_key):
                st.session_state[f"edit_{row['id']}"] = True
            if col5.button("🗑️", key=delete_key):
                cur.execute("DELETE FROM barang WHERE id = %s", (row["id"],))
                conn.commit()
                st.success(f"✅ Barang ID {row['id']} dihapus.")
                st.rerun()

            # Form edit (jika diklik)
            if st.session_state.get(f"edit_{row['id']}", False):
                with st.expander(f"Edit Barang ID {row['id']}"):
                    with st.form(f"form_edit_{row['id']}"):
                        nama_baru = st.text_input("Nama", value=row["nama"])
                        stok_baru = st.number_input("Stok", value=row["stok"], min_value=0)
                        submit = st.form_submit_button("💾 Simpan")
                        if submit:
                            cur.execute("UPDATE barang SET nama=%s, stok=%s WHERE id=%s",
                                        (nama_baru, stok_baru, row["id"]))
                            conn.commit()
                            st.success("✅ Barang berhasil diperbarui.")
                            st.session_state[f"edit_{row['id']}"] = False
                            st.rerun()

# --- Tutup koneksi ---
cur.close()
conn.close()
