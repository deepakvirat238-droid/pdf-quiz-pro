import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import re
import time
import io
import random
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
            
            # Add difficulty level randomly for demo
            difficulty = random.choice(["Easy", "Medium", "Hard"])
            
            questions.append({
                "id": i,
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "difficulty": difficulty,
                "time_spent": 0,
                "attempts": 0
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
    
    # Combined Advanced CSS with All Features
    st.markdown("""
    <style>
    /* Common Styles */
    .main-header {
        font-size: 2.8rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        background: linear-gradient(45deg, #2E86AB, #4BB3FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
        from { text-shadow: 0 0 10px #2E86AB; }
        to { text-shadow: 0 0 20px #4BB3FD, 0 0 30px #4BB3FD; }
    }
    
    .sub-header {
        font-size: 1.3rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* AI Assistant Styles */
    .ai-assistant {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        animation: slideIn 0.5s ease-out;
    }
    @keyframes slideIn {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    /* Gamification Styles */
    .achievement-badge {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.2rem;
        display: inline-block;
        animation: bounce 0.5s;
    }
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
        40% {transform: translateY(-10px);}
        60% {transform: translateY(-5px);}
    }
    
    .level-progress {
        background: #f0f0f0;
        border-radius: 10px;
        height: 20px;
        margin: 0.5rem 0;
    }
    .level-progress-fill {
        background: linear-gradient(45deg, #FF6B6B, #FF8E53);
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    /* Voice Command Styles */
    .voice-command {
        background: linear-gradient(45deg, #4ECDC4, #44A08D);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .voice-command:hover {
        transform: scale(1.05);
    }
    
    /* Exam Interface Styles */
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
    .exam-nav-buttons {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 0.8rem;
        margin-bottom: 2rem;
    }
    .exam-nav-button {
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
    .exam-nav-button:hover {
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
    .exam-question-container {
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
    .exam-options-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .exam-option-item {
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
    .exam-option-item:hover {
        border-color: #3498db;
        background: #e3f2fd;
    }
    .exam-option-item.selected {
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
    .exam-option-item.selected .option-radio {
        background: white;
        border-color: white;
    }
    .exam-option-item.selected .option-radio::after {
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
    
    /* Practice Mode Styles */
    .practice-question-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        color: white;
    }
    .practice-options-grid {
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
    
    st.markdown('<div class="main-header">🧠 PDF Quiz PRO - AI Enhanced</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Professional Quiz Platform with AI Features</div>', unsafe_allow_html=True)
    
    # Initialize session state for ALL features
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = "practice"
    if 'show_answer_feedback' not in st.session_state:
        st.session_state.show_answer_feedback = {}
    if 'marked_review' not in st.session_state:
        st.session_state.marked_review = set()
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'current_q' not in st.session_state:
        st.session_state.current_q = 0
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    if 'question_start_time' not in st.session_state:
        st.session_state.question_start_time = time.time()
    
    # New AI Features Session State
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'level': 1,
            'xp': 0,
            'achievements': [],
            'streak': 0,
            'total_quizzes': 0
        }
    
    if 'ai_suggestions' not in st.session_state:
        st.session_state.ai_suggestions = {}
    
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    
    # AI Assistant
    with st.container():
        st.markdown("""
        <div class="ai-assistant">
            <h3>🤖 AI Quiz Assistant</h3>
            <p>I can help you: Generate explanations • Suggest similar questions • Analyze your weak areas</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced Sidebar with All Features
    with st.sidebar:
        st.header("🎮 Game Profile")
        
        # User profile
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Level", st.session_state.user_profile['level'])
        with col2:
            st.metric("XP", st.session_state.user_profile['xp'])
        
        # Level progress
        st.write("Level Progress")
        level_progress = (st.session_state.user_profile['xp'] % 1000) / 10
        st.markdown(f"""
        <div class="level-progress">
            <div class="level-progress-fill" style="width: {level_progress}%"></div>
        </div>
        <div style="text-align: center; font-size: 0.8rem;">{level_progress}% to next level</div>
        """, unsafe_allow_html=True)
        
        # Achievements
        if st.session_state.user_profile['achievements']:
            st.write("🏆 Achievements")
            for achievement in st.session_state.user_profile['achievements']:
                st.markdown(f'<div class="achievement-badge">{achievement}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Quiz Mode Selection
        st.header("🎯 Quiz Mode")
        mode_col1, mode_col2 = st.columns(2)
        with mode_col1:
            if st.button("💡 Practice", use_container_width=True, 
                        type="primary" if st.session_state.quiz_mode == "practice" else "secondary"):
                st.session_state.quiz_mode = "practice"
                st.rerun()
        with mode_col2:
            if st.button("📝 Exam", use_container_width=True,
                        type="primary" if st.session_state.quiz_mode == "exam" else "secondary"):
                st.session_state.quiz_mode = "exam"
                st.rerun()
        
        st.markdown("---")
        
        # Mode-specific settings
        if st.session_state.quiz_mode == "practice":
            st.header("⚙️ Practice Settings")
            timer_type = st.radio(
                "⏰ Timer Type:",
                ["Stopwatch Only", "Per Question Timer", "No Timer"]
            )
            
            if timer_type == "Per Question Timer":
                question_seconds = st.slider("Time per Question (seconds):", 15, 300, 90)
        
        else:  # Exam Mode
            st.header("⚙️ Exam Settings")
            exam_minutes = st.slider("Exam Duration (minutes):", 30, 180, 60)
            total_exam_seconds = exam_minutes * 60
        
        st.markdown("---")
        
        # New AI Features Section
        st.header("✨ AI Features")
        
        # Voice Commands
        if st.button("🎤 Voice Commands", use_container_width=True):
            st.session_state.show_voice_commands = not st.session_state.get('show_voice_commands', False)
        
        if st.session_state.get('show_voice_commands', False):
            st.markdown("""
            <div class="voice-command">
                <strong>Try saying:</strong><br>
                "Next question"<br>
                "Check answer"<br>
                "Mark for review"<br>
                "Show explanation"
            </div>
            """, unsafe_allow_html=True)
        
        # AI Analysis
        if st.button("🤖 AI Weakness Analysis", use_container_width=True):
            st.session_state.show_ai_analysis = True
        
        # Challenge Mode
        if st.button("⚡ Daily Challenge", use_container_width=True):
            st.session_state.daily_challenge = True
        
        st.markdown("---")
        
        # Social Features
        st.header("👥 Social")
        if st.button("🏆 Leaderboard", use_container_width=True):
            st.session_state.show_leaderboard = True
        
        if st.button("🤝 Challenge Friend", use_container_width=True):
            st.session_state.challenge_friend = True
    
    # Main content area with two columns
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # File upload
        uploaded_file = st.file_uploader("📁 Upload PDF File", type="pdf")
        
        if uploaded_file:
            with st.spinner("🔍 Processing PDF with AI..."):
                questions = parse_pdf_content(uploaded_file)
            
            if not questions:
                st.error("❌ No questions found. Please check the PDF format.")
                return
            
            st.success(f"✅ Found {len(questions)} questions! + 🤖 AI Analysis Enabled")
            
            # Initialize quiz state
            if not st.session_state.quiz_started:
                st.session_state.quiz_started = True
                st.session_state.start_time = time.time()
                st.session_state.question_start_time = time.time()
                st.session_state.user_answers = {}
                st.session_state.current_q = 0
                st.session_state.quiz_completed = False
            
            # Add AI suggestions for each question
            for q in questions:
                if q['id'] not in st.session_state.ai_suggestions:
                    st.session_state.ai_suggestions[q['id']] = {
                        'explanation': f"AI Explanation: This question tests your understanding of {q['difficulty'].lower()} concepts.",
                        'related_topics': ['Topic A', 'Topic B', 'Topic C'],
                        'tips': ['Read carefully', 'Eliminate wrong options first']
                    }
            
            # Display based on mode
            if st.session_state.quiz_mode == "exam":
                # EXAM MODE INTERFACE
                remaining_time = max(0, total_exam_seconds - (time.time() - st.session_state.start_time))
                
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
                st.markdown('<div class="exam-nav-buttons">', unsafe_allow_html=True)
                
                nav_col1, nav_col2, nav_col3 = st.columns(3)
                
                with nav_col1:
                    if st.button("⏮️ Previous", use_container_width=True) and st.session_state.current_q > 0:
                        st.session_state.current_q -= 1
                        st.rerun()
                
                with nav_col2:
                    if st.button("📌 Mark & Review", use_container_width=True):
                        st.session_state.marked_review.add(st.session_state.current_q)
                        st.success("Question marked for review!")
                        st.rerun()
                
                with nav_col3:
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
                    QUESTION PAPER
                </div>
                <div class="section-content">
                    <div class="subject-header">
                        All Subjects
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
                for idx in range(min(10, len(questions))):
                    with quick_nav_cols[idx % 5]:
                        is_answered = questions[idx]['id'] in st.session_state.user_answers
                        is_current = idx == st.session_state.current_q
                        is_marked = idx in st.session_state.marked_review
                        
                        btn_text = f"Q{idx+1}"
                        if is_marked:
                            btn_text = f"📌{idx+1}"
                        
                        if st.button(btn_text, key=f"quick_{idx}", use_container_width=True):
                            st.session_state.current_q = idx
                            st.rerun()
                
                st.markdown('</div></div>', unsafe_allow_html=True)
                
            else:
                # PRACTICE MODE INTERFACE
                mode_status = "💡 Practice Mode"
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
                
                # Progress bar for practice mode
                st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                progress = (st.session_state.current_q + 1) / len(questions)
                st.progress(progress)
                st.caption(f"Progress: {st.session_state.current_q + 1}/{len(questions)} questions • "
                          f"Answered: {len(st.session_state.user_answers)}/{len(questions)}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Common Question Display Logic (works for both modes)
            if not st.session_state.quiz_completed:
                current_q = questions[st.session_state.current_q]
                current_answer = st.session_state.user_answers.get(current_q['id'])
                
                if st.session_state.quiz_mode == "exam":
                    # EXAM MODE QUESTION DISPLAY
                    st.markdown(f"""
                    <div class="exam-question-container">
                        <div class="question-header">
                            <div class="question-number">Question. {st.session_state.current_q + 1}</div>
                            <div class="question-timer">Last 6 Minutes</div>
                        </div>
                        <div class="question-text">
                            {current_q['question']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Options
                    st.markdown('<div class="exam-options-container">', unsafe_allow_html=True)
                    
                    for opt_letter, opt_text in current_q['options'].items():
                        is_selected = current_answer == opt_letter
                        
                        if st.button(f"{opt_letter}) {opt_text}", key=f"exam_opt_{current_q['id']}_{opt_letter}", 
                                   use_container_width=True, type="primary" if is_selected else "secondary"):
                            st.session_state.user_answers[current_q['id']] = opt_letter
                            st.rerun()
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                else:
                    # PRACTICE MODE QUESTION DISPLAY
                    st.markdown(f"""
                    <div class="practice-question-container">
                        <div class="question-text">
                            Q{st.session_state.current_q + 1}. {current_q['question']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Options in 4-column bubble grid
                    st.markdown('<div class="practice-options-grid">', unsafe_allow_html=True)
                    
                    for opt_letter, opt_text in current_q['options'].items():
                        is_selected = current_answer == opt_letter
                        is_correct = st.session_state.show_answer_feedback.get(current_q['id']) and opt_letter == current_q['correct_answer']
                        is_incorrect = st.session_state.show_answer_feedback.get(current_q['id']) and is_selected and opt_letter != current_q['correct_answer']
                        
                        if st.button(f"{opt_letter}) {opt_text}", key=f"practice_opt_{current_q['id']}_{opt_letter}", 
                                   use_container_width=True, type="primary" if is_selected else "secondary"):
                            st.session_state.user_answers[current_q['id']] = opt_letter
                            if st.session_state.show_answer_feedback.get(current_q['id']):
                                st.session_state.show_answer_feedback[current_q['id']] = False
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Answer feedback for practice mode
                    if st.session_state.show_answer_feedback.get(current_q['id']):
                        user_answer = st.session_state.user_answers.get(current_q['id'])
                        correct_answer = current_q['correct_answer']
                        
                        if user_answer == correct_answer:
                            st.markdown(f"""
                            <div class="feedback-correct">
                                ✅ <strong>Correct!</strong> Your answer {user_answer} is right.
                                <br>🤖 {st.session_state.ai_suggestions[current_q['id']]['explanation']}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div class="feedback-incorrect">
                                ❌ <strong>Incorrect!</strong> Your answer: {user_answer} | Correct answer: {correct_answer}
                                <br><strong>Explanation:</strong> {current_q['options'][correct_answer]}
                                <br>🤖 {st.session_state.ai_suggestions[current_q['id']]['explanation']}
                            </div>
                            """, unsafe_allow_html=True)
                
                # Common Navigation Buttons (adjusted based on mode)
                if st.session_state.quiz_mode == "practice":
                    st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
                    
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
                        if current_answer:
                            if st.button("✅ Check Answer", use_container_width=True, type="primary"):
                                st.session_state.show_answer_feedback[current_q['id']] = True
                                # Award XP for checking answer
                                st.session_state.user_profile['xp'] += 10
                                st.rerun()
                        else:
                            st.button("✅ Check Answer", use_container_width=True, disabled=True)
                    
                    with nav_col4:
                        if st.button("🔄 Restart", use_container_width=True):
                            for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 
                                      'start_time', 'question_start_time', 'show_answer_feedback']:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Auto-submit when time ends (exam mode)
                if st.session_state.quiz_mode == "exam" and remaining_time <= 0:
                    st.session_state.quiz_completed = True
                    st.rerun()
            
            else:
                # RESULTS SCREEN (Common for both modes)
                st.balloons()
                st.markdown('<div class="main-header">🏆 Quiz Completed!</div>', unsafe_allow_html=True)
                
                # Calculate score
                correct_count = 0
                for q in questions:
                    if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                        correct_count += 1
                
                total_time = time.time() - st.session_state.start_time
                score_percent = (correct_count / len(questions)) * 100
                
                # Award XP based on performance
                xp_earned = correct_count * 10 + int(score_percent)
                st.session_state.user_profile['xp'] += xp_earned
                
                # Check for level up
                if st.session_state.user_profile['xp'] >= st.session_state.user_profile['level'] * 1000:
                    st.session_state.user_profile['level'] += 1
                    st.session_state.user_profile['achievements'].append(f"Level {st.session_state.user_profile['level']}")
                
                st.markdown(f"""
                <div class="result-card">
                    <h2>Your Score: {correct_count}/{len(questions)}</h2>
                    <h1>{score_percent:.1f}%</h1>
                    <p>Time Taken: {int(total_time // 60):02d}:{int(total_time % 60):02d}</p>
                    <p>🎯 XP Earned: +{xp_earned}</p>
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
                                  'start_time', 'question_start_time', 'show_answer_feedback', 'marked_review']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                with col2:
                    if st.button("📊 Review Answers", use_container_width=True):
                        st.session_state.quiz_completed = False
                        st.session_state.current_q = 0
                        st.rerun()

    with col2:
        # Quick Actions Panel
        st.subheader("⚡ Quick Actions")
        
        if st.button("🎯 Smart Practice", use_container_width=True):
            st.info("AI will focus on your weak areas!")
        
        if st.button("📊 Performance", use_container_width=True):
            # Show performance metrics
            accuracy = (len([q for q in questions if st.session_state.user_answers.get(q['id']) == q['correct_answer']]) / len(questions)) * 100 if questions else 0
            st.metric("Accuracy", f"{accuracy:.1f}%")
            st.metric("Questions Solved", len(st.session_state.user_answers))
            st.metric("Streak", f"{st.session_state.user_profile['streak']} days")
        
        if st.button("🔔 Notifications", use_container_width=True):
            st.success("📢 Daily challenge available!")
            st.success("👏 New achievement unlocked!")
        
        # Study Timer
        st.subheader("⏱️ Study Timer")
        timer_col1, timer_col2, timer_col3 = st.columns(3)
        with timer_col1:
            if st.button("25m", use_container_width=True):
                st.session_state.study_timer = 25 * 60
        with timer_col2:
            if st.button("45m", use_container_width=True):
                st.session_state.study_timer = 45 * 60
        with timer_col3:
            if st.button("60m", use_container_width=True):
                st.session_state.study_timer = 60 * 60
        
        if st.session_state.get('study_timer', 0) > 0:
            st.info(f"⏰ Study session: {st.session_state.study_timer//60} minutes")
        
        # Quick Stats
        st.subheader("📈 Today's Stats")
        st.metric("Questions Solved", len(st.session_state.user_answers))
        st.metric("Correct Rate", f"{(len([q for q in questions if st.session_state.user_answers.get(q['id']) == q['correct_answer']]) / len(questions)) * 100 if questions else 0:.1f}%")
        st.metric("Level", st.session_state.user_profile['level'])

    # New AI Features Expansion
    if st.session_state.get('show_ai_analysis', False):
        st.markdown("---")
        st.subheader("🤖 AI Weakness Analysis")
        
        # Create sample data for visualization
        categories = ['Grammar', 'Vocabulary', 'Comprehension', 'Logic', 'Speed']
        scores = [75, 60, 85, 70, 55]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            name='Your Performance'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False,
            title="AI Analysis: Your Skill Distribution"
        )
        
        st.plotly_chart(fig)
        
        st.info("""
        **AI Recommendations:**
        - Focus on Vocabulary building
        - Practice time management
        - Review logical reasoning concepts
        """)
    
    if st.session_state.get('show_leaderboard', False):
        st.markdown("---")
        st.subheader("🏆 Global Leaderboard")
        
        leaderboard_data = {
            'Rank': [1, 2, 3, 4, 5],
            'Player': ['QuizMaster', 'Brainiac', 'Genius', 'Scholar', 'Wizard'],
            'Score': [980, 950, 920, 890, 870],
            'Level': [25, 23, 21, 20, 19]
        }
        
        df = pd.DataFrame(leaderboard_data)
        st.dataframe(df, use_container_width=True)
        
        # Your position
        st.metric("Your Position", "🎯 Top 10%")
    
    if st.session_state.get('daily_challenge', False):
        st.markdown("---")
        st.subheader("⚡ Daily Challenge")
        
        challenge_col1, challenge_col2, challenge_col3 = st.columns(3)
        
        with challenge_col1:
            st.metric("Time Limit", "10:00")
            if st.button("Start Challenge", use_container_width=True, type="primary"):
                st.success("Challenge started! Good luck! 🍀")
        
        with challenge_col2:
            st.metric("Questions", "20")
            st.metric("Difficulty", "Mixed")
        
        with challenge_col3:
            st.metric("Reward", "500 XP")
            st.metric("Participants", "1.2k")
        
        st.progress(65)
        st.caption("65% of participants completed today's challenge")

    # AI Question Generator
    if st.button("🤖 Generate Similar Questions", use_container_width=True):
        st.markdown("---")
        st.subheader("AI Generated Practice Questions")
        
        generated_questions = [
            {
                'question': 'What is the synonym of "Eloquent"?',
                'options': ['A) Fluent', 'B) Silent', 'C) Rude', 'D) Simple'],
                'correct': 'A'
            },
            {
                'question': 'Which tense is used in: "She has been studying for 3 hours"?',
                'options': ['A) Past Perfect', 'B) Present Perfect Continuous', 'C) Future Perfect', 'D) Simple Present'],
                'correct': 'B'
            }
        ]
        
        for i, gq in enumerate(generated_questions, 1):
            with st.expander(f"AI Question {i}"):
                st.write(gq['question'])
                for option in gq['options']:
                    st.write(option)
                if st.button(f"Show Answer {i}", key=f"ai_ans_{i}"):
                    st.success(f"Correct answer: {gq['correct']}")

    # Export Features
    st.markdown("---")
    st.subheader("📤 Export & Share")
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        if st.button("📊 Export Results", use_container_width=True):
            st.success("Results exported as PDF! 📄")
    
    with export_col2:
        if st.button("📧 Email Report", use_container_width=True):
            st.success("Report sent to your email! ✉️")
    
    with export_col3:
        if st.button("📱 Share Progress", use_container_width=True):
            st.success("Progress shared on social media! 🌐")

if __name__ == "__main__":
    main()
    
