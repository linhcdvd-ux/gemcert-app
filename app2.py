import hashlib
import sqlite3
import streamlit as st

DB_FILE = "gemcert_commercial.db"


# 1. Hàm mã hóa mật khẩu đơn giản
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# 2. Khởi tạo bảng User & Kiểm tra tài khoản
def init_auth_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            role TEXT, -- 'ADMIN' hoặc 'OPERATOR'
            max_quota INT, -- Số chứng thư tối đa được tạo
            used_quota INT DEFAULT 0
        )
    """)
    # Tạo sẵn 1 tài khoản Admin và 1 tài khoản Nhân viên (Giới hạn 10 chứng thư)
    c.execute(
        "INSERT OR IGNORE INTO users VALUES ('admin', ?, 'ADMIN', 999999, 0)",
        (hash_password("admin123"),),
    )
    c.execute(
        "INSERT OR IGNORE INTO users VALUES ('khachhang1', ?,"
        " 'OPERATOR', 10, 0)",
        (hash_password("user123"),),
    )
    conn.commit()
    conn.close()


init_auth_db()


def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT role, max_quota, used_quota FROM users WHERE username=? AND"
        " password=?",
        (username, hash_password(password)),
    )
    user = c.fetchone()
    conn.close()
    return user


# 3. Giao diện Đăng nhập
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Đăng Nhập Hệ Thống GemCert")
    user_input = st.text_input("Tên đăng nhập")
    pass_input = st.text_input("Mật khẩu", type="password")

    if st.button("Đăng nhập"):
        user_info = check_login(user_input, pass_input)
        if user_info:
            st.session_state["logged_in"] = True
            st.session_state["username"] = user_input
            st.session_state["role"] = user_info[0]
            st.session_state["max_quota"] = user_info[1]
            st.session_state["used_quota"] = user_info[2]
            st.rerun()
        else:
            st.error("❌ Tên đăng nhập hoặc mật khẩu không chính xác!")
    st.stop()

# 4. Kiểm tra Giới hạn (Quota) khi người dùng thao tác
st.sidebar.write(f"👤 Tài khoản: **{st.session_state['username']}**")
st.sidebar.write(f"🔰 Quyền: **{st.session_state['role']}**")
st.sidebar.write(
    f"📊 Đã dùng: {st.session_state['used_quota']} /"
    f" {st.session_state['max_quota']} chứng thư"
)

if st.sidebar.button("Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

# ---------------------------------------------------------
# GIỚI HẠN QUYỀN TRÊN MENU
# ---------------------------------------------------------
if st.session_state["role"] == "ADMIN":
    menu = st.sidebar.radio(
        "Menu Quản trị",
        ["Tạo Chứng Thư Mới", "Quản Lý Lịch Sử", "Cấu Hình Doanh Nghiệp"],
    )
else:
    # Người dùng bị giới hạn chỉ được dùng chức năng Tạo chứng thư
    menu = st.sidebar.radio("Menu Chức Năng", ["Tạo Chứng Thư Mới"])

# Kiểm tra nếu hết Quota (Hạn ngạch)
if (
    st.session_state["used_quota"] >= st.session_state["max_quota"]
    and st.session_state["role"] != "ADMIN"
):
    st.error(
        "⚠️ Bạn đã sử dụng hết số lượng chứng thư cho phép! Vui lòng liên hệ"
        " Admin để gia hạn."
    )
    st.stop()