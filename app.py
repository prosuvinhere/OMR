import streamlit as st
import re

# Page configuration
st.set_page_config(page_title="OMR Answer Key Formatter", layout="wide")

st.title("📝 Realistic OMR Answer Key")
st.write("Paste your raw answer key text below. The script will render it as a realistic, stylized OMR sheet for effortless side-by-side comparison.")

# Inject Custom HTML/CSS for the OMR styling
omr_css = """
<style>
.omr-row { 
    display: flex; 
    align-items: center; 
    margin-bottom: 6px; 
    font-family: 'Courier New', Courier, monospace; 
}
.q-num { 
    width: 35px; 
    text-align: right; 
    margin-right: 12px; 
    color: #555; 
    font-size: 14px;
    font-weight: bold;
}
.bubble { 
    border-radius: 50%; 
    border: 2px solid #a0a0a0; 
    width: 24px; 
    height: 24px; 
    display: inline-flex; 
    align-items: center; 
    justify-content: center; 
    margin: 0 4px; 
    font-size: 12px; 
    font-weight: bold;
    color: #a0a0a0;
    background-color: transparent;
}
.bubble.filled { 
    background-color: #2b3a42; 
    color: white; 
    border-color: #2b3a42; 
}
.omr-col {
    border: 1px solid #e0e0e0;
    padding: 15px 10px;
    border-radius: 8px;
    background-color: #fcfcfc;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
}
</style>
"""
st.markdown(omr_css, unsafe_allow_html=True)

# Input area
raw_text = st.text_area("Paste Answer Key Data:", height=150)

if st.button("Format Answer Key", type="primary"):
    if raw_text:
        answers = []
        
        # Process line by line to differentiate Questions (Q.) and Answers (A.)
        for line in raw_text.split('\n'):
            # Check if the line contains answers
            if 'A.' in line:
                # Isolate the part of the line after 'A.'
                ans_part = line.split('A.')[1]
                # Extract digits just from the answer section
                digits = re.findall(r'\d+', ans_part)
                # Convert to integers, ensuring they are valid options 1-4
                answers.extend([int(d) for d in digits if int(d) in [1, 2, 3, 4]])
        
        if len(answers) >= 180:
            final_answers = answers[:180]
            
            st.success("✅ Successfully rendered! Compare these columns directly to your sheet.")
            st.write("---")
            
            # Create 5 columns in Streamlit
            cols = st.columns(5)
            
            # Populate each column with 36 questions
            for col_idx, col in enumerate(cols):
                start_idx = col_idx * 36
                end_idx = start_idx + 36
                col_answers = final_answers[start_idx:end_idx]
                
                # Build the HTML for this specific column
                html_content = '<div class="omr-col">'
                
                for row_idx, ans in enumerate(col_answers):
                    q_number = start_idx + row_idx + 1
                    
                    # Row container and formatted question number
                    row_html = f'<div class="omr-row"><div class="q-num">{q_number:03d}</div>'
                    
                    # Generate the 4 bubbles
                    for opt in [1, 2, 3, 4]:
                        if opt == ans:
                            row_html += f'<div class="bubble filled">{opt}</div>'
                        else:
                            row_html += f'<div class="bubble">{opt}</div>'
                            
                    row_html += '</div>'
                    html_content += row_html
                    
                html_content += '</div>'
                
                # Render the HTML block in the current Streamlit column
                col.markdown(html_content, unsafe_allow_html=True)
                
        else:
            st.error(f"Expected at least 180 valid answers (1-4), but only found {len(answers)}. Please check the pasted text structure.")
    else:
        st.warning("Please paste the raw text before formatting.")
