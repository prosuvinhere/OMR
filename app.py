import streamlit as st
import re
from fpdf import FPDF

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="OMR Grader", layout="wide", page_icon="📝")

# ── Session state ─────────────────────────────────────────────────────────────
if "answer_key" not in st.session_state:
    st.session_state.answer_key = []

# ── App header ────────────────────────────────────────────────────────────────
st.title("📝 OMR Grader")
st.markdown("Mark, key, evaluate — all in one place. **(180 Questions)**")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["① Fill answer sheet", "② Upload answer key", "③ View results"])

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — STUDENT OMR SHEET
# ═════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Your answer sheet")
    st.caption("Select your answer for each question.")

    cols = st.columns(5)
    for col_idx, col in enumerate(cols):
        start_q = col_idx * 36
        end_q   = start_q + 36
        
        col.subheader(f"Q{start_q+1:03d} – Q{end_q:03d}")
        for q in range(start_q + 1, end_q + 1):
            col.radio(
                f"Q{q:03d}",
                options=[1, 2, 3, 4],
                index=None,
                horizontal=True,
                key=f"student_ans_{q}"
            )

# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — ANSWER KEY
# ═════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Upload answer key")
    st.caption("Paste raw text. Any line containing `A. 3` (where 3 is 1–4) will be parsed as an answer.")

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
                st.success("✅ Answer key loaded — 180 questions parsed successfully.")
            else:
                st.error(f"❌ Found {len(answers)} answers — need at least 180. Check your format.")
        else:
            st.warning("⚠️ Please paste some text first.")

    # ── Key preview & PDF ────────────────────────────────────────────────────
    if len(st.session_state.answer_key) == 180:
        final_answers = st.session_state.answer_key

        # PDF generation
        class OMR_PDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 18)
                self.cell(0, 10, "OMR Answer Key Reference", align="C", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", "", 10)
                self.cell(0, 6, "180 Questions - formatted into vertical columns", align="C", new_x="LMARGIN", new_y="NEXT")    
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
                pdf.cell(8, 5, f"{q_num:03d}", align="R")
                for opt in [1, 2, 3, 4]:
                    cx = x_off + 10 + opt * 5.5
                    cy = y_off + 2.5
                    r  = 2.2
                    if opt == ans:
                        pdf.set_fill_color(0, 0, 0)
                        pdf.ellipse(cx - r, cy - r, r * 2, r * 2, style="F")
                    else:
                        pdf.set_draw_color(150, 150, 150)
                        pdf.ellipse(cx - r, cy - r, r * 2, r * 2, style="D")

        st.download_button(
            "📄 Download Answer Key PDF",
            data=bytes(pdf.output()),
            file_name="OMR_Answer_Key.pdf",
            mime="application/pdf",
        )

        st.divider()
        st.subheader("Key preview")

        preview_cols = st.columns(5)
        for col_idx, col in enumerate(preview_cols):
            start_idx = col_idx * 36
            col_answers = final_answers[start_idx: start_idx + 36]
            col.write(f"**Q{start_idx+1:03d} – Q{start_idx+36:03d}**")
            
            for row_idx, ans in enumerate(col_answers):
                q = start_idx + row_idx + 1
                col.write(f"`Q{q:03d}`: Option **{ans}**")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — RESULTS
# ═════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Evaluation results")

    if len(st.session_state.answer_key) != 180:
        st.warning("⚠️ Please load a valid 180-question answer key in the **Answer Key** tab first.")
    else:
        st.caption("Adjust the marking scheme then calculate your score.")

        mc1, mc2 = st.columns(2)
        with mc1:
            points_correct = st.number_input("✅ Correct Points", value=4, step=1)
        with mc2:
            points_incorrect = st.number_input("❌ Incorrect Points", value=-1, step=1)

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
            pct         = max(0, min(100, round(total_score / max_score * 100))) if max_score else 0

            # ── Streamlit Native Metrics ──────────────────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Score", f"{total_score} / {max_score}")
            m2.metric("Correct", correct)
            m3.metric("Incorrect", incorrect)
            m4.metric("Unattempted", unattempted)

            st.progress(pct / 100, text=f"Overall Accuracy: {pct}%")

            # ── PDF Generation Block ──────────────────────────────────────────────
            class Result_PDF(FPDF):
                def header(self):
                    self.set_font("Helvetica", "B", 18)
                    self.cell(0, 10, "OMR Evaluation Results", align="C", new_x="LMARGIN", new_y="NEXT")
                    self.set_font("Helvetica", "", 11)
                    self.cell(0, 6, f"Final Score: {total_score} / {max_score}  |  Accuracy: {pct}%", align="C", new_x="LMARGIN", new_y="NEXT")
                    self.line(10, 30, 200, 30)
                    self.ln(10)

            res_pdf = Result_PDF()
            res_pdf.add_page()
            col_width, start_x, start_y = 38, 12, 35

            for col_idx in range(5):
                x_off  = start_x + col_idx * col_width
                start_q = col_idx * 36
                for row_idx, d in enumerate(eval_data[start_q : start_q + 36]):
                    y_off = start_y + row_idx * 6.5
                    q_num = d["q"]
                    
                    res_pdf.set_xy(x_off, y_off)
                    res_pdf.set_font("Helvetica", "B", 9)
                    res_pdf.cell(8, 5, f"{q_num:03d}", align="R")
                    
                    for opt in [1, 2, 3, 4]:
                        cx = x_off + 10 + opt * 5.5
                        cy = y_off + 2.5
                        r  = 2.2
                        
                        if d["status"] == "correct" and opt == d["ca"]:
                            fill_c, draw_c, style = (45, 198, 83), (45, 198, 83), "DF"  # Green
                        elif d["status"] == "wrong" and opt == d["sa"]:
                            fill_c, draw_c, style = (239, 35, 60), (239, 35, 60), "DF"  # Red
                        elif d["status"] in ("wrong", "unattempted") and opt == d["ca"]:
                            fill_c, draw_c, style = (248, 150, 30), (248, 150, 30), "DF"  # Orange
                        else:
                            fill_c, draw_c, style = (255, 255, 255), (150, 150, 150), "D" # Empty
                            
                        res_pdf.set_fill_color(*fill_c)
                        res_pdf.set_draw_color(*draw_c)
                        res_pdf.ellipse(cx - r, cy - r, r * 2, r * 2, style=style)

            st.download_button(
                label="📄 Download Evaluated OMR PDF",
                data=bytes(res_pdf.output()),
                file_name="Evaluated_OMR_Results.pdf",
                mime="application/pdf"
            )

            # ── Streamlit Native Breakdown ──────────────────────────────────────────────
            st.divider()
            st.subheader("Detailed breakdown")
            st.markdown("✅ **Correct** | ❌ **Wrong** | ⚪ **Unattempted**")
            
            res_cols = st.columns(5)
            for col_idx, col in enumerate(res_cols):
                start_idx = col_idx * 36
                col.write(f"**Q{start_idx+1:03d} – Q{start_idx+36:03d}**")
                
                for d in eval_data[start_idx: start_idx + 36]:
                    icon = "✅" if d["status"] == "correct" else "❌" if d["status"] == "wrong" else "⚪"
                    sa_str = d["sa"] if d["sa"] else "-"
                    col.write(f"{icon} `Q{d['q']:03d}`: You: **{sa_str}** | Key: **{d['ca']}**")
