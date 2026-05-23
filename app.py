import streamlit as st
import re
from fpdf import FPDF

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="OMR Grader", layout="wide", page_icon="📝")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap');

/* ── global resets ── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

/* ── hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.8rem !important; padding-bottom: 3rem !important; }

/* ── app header ── */
.omr-header {
    display: flex; align-items: center; gap: 14px;
    padding: 0 0 20px; border-bottom: 1px solid #dde0ea; margin-bottom: 28px;
}
.omr-header-icon {
    width: 44px; height: 44px; background: #1a1f2e; border-radius: 10px;
    display: flex; align-items: center; justify-content: center; font-size: 22px;
}
.omr-header-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 22px; color: #1a1f2e; letter-spacing: -0.3px; line-height: 1.2;
}
.omr-header-sub { font-size: 13px; color: #8a92a8; margin-top: 2px; }
.omr-header-badge {
    margin-left: auto; font-size: 11px; font-weight: 500;
    font-family: 'DM Mono', monospace; color: #4361ee;
    background: #eef0fd; border: 1px solid #c7ccf7;
    border-radius: 6px; padding: 4px 10px; letter-spacing: 0.5px; text-transform: uppercase;
}

/* ── section heading ── */
.section-title {
    font-family: 'Playfair Display', serif !important;
    font-size: 18px !important; color: #1a1f2e; margin-bottom: 4px !important;
}
.section-desc { font-size: 13px; color: #8a92a8; margin-bottom: 18px; line-height: 1.5; }

/* ── OMR column card ── */
.omr-col-card {
    background: #ffffff; border: 1px solid #dde0ea;
    border-radius: 12px; padding: 12px 10px; margin-bottom: 0;
}
.omr-col-label {
    font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
    letter-spacing: 1px; color: #8a92a8; text-transform: uppercase;
    margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #f4f5f8;
}

/* ── OMR row & bubbles ── */
.omr-row { display: flex; align-items: center; gap: 4px; margin-bottom: 3px; }
.q-num {
    font-family: 'DM Mono', monospace; font-size: 10px; color: #8a92a8;
    width: 26px; text-align: right; flex-shrink: 0;
}
.bubble {
    width: 26px; height: 26px; border-radius: 50%;
    border: 1.5px solid #dde0ea;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
    color: #8a92a8;
}
.bubble.filled  { background: #1a1f2e; color: #fff; border-color: #1a1f2e; }
.bubble.correct { background: #2dc653; color: #fff; border-color: #2dc653; }
.bubble.wrong   { background: #ef233c; color: #fff; border-color: #ef233c; }
.bubble.missed  { background: #f8961e; color: #fff; border-color: #f8961e; }

/* ── metric cards ── */
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.metric-card {
    background: #ffffff; border: 1px solid #dde0ea;
    border-radius: 12px; padding: 16px 18px;
}
.metric-card.dark { background: #1a1f2e; }
.metric-lbl {
    font-family: 'DM Mono', monospace; font-size: 10px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 0.7px;
    color: #8a92a8; margin-bottom: 6px;
}
.metric-card.dark .metric-lbl { color: #7a8ab0; }
.metric-val {
    font-family: 'Playfair Display', serif; font-size: 28px; color: #1a1f2e; line-height: 1;
}
.metric-card.dark .metric-val { color: #ffffff; }
.metric-val.green { color: #2dc653; }
.metric-val.red   { color: #ef233c; }
.metric-val.muted { color: #8a92a8; }

/* ── progress bar ── */
.prog-wrap {
    background: #eceef3; border-radius: 6px; height: 7px;
    margin-bottom: 24px; overflow: hidden;
}
.prog-fill {
    height: 100%; border-radius: 6px;
    background: linear-gradient(90deg, #4361ee, #7b2fe8);
    transition: width 0.5s ease;
}

/* ── legend ── */
.legend { display: flex; gap: 18px; margin-bottom: 16px; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 7px; font-size: 12px; color: #8a92a8; }
.legend-dot { width: 13px; height: 13px; border-radius: 50%; flex-shrink: 0; }

/* ── alert boxes ── */
.alert { border-radius: 8px; padding: 11px 16px; font-size: 13px; margin-top: 12px; line-height: 1.5; }
.alert.success { background:#ecfdf5; border:1px solid #a7f3d0; color:#065f46; }
.alert.error   { background:#fef2f2; border:1px solid #fca5a5; color:#7f1d1d; }
.alert.warn    { background:#fffbeb; border:1px solid #fcd34d; color:#78350f; }

/* ── streamlit radio tweaks (OMR bubbles) ── */
div[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"] > div {
    display: flex !important; flex-direction: row !important; gap: 6px !important;
}
div[data-testid="stRadio"] div[role="radio"] {
    border: 1.5px solid #dde0ea !important; border-radius: 50% !important;
    width: 30px !important; height: 30px !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
    font-family: 'DM Mono', monospace !important; font-size: 11px !important;
    cursor: pointer !important; transition: all 0.12s !important;
}
div[data-testid="stRadio"] div[role="radio"][aria-checked="true"] {
    background: #1a1f2e !important; color: #fff !important; border-color: #1a1f2e !important;
}
div[data-testid="stRadio"] div[role="radio"]:hover {
    border-color: #4361ee !important;
}

/* ── number inputs ── */
div[data-testid="stNumberInput"] input {
    font-family: 'DM Mono', monospace; text-align: center;
    border-radius: 8px; border: 1px solid #dde0ea;
}

/* ── primary button ── */
div[data-testid="stButton"] > button {
    background: #1a1f2e; color: #fff; border: none;
    border-radius: 8px; padding: 10px 22px;
    font-family: 'DM Sans', sans-serif; font-weight: 500;
    transition: all 0.15s;
}
div[data-testid="stButton"] > button:hover { background: #3a4155; transform: translateY(-1px); }

/* ── download button ── */
div[data-testid="stDownloadButton"] > button {
    background: #ffffff; color: #1a1f2e;
    border: 1px solid #dde0ea; border-radius: 8px;
    font-family: 'DM Sans', sans-serif; font-weight: 500;
    transition: all 0.15s;
}
div[data-testid="stDownloadButton"] > button:hover { background: #f4f5f8; }

/* ── tab bar ── */
button[data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "answer_key" not in st.session_state:
    st.session_state.answer_key = []

# ── App header ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="omr-header">
  <div class="omr-header-icon">📝</div>
  <div>
    <div class="omr-header-title">OMR Grader</div>
    <div class="omr-header-sub">Mark, key, evaluate — all in one place</div>
  </div>
  <div class="omr-header-badge">180 Questions</div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["① Fill answer sheet", "② Upload answer key", "③ View results"])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — STUDENT OMR SHEET
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-title">Your answer sheet</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-desc">Click a bubble to select your answer for each question.</div>', unsafe_allow_html=True)

    cols = st.columns(5)
    for col_idx, col in enumerate(cols):
        start_q = col_idx * 36
        end_q   = start_q + 36
        label   = f"Q{str(start_q+1).zfill(3)}–Q{str(end_q).zfill(3)}"

        col.markdown(f'<div class="omr-col-card"><div class="omr-col-label">{label}</div></div>', unsafe_allow_html=True)
        for q in range(start_q + 1, end_q + 1):
            col.radio(
                f"Q{q:03d}",
                options=[1, 2, 3, 4],
                index=None,
                horizontal=True,
                key=f"student_ans_{q}",
                label_visibility="collapsed",
            )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANSWER KEY
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">Upload answer key</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-desc">Paste raw text — any line containing <code>A. 3</code> (where 3 is 1–4) will be parsed as an answer.</div>',
        unsafe_allow_html=True,
    )

    raw_text = st.text_area("Paste answer key text:", height=160, placeholder="Q.1 A. 3\nQ.2 A. 1\nQ.3 A. 4\n...")

    if st.button("⚡ Parse answer key", type="primary"):
        if raw_text.strip():
            answers = []
            for line in raw_text.split("\n"):
                if "A." in line:
                    part   = line.split("A.")[1]
                    digits = [int(d) for d in re.findall(r"\d+", part) if int(d) in [1, 2, 3, 4]]
                    answers.extend(digits)

            if len(answers) >= 180:
                st.session_state.answer_key = answers[:180]
                st.markdown('<div class="alert success">✅ Answer key loaded — 180 questions parsed successfully.</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="alert error">❌ Found {len(answers)} answers — need at least 180. Check your format.</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div class="alert warn">⚠️ Please paste some text first.</div>', unsafe_allow_html=True)

    # ── Key preview & PDF ────────────────────────────────────────────────────
    if len(st.session_state.answer_key) == 180:
        final_answers = st.session_state.answer_key

        # PDF generation
        class OMR_PDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 18)
                self.set_text_color(26, 31, 46)
                self.cell(0, 10, "OMR Answer Key Reference", align="C", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 10)
                self.set_text_color(100, 100, 100)
                self.cell(0, 6, "180 Questions — formatted into vertical columns", align="C", new_x="LMARGIN", new_y="NEXT")
                self.line(10, 30, 200, 30)
                self.ln(10)

        pdf = OMR_PDF()
        pdf.add_page()
        col_width, start_x, start_y = 38, 12, 35

        for col_idx in range(5):
            x_off  = start_x + col_idx * col_width
            start_q = col_idx * 36
            for row_idx, ans in enumerate(final_answers[start_q: start_q + 36]):
                y_off = start_y + row_idx * 6.5
                q_num = start_q + row_idx + 1
                pdf.set_xy(x_off, y_off)
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(8, 5, f"{q_num:03d}", align="R")
                for opt in [1, 2, 3, 4]:
                    cx = x_off + 10 + opt * 5.5
                    cy = y_off + 2.5
                    r  = 2.2
                    if opt == ans:
                        pdf.set_fill_color(26, 31, 46); pdf.set_draw_color(26, 31, 46)
                        pdf.ellipse(cx - r, cy - r, r * 2, r * 2, style="DF")
                        pdf.set_text_color(255, 255, 255)
                    else:
                        pdf.set_fill_color(255, 255, 255); pdf.set_draw_color(150, 150, 150)
                        pdf.ellipse(cx - r, cy - r, r * 2, r * 2, style="D")
                        pdf.set_text_color(150, 150, 150)
                    pdf.set_xy(cx - 2, cy - 2)
                    pdf.set_font("Helvetica", "B", 6)
                    pdf.cell(4, 4, str(opt), align="C")

        st.download_button(
            "📄 Download answer key PDF",
            data=bytes(pdf.output()),
            file_name="OMR_Answer_Key.pdf",
            mime="application/pdf",
        )

        st.divider()
        st.markdown('<div class="section-title">Key preview</div>', unsafe_allow_html=True)

        preview_cols = st.columns(5)
        for col_idx, col in enumerate(preview_cols):
            start_idx = col_idx * 36
            col_answers = final_answers[start_idx: start_idx + 36]
            label = f"Q{str(start_idx+1).zfill(3)}–Q{str(start_idx+36).zfill(3)}"

            html = f'<div class="omr-col-card"><div class="omr-col-label">{label}</div>'
            for row_idx, ans in enumerate(col_answers):
                q = start_idx + row_idx + 1
                html += f'<div class="omr-row"><div class="q-num">{q:03d}</div>'
                for opt in [1, 2, 3, 4]:
                    cls = "bubble filled" if opt == ans else "bubble"
                    html += f'<div class="{cls}">{opt}</div>'
                html += "</div>"
            html += "</div>"
            col.markdown(html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — RESULTS
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Evaluation results</div>', unsafe_allow_html=True)

    if len(st.session_state.answer_key) != 180:
        st.markdown(
            '<div class="alert warn">⚠️ Please load a valid 180-question answer key in the <strong>Answer Key</strong> tab first.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="section-desc">Adjust the marking scheme then calculate your score.</div>', unsafe_allow_html=True)

        mc1, mc2, _ = st.columns([1, 1, 4])
        with mc1:
            points_correct   = st.number_input("✅ Correct", value=4,  step=1)
        with mc2:
            points_incorrect = st.number_input("❌ Incorrect", value=-1, step=1)

        if st.button("Calculate my score", type="primary"):
            correct = incorrect = unattempted = 0
            eval_data = []

            for i in range(1, 181):
                sa = st.session_state.get(f"student_ans_{i}")
                ca = st.session_state.answer_key[i - 1]
                if sa is None:
                    unattempted += 1; status = "unattempted"
                elif sa == ca:
                    correct += 1;     status = "correct"
                else:
                    incorrect += 1;   status = "wrong"
                eval_data.append({"q": i, "sa": sa, "ca": ca, "status": status})

            total_score = correct * points_correct + incorrect * points_incorrect
            max_score   = 180 * points_correct
            pct         = max(0, round(total_score / max_score * 100)) if max_score else 0

            # ── Metric cards ──────────────────────────────────────────────
            st.markdown(f"""
            <div class="metric-grid">
              <div class="metric-card dark">
                <div class="metric-lbl">Total score</div>
                <div class="metric-val">{total_score}<span style="font-size:15px;opacity:.5"> / {max_score}</span></div>
              </div>
              <div class="metric-card">
                <div class="metric-lbl">Correct</div>
                <div class="metric-val green">{correct}</div>
              </div>
              <div class="metric-card">
                <div class="metric-lbl">Incorrect</div>
                <div class="metric-val red">{incorrect}</div>
              </div>
              <div class="metric-card">
                <div class="metric-lbl">Unattempted</div>
                <div class="metric-val muted">{unattempted}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Progress bar ──────────────────────────────────────────────
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:12px;color:#8a92a8;margin-bottom:6px">'
                f'<span>Score percentage</span><span>{pct}%</span></div>'
                f'<div class="prog-wrap"><div class="prog-fill" style="width:{pct}%"></div></div>',
                unsafe_allow_html=True,
            )

            st.divider()
            st.markdown('<div class="section-title">Detailed breakdown</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="legend">
              <div class="legend-item"><div class="legend-dot" style="background:#2dc653"></div> Correct</div>
              <div class="legend-item"><div class="legend-dot" style="background:#ef233c"></div> Your wrong pick</div>
              <div class="legend-item"><div class="legend-dot" style="background:#f8961e"></div> Missed correct answer</div>
              <div class="legend-item"><div class="legend-dot" style="background:#dde0ea"></div> Unattempted</div>
            </div>
            """, unsafe_allow_html=True)

            res_cols = st.columns(5)
            for col_idx, col in enumerate(res_cols):
                start_idx = col_idx * 36
                label = f"Q{str(start_idx+1).zfill(3)}–Q{str(start_idx+36).zfill(3)}"
                html = f'<div class="omr-col-card"><div class="omr-col-label">{label}</div>'
                for d in eval_data[start_idx: start_idx + 36]:
                    html += f'<div class="omr-row"><div class="q-num">{d["q"]:03d}</div>'
                    for opt in [1, 2, 3, 4]:
                        if d["status"] == "correct" and opt == d["ca"]:
                            cls = "bubble correct"
                        elif d["status"] == "wrong" and opt == d["sa"]:
                            cls = "bubble wrong"
                        elif d["status"] in ("wrong", "unattempted") and opt == d["ca"]:
                            cls = "bubble missed"
                        else:
                            cls = "bubble"
                        html += f'<div class="{cls}">{opt}</div>'
                    html += "</div>"
                html += "</div>"
                col.markdown(html, unsafe_allow_html=True)
