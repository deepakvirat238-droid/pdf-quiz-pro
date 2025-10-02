import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import re
import time
import io

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF with OCR support for scanned PDFs"""
    text = ""
    
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # Try to extract text directly first
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                else:
                    # If no text found, use OCR for scanned PDFs
                    try:
                        image = page.to_image()
                        img_bytes = io.BytesIO()
                        image.save(img_bytes, format='PNG')
                        img_bytes.seek(0)
                        ocr_text = pytesseract.image_to_string(Image.open(img_bytes))
                        text += ocr_text + "\n"
                    except:
                        st.warning("Some pages might not have readable text")
                        continue
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
    
    return text

def parse_pdf_content(pdf_file):
    questions = []
    text = extract_text_from_pdf(pdf_file)
    
    question_blocks = re.split(r'Q\d+\.', text)
    
    for i, block in enumerate(question_blocks[1:], 1):
        try:
            question_match = re.search(r'^(.*?)(?=A\)|Answer:)', block, re.DOTALL)
            if not question_match: continue
            
            question_text = question_match.group(1).strip()
            
            options = {}
            option_matches = re.findall(r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|Answer:|$)', block)
            for opt_letter, opt_text in option_matches:
                options[opt_letter] = opt_text.strip()
            
            answer_match = re.search(r'Answer:\s*([A-E])', block)
            if not answer_match: continue
            
            correct_answer = answer_match.group(1)
            
            questions.append({
                "id": i,
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer
            })
        except: continue
    
    return questions

def main():
    st.set_page_config(
        page_title="PDF Quiz PRO", 
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Professional CSS - Exam Interface Style
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    .time-left-box {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3);
    }
    .time-left-text {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .time-left-timer {
        font-size: 2.5rem;
        font-weight: 700;
        font-family: 'Courier New', monospace;
    }
    .nav-buttons-container {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 0.8rem;
        margin-bottom: 2rem;
    }
    .nav-button {
        padding: 1rem;
        border-radius: 8px;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid #3498db;
        background: white;
        color: #3498db;
    }
    .nav-button:hover {
        background: #3498db;
        color: white;
        transform: translateY(-2px);
    }
    .section-header {
        background: #2c3e50;
        color: white;
        padding: 1rem;
        border-radius: 8px 8px 0 0;
        margin-bottom: 0;
        font-weight: 600;
    }
    .section-content {
        background: #ecf0f1;
        padding: 1.5rem;
        border-radius: 0 0 8px 8px;
        margin-bottom: 2rem;
    }
    .subject-header {
        background: #34495e;
        color: white;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .question-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #3498db;
    }
    .question-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #ecf0f1;
    }
    .question-number {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
    }
    .question-timer {
        background: #e74c3c;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .question-text {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .options-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .option-item {
        background: #f8f9fa;
        padding: 1.2rem;
        border-radius: 8px;
        border: 2px solid #e9ecef;
        transition: all 0.3s ease;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .option-item:hover {
        border-color: #3498db;
        background: #e3f2fd;
    }
    .option-item.selected {
        border-color: #3498db;
        background: #3498db;
        color: white;
    }
    .option-radio {
        width: 20px;
        height: 20px;
        border: 2px solid #bdc3c7;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .option-item.selected .option-radio {
        background: white;
        border-color: white;
    }
    .option-item.selected .option-radio::after {
        content: "●";
        color: #3498db;
        font-size: 14px;
    }
    .option-text {
        flex: 1;
        font-weight: 500;
    }
    .answered-stats {
        background: #27ae60;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .quick-nav-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .quick-nav-btn {
        padding: 0.8rem;
        border-radius: 6px;
        text-align: center;
        cursor: pointer;
        background: #ecf0f1;
        border: 2px solid #bdc3c7;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .quick-nav-btn.answered {
        background: #27ae60;
        color: white;
        border-color: #27ae60;
    }
    .quick-nav-btn.current {
        background: #3498db;
        color: white;
        border-color: #3498db;
        transform: scale(1.1);
    }
    .quick-nav-btn:hover {
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">📝 Online Examination Portal</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = "mock_test"
    if 'marked_review' not in st.session_state:
        st.session_state.marked_review = set()
    
    # File upload
    uploaded_file = st.file_uploader("📁 Upload Question Paper PDF", type="pdf")
    
    if uploaded_file:
        with st.spinner("🔍 Processing Question Paper..."):
            questions = parse_pdf_content(uploaded_file)
        
        if not questions:
            st.error("❌ No questions found. Please check the PDF format.")
            return
        
        # Initialize session state
        if 'user_answers' not in st.session_state:
            st.session_state.user_answers = {}
        if 'current_q' not in st.session_state:
            st.session_state.current_q = 0
        if 'quiz_started' not in st.session_state:
            st.session_state.quiz_started = True
        if 'start_time' not in st.session_state:
            st.session_state.start_time = time.time()
        if 'quiz_completed' not in st.session_state:
            st.session_state.quiz_completed = False
        
        # Exam settings
        total_exam_time = 60 * 60  # 1 hour exam
        remaining_time = max(0, total_exam_time - (time.time() - st.session_state.start_time))
        
        # Time Left Display
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        
        st.markdown(f"""
        <div class="time-left-box">
            <div class="time-left-text">Time Left</div>
            <div class="time-left-timer">{minutes:02d} : {seconds:02d}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Buttons
        st.markdown('<div class="nav-buttons-container">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⏮️ Previous Question", use_container_width=True):
                if st.session_state.current_q > 0:
                    st.session_state.current_q -= 1
                    st.rerun()
        
        with col2:
            if st.button("📌 Mark & Review", use_container_width=True):
                st.session_state.marked_review.add(st.session_state.current_q)
                st.success("Question marked for review!")
                st.rerun()
        
        with col3:
            if st.button("💾 Save & Next", use_container_width=True, type="primary"):
                if st.session_state.current_q < len(questions) - 1:
                    st.session_state.current_q += 1
                    st.rerun()
                else:
                    st.session_state.quiz_completed = True
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Exam Sections
        st.markdown("""
        <div class="section-header">
            PART-A
        </div>
        <div class="section-content">
            <div class="subject-header">
                English Language
            </div>
        """, unsafe_allow_html=True)
        
        # Answered statistics
        answered_count = len(st.session_state.user_answers)
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <div><strong>Total answered: {answered_count}</strong></div>
            <div class="answered-stats">{answered_count}/{len(questions)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Navigation Grid
        st.markdown("<div style='font-weight: 600; margin-bottom: 0.5rem;'>Quick Navigation:</div>", unsafe_allow_html=True)
        st.markdown('<div class="quick-nav-grid">', unsafe_allow_html=True)
        
        quick_nav_cols = st.columns(5)
        for idx in range(min(10, len(questions))):  # Show first 10 questions
            with quick_nav_cols[idx % 5]:
                is_answered = questions[idx]['id'] in st.session_state.user_answers
                is_current = idx == st.session_state.current_q
                is_marked = idx in st.session_state.marked_review
                
                btn_class = "quick-nav-btn"
                if is_current:
                    btn_class += " current"
                elif is_answered:
                    btn_class += " answered"
                
                btn_text = f"Q{idx+1}"
                if is_marked:
                    btn_text = f"📌{idx+1}"
                
                if st.button(btn_text, key=f"quick_{idx}", use_container_width=True):
                    st.session_state.current_q = idx
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # Close section-content
        
        # Current Question Display
        if not st.session_state.quiz_completed:
            current_q = questions[st.session_state.current_q]
            current_answer = st.session_state.user_answers.get(current_q['id'])
            
            # Question time calculation (mock - last 6 minutes)
            question_time_remaining = 360  # 6 minutes in seconds
            
            st.markdown(f"""
            <div class="question-container">
                <div class="question-header">
                    <div class="question-number">Question. {st.session_state.current_q + 1}</div>
                    <div class="question-timer">Last 6 Minutes</div>
                </div>
                <div class="question-text">
                    {current_q['question']}
                </div>
            """, unsafe_allow_html=True)
            
            # Options
            st.markdown('<div class="options-container">', unsafe_allow_html=True)
            
            for opt_letter, opt_text in current_q['options'].items():
                is_selected = current_answer == opt_letter
                option_class = "option-item"
                if is_selected:
                    option_class += " selected"
                
                st.markdown(f"""
                <div class="{option_class}" onclick="selectOption('{opt_letter}')">
                    <div class="option-radio"></div>
                    <div class="option-text">{opt_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Hidden radio button for functionality
                if st.button(f"Select {opt_letter}", key=f"opt_{current_q['id']}_{opt_letter}", 
                           use_container_width=True, type="primary" if is_selected else "secondary"):
                    st.session_state.user_answers[current_q['id']] = opt_letter
                    st.rerun()
            
            st.markdown('</div></div>', unsafe_allow_html=True)
            
            # Auto-submit when time ends
            if remaining_time <= 0:
                st.session_state.quiz_completed = True
                st.rerun()
        
        else:
            # Results screen
            st.balloons()
            st.markdown('<div class="main-header">🏆 Examination Completed!</div>', unsafe_allow_html=True)
            
            # Calculate score
            correct_count = 0
            for q in questions:
                if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                    correct_count += 1
            
            total_time = time.time() - st.session_state.start_time
            score_percent = (correct_count / len(questions)) * 100
            
            st.markdown(f"""
            <div class="section-content" style="text-align: center;">
                <h2>Final Score: {correct_count}/{len(questions)}</h2>
                <h1 style="color: #2c3e50; font-size: 3rem;">{score_percent:.1f}%</h1>
                <p>Time Taken: {int(total_time // 60):02d}:{int(total_time % 60):02d}</p>
                <p style="font-size: 1.2rem; color: {'#27ae60' if score_percent >= 60 else '#e74c3c'};">
                    {'🎯 Excellent Performance!' if score_percent >= 90 else 
                     '🌟 Good Job!' if score_percent >= 70 else 
                     '👍 Passed!' if score_percent >= 60 else '💪 Needs Improvement!'}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Restart button
            if st.button("🔄 Start New Exam", use_container_width=True, type="primary"):
                for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 'start_time', 'marked_review']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    else:
        st.info("👆 Please upload a PDF question paper to start the examination")
        
        with st.expander("📋 Expected Question Paper Format", expanded=True):
            st.code("""
Q1. Select the most appropriate ANTONYM of the given word.
MEDDLE (v)
A) Ignore
B) Prize  
C) Fortify
D) Support
Answer: A

Q2. Choose the correct synonym...
A) Option 1
B) Option 2
C) Option 3
D) Option 4
Answer: B
            """)

if __name__ == "__main__":
    main()
    
