import streamlit as st
import re
from fpdf import FPDF
import pandas as pd

# --- Page configuration ---
st.set_page_config(page_title="Online OMR & Grader", layout="wide")

# --- Custom CSS ---
streamlit_css = """
<style>
/* Original Answer Key Styling */
.omr-row { display: flex; align-items: center; margin-bottom: 6px; font-family: 'Courier New', Courier, monospace; }
.q-num { width: 35px; text-align: right; margin-right: 12px; color: #555; font-size: 14px; font-weight: bold; }
.bubble { border-radius: 50%; border: 2px solid #a0a0a0; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; margin: 0 4px; font-size: 12px; font-weight: bold; color: #a0a0a0; }
.bubble.filled { background-color: #2b3a42; color: white; border-color: #2b3a42; }

/* Evaluation Styling */
.bubble.correct { background-color: #4CAF50; color: white; border-color: #4CAF50; }
.bubble.incorrect { background-color: #F44336; color: white; border-color: #F44336; }
.bubble.missed { background-color: #FFC107; color: white; border-color: #FFC107; }

.omr-col { border: 1px solid #e0e0e0; padding: 15px 10px; border-radius: 8px; background-color: #fcfcfc; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px;}
</style>
"""
st.markdown(streamlit_css, unsafe_allow_html=True)

# --- Initialize session state ---
if "answer_key" not in st.session_state:
    st.session_state.answer_key = []

# --- Main Title ---
st.title("📝 Interactive OMR Filler & Grader")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["1️⃣ Fill OMR Sheet", "2️⃣ Upload Answer Key", "3️⃣ View Results"])

# ==========================================
# TAB 1: ONLINE OMR FILLING (STUDENT)
# ==========================================
with tab1:
    st.header("Online OMR Sheet")
    st.write("Mark your answers below. Leave blank for unattempted questions.")
    
    # Render 180 questions in 5 columns
    cols = st.columns(5)
    for col_idx, col in enumerate(cols):
        start_q = col_idx * 36
        end_q = start_q + 36
        
        with col:
            st.markdown('<div class="omr-col">', unsafe_allow_html=True)
            for q in range(start_q + 1, end_q + 1):
                # We use Streamlit's radio buttons to simulate OMR bubbles
                st.radio(
                    f"**Q{q:03d}**", 
                    options=[1, 2, 3, 4], 
                    index=None, # None leaves it blank by default
                    horizontal=True, 
                    key=f"student_ans_{q}"
                )
            st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TAB 2: ANSWER KEY PARSER (ORIGINAL CODE)
# ==========================================
with tab2:
    st.header("Upload & Format Answer Key")
    st.write("Paste your raw answer key text below. Format expectation: `Q.1 A. 3` or similar strings containing `A. [1-4]`")

    raw_text = st.text_area("Paste Answer Key Data:", height=150)

    if st.button("Format Answer Key", type="primary"):
        if raw_text:
            answers = []
            for line in raw_text.split('\n'):
                if 'A.' in line:
                    ans_part = line.split('A.')[1]
                    digits = re.findall(r'\d+', ans_part)
                    answers.extend([int(d) for d in digits if int(d) in [1, 2, 3, 4]])
            
            if len(answers) >= 180:
                st.session_state.answer_key = answers[:180]
                st.success("✅ Answer key successfully parsed and saved in memory!")
            else:
                st.error(f"Expected at least 180 valid answers (1-4), but only found {len(answers)}. Please check the pasted text structure.")
        else:
            st.warning("Please paste the raw text before formatting.")

    # Render Visuals & PDF if Answer Key is present
    if len(st.session_state.answer_key) == 180:
        final_answers = st.session_state.answer_key

        # --- GENERATE PDF ---
        class OMR_PDF(FPDF):
            def header(self):
                self.set_font("Helvetica", 'B', 18)
                self.set_text_color(43, 58, 66)
                self.cell(0, 10, "OMR Answer Key Reference", align="C", new_x="LMARGIN", new_y="NEXT")
                self.set_font("Helvetica", '', 10)
                self.set_text_color(100, 100, 100)
                self.cell(0, 6, "180 Questions - Formatted into vertical columns", align="C", new_x="LMARGIN", new_y="NEXT")
                self.line(10, 30, 200, 30)
                self.ln(10)

        pdf = OMR_PDF()
        pdf.add_page()
        
        col_width = 38
        start_x = 12
        start_y = 35
        
        for col_idx in range(5):
            x_offset = start_x + (col_idx * col_width)
            start_q = col_idx * 36
            end_q = start_q + 36
            col_answers = final_answers[start_q:end_q]
            
            for row_idx, ans in enumerate(col_answers):
                y_offset = start_y + (row_idx * 6.5)
                q_num = start_q + row_idx + 1
                
                # Question Number
                pdf.set_xy(x_offset, y_offset)
                pdf.set_font("Helvetica", 'B', 9)
                pdf.set_text_color(80, 80, 80)
                pdf.cell(8, 5, f"{q_num:03d}", align="R")
                
                # Bubbles
                for opt in [1, 2, 3, 4]:
                    cx = x_offset + 10 + (opt * 5.5)
                    cy = y_offset + 2.5
                    radius = 2.2
                    
                    if opt == ans:
                        pdf.set_fill_color(43, 58, 66)
                        pdf.set_draw_color(43, 58, 66)
                        pdf.ellipse(cx - radius, cy - radius, radius*2, radius*2, style="DF")
                        pdf.set_text_color(255, 255, 255)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                        pdf.set_draw_color(150, 150, 150)
                        pdf.ellipse(cx - radius, cy - radius, radius*2, radius*2, style="D")
                        pdf.set_text_color(150, 150, 150)
                    
                    pdf.set_xy(cx - 2, cy - 2)
                    pdf.set_font("Helvetica", 'B', 6)
                    pdf.cell(4, 4, str(opt), align="C")

        pdf_bytes = bytes(pdf.output())
        
        st.download_button(
            label="📄 Download Answer Key PDF",
            data=pdf_bytes,
            file_name="OMR_Answer_Key_Formatted.pdf",
            mime="application/pdf"
        )
        st.write("---")
        
        # --- RENDER VISUAL UI ---
        st.write("### Answer Key Preview")
        cols = st.columns(5)
        for col_idx, col in enumerate(cols):
            start_idx = col_idx * 36
            end_idx = start_idx + 36
            col_answers = final_answers[start_idx:end_idx]
            
            html_content = '<div class="omr-col">'
            for row_idx, ans in enumerate(col_answers):
                q_number = start_idx + row_idx + 1
                row_html = f'<div class="omr-row"><div class="q-num">{q_number:03d}</div>'
                for opt in [1, 2, 3, 4]:
                    if opt == ans:
                        row_html += f'<div class="bubble filled">{opt}</div>'
                    else:
                        row_html += f'<div class="bubble">{opt}</div>'
                row_html += '</div>'
                html_content += row_html
            html_content += '</div>'
            col.markdown(html_content, unsafe_allow_html=True)


# ==========================================
# TAB 3: GRADE & RESULTS
# ==========================================
with tab3:
    st.header("Evaluation Results")
    
    if len(st.session_state.answer_key) != 180:
        st.warning("⚠️ Please upload and format a valid 180-question answer key in **Tab 2** to calculate results.")
    else:
        # Settings for grading scheme
        st.write("### Marking Scheme")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            points_correct = st.number_input("Points per Correct Answer", value=4, step=1)
        with col_m2:
            points_incorrect = st.number_input("Negative Points per Incorrect Answer", value=-1, step=1)
            
        if st.button("Calculate My Score", type="primary"):
            correct = 0
            incorrect = 0
            unattempted = 0
            
            evaluation_data = []

            for i in range(1, 181):
                student_ans = st.session_state.get(f"student_ans_{i}")
                correct_ans = st.session_state.answer_key[i-1]
                
                status = ""
                if student_ans is None:
                    unattempted += 1
                    status = "Unattempted"
                elif student_ans == correct_ans:
                    correct += 1
                    status = "Correct"
                else:
                    incorrect += 1
                    status = "Incorrect"
                    
                evaluation_data.append({
                    "Q Num": i,
                    "Your Answer": student_ans if student_ans else "-",
                    "Correct Answer": correct_ans,
                    "Status": status
                })

            total_score = (correct * points_correct) + (incorrect * points_incorrect)
            max_score = 180 * points_correct

            # --- Score Metrics ---
            st.divider()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Score", f"{total_score} / {max_score}")
            m2.metric("✅ Correct", correct)
            m3.metric("❌ Incorrect", incorrect)
            m4.metric("⚪ Unattempted", unattempted)
            
            st.divider()

            # --- Visual Result Breakdown ---
            st.write("### Detailed Visual Breakdown")
            st.markdown("""
            * **Green Bubble**: Correct answer.
            * **Red Bubble**: Your incorrect selection.
            * **Yellow Bubble**: Correct answer you missed (when wrong or unattempted).
            """)
            
            # Reusing the HTML rendering for visual feedback
            res_cols = st.columns(5)
            for col_idx, col in enumerate(res_cols):
                start_idx = col_idx * 36
                end_idx = start_idx + 36
                
                html_content = '<div class="omr-col">'
                for q_idx in range(start_idx, end_idx):
                    data = evaluation_data[q_idx]
                    q_number = data["Q Num"]
                    s_ans = data["Your Answer"]
                    c_ans = data["Correct Answer"]
                    
                    row_html = f'<div class="omr-row"><div class="q-num">{q_number:03d}</div>'
                    
                    for opt in [1, 2, 3, 4]:
                        if opt == c_ans and s_ans == c_ans:
                            # User got it right
                            row_html += f'<div class="bubble correct">{opt}</div>'
                        elif opt == s_ans and s_ans != c_ans:
                            # User chose this, but it's wrong
                            row_html += f'<div class="bubble incorrect">{opt}</div>'
                        elif opt == c_ans and s_ans != c_ans:
                            # This was the correct answer, but user didn't choose it
                            row_html += f'<div class="bubble missed">{opt}</div>'
                        else:
                            # Normal unselected bubble
                            row_html += f'<div class="bubble">{opt}</div>'
                            
                    row_html += '</div>'
                    html_content += row_html
                html_content += '</div>'
                col.markdown(html_content, unsafe_allow_html=True)
