import streamlit as st
import re
from fpdf import FPDF

# Page configuration
st.set_page_config(page_title="OMR Answer Key Formatter", layout="wide")

st.title("📝 Realistic OMR Answer Key & Exporter")
st.write("Paste your raw answer key text below to view it as a stylized OMR sheet and download it as a PDF.")

# Initialize session state to hold the parsed answers
if "answers" not in st.session_state:
    st.session_state.answers = []

# Inject Custom HTML/CSS for the Streamlit UI styling
streamlit_css = """
<style>
.omr-row { display: flex; align-items: center; margin-bottom: 6px; font-family: 'Courier New', Courier, monospace; }
.q-num { width: 35px; text-align: right; margin-right: 12px; color: #555; font-size: 14px; font-weight: bold; }
.bubble { border-radius: 50%; border: 2px solid #a0a0a0; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; margin: 0 4px; font-size: 12px; font-weight: bold; color: #a0a0a0; }
.bubble.filled { background-color: #2b3a42; color: white; border-color: #2b3a42; }
.omr-col { border: 1px solid #e0e0e0; padding: 15px 10px; border-radius: 8px; background-color: #fcfcfc; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
</style>
"""
st.markdown(streamlit_css, unsafe_allow_html=True)

# Input area
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
            st.session_state.answers = answers[:180]
        else:
            st.error(f"Expected at least 180 valid answers (1-4), but only found {len(answers)}. Please check the pasted text structure.")
    else:
        st.warning("Please paste the raw text before formatting.")

# If we have successfully parsed answers, render UI and Download button
if st.session_state.answers:
    final_answers = st.session_state.answers

    # --- 1. GENERATE PURE PYTHON PDF USING FPDF2 ---
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
                
                # Number inside bubble
                pdf.set_xy(cx - 2, cy - 2)
                pdf.set_font("Helvetica", 'B', 6)
                pdf.cell(4, 4, str(opt), align="C")

    # Generate PDF bytes and convert to standard bytes for Streamlit
    pdf_bytes = bytes(pdf.output())
    
    # Render Streamlit Download Button
    st.success("✅ Successfully rendered!")
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        st.download_button(
            label="📄 Download PDF",
            data=pdf_bytes,
            file_name="OMR_Answer_Key_Formatted.pdf",
            mime="application/pdf"
        )
    st.write("---")
    
    # --- 2. RENDER THE STREAMLIT VISUAL UI ---
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
