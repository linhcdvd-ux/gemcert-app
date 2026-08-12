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

# 4. Kiểm tra Giới hạn (Quota) trên thanh Sidebar
st.sidebar.write(f"👤 Tài khoản: **{st.session_state['username']}**")
st.sidebar.write(f"🔰 Quyền: **{st.session_state['role']}**")
st.sidebar.write(
    f"📊 Đã dùng: {st.session_state['used_quota']} /"
    f" {st.session_state['max_quota']} chứng thư"
)

if st.sidebar.button("Đăng xuất"):
    st.session_state["logged_in"] = False
    st.rerun()

# GIỚI HẠN QUYỀN TRÊN MENU
if st.session_state["role"] == "ADMIN":
    menu = st.sidebar.radio(
        "Menu Quản trị",
        ["Tạo Chứng Thư Mới", "Quản Lý Lịch Sử", "Cấu Hình Doanh Nghiệp"],
    )
else:
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

# ---------------------------------------------------------
# 5. HIỂN THỊ GIAO DIỆN CHÍNH THEO MENU DỰA VÀO LỰA CHỌN
# ---------------------------------------------------------
if menu == "Tạo Chứng Thư Mới":
    st.title("📜 Tạo Chứng Thư Mới")
    st.write("Nhập thông tin mẫu đá / sản phẩm để xuất chứng thư:")

    with st.form("form_tao_chung_thu"):
        col1, col2 = st.columns(2)
        with col1:
            ten_san_pham = st.text_input("Tên đá / Loại đá", placeholder="Ví dụ: Ruby tự nhiên")
            ma_so = st.text_input("Mã số chứng thư", placeholder="Ví dụ: GC-2026-001")
            trong_luong = st.text_input("Trọng lượng", placeholder="Ví dụ: 2.5 Carat")
        with col2:
            mau_sac = st.text_input("Màu sắc", placeholder="Ví dụ: Đỏ huyết bồ câu")
            kich_thuoc = st.text_input("Kích thước", placeholder="Ví dụ: 8.0 x 6.5 mm")
            hinh_dang = st.text_input("Hình dạng & Kiểu cắt", placeholder="Ví dụ: Oval Faceted")
            
        st.markdown("---")
        uploaded_file = st.file_handling = st.file_uploader("Tải ảnh mẫu đá / chứng thư", type=["png", "jpg", "jpeg"])

        btn_submit = st.form_submit_button("🚀 Xuất Chứng Thư")

        if btn_submit:
            if ten_san_pham and ma_so:
                # 1. Cập nhật số lượng đã dùng trong Database
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute(
                    "UPDATE users SET used_quota = used_quota + 1 WHERE username = ?",
                    (st.session_state["username"],)
                )
                conn.commit()
                conn.close()

                # 2. Cập nhật lại session state & làm mới trang
                st.session_state["used_quota"] += 1
                st.success(f"✅ Đã tạo thành công chứng thư mã: **{ma_so}**!")
                st.balloons()
                st.rerun()
                
            else:
                st.warning("⚠️ Vui lòng nhập tối thiểu Tên đá và Mã số chứng thư!")

elif menu == "Quản Lý Lịch Sử":
    st.title("📋 Quản Lý Lịch Sử Chứng Thư")
    st.info("Chức năng xem lại toàn bộ chứng thư đã tạo (Dành cho Admin).")

elif menu == "Cấu Hình Doanh Nghiệp":
    st.title("⚙️ Cấu Hình Doanh Nghiệp")
    st.info("Chức năng chỉnh sửa thông tin thương hiệu, logo, mẫu in (Dành cho Admin).")