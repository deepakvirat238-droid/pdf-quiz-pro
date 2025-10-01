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
    
    # ✅ SIMPLIFIED PARSING - Debug code hata diya
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
        except: 
            continue
    
    return questions

def main():
    st.set_page_config(
        page_title="PDF Quiz PRO", 
        page_icon="🚀",
        layout="wide"
    )
    
    # Professional CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .question-box {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
    }
    .timer-box {
        background-color: #ff6b6b;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🚀 PDF Quiz PRO</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced PDF Quiz with Timer, OCR & Professional Features</div>', unsafe_allow_html=True)
    
    # Sidebar for professional features
    with st.sidebar:
        st.header("⚙️ Quiz Settings")
        
        # Timer settings
        timer_enabled = st.checkbox("Enable Timer", value=True)
        if timer_enabled:
            minutes = st.number_input("Minutes", min_value=1, max_value=60, value=10)
            total_seconds = minutes * 60
        
        st.header("🔍 Quick Navigation")
    
    with st.expander("📋 Expected Format (4-5 Options)", expanded=False):
        st.code("""
Q1. What is the capital of France?
A) London
B) Berlin  
C) Paris
D) Madrid
E) Rome
Answer: C
        """)
    
    uploaded_file = st.file_uploader("📁 Upload PDF File", type="pdf")
    
    if uploaded_file:
        with st.spinner("🔍 Processing PDF... (OCR enabled for scanned PDFs)"):
            questions = parse_pdf_content(uploaded_file)
        
        if not questions:
            st.error("❌ No questions found. Please check the PDF format.")
            return
        
        st.success(f"✅ Found {len(questions)} questions!")
        
        # ✅ DEBUG: Simple check
        st.info(f"📊 First question preview: {questions[0]['question'][:50]}...")
        
        # Initialize session state
        if 'user_answers' not in st.session_state:
            st.session_state.user_answers = {}
        if 'current_q' not in st.session_state:
            st.session_state.current_q = 0
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = {}
        if 'quiz_started' not in st.session_state:
            st.session_state.quiz_started = True
        if 'start_time' not in st.session_state:
            st.session_state.start_time = time.time()
        if 'quiz_completed' not in st.session_state:
            st.session_state.quiz_completed = False
        
        # Timer logic
        if timer_enabled and not st.session_state.quiz_completed:
            elapsed_time = time.time() - st.session_state.start_time
            remaining_time = max(0, total_seconds - elapsed_time)
            
            if remaining_time <= 0:
                st.session_state.quiz_completed = True
                st.error("⏰ Time's up! Quiz auto-submitted.")
            
            minutes_remaining = int(remaining_time // 60)
            seconds_remaining = int(remaining_time % 60)
            
            st.markdown(f"""
            <div class="timer-box">
                ⏰ Time Remaining: {minutes_remaining:02d}:{seconds_remaining:02d}
            </div>
            """, unsafe_allow_html=True)
        
        # Quick Navigation - Jump to any question
        st.sidebar.subheader("📍 Jump to Question")
        col_count = 5
        cols = st.sidebar.columns(col_count)
        
        for idx in range(len(questions)):
            with cols[idx % col_count]:
                if st.button(f"Q{idx+1}", key=f"nav_{idx}"):
                    st.session_state.current_q = idx
                    st.rerun()
        
        # Main quiz interface
        if not st.session_state.quiz_completed:
            current_q = questions[st.session_state.current_q]
            
            st.markdown(f"""
            <div class="question-box">
                <h3>Q{st.session_state.current_q + 1}. {current_q['question']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Options
            user_answer = st.radio(
                "**Select your answer:**",
                options=list(current_q['options'].keys()),
                format_func=lambda x: f"**{x})** {current_q['options'][x]}",
                key=f"q_{current_q['id']}"
            )
            
            st.session_state.user_answers[current_q['id']] = user_answer
            
            # Check Answer Button at bottom
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✅ Check Answer", use_container_width=True):
                    st.session_state.show_answer[current_q['id']] = True
            
            # Show answer if checked
            if st.session_state.show_answer.get(current_q['id']):
                if user_answer == current_q['correct_answer']:
                    st.success("🎉 Correct! Well done!")
                else:
                    st.error(f"❌ Incorrect! Correct answer is **{current_q['correct_answer']}) {current_q['options'][current_q['correct_answer']]}**")
            
            # Navigation buttons at bottom
            st.markdown("---")
            nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1, 1, 1, 1])
            
            with nav_col1:
                if st.button("◀ Previous", use_container_width=True) and st.session_state.current_q > 0:
                    st.session_state.current_q -= 1
                    st.rerun()
            
            with nav_col2:
                if st.session_state.current_q < len(questions) - 1:
                    if st.button("Next ▶", use_container_width=True):
                        st.session_state.current_q += 1
                        st.rerun()
            
            with nav_col3:
                if st.session_state.current_q == len(questions) - 1:
                    if st.button("Finish 🏁", use_container_width=True, type="primary"):
                        st.session_state.quiz_completed = True
                        st.rerun()
            
            with nav_col4:
                if st.button("🔄 Restart", use_container_width=True):
                    for key in ['user_answers', 'current_q', 'show_answer', 'quiz_completed', 'score', 'quiz_started', 'start_time']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            # Progress bar
            progress = (st.session_state.current_q + 1) / len(questions)
            st.progress(progress)
            st.caption(f"Progress: {st.session_state.current_q + 1}/{len(questions)} questions")
        
        # Show results when completed
        else:
            st.balloons()
            st.markdown('<div class="main-header">🏆 Quiz Completed!</div>', unsafe_allow_html=True)
            
            # Calculate score
            correct_count = 0
            for q in questions:
                if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                    correct_count += 1
            
            score_percent = (correct_count / len(questions)) * 100
            
            # Display score with emoji based on performance
            if score_percent == 100:
                st.success(f"🎯 Perfect Score! {correct_count}/{len(questions)} (100%)")
            elif score_percent >= 80:
                st.success(f"🌟 Excellent! {correct_count}/{len(questions)} ({score_percent:.1f}%)")
            elif score_percent >= 60:
                st.info(f"👍 Good Job! {correct_count}/{len(questions)} ({score_percent:.1f}%)")
            else:
                st.warning(f"💪 Keep Practicing! {correct_count}/{len(questions)} ({score_percent:.1f}%)")
            
            # Detailed results
            with st.expander("📊 Detailed Results", expanded=True):
                for i, q in enumerate(questions):
                    user_ans = st.session_state.user_answers.get(q['id'])
                    correct_ans = q['correct_answer']
                    
                    if user_ans == correct_ans:
                        st.success(f"**Q{i+1}. {q['question']}** - Your answer: {user_ans} ✅")
                    else:
                        st.error(f"**Q{i+1}. {q['question']}** - Your answer: {user_ans} ❌ | Correct: {correct_ans}")
            
            # Restart button
            if st.button("🔄 Start New Quiz", use_container_width=True):
                for key in ['user_answers', 'current_q', 'show_answer', 'quiz_completed', 'score', 'quiz_started', 'start_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()
