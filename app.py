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
from PIL import Image
import urllib.parse

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

def build_qr_url(day: int|None, pain: int, medications: list[str]) -> str:
    """
    QR kodu bir sayfaya yönlendirsin ve özet veriler URL parametrelerinde iletilsin.
    Format: https://lunasync-web-ozet.com/ozet?gun=[int]&agr=[int]&ilaclar=[virgülle ayrılmış]
    (Demo için localhost:8502/ozet ya da başka sabit endpoint olabilir!)
    """
    meds = ",".join(medications) if medications else ""
    gun = f"{day}" if (day is not None and day != "") else ""
    agr = f"{pain}" if pain else ""
    # Demo/test için url: http://lunasync-qr.web.app/ozet veya localhost:8502/ozet
    base = "https://lunasync-ozet.web.app/ozet"
    params = {"gun": gun, "agr": agr, "ilaclar": meds}
    url = base + "?" + urllib.parse.urlencode(params)
    return url

def parse_ozet_params(query_str: str) -> dict:
    # Yardımcı: Parametreleri parse et
    parsed = urllib.parse.parse_qs(query_str)
    def get_first(k): return parsed[k][0] if k in parsed and parsed[k] else ""
    ilaclar_value = get_first("ilaclar")
    meds = ilaclar_value.split(",") if ilaclar_value.strip() else []
    return {
        "gun": get_first("gun"),
        "agr": get_first("agr"),
        "ilaclar": meds
    }

def phase_for_day(day: int, cycle_len: int) -> str:
    # Faz sadece ekranda, QR'da yok!
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
    # Koyu tema grafik
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
        "QR koddan elde edilen kısa formatlı web bağlantısı (URL) kopyalayın veya parametreleri girin. "
        "Ya da doğrudan QR ile tarayarak açılan özet sayfasını kullanın."
    )

    url = st.text_input("Web bağlantısı (QR linki)", placeholder="https://lunasync-ozet.web.app/ozet?gun=13&agr=5&ilaclar=Parol,Apranax")
    gun = st.text_input("Döngü günü", value="")
    agr = st.text_input("Ağrı (1–10)", value="")
    ilaclar = st.text_input("İlaçlar (virgülle)", value="")

    parsed = {"gun": "", "agr": "", "ilaclar": []}
    if url and "?gun=" in url:
        # parse from url
        query_str = url.split("?", 1)[1]
        parsed = parse_ozet_params(query_str)
        gun, agr, ilaclar = parsed["gun"], parsed["agr"], ",".join(parsed["ilaclar"])

    if st.button("Kısa özet göster", key="doc_parse"):
        meds = [x.strip() for x in ilaclar.split(",") if x.strip()]
        rows = [
            {"Alan": "Döngü Günü", "Değer": gun or "-"},
            {"Alan": "Ağrı (1–10)", "Değer": agr or "-"},
            {"Alan": "İlaçlar", "Değer": ", ".join(meds) if meds else "-"},
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=False, width="stretch", hide_index=True)
        payload = {
            "pain_scale_1_10": int(agr) if (agr and agr.isdigit()) else 0,
            "cycle_day": int(gun) if (gun and gun.isdigit()) else None,
            "cycle_length_days": None,
            "last_period": None,
            "phase": "",
            "medications": meds,
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
    inject_css()

    st.markdown('<h2>LunaSync</h2>', unsafe_allow_html=True)
    st.caption('<span style="color:#fff;">Koyu temada kadın sağlığı — döngü, ağrı ve ilaç özeti.</span>',
               unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<span class="luna-title-custom">Menü</span>', unsafe_allow_html=True)
        page = st.radio(
            "Sayfa",
            ["Ana panel", "Doktor görünümü (QR okuma / web özet linki)"],
            label_visibility="collapsed",
        )

    if page == "Doktor görünümü (QR okuma / web özet linki)":
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

    # QR URL oluştur
    qr_url = build_qr_url(cday, int(pain), medications)

    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Verileri QR koda dönüştür"):
            st.session_state["show_qr"] = True
    with c2:
        st.download_button(
            label="Özet grafiği indir (HTML)",
            data=_build_standalone_html(payload),
            file_name="lunasync_ozet.html",
            mime="text/html",
            help="Doktor bilgisayarında tarayıcıda açılabilir.",
        )

    if st.session_state.get("show_qr"):
        # QR kodu yüksek kontrast (siyah-beyaz) ve link olarak!
        qr = qrcode.QRCode(
            version=None,
            box_size=8,
            border=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        # High contrast: black and white
        img = qr.make_image(fill_color="black", back_color="white").convert("1")
        buf = BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        st.image(
            Image.open(BytesIO(png_bytes)),
            caption=f"QR kodu taratın: açılan web sayfasında özet göreceksiniz.",
            width=292,
        )
        st.markdown(
            f'<span style="color:{WHITE};font-size:0.95rem;">'
            f'İpucu: Kameradan okuttuğunuzda açılan sayfa özeti gösterecek.<br>'
            f'<small>Bağlantı:</small> <code style="color:#fff;background:#333;padding:3px 5px;border-radius:7px;">{qr_url}</code>'
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

def _build_standalone_html(payload: dict) -> bytes:
    """Mini rapor karanlık tema ile (Plotly CDN)."""
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

if __name__ == "__main__":
    main()