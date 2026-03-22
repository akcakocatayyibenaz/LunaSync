import streamlit as st
import qrcode
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Dijital Kartvizit Oluşturucu", page_icon="💼", layout="wide")

# --- CUSTOM STYLES ---
st.markdown("""
    <style>
    body {background: #222226;}
    .block-container {padding-top: 1.4vw !important;}
    .digital-card {
        background: #2F2F2F;
        border-radius: 26px;
        padding: 3.2rem 2.2rem 2.6rem 2.2rem;
        max-width: 480px;
        margin: 0 auto 2em auto;
        border: 2.8px solid #F8C8DC;
        color: #fff;
        box-shadow: 0 8px 38px rgba(32,32,32,0.18);
    }
    .digital-card .title {
        color: #F8C8DC;
        font-size: 2.2em;
        font-weight: 900;
        letter-spacing: 1px;
        font-family:'Montserrat','Helvetica Neue',Arial,sans-serif;
        margin-bottom: 0.25em;
        text-align: left;
    }
    .digital-card .subtitle {
        color: #fff;
        font-size: 1.2em;
        margin-bottom: 1.5em;
        font-weight: 500;
        font-family:'Montserrat','Segoe UI',Arial,sans-serif;
    }
    .digital-card .field-label {
        color: #F8C8DC;
        font-weight: 600;
        min-width:95px;
        display:inline-block;
    }
    .digital-card .info-row {
        margin-bottom: 0.85em;
        font-size: 1.07em;
        font-family:'Montserrat','Segoe UI',Arial,sans-serif;
        color: #fff;
    }
    .digital-card a {
        color: #F8C8DC;
        text-decoration: none;
        word-break: break-all;
    }
    .digital-card a:hover {
        color: #fff;
        text-decoration: underline;
    }
    .qr-main {
        margin-top:2.2em;
        width:100%;
        display:flex;
        flex-direction:column;
        align-items:center;
    }
    .block-container {
        background: #222226;
    }
    .stDownloadButton>button {
        width:100%;
        font-size:1.08em;
    }
    .stButton>button {
        background-color: #F8C8DC;
        color: #2F2F2F;
        font-weight: 800;
        border: none;
        border-radius: 12px !important;
        padding: .78em 2.6em !important;
        font-size: 1.2em !important;
        margin: 0.55em 0 0.6em 0 !important;
        transition: 0.11s;
    }
    .stButton>button:hover {
        background-color: #fff;
        color: #c5276a;
    }
    @media (max-width: 700px) {
        .digital-card { padding: 1.1rem 0.4rem !important; max-width:99vw; font-size:96%; }
        .digital-card .title { font-size:1.3em;}
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: USER FORM ---
st.sidebar.markdown("<h2 style='color:#F8C8DC;'>Dijital Kartvizit Bilgileri</h2>", unsafe_allow_html=True)
full_name = st.sidebar.text_input("Ad Soyad", max_chars=48)
title = st.sidebar.text_input("Unvan", max_chars=48, help="Görev veya pozisyonunuz.")
email = st.sidebar.text_input("E-posta", max_chars=60)
linkedin = st.sidebar.text_input("LinkedIn Linki", max_chars=85, placeholder="https://linkedin.com/in/kullanici")
whatsapp = st.sidebar.text_input("WhatsApp", max_chars=35, placeholder="+90 5xx xxx xx xx")
other_links = st.sidebar.text_input("Diğer Bağlantılar", max_chars=255, help="Instagram, web sitesi vb. bir URL")

st.markdown("<div style='height:1.2em;'></div>", unsafe_allow_html=True)

# --- MAIN CARD ---
card_html = f"""
<div class="digital-card">
    <div class="title">{full_name if full_name.strip() else "Ad Soyad"}</div>
    <div class="subtitle">{title if title.strip() else "Unvanınız"}</div>
    <div class="info-row"><span class="field-label">E-posta:</span> {email if email.strip() else "-"}</div>
    <div class="info-row"><span class="field-label">LinkedIn:</span>
        {'<a href="'+linkedin+'" target="_blank">'+linkedin+'</a>' if linkedin.strip() else '-'}</div>
    <div class="info-row"><span class="field-label">WhatsApp:</span> {whatsapp if whatsapp.strip() else "-"}</div>
    <div class="info-row"><span class="field-label">Diğer:</span>
        {'<a href="'+other_links+'" target="_blank">'+other_links+'</a>' if other_links.strip() else '-'}</div>
</div>
"""
st.markdown(card_html, unsafe_allow_html=True)

# --- QR KOD OLUŞTURMA ---
qr_ready = full_name.strip() or title.strip() or email.strip() or linkedin.strip() or whatsapp.strip() or other_links.strip()

if "qr_image" not in st.session_state:
    st.session_state["qr_image"] = None

qr_btn = st.button("QR Kod Oluştur", use_container_width=True)

def generate_card_data(
    name, title, email, linkedin, whatsapp, other_links
):
    # Tüm girilen bilgileri okunur ve bloklu şık formatta birleştirir.
    data = f"Dijital Kartvizit\n\n"
    if name.strip():
        data += f"Ad Soyad: {name.strip()}\n"
    if title.strip():
        data += f"Unvan: {title.strip()}\n"
    if email.strip():
        data += f"E-posta: {email.strip()}\n"
    if linkedin.strip():
        data += f"LinkedIn: {linkedin.strip()}\n"
    if whatsapp.strip():
        data += f"WhatsApp: {whatsapp.strip()}\n"
    if other_links.strip():
        data += f"Diğer: {other_links.strip()}\n"
    return data.strip()

if qr_btn and qr_ready:
    qr_content = generate_card_data(full_name, title, email, linkedin, whatsapp, other_links)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    qr_img: Image.Image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)
    st.session_state.qr_image = buf

if st.session_state.qr_image:
    st.markdown('<div class="qr-main">', unsafe_allow_html=True)
    st.image(st.session_state.qr_image, width=210, caption="Kartvizit QR Kodu", use_column_width=False)
    st.download_button(
        "QR Kodu İndir",
        data=st.session_state.qr_image,
        file_name="dijital_kartvizit_qr.png",
        mime="image/png",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)