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
    
    # Professional CSS - Ediquity Style
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.8rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .question-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        color: white;
    }
    .question-text {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    .options-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-top: 1rem;
    }
    .option-card {
        background: rgba(255,255,255,0.95);
        padding: 1.2rem;
        border-radius: 12px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        cursor: pointer;
        color: #333;
    }
    .option-card:hover {
        border-color: #2E86AB;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .option-card.selected {
        border-color: #2E86AB;
        background: #e3f2fd;
    }
    .timer-box {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        color: white;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-weight: bold;
        text-align: center;
        font-size: 1.2rem;
        box-shadow: 0 5px 15px rgba(255,107,107,0.3);
        margin-bottom: 2rem;
    }
    .progress-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .nav-button {
        padding: 0.8rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .nav-button-primary {
        background: linear-gradient(45deg, #2E86AB, #4BB3FD);
        color: white;
    }
    .nav-button-secondary {
        background: #6c757d;
        color: white;
    }
    .result-card {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">📚 PDF Quiz PRO</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Professional Quiz Platform - Ediquity Style</div>', unsafe_allow_html=True)
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Quiz Settings")
        
        # Timer type selection
        timer_type = st.radio(
            "⏰ Timer Type:",
            ["Full Quiz Timer", "Per Question Timer", "No Timer"]
        )
        
        if timer_type == "Full Quiz Timer":
            quiz_minutes = st.slider("Total Quiz Time (minutes):", 1, 60, 15)
            total_seconds = quiz_minutes * 60
        elif timer_type == "Per Question Timer":
            question_seconds = st.slider("Time per Question (seconds):", 10, 300, 60)
        
        st.markdown("---")
        st.header("🔍 Navigation")
    
    # File upload
    uploaded_file = st.file_uploader("📁 Upload PDF File", type="pdf")
    
    if uploaded_file:
        with st.spinner("🔍 Processing PDF... Creating your quiz..."):
            questions = parse_pdf_content(uploaded_file)
        
        if not questions:
            st.error("❌ No questions found. Please check the PDF format.")
            return
        
        st.success(f"✅ Found {len(questions)} questions!")
        
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
        if 'question_start_time' not in st.session_state:
            st.session_state.question_start_time = time.time()
        
        # Timer logic
        if timer_type != "No Timer" and not st.session_state.quiz_completed:
            if timer_type == "Full Quiz Timer":
                elapsed_time = time.time() - st.session_state.start_time
                remaining_time = max(0, total_seconds - elapsed_time)
                
                if remaining_time <= 0:
                    st.session_state.quiz_completed = True
                    st.error("⏰ Time's up! Quiz auto-submitted.")
                
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                
                st.markdown(f"""
                <div class="timer-box">
                    ⏰ Total Time Remaining: {minutes:02d}:{seconds:02d}
                </div>
                """, unsafe_allow_html=True)
            
            elif timer_type == "Per Question Timer":
                elapsed_question_time = time.time() - st.session_state.question_start_time
                remaining_question_time = max(0, question_seconds - elapsed_question_time)
                
                if remaining_question_time <= 0:
                    # Auto move to next question
                    if st.session_state.current_q < len(questions) - 1:
                        st.session_state.current_q += 1
                        st.session_state.question_start_time = time.time()
                        st.rerun()
                    else:
                        st.session_state.quiz_completed = True
                
                st.markdown(f"""
                <div class="timer-box">
                    ⏰ Question Time: {int(remaining_question_time)} seconds
                </div>
                """, unsafe_allow_html=True)
        
        # Quick Navigation
        st.sidebar.subheader("📍 Jump to Question")
        cols = st.sidebar.columns(4)
        for idx in range(len(questions)):
            with cols[idx % 4]:
                btn_type = "primary" if idx == st.session_state.current_q else "secondary"
                if st.button(f"Q{idx+1}", key=f"nav_{idx}"):
                    st.session_state.current_q = idx
                    st.session_state.question_start_time = time.time()
                    st.rerun()
        
        # Progress bar
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        progress = (st.session_state.current_q + 1) / len(questions)
        st.progress(progress)
        st.caption(f"Progress: {st.session_state.current_q + 1}/{len(questions)} questions")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Main quiz interface
        if not st.session_state.quiz_completed:
            current_q = questions[st.session_state.current_q]
            
            # Question container - Ediquity style
            st.markdown(f"""
            <div class="question-container">
                <div class="question-text">
                    Q{st.session_state.current_q + 1}. {current_q['question']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Options in grid layout
            st.markdown('<div class="options-grid">', unsafe_allow_html=True)
            
            # Create two columns for options
            col1, col2 = st.columns(2)
            
            options_list = list(current_q['options'].items())
            half = len(options_list) // 2
            
            with col1:
                for opt_letter, opt_text in options_list[:half]:
                    is_selected = st.session_state.user_answers.get(current_q['id']) == opt_letter
                    selection_class = "selected" if is_selected else ""
                    
                    st.markdown(f"""
                    <div class="option-card {selection_class}" onclick="selectOption('{opt_letter}')">
                        <strong>{opt_letter})</strong> {opt_text}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Hidden radio for functionality
                    if st.button(f"Select {opt_letter}", key=f"btn_{current_q['id']}_{opt_letter}", 
                               type="primary" if is_selected else "secondary"):
                        st.session_state.user_answers[current_q['id']] = opt_letter
                        st.rerun()
            
            with col2:
                for opt_letter, opt_text in options_list[half:]:
                    is_selected = st.session_state.user_answers.get(current_q['id']) == opt_letter
                    selection_class = "selected" if is_selected else ""
                    
                    st.markdown(f"""
                    <div class="option-card {selection_class}" onclick="selectOption('{opt_letter}')">
                        <strong>{opt_letter})</strong> {opt_text}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Select {opt_letter}", key=f"btn2_{current_q['id']}_{opt_letter}",
                               type="primary" if is_selected else "secondary"):
                        st.session_state.user_answers[current_q['id']] = opt_letter
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Navigation buttons
            st.markdown("---")
            nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
            
            with nav_col1:
                if st.button("◀ Previous", use_container_width=True) and st.session_state.current_q > 0:
                    st.session_state.current_q -= 1
                    st.session_state.question_start_time = time.time()
                    st.rerun()
            
            with nav_col2:
                if st.session_state.current_q < len(questions) - 1:
                    if st.button("Next ▶", use_container_width=True):
                        st.session_state.current_q += 1
                        st.session_state.question_start_time = time.time()
                        st.rerun()
                else:
                    if st.button("Finish 🏁", use_container_width=True, type="primary"):
                        st.session_state.quiz_completed = True
                        st.rerun()
            
            with nav_col3:
                if st.button("📌 Mark for Review", use_container_width=True):
                    st.info("Question marked for review!")
            
            with nav_col4:
                if st.button("🔄 Restart Quiz", use_container_width=True):
                    for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 'start_time', 'question_start_time']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        
        # Results screen
        else:
            st.balloons()
            st.markdown('<div class="main-header">🏆 Quiz Completed!</div>', unsafe_allow_html=True)
            
            # Calculate score
            correct_count = 0
            for q in questions:
                if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                    correct_count += 1
            
            score_percent = (correct_count / len(questions)) * 100
            
            # Results card
            st.markdown(f"""
            <div class="result-card">
                <h2>Your Score: {correct_count}/{len(questions)}</h2>
                <h1>{score_percent:.1f}%</h1>
                <p>{'🎯 Perfect Score!' if score_percent == 100 else '🌟 Great Job!' if score_percent >= 80 else '👍 Well Done!'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Detailed results
            with st.expander("📊 Detailed Analysis", expanded=True):
                for i, q in enumerate(questions):
                    user_ans = st.session_state.user_answers.get(q['id'])
                    correct_ans = q['correct_answer']
                    is_correct = user_ans == correct_ans
                    
                    if is_correct:
                        st.success(f"**Q{i+1}.** {q['question']} - ✅ Your answer: {user_ans}")
                    else:
                        st.error(f"**Q{i+1}.** {q['question']} - ❌ Your answer: {user_ans} | ✅ Correct: {correct_ans}")
            
            # Restart button
            if st.button("🔄 Start New Quiz", use_container_width=True, type="primary"):
                for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 'start_time', 'question_start_time']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    # JavaScript for better interaction
    st.markdown("""
    <script>
    function selectOption(option) {
        // This would need proper Streamlit components for full functionality
        console.log("Selected option: " + option);
    }
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
