import streamlit as st
import qrcode
from PIL import Image
from io import BytesIO
from urllib.parse import quote

# --------- QUERY PARAMS CHECK ----------
query_params = st.query_params

# -- COLORS/STYLES
CARD_BG = "#2F2F2F"
HIGHLIGHT = "#F8C8DC"
WHITE = "#FFFFFF"

def make_card(name, title, email, linkedin, whatsapp, others):
    _name = name.strip() or "Ad Soyad"
    _title = title.strip() or "Unvanınız"
    _email = email.strip()
    _linkedin = linkedin.strip()
    _whatsapp = whatsapp.strip()
    _others = others.strip()
    html = f"""
    <div class="digital-card">
        <div class="title">{_name}</div>
        <div class="subtitle">{_title}</div>
        <div class="info-row"><span class="field-label">E-posta:</span> {f'<a href="mailto:{_email}">{_email}</a>' if _email else "-"}</div>
        <div class="info-row"><span class="field-label">LinkedIn:</span> {f'<a href="{_linkedin}" target="_blank">{_linkedin}</a>' if _linkedin else "-"}</div>
        <div class="info-row"><span class="field-label">WhatsApp:</span> {f'<a href="https://wa.me/{_whatsapp.lstrip("+").replace(" ","").replace("-","")}" target="_blank">{_whatsapp}</a>' if _whatsapp else "-"}</div>
        <div class="info-row"><span class="field-label">Diğer:</span> {f'<a href="{_others}" target="_blank">{_others}</a>' if _others else "-"}</div>
    </div>
    """
    return html

# -- STYLES (always apply, because card is always shown)
st.markdown(f"""
<style>
html, body, [class*="css"] {{
    background-color: #222226 !important;
}}
.block-container {{padding-top:12px; background: #222226;}}
.digital-card {{
    background: {CARD_BG};
    border-radius: 28px;
    padding: 2.5rem 2rem 2rem 2rem;
    max-width: 430px;
    margin: 0 auto;
    border: 2.5px solid {HIGHLIGHT};
    color: #fff;
    box-shadow: 0 6px 26px rgba(47,47,47,0.16);
}}
.digital-card .title {{
    color: {HIGHLIGHT};
    font-size: 2.1em;
    font-weight: 800;
    font-family:'Montserrat','Helvetica Neue',Arial,sans-serif;
    margin-bottom: 0.23em;
    word-break: break-all;
    text-align:left;
}}
.digital-card .subtitle {{
    color: #fff;
    font-size: 1.18em;
    margin-bottom: 1.1em;
    font-weight: 500;
    font-family:'Montserrat','Segoe UI',Arial,sans-serif;
}}
.digital-card .field-label {{
    color: {HIGHLIGHT};
    font-weight: 600;
    display:inline-block;
    min-width:105px;
}}
.digital-card .info-row {{
    margin-bottom: 0.82em;
    font-size: 1em;
    font-family:'Montserrat','Segoe UI',Arial,sans-serif;
    color: #fff;
    word-break: break-all;
}}
.digital-card .info-row a {{
    color: {HIGHLIGHT};
    text-decoration: none;
}}
.digital-card .info-row a:hover {{
    text-decoration: underline;
    color: #fff;
}}
.qr-main {{
    margin-top:2.1em;
    width:100%;
    display:flex;
    flex-direction:column;
    align-items:center;
}}
.stButton>button {{
    background-color: {HIGHLIGHT};
    color: {CARD_BG};
    font-weight: 800;
    border: none;
    border-radius: 13px !important;
    padding: .85em 2.7em !important;
    font-size: 1.2em !important;
    margin: 0.6em 0 0.7em 0 !important;
    transition: 0.11s;
}}
.stButton>button:hover {{
    background-color: #fff;
    color: #c5276a;
}}
/* QR download custom style */
.qr-download-btn > button {{
    background-color: {HIGHLIGHT} !important;
    color: {CARD_BG} !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 13px !important;
    padding: .7em 1.8em !important;
    font-size: 1.03em !important;
    margin-top: 0.7em !important;
    margin-bottom: 2.2em !important;
}}
.qr-download-btn > button:hover {{
    background: #ffffff !important;
    color: #c5276a !important;
    border: 1px solid {HIGHLIGHT} !important;
}}
@media (max-width: 720px) {{
    .digital-card {{padding: 1.1rem 0.5rem !important; max-width:98vw;}}
    .digital-card .title {{font-size:1.25em;}}
    .block-container {{padding-left:4px !important; padding-right:2px !important;}}
}}
</style>
""", unsafe_allow_html=True)

# ---- ADDRESS TO USE FOR QR ----
BASE_APP_URL = "https://lunasync.streamlit.app/"

def get_card_url(base_url, name, title, email, linkedin, whatsapp, others):
    params = (
        f"?name={quote(name or '')}"
        f"&title={quote(title or '')}"
        f"&email={quote(email or '')}"
        f"&linkedin={quote(linkedin or '')}"
        f"&whatsapp={quote(whatsapp or '')}"
        f"&others={quote(others or '')}"
    )
    return base_url.rstrip("/") + "/" + params

if "qr_image" not in st.session_state:
    st.session_state["qr_image"] = None
    st.session_state["qr_url"] = ""

# ------------- SHOW ONLY CARD IF QUERY_PARAMS -------------
if "name" in query_params:
    # Sadece kartvizit görünümü, giriş ve sidebar yok!
    name = query_params.get("name", "")
    title = query_params.get("title", "")
    email = query_params.get("email", "")
    linkedin = query_params.get("linkedin", "")
    whatsapp = query_params.get("whatsapp", "")
    others = query_params.get("others", "")

    # Hide sidebar (Streamlit v1.23+: use option):
    st.set_page_config(layout="centered", initial_sidebar_state="collapsed")
    st.markdown(
        "<br><br>", unsafe_allow_html=True
    )
    st.markdown(make_card(name, title, email, linkedin, whatsapp, others), unsafe_allow_html=True)
    st.stop()

# ------------ NORMAL FORM/APP FLOW (show sidebar + card + QR) -----------
# -------- SIDEBAR INPUT ---------
st.sidebar.markdown(f"<h2 style='color:{HIGHLIGHT};'>Dijital Kartvizit Bilgileri</h2>", unsafe_allow_html=True)
full_name = st.sidebar.text_input("Ad Soyad", max_chars=48, placeholder="Adınız ve Soyadınız")
title = st.sidebar.text_input("Unvan", max_chars=48, help="Pozisyon, branş vb.", placeholder="Ör: Biyomedikal Mühendisi")
email = st.sidebar.text_input("E-posta", max_chars=60, placeholder="ornek@eposta.com")
linkedin = st.sidebar.text_input("LinkedIn Linki", max_chars=85, placeholder="https://linkedin.com/in/...")
whatsapp = st.sidebar.text_input("WhatsApp", max_chars=35, placeholder="+90 5xx xxx xx xx")
others = st.sidebar.text_input("Diğer Bağlantılar", max_chars=255, help="Instagram, web sitesi vb.", placeholder="https://...")

# --------- CARD (MAIN AREA) -----------
st.markdown(make_card(full_name, title, email, linkedin, whatsapp, others), unsafe_allow_html=True)
st.markdown("<div style='height:1em;'></div>", unsafe_allow_html=True)

# ------------ QR BUTTON + CREATE LINK --------------
st.markdown('<div style="width:100%;text-align:center;">', unsafe_allow_html=True)
qr_btn = st.button("QR Kod Oluştur", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if qr_btn:
    card_url = get_card_url(BASE_APP_URL, full_name, title, email, linkedin, whatsapp, others)
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(card_url)
    qr.make(fit=True)
    qr_img: Image.Image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)
    st.session_state["qr_image"] = buf
    st.session_state["qr_url"] = card_url

if st.session_state.get("qr_image"):
    st.markdown('<div class="qr-main">', unsafe_allow_html=True)
    st.image(st.session_state.qr_image, width=230, caption="Kartvizit QR Kodu", use_column_width=False)
    st.markdown(
        f'<p style="margin:0.8em 0 0.5em 0; color:{HIGHLIGHT}; font-weight:600;">Bağlantı: <a href="{st.session_state["qr_url"]}" style="color:{HIGHLIGHT};word-break:break-all;">{st.session_state["qr_url"]}</a></p>', 
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="qr-download-btn">', unsafe_allow_html=True)
        st.download_button(
            label="QR Kodu İndir",
            data=st.session_state["qr_image"],
            file_name="LunaSync_QR.png",
            mime="image/png",
            use_container_width=False,
            key="qr_download_button"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)