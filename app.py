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
    
    # Professional CSS - Ediquity Style with Bubble Options
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
        margin-bottom: 1rem;
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
        grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 0.8rem;
        margin-top: 1rem;
    }
    .bubble-option {
        background: rgba(255,255,255,0.95);
        padding: 1rem;
        border-radius: 25px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        cursor: pointer;
        color: #333;
        text-align: center;
        font-weight: 500;
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .bubble-option:hover {
        border-color: #2E86AB;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .bubble-option.selected {
        border-color: #2E86AB;
        background: #e3f2fd;
        transform: scale(1.05);
    }
    .bubble-option.correct {
        border-color: #28a745;
        background: #d4edda;
        color: #155724;
    }
    .bubble-option.incorrect {
        border-color: #dc3545;
        background: #f8d7da;
        color: #721c24;
    }
    .timer-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .timer-box {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        font-weight: bold;
        text-align: center;
        font-size: 1.1rem;
        box-shadow: 0 5px 15px rgba(255,107,107,0.3);
    }
    .stopwatch-box {
        background: linear-gradient(45deg, #4ECDC4, #44A08D);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        font-weight: bold;
        text-align: center;
        font-size: 1.1rem;
        box-shadow: 0 5px 15px rgba(78,205,196,0.3);
    }
    .progress-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .mode-buttons {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .mode-button {
        flex: 1;
        padding: 1rem;
        border-radius: 10px;
        font-weight: 600;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .mode-button.active {
        background: linear-gradient(45deg, #2E86AB, #4BB3FD);
        color: white;
        transform: scale(1.02);
    }
    .mode-button.inactive {
        background: #e9ecef;
        color: #6c757d;
    }
    .result-card {
        background: linear-gradient(135deg, #00b09b, #96c93d);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feedback-correct {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .feedback-incorrect {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
    .nav-buttons {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr 1fr;
        gap: 1rem;
        margin-top: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">📚 PDF Quiz PRO</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Professional Quiz Platform - Enhanced Ediquity Style</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = "practice"  # "practice" or "mock_test"
    if 'show_answer_feedback' not in st.session_state:
        st.session_state.show_answer_feedback = {}
    
    # Sidebar for settings
    with st.sidebar:
        st.header("🎯 Quiz Mode")
        
        # Quiz mode selection
        mode_col1, mode_col2 = st.columns(2)
        with mode_col1:
            if st.button("💡 Practice Mode", use_container_width=True):
                st.session_state.quiz_mode = "practice"
                st.rerun()
        with mode_col2:
            if st.button("📝 Mock Test", use_container_width=True):
                st.session_state.quiz_mode = "mock_test"
                st.rerun()
        
        st.markdown("---")
        st.header("⚙️ Timer Settings")
        
        if st.session_state.quiz_mode == "mock_test":
            timer_type = st.radio(
                "⏰ Timer Type:",
                ["Full Quiz Timer", "Per Question Timer", "No Timer"]
            )
            
            if timer_type == "Full Quiz Timer":
                quiz_minutes = st.slider("Total Quiz Time (minutes):", 5, 120, 30)
                total_seconds = quiz_minutes * 60
            elif timer_type == "Per Question Timer":
                question_seconds = st.slider("Time per Question (seconds):", 15, 300, 90)
        else:
            timer_type = "No Timer"
            st.info("⏰ Timer disabled in Practice Mode")
        
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
        if 'total_elapsed_time' not in st.session_state:
            st.session_state.total_elapsed_time = 0
        
        # Mode display
        mode_status = "💡 Practice Mode" if st.session_state.quiz_mode == "practice" else "📝 Mock Test Mode"
        st.info(f"**Current Mode:** {mode_status}")
        
        # Timer and Stopwatch Display
        if not st.session_state.quiz_completed:
            current_time = time.time()
            question_elapsed = current_time - st.session_state.question_start_time
            total_elapsed = current_time - st.session_state.start_time
            
            st.markdown('<div class="timer-container">', unsafe_allow_html=True)
            
            # Stopwatch for current question
            st.markdown(f"""
            <div class="stopwatch-box">
                ⏱️ Current Question: {int(question_elapsed // 60):02d}:{int(question_elapsed % 60):02d}
            </div>
            """, unsafe_allow_html=True)
            
            # Stopwatch for total time
            st.markdown(f"""
            <div class="stopwatch-box">
                ⏱️ Total Time: {int(total_elapsed // 60):02d}:{int(total_elapsed % 60):02d}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Timer logic for mock test
            if st.session_state.quiz_mode == "mock_test" and timer_type != "No Timer":
                if timer_type == "Full Quiz Timer":
                    remaining_time = max(0, total_seconds - total_elapsed)
                    
                    if remaining_time <= 0:
                        st.session_state.quiz_completed = True
                        st.error("⏰ Time's up! Quiz auto-submitted.")
                    
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    
                    st.markdown(f"""
                    <div class="timer-box">
                        ⏰ Quiz Time Remaining: {minutes:02d}:{seconds:02d}
                    </div>
                    """, unsafe_allow_html=True)
                
                elif timer_type == "Per Question Timer":
                    remaining_question_time = max(0, question_seconds - question_elapsed)
                    
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
        nav_cols = st.sidebar.columns(4)
        for idx in range(len(questions)):
            with nav_cols[idx % 4]:
                answer_status = "✅" if st.session_state.user_answers.get(questions[idx]['id']) else "⭕"
                if st.button(f"{answer_status}Q{idx+1}", key=f"nav_{idx}"):
                    st.session_state.current_q = idx
                    st.session_state.question_start_time = time.time()
                    st.rerun()
        
        # Progress bar
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        progress = (st.session_state.current_q + 1) / len(questions)
        st.progress(progress)
        st.caption(f"Progress: {st.session_state.current_q + 1}/{len(questions)} questions • "
                  f"Answered: {len(st.session_state.user_answers)}/{len(questions)}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Main quiz interface
        if not st.session_state.quiz_completed:
            current_q = questions[st.session_state.current_q]
            current_answer = st.session_state.user_answers.get(current_q['id'])
            
            # Question container
            st.markdown(f"""
            <div class="question-container">
                <div class="question-text">
                    Q{st.session_state.current_q + 1}. {current_q['question']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Options in 4-column bubble grid
            st.markdown('<div class="options-grid">', unsafe_allow_html=True)
            
            options_list = list(current_q['options'].items())
            
            for opt_letter, opt_text in options_list:
                is_selected = current_answer == opt_letter
                is_correct = st.session_state.show_answer_feedback.get(current_q['id']) and opt_letter == current_q['correct_answer']
                is_incorrect = st.session_state.show_answer_feedback.get(current_q['id']) and is_selected and opt_letter != current_q['correct_answer']
                
                bubble_class = "bubble-option"
                if is_selected:
                    bubble_class += " selected"
                if is_correct:
                    bubble_class += " correct"
                if is_incorrect:
                    bubble_class += " incorrect"
                
                st.markdown(f"""
                <div class="{bubble_class}" onclick="selectOption('{opt_letter}')">
                    <strong>{opt_letter})</strong> {opt_text}
                </div>
                """, unsafe_allow_html=True)
                
                # Hidden button for functionality
                if st.button(f"Select {opt_letter}", key=f"btn_{current_q['id']}_{opt_letter}", 
                           use_container_width=True, type="primary" if is_selected else "secondary"):
                    st.session_state.user_answers[current_q['id']] = opt_letter
                    if st.session_state.show_answer_feedback.get(current_q['id']):
                        st.session_state.show_answer_feedback[current_q['id']] = False
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Answer feedback for practice mode
            if st.session_state.quiz_mode == "practice" and st.session_state.show_answer_feedback.get(current_q['id']):
                user_answer = st.session_state.user_answers.get(current_q['id'])
                correct_answer = current_q['correct_answer']
                
                if user_answer == correct_answer:
                    st.markdown(f"""
                    <div class="feedback-correct">
                        ✅ <strong>Correct!</strong> Your answer {user_answer} is right.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="feedback-incorrect">
                        ❌ <strong>Incorrect!</strong> Your answer: {user_answer} | Correct answer: {correct_answer}
                        <br><strong>Explanation:</strong> {current_q['options'][correct_answer]}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Action buttons
            st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("◀ Previous", use_container_width=True) and st.session_state.current_q > 0:
                    st.session_state.current_q -= 1
                    st.session_state.question_start_time = time.time()
                    st.rerun()
            
            with col2:
                if st.session_state.current_q < len(questions) - 1:
                    if st.button("Next ▶", use_container_width=True):
                        st.session_state.current_q += 1
                        st.session_state.question_start_time = time.time()
                        st.rerun()
                else:
                    if st.button("Finish 🏁", use_container_width=True, type="primary"):
                        st.session_state.quiz_completed = True
                        st.rerun()
            
            with col3:
                if st.session_state.quiz_mode == "practice" and current_answer:
                    if st.button("✅ Check Answer", use_container_width=True, type="primary"):
                        st.session_state.show_answer_feedback[current_q['id']] = True
                        st.rerun()
                else:
                    st.button("✅ Check Answer", use_container_width=True, disabled=True)
            
            with col4:
                if st.button("🔄 Restart", use_container_width=True):
                    for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 
                              'start_time', 'question_start_time', 'show_answer_feedback']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Results screen
        else:
            st.balloons()
            st.markdown('<div class="main-header">🏆 Quiz Completed!</div>', unsafe_allow_html=True)
            
            # Calculate score and time
            correct_count = 0
            for q in questions:
                if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                    correct_count += 1
            
            total_time = time.time() - st.session_state.start_time
            score_percent = (correct_count / len(questions)) * 100
            
            # Results card
            st.markdown(f"""
            <div class="result-card">
                <h2>Your Score: {correct_count}/{len(questions)}</h2>
                <h1>{score_percent:.1f}%</h1>
                <p>Time Taken: {int(total_time // 60):02d}:{int(total_time % 60):02d}</p>
                <p>{'🎯 Perfect Score!' if score_percent == 100 else '🌟 Excellent!' if score_percent >= 90 else '👍 Great Job!' if score_percent >= 70 else '💪 Keep Practicing!'}</p>
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
            
            # Restart options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Start New Quiz", use_container_width=True, type="primary"):
                    for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 
                              'start_time', 'question_start_time', 'show_answer_feedback']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            with col2:
                if st.button("📊 Review Answers", use_container_width=True):
                    st.session_state.quiz_completed = False
                    st.session_state.current_q = 0
                    st.rerun()

    # Add some sample questions if no file uploaded
    else:
        st.info("👆 Please upload a PDF file to start the quiz")
        
        with st.expander("📋 Expected PDF Format", expanded=True):
            st.code("""
Q1. What is the capital of France?
A) London
B) Berlin  
C) Paris
D) Madrid
E) Rome
Answer: C

Q2. Which planet is known as the Red Planet?
A) Earth
B) Mars
C) Jupiter
D) Venus
Answer: B
            """)

if __name__ == "__main__":
    main()
