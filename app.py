def test_connection():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT current_date;")
    result = cur.fetchone()
    st.success(f"Koneksi berhasil! Hari ini: {result[0]}")
    cur.close()
    conn.close()

# Di dalam Streamlit layout:
st.title("Test Koneksi DB")
if st.button("Cek Koneksi"):
    test_connection()
