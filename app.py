"""
LunaSync — Kadın sağlığı takip uygulaması (Streamlit) / Koyu Tema
"""

from __future__ import annotations

import json
from datetime import date
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import qrcode
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# —— Tema renkleri (Koyu) ——
DARK_BG = "#2F2F2F"
WHITE = "#FFFFFF"
DUST_PINK = "#F8C8DC"
BUTTON_TEXT = "#2F2F2F"

DEFAULT_MEDS = [
    "Parol",
    "Arveles",
    "Majezik",
    "Apranax",
    "Dikloron",
    "Buscopan",
    "Diğer / elle ekle",
]

def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {DARK_BG};
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #313137 0%, #23232A 100%);
            border-right: 1px solid #444;
        }}
        div[data-testid="stDecoration"] {{
            background: linear-gradient(90deg, {DUST_PINK}A0, #313137);
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {WHITE} !important;
            font-weight: 700;
            letter-spacing: -0.01em;
        }}
        p, span, label, .css-16idsys, .css-nahz7x, .luna-title-custom, .luna-badge {{
            color: {WHITE} !important;
        }}
        .luna-card {{
            background: #3A3840;
            border: 1px solid {DUST_PINK};
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 24px rgba(0,0,0,0.24);
        }}
        .luna-badge {{
            display: inline-block;
            background: {DUST_PINK}33;
            color: {WHITE};
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            font-size: 0.85rem;
            border: 1px solid {DUST_PINK};
            margin-bottom: 0.5rem;
        }}
        .luna-title-custom {{
            color: {DUST_PINK};
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            margin-bottom: 0.35rem;
            font-weight: 700;
        }}
        .stButton > button {{
            background: {DUST_PINK};
            color: {BUTTON_TEXT};
            border: none;
            border-radius: 12px;
            font-weight: 700;
            padding: 0.65rem 1.24rem;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }}
        .stButton > button:hover {{
            border: 1px solid {WHITE};
            box-shadow: 0 4px 16px {DUST_PINK}80;
            background: linear-gradient(90deg, {DUST_PINK} 60%, #FFD5EC 100%);
        }}
        .stTextInput > div > div > input, .stMultiSelect, .stNumberInput, .stSlider, .stTextArea {{
            color: {WHITE} !important;
            background: #23232A !important;
        }}
        .stDownloadButton button {{
            background: {DUST_PINK};
            color: {BUTTON_TEXT};
            border-radius: 12px;
            font-weight: 700;
        }}
        .stDownloadButton button:hover {{
            border: 1px solid {WHITE};
            background: #FFD5EC;
        }}
        /* Table style override */
        .stDataFrame, .stDataFrame div, .stDataFrame table, .stDataFrame th, .stDataFrame td {{
          color: {WHITE} !important;
          background: #2F2F2F !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def cycle_day_from_last_period(last: date, cycle_len: int, today: date) -> int | None:
    if cycle_len < 1:
        return None
    delta = (today - last).days
    if delta < 0:
        return None
    return (delta % cycle_len) + 1

def phase_for_day(day: int, cycle_len: int) -> str:
    if day <= 5:
        return "Menstrual (Regl)"
    ovulation_approx = max(6, cycle_len - 14)
    if abs(day - ovulation_approx) <= 1:
        return "Ovülasyon çevresi"
    if day < ovulation_approx:
        return "Foliküler faz"
    return "Luteal faz"

def build_payload(
    last_period: str,
    cycle_length: int,
    cycle_day: int | None,
    phase: str,
    pain: int,
    medications: list[str],
) -> dict:
    return {
        "last_period": last_period,
        "cycle_length_days": cycle_length,
        "cycle_day": cycle_day,
        "phase": phase,
        "pain_scale_1_10": pain,
        "medications": medications,
    }

def fig_doctor_summary(payload: dict) -> go.Figure:
    pain = payload.get("pain_scale_1_10", 0)
    cday = payload.get("cycle_day")
    clen = payload.get("cycle_length_days", 28)
    meds = payload.get("medications") or []

    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.58, 0.42],
        subplot_titles=("Sayısal özet", "İlaçlar"),
        vertical_spacing=0.14,
    )

    fig.add_trace(
        go.Bar(
            x=["Ağrı (1–10)", "Döngü günü", "Döngü süresi"],
            y=[pain, cday if cday is not None else 0, clen],
            marker_color=[DUST_PINK, DUST_PINK, "#8B8B8B"],
            text=[f"{pain}", f"{cday if cday is not None else '-'}", f"{clen}"],
            textposition="outside",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    if meds:
        fig.add_trace(
            go.Bar(
                x=meds,
                y=[1] * len(meds),
                marker_color=DUST_PINK,
                text=["✓"] * len(meds),
                textposition="inside",
                showlegend=False,
                hovertemplate="%{x}<extra></extra>",
            ),
            row=2,
            col=1,
        )
    else:
        fig.add_trace(
            go.Bar(
                x=["Yok"],
                y=[0.5],
                marker_color="#444",
                text=["İlaç seçilmedi"],
                textposition="inside",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        title=dict(
            text="LunaSync — Hızlı özet",
            font=dict(color=WHITE, size=17)
        ),
        paper_bgcolor=DARK_BG,
        plot_bgcolor="#252526",
        font=dict(color=WHITE, family="Segoe UI, sans-serif"),
        height=520,
        margin=dict(t=68, b=42, l=38, r=28),
        showlegend=False,
    )
    fig.update_yaxes(title_text="Değer", gridcolor="#646464", color=WHITE, row=1, col=1)
    fig.update_xaxes(gridcolor="#535353", color=WHITE, row=1, col=1)
    fig.update_yaxes(
        title_text="Seçildi",
        range=[0, 1.35],
        showticklabels=False,
        gridcolor="#4A4151",
        color=WHITE,
        row=2,
        col=1,
    )
    fig.update_xaxes(gridcolor="#414141", color=WHITE, row=2, col=1)
    return fig

def render_doctor_decode():
    st.subheader("Doktor görünümü")
    st.caption(
        "QR koddan elde edilen düz metni girin. Alt kısımdan özet ve grafik göreceksiniz."
    )

    raw = st.text_area(
        "QR içeriği (düz metin, ör: LunaSync Özet - Gün: 12, Ağrı Seviyesi: 7, Kullanılan İlaçlar: Parol,Apranax)",
        height=120,
        placeholder="LunaSync Özet - Gün: 12, Ağrı Seviyesi: 7, Kullanılan İlaçlar: Parol,Apranax"
    )

    gun = ""
    agr = ""
    ilaclar = []
    if raw.strip().startswith("LunaSync Özet"):
        try:
            parts = raw.split(" - ")[1].split(", ")
            gun = parts[0].replace("Gün: ", "").strip()
            agr = parts[1].replace("Ağrı Seviyesi: ", "").strip()
            ilaclar_raw = parts[2].replace("Kullanılan İlaçlar: ", "").strip()
            ilaclar = [x.strip() for x in ilaclar_raw.split(",") if x.strip()]
        except Exception:
            pass

    if st.button("Kısa özet göster", key="doc_parse"):
        rows = [
            {"Alan": "Döngü Günü", "Değer": gun or "-"},
            {"Alan": "Ağrı (1–10)", "Değer": agr or "-"},
            {"Alan": "İlaçlar", "Değer": ", ".join(ilaclar) if ilaclar else "-"},
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=False, width="stretch", hide_index=True)
        payload = {
            "pain_scale_1_10": int(agr) if (agr and agr.isdigit()) else 0,
            "cycle_day": int(gun) if (gun and gun.isdigit()) else None,
            "cycle_length_days": None,
            "last_period": None,
            "phase": "",
            "medications": ilaclar,
        }
        st.plotly_chart(fig_doctor_summary(payload), use_container_width=False, width="stretch")

def main() -> None:
    st.set_page_config(
        page_title="LunaSync",
        page_icon="🌙",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    if "show_qr" not in st.session_state:
        st.session_state["show_qr"] = False
    if "show_card" not in st.session_state:
        st.session_state["show_card"] = False
    inject_css()

    st.markdown('<h2>LunaSync</h2>', unsafe_allow_html=True)
    st.caption('<span style="color:#fff;">Koyu temada kadın sağlığı — döngü, ağrı ve ilaç özeti.</span>',
               unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<span class="luna-title-custom">Menü</span>', unsafe_allow_html=True)
        page = st.radio(
            "Sayfa",
            ["Ana panel", "Doktor görünümü (QR okuma / düz metin)"],
            label_visibility="collapsed",
        )

    if page == "Doktor görünümü (QR okuma / düz metin)":
        render_doctor_decode()
        return

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown('<span class="luna-title-custom">Döngü Bilgisi</span>', unsafe_allow_html=True)
        last = st.date_input("Son regl başlangıcı", value=date.today(), key="lastp")
        cycle_len = st.number_input(
            "Döngü süresi (gün)",
            min_value=15,
            max_value=45,
            value=28,
            step=1,
        )

    today = date.today()
    cday = cycle_day_from_last_period(last, int(cycle_len), today)
    phase = phase_for_day(cday, int(cycle_len)) if cday is not None else "-"

    with col_right:
        st.markdown('<span class="luna-title-custom">Durum</span>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="luna-card">
              <span class="luna-badge">Bugünün döngü günü</span>
              <h2 style="margin:0.5rem 0 0 0; color:{WHITE}; font-size:2rem;">
                {cday if cday is not None else "-"}
              </h2>
              <p style="color:{WHITE}; opacity:0.85; margin-top:0.75rem;">
                <strong>Faz:</strong> {phase}
              </p>
              <p style="color:{WHITE}; opacity:0.6; font-size:0.85rem; margin-top:0.5rem;">
                Bilgilendirme amaçlıdır; tıbbi tanı yerine geçmez.
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown('<span class="luna-title-custom">İlaçlar</span>', unsafe_allow_html=True)
    meds_sel = st.multiselect(
        "Hafızadaki ilaçlardan seçin (birden fazla işaretleyebilirsiniz)",
        DEFAULT_MEDS,
        default=[],
    )
    custom_med = st.text_input("Ek ilaç adı (isteğe bağlı)", placeholder="Örn: İbuprofen")
    medications = list(meds_sel)
    if custom_med.strip():
        medications.append(custom_med.strip())

    st.markdown('<span class="luna-title-custom">Ağrı Skalası</span>', unsafe_allow_html=True)
    pain = st.slider(
        "Şu anki ağrı düzeyi (1 = çok hafif, 10 = dayanılmaz)",
        min_value=1,
        max_value=10,
        value=3,
        help="Doktorunuzla paylaşmak için kaydedilir.",
    )

    payload = build_payload(
        last_period=last.isoformat(),
        cycle_length=int(cycle_len),
        cycle_day=cday,
        phase=phase,
        pain=int(pain),
        medications=medications,
    )

    gün_txt = str(cday) if cday is not None else "-"
    ağrı_txt = str(pain)
    ilaclar_txt = ", ".join(medications) if medications else "-"
    qr_data = f"LunaSync Özet - Gün: {gün_txt}, Ağrı Seviyesi: {ağrı_txt}, Kullanılan İlaçlar: {ilaclar_txt}"

    st.divider()
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        if st.button("Verileri QR koda dönüştür"):
            st.session_state["show_qr"] = True
        if st.button("Görsel kart oluştur"):
            st.session_state["show_card"] = True
    with c2:
        st.download_button(
            label="Özet grafiği indir (HTML)",
            data=_build_standalone_html(payload),
            file_name="lunasync_ozet.html",
            mime="text/html",
            help="Doktor bilgisayarında tarayıcıda açılabilir.",
        )

    if st.session_state.get("show_qr"):
        qr = qrcode.QRCode(
            version=None,
            box_size=8,
            border=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("1")
        buf = BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        st.image(
            Image.open(BytesIO(png_bytes)),
            caption=f"QR kodunu okutun. İçeriği sadece kısa özet metnidir. Tarayıcıya göndermez.",
            width=292,
        )
        st.markdown(
            f'<span style="color:{WHITE};font-size:0.97rem;">'
            f'İçerik:<br>'
            f'<code style="color:#fff;background:#333;padding:3px 5px;border-radius:7px;">{qr_data}</code>'
            '</span>', unsafe_allow_html=True
        )
        st.download_button(
            "QR görselini indir (PNG)",
            data=png_bytes,
            file_name="lunasync_qr.png",
            mime="image/png",
        )

        preview_fig = fig_doctor_summary(payload)
        st.plotly_chart(preview_fig, use_container_width=False, width="stretch")

    if st.session_state.get("show_card"):
        card_img = create_summary_card(
            gun=gün_txt, ağrı=ağrı_txt, ilaçlar=medications
        )
        buf = BytesIO()
        card_img.save(buf, format="PNG")
        card_bytes = buf.getvalue()
        st.image(
            Image.open(BytesIO(card_bytes)),
            caption="Görsel klinik özet kartı. Galerinize kaydedebilirsiniz.",
            use_column_width=True,
        )
        st.download_button(
            "Klinik özet kartını indir (PNG)",
            data=card_bytes,
            file_name=f"lunasync_kart_gun{gün_txt}.png",
            mime="image/png",
        )

def _build_standalone_html(payload: dict) -> bytes:
    fig = fig_doctor_summary(payload)
    fig_json = fig.to_json()
    table_html = pd.DataFrame(
        [
            ["Döngü günü", payload.get("cycle_day", "-")],
            ["Ağrı 1–10", payload.get("pain_scale_1_10", "-")],
            ["İlaçlar", ", ".join(payload.get("medications") or []) or "-"],
            ["Faz", payload.get("phase", "-")],
        ],
        columns=["Alan", "Değer"],
    ).to_html(index=False, classes="tbl", border=0)
    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>LunaSync Özet</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
body {{ font-family: Segoe UI, system-ui, sans-serif; background:#23232A; color:{WHITE}; margin:2rem; }}
h1 {{ color:{DUST_PINK}; font-weight:700; font-size:1.15rem; }}
.tbl {{ border-collapse: collapse; width:100%; max-width:480px; margin:1rem 0; }}
.tbl th, .tbl td {{ border:1px solid #444; padding:8px 12px; text-align:left; color:{WHITE}; background:#2F2F2F; }}
.tbl th {{ background:#3A3840; color:{DUST_PINK}; }}
</style>
</head>
<body>
<h1>LunaSync — Klinik özet</h1>
{table_html}
<div id="g"></div>
<script>
var fig = {fig_json};
Plotly.newPlot('g', fig.data, fig.layout, {{responsive:true}});
</script>
</body>
</html>"""
    return html.encode("utf-8")

def create_summary_card(gun: str, ağrı: str, ilaçlar: list[str]) -> Image.Image:
    """Görsel klinik özet kartı hazırla: Gün, ağrı seviyesi, termometre ikonu, ilaçlar liste olarak."""
    # Görsel boyut ve renkler
    W, H = 550, 330
    BG = (47, 47, 47)
    HEAD = DUST_PINK
    FONTCOLOR = WHITE
    try:
        font_bold = ImageFont.truetype("arialbd.ttf", 36)
        font_bold_big = ImageFont.truetype("arialbd.ttf", 54)
        font = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 20)
        font_semi = ImageFont.truetype("arial.ttf", 23)
    except:
        font_bold = ImageFont.load_default()
        font_bold_big = ImageFont.load_default()
        font = ImageFont.load_default()
        font_semi = ImageFont.load_default()
        font_small = ImageFont.load_default()

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Başlık
    d.text((W//2, 33), "LunaSync Özet", anchor="mm", fill=HEAD, font=font_bold)
    # Döngü Günü
    d.text((56, 82), "Döngü Günü:", anchor="lm", fill=FONTCOLOR, font=font)
    d.text((210, 82), f"{gun}", anchor="mm", fill=FONTCOLOR, font=font_bold_big)
    # Ağrı seviyesi ve termometre simgesi
    d.text((56, 142), "Ağrı Seviyesi:", anchor="lm", fill=FONTCOLOR, font=font)
    # Termometre (emoji) + değer
    thermometer = "\U0001F321"
    thermometer_color = (248,200,220)
    # Termometre değer yanına, emoji yoksa görsel çizmeyebilir; metinle göster.
    d.text((56, 170), f"{thermometer} {ağrı}/10", anchor="lm", fill=thermometer_color, font=font_semi)

    # İlaçlar başlık
    d.text((56, 215), "Kullanılan İlaçlar:", anchor="lm", fill=FONTCOLOR, font=font)
    ilac_str = ilaçlar if ilaçlar else ["-"]
    y_start = 250
    for idx, ilac in enumerate(ilac_str):
        d.text((72, y_start + idx*29), f"- {ilac}", anchor="lm", fill=FONTCOLOR, font=font_small)

    # Alt bilgi
    d.text((W-24, H-16), "LunaSync • kadin sağlığı kliniği özet kartı", fill=HEAD, font=font_small, anchor="rd")

    return img

if __name__ == "__main__":
    main()