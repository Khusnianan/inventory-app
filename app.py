import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# --- Koneksi ke DB ---
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

# --- Login System with DB ---
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
            st.success(f"✅ Berhasil login sebagai {st.session_state.role.upper()}")
            st.rerun()
        else:
            st.error("❌ Username atau password salah.")
    st.stop()
    
# --- Tombol Logout ---
st.sidebar.title("👤 Akun")
st.sidebar.markdown(f"Login sebagai: `{st.session_state.role}`")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.rerun()

st.title("📦 Inventory Barang")

# --- Registrasi User Baru (admin only) ---
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
                st.success(f"✅ Akun `{new_user}` berhasil dibuat sebagai `{new_role}`!")
                st.rerun()
            except psycopg2.errors.UniqueViolation:
                st.error("❌ Username sudah digunakan.")
                conn.rollback()

# --- Tambah Barang (admin only) ---
if st.session_state.role == "admin":
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
            st.rerun()

# --- Tampilkan Barang ---
st.subheader("📋 Daftar Barang")

cur.execute("SELECT * FROM barang ORDER BY id DESC")
rows = cur.fetchall()
df = pd.DataFrame(rows, columns=['id', 'nama', 'stok', 'tanggal'])

for index, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([1.5, 3, 2, 3, 2])
    col1.write(row["id"])
    col2.write(row["nama"])
    col3.write(row["stok"])
    col4.write(row["tanggal"])

    # Hapus barang (admin only)
    if st.session_state.role == "admin":
        if col5.button("🗑️ Hapus", key=f"hapus_{row['id']}"):
            cur.execute("DELETE FROM barang WHERE id = %s", (row["id"],))
            conn.commit()
            st.success(f"Barang ID {row['id']} dihapus.")
            st.rerun()

# --- Edit Barang (admin only) ---
if st.session_state.role == "admin":
    st.subheader("✏️ Edit Barang")
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
                    st.rerun()
    else:
        st.info("Belum ada data barang untuk diedit.")

# --- Tutup koneksi ---
cur.close()
conn.close()
