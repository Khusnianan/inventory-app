import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# --- Config & Styling ---
st.set_page_config(page_title="Inventory", page_icon="📦", layout="wide")

st.markdown("""
    <style>
    .stButton>button { background-color: #4CAF50; color: white; }
    .stForm>form { background-color: #ffffff; padding: 20px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

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
    st.title("🔐 Login Inventory System")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login = st.button("Login")

    if login:
        cur.execute("SELECT role FROM users WHERE username = %s AND password = %s", (username, password))
        result = cur.fetchone()
        if result:
            st.session_state.logged_in = True
            st.session_state.role = result[0]
            st.success(f"✅ Login sebagai {st.session_state.role.upper()}")
            st.rerun()
        else:
            st.error("❌ Username atau password salah.")
    st.stop()

# --- Sidebar ---
st.sidebar.title("📂 Menu")
menu = st.sidebar.radio("Navigasi", ["Dashboard", "Transaksi In", "Transaksi Out", "Manajemen Stok"])

st.sidebar.markdown("## 👤 Login Info")
st.sidebar.markdown(f"**Role:** `{st.session_state.role}`")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

# --- Dashboard / Home ---
if menu == "Dashboard":
    st.title("📦 Dashboard Inventory")
    st.caption("Kelola data barang masuk & keluar dengan mudah dan aman.")

    # Registrasi user baru
    if st.session_state.role == "admin":
        with st.expander("📝 Registrasi User Baru"):
            st.subheader("Buat Akun Baru")
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["admin", "user"])
            create_btn = st.button("Buat Akun")

            if create_btn and new_user and new_pass:
                try:
                    cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                                (new_user, new_pass, new_role))
                    conn.commit()
                    st.success(f"✅ Akun `{new_user}` berhasil dibuat.")
                    st.rerun()
                except psycopg2.errors.UniqueViolation:
                    st.error("❌ Username sudah digunakan.")
                    conn.rollback()

# --- Transaksi IN ---
if menu == "Transaksi In":
    st.title("📥 Transaksi Masuk")

    cur.execute("SELECT id, nama FROM barang ORDER BY nama")
    barang_list = cur.fetchall()
    barang_dict = {f"{nama} (ID:{id})": id for id, nama in barang_list}

    selected = st.selectbox("Pilih Barang", list(barang_dict.keys()))
    jumlah = st.number_input("Jumlah Masuk", min_value=1, step=1)
    simpan = st.button("💾 Simpan Transaksi Masuk")

    if simpan:
        barang_id = barang_dict[selected]
        cur.execute("INSERT INTO transaksi (tipe, barang_id, jumlah) VALUES ('in', %s, %s)", (barang_id, jumlah))
        cur.execute("UPDATE barang SET stok = stok + %s WHERE id = %s", (jumlah, barang_id))
        conn.commit()
        st.success("✅ Transaksi masuk disimpan.")
        st.rerun()

# --- Transaksi OUT ---
if menu == "Transaksi Out":
    st.title("📤 Transaksi Keluar")

    cur.execute("SELECT id, nama, stok FROM barang ORDER BY nama")
    barang_list = cur.fetchall()
    barang_dict = {f"{nama} (stok: {stok})": (id, stok) for id, nama, stok in barang_list}

    selected = st.selectbox("Pilih Barang", list(barang_dict.keys()))
    jumlah = st.number_input("Jumlah Keluar", min_value=1, step=1)
    kirim = st.button("📤 Simpan Transaksi Keluar")

    if kirim:
        barang_id, stok_tersedia = barang_dict[selected]
        if jumlah > stok_tersedia:
            st.error("❌ Stok tidak cukup.")
        else:
            cur.execute("INSERT INTO transaksi (tipe, barang_id, jumlah) VALUES ('out', %s, %s)", (barang_id, jumlah))
            cur.execute("UPDATE barang SET stok = stok - %s WHERE id = %s", (jumlah, barang_id))
            conn.commit()
            st.success("✅ Transaksi keluar berhasil disimpan.")
            st.rerun()

# --- Manajemen Stok ---
if menu == "Manajemen Stok":
    st.title("📦 Manajemen Stok Barang")

    cur.execute("SELECT * FROM barang ORDER BY id")
    df = pd.DataFrame(cur.fetchall(), columns=["id", "nama", "stok", "tanggal"])
    st.dataframe(df, use_container_width=True)

    if st.session_state.role == "admin":
        with st.expander("✏️ Edit Barang"):
            pilih = st.selectbox("Pilih Barang", df["id"].astype(str) + " - " + df["nama"])
            barang_id = int(pilih.split(" - ")[0])
            cur.execute("SELECT nama, stok FROM barang WHERE id = %s", (barang_id,))
            nama_lama, stok_lama = cur.fetchone()

            with st.form("form_edit_stok"):
                nama_baru = st.text_input("Nama Barang", value=nama_lama)
                stok_baru = st.number_input("Stok", value=stok_lama, min_value=0, step=1)
                simpan_edit = st.form_submit_button("💾 Simpan Perubahan")

                if simpan_edit:
                    cur.execute("UPDATE barang SET nama = %s, stok = %s WHERE id = %s",
                                (nama_baru, stok_baru, barang_id))
                    conn.commit()
                    st.success("✅ Barang berhasil diperbarui.")
                    st.rerun()
    else:
        st.info("👀 Hanya admin yang bisa mengedit barang.")

# --- Tutup koneksi DB ---
cur.close()
conn.close()
