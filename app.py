import base64
import io
import os
import barcode
from barcode.writer import ImageWriter
from jinja2 import Template
from playwright.sync_api import sync_playwright
import qrcode
import streamlit as st

st.set_page_config(
    page_title="Phần Mềm Tạo Chứng Thư Giám Định Đá Quý", layout="wide"
)

# ---------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------


def image_bytes_to_b64(image_bytes, mime_type="image/png"):
    encoded = base64.b64encode(image_bytes).decode()
    return f"data:{mime_type};base64,{encoded}"


def generate_qr_b64(data):
    if not data:
        return ""
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return image_bytes_to_b64(buffer.getvalue(), "image/png")


def generate_barcode_b64(gtin_code):
    if not gtin_code:
        return ""
    Code128 = barcode.get_barcode_class("code128")
    buffer = io.BytesIO()
    writer = ImageWriter()
    bc = Code128(gtin_code, writer=writer)
    bc.write(buffer, options={"write_text": False, "module_height": 10.0})
    return image_bytes_to_b64(buffer.getvalue(), "image/png")


# ---------------------------------------------------------
# HTML TEMPLATE
# ---------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,400;0,500;0,700;1,400;1,700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Roboto', Arial, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
            width: 1000px;
            height: 720px;
            padding: 25px 35px;
            background: #FAF7F2; 
            color: #111111;
            position: relative;
        }
        
        .container {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .top-section {
            display: flex;
            justify-content: space-between;
            gap: 20px;
        }

        .left-col { width: 58%; }
        .right-col {
            width: 38%;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .yellow-header {
            background-color: #F1AF00;
            border-radius: 2px;
            padding: 7px 12px;
            text-align: center;
            margin-bottom: 12px;
        }
        .yellow-header .title-vi { font-size: 13px; font-weight: 700; color: #000000; letter-spacing: 0.2px; }
        .yellow-header .title-en { font-size: 10.5px; font-weight: 700; color: #000000; margin-top: 1px; }
        .yellow-header .subtext { font-size: 8.5px; margin-top: 3px; color: #111111; line-height: 1.2; }

        .doc-title-box { text-align: center; margin-bottom: 8px; }
        .doc-title-vi { font-size: 16px; font-weight: 700; color: #000000; text-transform: uppercase; letter-spacing: 0.5px; }
        .doc-title-en { font-size: 12px; font-weight: 700; color: #222222; text-transform: uppercase; }
        .report-info { text-align: center; font-size: 13px; margin-top: 4px; margin-bottom: 10px; color: #000000; }
        .blue-text { color: #10216B; font-weight: 700; }

        .product-title-box { text-align: center; margin-bottom: 12px; }
        .product-title-vi { font-size: 15px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; color: #000000; }
        .product-title-en { font-size: 12px; font-weight: 700; text-transform: uppercase; color: #000000; }

        .section-header {
            background-color: #DC8555;
            font-weight: 700;
            font-size: 12.5px;
            padding: 4px 8px;
            margin-top: 8px;
            border-radius: 2px 2px 0 0;
            color: #000000;
        }

        .data-table-container {
            background-color: #F8E2D2;
            padding: 4px 6px;
            margin-bottom: 6px;
            border-radius: 0 0 2px 2px;
        }

        .data-table { width: 100%; font-size: 12px; border-collapse: collapse; }
        .data-table td { padding: 3px 4px; vertical-align: top; }
        .label-cell { width: 50%; color: #111111; }
        .value-cell { width: 50%; text-align: right; font-weight: 500; color: #000000; }
        .sub-label { font-size: 10.5px; color: #333333; display: block; font-style: italic; }

        .img-frame {
            width: 240px;
            height: 240px;
            background-color: #000000;
            border: 2px solid #000000;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            margin-bottom: 10px;
        }
        .img-frame img { width: 100%; height: 100%; object-fit: cover; }

        .gtin-box { font-size: 13px; font-weight: 700; text-align: center; margin-bottom: 4px; color: #000000; }
        
        .barcode-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 12px;
        }
        .barcode-img { 
            width: 210px; 
            height: 48px; 
            object-fit: fill;
        }
        .barcode-text {
            font-size: 11px;
            font-weight: 500;
            letter-spacing: 1.5px;
            color: #111111;
            margin-top: 2px;
        }

        /* KHỐI KẾT LUẬN & NHẬN XÉT: DỊCH NỘI DUNG SÁT VỀ BÊN TRÁI GẦN NHÃN */
        .conclusion-box { width: 100%; font-size: 12.5px; line-height: 1.35; color: #000000; }
        .conclusion-row { 
            display: flex; 
            justify-content: flex-start; 
            gap: 15px; 
            align-items: flex-start;
            margin-bottom: 6px; 
        }
        .conclusion-label { min-width: 80px; }
        .conclusion-val { text-align: left; }

        /* CHÂN TRANG */
        .footer-section {
            display: flex;
            justify-content: flex-end;
            align-items: flex-end;
            gap: 20px;
            margin-top: -30px; 
            position: relative;
        }

        .qr-box { 
            display: flex; 
            flex-direction: column;
            align-items: center; 
            gap: 4px;
            margin-bottom: -5px;
        }
        .qr-box img { 
            width: 75px; 
            height: 75px; 
        }
        .qr-text {
            font-size: 11px;
            font-weight: 500;
            color: #000000;
            text-align: center;
            white-space: nowrap;
        }

        .signer-box {
            text-align: center;
            position: relative;
            width: 260px;
            min-height: 115px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
        }
        .signer-title-1 { font-size: 12px; font-weight: 700; color: #000000; }
        .signer-title-2 { font-size: 12px; font-weight: 700; color: #000000; margin-bottom: 50px; }
        .signer-name { font-size: 13px; font-weight: 700; text-transform: uppercase; color: #000000; letter-spacing: 0.3px; }

        .stamp-overlay {
            position: absolute;
            width: 155px;
            top: 55%;
            left: 20%;
            transform: translate(-50%, -50%);
            opacity: 0.88;
            pointer-events: none;
            z-index: 2;
        }
    </style>
</head>
<body>
    <div class="container">
        <div>
            <div class="top-section">
                <!-- CỘT TRÁI -->
                <div class="left-col">
                    <div class="yellow-header">
                        <div class="title-vi">VIỆN NGHIÊN CỨU ĐÁ QUÝ VÀ VÀNG VINAGEMS</div>
                        <div class="title-en">INSTITUTE FOR GEMS AND GOLD RESEARCH OF VINAGEMS</div>
                        <div class="subtext">GIẤY CHỨNG NHẬN ĐĂNG KÝ HOẠT ĐỘNG KHOA HỌC VÀ CÔNG NGHỆ SỐ A-14-15<br>DO BỘ TRƯỞNG BỘ KHOA HỌC VÀ CÔNG NGHỆ CẤP NGÀY 11 THÁNG 9 NĂM 2015</div>
                    </div>

                    <div class="doc-title-box">
                        <div class="doc-title-vi">CHỨNG THƯ GIÁM ĐỊNH ĐÁ QUÝ</div>
                        <div class="doc-title-en">GEM IDENTIFICATION REPORT</div>
                        <div class="report-info">
                            Số phiếu (Report No): <span class="blue-text">{{ report_no }}</span><br>
                            Ngày (Date): <span class="blue-text">{{ date }}</span>
                        </div>
                    </div>

                    <div class="product-title-box">
                        <div class="product-title-vi">{{ product_name_vi }}</div>
                        <div class="product-title-en">({{ product_name_en }})</div>
                    </div>

                    <div class="section-header">MÔ TẢ MẪU (Objects):</div>
                    <div class="data-table-container">
                        <table class="data-table">
                            <tr>
                                <td class="label-cell">TÊN MẪU (Items):</td>
                                <td class="value-cell">{{ item_type }}</td>
                            </tr>
                            <tr>
                                <td class="label-cell">TỔNG LƯỢNG (Weight):</td>
                                <td class="value-cell">{{ weight }}</td>
                            </tr>
                            <tr>
                                <td class="label-cell">SỐ LƯỢNG (Quantity):</td>
                                <td class="value-cell">{{ quantity }}</td>
                            </tr>
                        </table>
                    </div>

                    <div class="section-header">KẾT QUẢ GIÁM ĐỊNH (Testing Results):</div>
                    <div class="data-table-container">
                        <table class="data-table">
                            <tr>
                                <td class="label-cell">HÌNH DẠNG & KIỂU CHẾ TÁC:<span class="sub-label">(Shape and Cut)</span></td>
                                <td class="value-cell" style="vertical-align: middle;">{{ shape_and_cut }}</td>
                            </tr>
                            <tr>
                                <td class="label-cell">KÍCH THƯỚC:<span class="sub-label">(Measures)</span></td>
                                <td class="value-cell" style="vertical-align: middle;">{{ measures }}</td>
                            </tr>
                            <tr>
                                <td class="label-cell">MÀU SẮC (Color):</td>
                                <td class="value-cell">{{ color }}</td>
                            </tr>
                            <tr>
                                <td class="label-cell">ĐỘ ĐỀU MÀU (Eveness):</td>
                                <td class="value-cell">{{ eveness }}</td>
                            </tr>
                            <tr>
                                <td class="label-cell">ĐỘ TINH KHIẾT (Transparency):</td>
                                <td class="value-cell">{{ transparency }}</td>
                            </tr>
                            <tr>
                                <td class="label-cell">ĐẶC ĐIỂM BÊN TRONG:<span class="sub-label">(Internal features)</span></td>
                                <td class="value-cell" style="vertical-align: middle;">{{ internal_features }}</td>
                            </tr>
                        </table>
                    </div>
                </div>

                <!-- CỘT PHẢI -->
                <div class="right-col">
                    <div class="img-frame">
                        {% if product_image %}
                        <img src="{{ product_image }}">
                        {% endif %}
                    </div>

                    <div class="gtin-box">
                        Mã vạch (GTIN): <span class="blue-text">{{ gtin }}</span>
                    </div>
                    
                    <div class="barcode-container">
                        {% if barcode_image %}
                        <img src="{{ barcode_image }}" class="barcode-img">
                        {% endif %}
                        <span class="barcode-text">{{ gtin }}</span>
                    </div>

                    <div class="conclusion-box">
                        <div class="conclusion-row">
                            <div class="conclusion-label"><b>Kết luận:</b><br><span style="font-size: 10.5px; font-style: italic;">(Conclusion)</span></div>
                            <div class="conclusion-val" style="font-weight: 700;">{{ conclusion }}</div>
                        </div>
                        <div class="conclusion-row" style="margin-top: 6px;">
                            <div class="conclusion-label"><b>Nhận xét:</b><br><span style="font-size: 10.5px; font-style: italic;">(Comment)</span></div>
                            <div class="conclusion-val">{{ comment }}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- CHÂN TRANG -->
            <div class="footer-section">
                <div class="qr-box">
                    {% if qr_image %}
                    <img src="{{ qr_image }}">
                    {% endif %}
                    <div class="qr-text">Tra cứu chứng thư tại: www.igg.vn</div>
                </div>

                <div class="signer-box">
                    <div>
                        <div class="signer-title-1">KT. VIỆN TRƯỜNG</div>
                        <div class="signer-title-2">TRƯỞNG PHÒNG KIỂM ĐỊNH</div>
                    </div>
                    {% if stamp_image %}
                    <img src="{{ stamp_image }}" class="stamp-overlay">
                    {% endif %}
                    <div class="signer-name">{{ signer_name }}</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# ---------------------------------------------------------
# STREAMLIT APPLICATION
# ---------------------------------------------------------
st.title("💎 Phần Mềm Tạo & Chỉnh Sửa Chứng Thư Giám Định Đá Quý")

col_form, col_preview = st.columns([1, 1])

with col_form:
    st.subheader("📝 Nhập/Chỉnh Sửa Thông Số Chứng Thư")

    with st.expander("📌 Thông tin chung", expanded=True):
        report_no = st.text_input("Số phiếu (Report No)", "826150349")
        date = st.text_input("Ngày (Date)", "06/08/2026")
        product_name_vi = st.text_input(
            "Tên sản phẩm (Tiếng Việt)", "CẨM THẠCH TỰ NHIÊN"
        )
        product_name_en = st.text_input(
            "Tên sản phẩm (Tiếng Anh)", "NATURAL JADEITE"
        )

    with st.expander("📦 MÔ TẢ MẪU (Objects)", expanded=True):
        c1, c2, c3 = st.columns(3)
        item_type = c1.text_input("Tên mẫu", "Lắc tay")
        weight = c2.text_input("Tổng lượng", "15.07 g")
        quantity = c3.text_input("Số lượng", "29 viên")

    with st.expander("🔬 KẾT QUẢ GIÁM ĐỊNH (Testing Results)", expanded=True):
        shape_and_cut = st.text_input(
            "Hình dạng & kiểu chế tác", "Hình cầu, cabochon"
        )
        measures = st.text_input("KÍCH THƯỚC", "6.00 mm - 6.38 mm")
        c_col1, c_col2 = st.columns(2)
        color = c_col1.text_input("MÀU SẮC", "Xanh lục nhạt")
        eveness = c_col2.text_input("ĐỘ ĐỀU MÀU", "Màu phân bố đồng đều")
        transparency = st.text_input("ĐỘ TINH KHIẾT", "Bán trong - Đục")
        internal_features = st.text_input(
            "Đặc điểm bên trong", "Cấu trúc dạng sợi"
        )

    with st.expander("🏷️ Kết luận, Mã vạch & Người ký", expanded=True):
        gtin = st.text_input("Mã vạch (GTIN)", "8936151680537")
        conclusion = st.text_input("KẾT LUẬN", "Cẩm thạch tự nhiên (Loại A)")
        comment = st.text_input("NHẬN XÉT", "Hàng tốt loại A")
        signer_name = st.text_input("Người ký", "PHẠM TRUNG KIÊN")
        qr_link = st.text_input("Link tra cứu QR", "https://www.igg.vn")

    with st.expander("🖼️ Hình ảnh & Con dấu", expanded=True):
        img_file = st.file_uploader(
            "Ảnh sản phẩm (JPG/PNG)", type=["jpg", "png", "jpeg"]
        )
        stamp_file = st.file_uploader(
            "Ảnh con dấu/chữ ký (PNG nền trong suốt - Tùy chọn)", type=["png"]
        )

    generate_btn = st.button("🚀 Tạo / Cập Nhật Chứng Thư", type="primary")

with col_preview:
    st.subheader("🖼️ Xem Trước Chứng Thư & Xuất Ảnh")

    if img_file is not None:
        if generate_btn or "rendered_image_bytes" not in st.session_state:
            with st.spinner("Đang xuất chứng thư chất lượng cao..."):
                product_img_b64 = image_bytes_to_b64(
                    img_file.getvalue(), img_file.type
                )

                stamp_b64 = ""
                if stamp_file is not None:
                    stamp_b64 = image_bytes_to_b64(
                        stamp_file.getvalue(), stamp_file.type
                    )

                qr_b64 = generate_qr_b64(qr_link)
                barcode_b64 = generate_barcode_b64(gtin)

                template = Template(HTML_TEMPLATE)
                rendered_html = template.render(
                    report_no=report_no,
                    date=date,
                    product_name_vi=product_name_vi,
                    product_name_en=product_name_en,
                    item_type=item_type,
                    weight=weight,
                    quantity=quantity,
                    shape_and_cut=shape_and_cut,
                    measures=measures,
                    color=color,
                    eveness=eveness,
                    transparency=transparency,
                    internal_features=internal_features,
                    gtin=gtin,
                    conclusion=conclusion,
                    comment=comment,
                    signer_name=signer_name,
                    product_image=product_img_b64,
                    qr_image=qr_b64,
                    barcode_image=barcode_b64,
                    stamp_image=stamp_b64,
                )

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(
                        viewport={"width": 1000, "height": 720},
                        device_scale_factor=2,
                    )
                    page.set_content(rendered_html)
                    img_bytes = page.screenshot(type="png")
                    browser.close()

                st.session_state["rendered_image_bytes"] = img_bytes

        if "rendered_image_bytes" in st.session_state:
            st.image(
                st.session_state["rendered_image_bytes"],
                caption="Chứng thư được sinh tự động",
                use_container_width=True,
            )

            st.download_button(
                label="📥 Tải Ảnh Chứng Thư Sắc Nét (PNG)",
                data=st.session_state["rendered_image_bytes"],
                file_name=f"ChungThu_{report_no}.png",
                mime="image/png",
            )
    else:
        st.info(
            "👈 Vui lòng tải ảnh sản phẩm lên ở mục 'Hình ảnh & Con dấu' bên trái để hệ thống xuất chứng thư!"
        )