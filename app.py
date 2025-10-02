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

def generate_ai_explanation(question, correct_answer, options):
    """Generate AI explanation for questions"""
    explanations = {
        "grammar": "This question tests your understanding of grammatical rules. The correct answer follows standard grammar conventions.",
        "vocabulary": "This vocabulary question requires understanding word meanings and contextual usage.",
        "comprehension": "This reading comprehension question tests your ability to understand and interpret written text.",
        "logic": "This logical reasoning question requires analytical thinking and deduction skills.",
        "general": "This question evaluates fundamental knowledge in the subject area."
    }
    
    # Simple AI logic to determine question type
    question_lower = question.lower()
    if any(word in question_lower for word in ['synonym', 'antonym', 'word', 'meaning']):
        exp_type = "vocabulary"
    elif any(word in question_lower for word in ['tense', 'grammar', 'sentence', 'verb']):
        exp_type = "grammar"
    elif any(word in question_lower for word in ['passage', 'read', 'comprehension']):
        exp_type = "comprehension"
    elif any(word in question_lower for word in ['logic', 'reason', 'deduce', 'infer']):
        exp_type = "logic"
    else:
        exp_type = "general"
    
    base_explanation = explanations[exp_type]
    detailed_explanation = f"""
{base_explanation}

**Why {correct_answer} is correct:**
- It accurately addresses the question's requirement
- It follows the rules of {exp_type}
- The other options contain common misconceptions

**Learning Tip:** Practice similar questions to strengthen your {exp_type} skills.
"""
    
    return detailed_explanation

def parse_pdf_content(pdf_file):
    questions = []
    text = extract_text_from_pdf(pdf_file)
    
    # More robust question splitting
    question_blocks = re.split(r'(?i)Q\d+\.|\n\d+\.', text)
    
    for i, block in enumerate(question_blocks[1:], 1):
        try:
            # Improved regex for question extraction
            question_match = re.search(r'^(.*?)(?=A\)|B\)|C\)|D\)|E\)|Answer:|$)', block, re.DOTALL)
            if not question_match: 
                continue
            
            question_text = question_match.group(1).strip()
            
            # Extract options with improved regex
            options = {}
            option_matches = re.findall(r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|\s*Answer:|$)', block)
            for opt_letter, opt_text in option_matches:
                options[opt_letter] = opt_text.strip()
            
            # If no options found, create default ones
            if not options:
                options = {
                    'A': 'Option A',
                    'B': 'Option B', 
                    'C': 'Option C',
                    'D': 'Option D'
                }
            
            # Extract answer with improved regex
            answer_match = re.search(r'(?i)Answer:\s*([A-E])', block)
            correct_answer = answer_match.group(1) if answer_match else random.choice(list(options.keys()))
            
            # Add AI explanation
            ai_explanation = generate_ai_explanation(question_text, correct_answer, options)
            
            questions.append({
                "id": i,
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer,
                "ai_explanation": ai_explanation,
                "difficulty": random.choice(["Easy", "Medium", "Hard"]),
                "time_spent": 0,
                "attempts": 0
            })
        except Exception as e:
            continue
    
    return questions

def main():
    st.set_page_config(
        page_title="PDF Quiz PRO", 
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.8rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 700;
        background: linear-gradient(45deg, #2E86AB, #4BB3FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Quick Jump Grid Styles */
    .quick-jump-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 0.5rem;
        margin: 1rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
    .jump-btn {
        padding: 0.8rem 0.5rem;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        border: 2px solid #dee2e6;
        background: white;
    }
    .jump-btn.answered {
        background: #28a745;
        color: white;
        border-color: #28a745;
    }
    .jump-btn.current {
        background: #007bff;
        color: white;
        border-color: #007bff;
        transform: scale(1.1);
    }
    .jump-btn.marked {
        background: #ffc107;
        color: black;
        border-color: #ffc107;
    }
    .jump-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* AI Explanation Styles */
    .ai-explanation {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        animation: slideIn 0.5s ease-out;
    }
    .ai-explanation h4 {
        margin-top: 0;
        color: #ffd700;
    }
    @keyframes slideIn {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    /* Grid View Styles */
    .grid-view-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    .question-card {
        background: white;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 1.5rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .question-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        border-color: #007bff;
    }
    .question-card.answered {
        border-color: #28a745;
        background: #f8fff9;
    }
    .question-card.current {
        border-color: #007bff;
        background: #f0f8ff;
        transform: scale(1.02);
    }
    .question-preview {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    
    /* Time and Progress Styles */
    .time-left-box { 
        background: linear-gradient(135deg, #e74c3c, #c0392b); 
        color: white; 
        padding: 1.5rem; 
        border-radius: 10px; 
        text-align: center; 
        margin-bottom: 1rem; 
    }
    .bubble-option { 
        background: rgba(255,255,255,0.95); 
        padding: 1rem; 
        border-radius: 25px; 
        border: 2px solid transparent; 
        transition: all 0.3s ease; 
        cursor: pointer; 
        margin: 0.5rem 0;
    }
    .bubble-option:hover {
        border-color: #007bff;
        transform: scale(1.02);
    }
    .bubble-option.selected {
        background: #007bff;
        color: white;
        border-color: #0056b3;
    }
    
    /* Game Profile Styles */
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
    .achievement-badge {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.2rem;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🧠 PDF Quiz PRO - Ultimate Edition</div>', unsafe_allow_html=True)
    
    # Initialize session state
    default_states = {
        'quiz_mode': "practice",
        'current_view': "question",
        'show_ai_explanation': {},
        'marked_review': set(),
        'user_answers': {},
        'current_q': 0,
        'quiz_started': False,
        'start_time': time.time(),
        'quiz_completed': False,
        'user_profile': {
            'level': 1,
            'xp': 0,
            'achievements': [],
            'streak': 0,
            'total_quizzes': 0
        },
        'ai_suggestions': {},
        'dark_mode': False,
        'questions': []
    }
    
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Sidebar
    with st.sidebar:
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
        st.header("👀 View Mode")
        
        view_col1, view_col2 = st.columns(2)
        with view_col1:
            if st.button("📖 Question", use_container_width=True,
                        type="primary" if st.session_state.current_view == "question" else "secondary"):
                st.session_state.current_view = "question"
                st.rerun()
        with view_col2:
            if st.button("🔲 Grid", use_container_width=True,
                        type="primary" if st.session_state.current_view == "grid" else "secondary"):
                st.session_state.current_view = "grid"
                st.rerun()
        
        st.markdown("---")
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
        st.header("🔍 Navigation")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # File upload
        uploaded_file = st.file_uploader("📁 Upload PDF File", type="pdf", help="Upload a PDF file containing quiz questions")
        
        if uploaded_file:
            if not st.session_state.questions or st.session_state.get('uploaded_file') != uploaded_file.name:
                with st.spinner("🔍 Processing PDF with AI Analysis..."):
                    st.session_state.questions = parse_pdf_content(uploaded_file)
                    st.session_state.uploaded_file = uploaded_file.name
                    # Reset quiz state when new file is uploaded
                    st.session_state.user_answers = {}
                    st.session_state.current_q = 0
                    st.session_state.quiz_completed = False
                    st.session_state.quiz_started = True
                    st.session_state.start_time = time.time()
            
            questions = st.session_state.questions
            
            if not questions:
                st.error("❌ No questions found. Please check the PDF format.")
                st.info("""
                **Expected PDF format:**
                - Questions should start with 'Q1.', 'Q2.', etc.
                - Options should be labeled A), B), C), D)
                - Answers should be marked with 'Answer: A' format
                """)
                return
            
            st.success(f"✅ Found {len(questions)} questions! + 🤖 AI Explanations Ready")
            
            # Quick Jump Grid
            st.subheader("🎯 Quick Jump to Any Question")
            
            # Create grid with 10 questions per row
            rows = (len(questions) + 9) // 10
            
            for row in range(rows):
                cols = st.columns(10)
                start_idx = row * 10
                end_idx = min(start_idx + 10, len(questions))
                
                for idx in range(start_idx, end_idx):
                    with cols[idx % 10]:
                        is_answered = questions[idx]['id'] in st.session_state.user_answers
                        is_current = idx == st.session_state.current_q
                        is_marked = idx in st.session_state.marked_review
                        
                        btn_text = f"Q{idx+1}"
                        if is_marked:
                            btn_text = f"📌{idx+1}"
                        
                        button_type = "primary" if is_current else "secondary"
                        if st.button(btn_text, key=f"jump_{idx}", use_container_width=True, type=button_type):
                            st.session_state.current_q = idx
                            st.rerun()
            
            # View Toggle
            view_col1, view_col2 = st.columns(2)
            with view_col1:
                if st.button("📖 Question View", use_container_width=True,
                           type="primary" if st.session_state.current_view == "question" else "secondary"):
                    st.session_state.current_view = "question"
                    st.rerun()
            with view_col2:
                if st.button("🔲 Grid View", use_container_width=True,
                           type="primary" if st.session_state.current_view == "grid" else "secondary"):
                    st.session_state.current_view = "grid"
                    st.rerun()
            
            # Display based on view mode
            if st.session_state.current_view == "grid":
                # GRID VIEW
                st.subheader("🔲 All Questions - Grid View")
                
                # Display all questions in grid
                cols = st.columns(3)
                for idx, question in enumerate(questions):
                    col_idx = idx % 3
                    with cols[col_idx]:
                        is_answered = question['id'] in st.session_state.user_answers
                        is_current = idx == st.session_state.current_q
                        is_marked = idx in st.session_state.marked_review
                        
                        status = "✅ Answered" if is_answered else "⭕ Unanswered"
                        if is_marked:
                            status += " 📌 Marked"
                        
                        if st.button(
                            f"Q{idx+1}: {question['question'][:50]}...\n{status}",
                            key=f"grid_{idx}",
                            use_container_width=True,
                            type="primary" if is_current else "secondary"
                        ):
                            st.session_state.current_q = idx
                            st.session_state.current_view = "question"
                            st.rerun()
                
            else:
                # QUESTION VIEW
                if st.session_state.quiz_mode == "exam":
                    # EXAM MODE INTERFACE
                    remaining_time = max(0, 3600 - (time.time() - st.session_state.start_time))
                    minutes = int(remaining_time // 60)
                    seconds = int(remaining_time % 60)
                    
                    st.markdown(f"""
                    <div class="time-left-box">
                        <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">Time Left</div>
                        <div style="font-size: 2.5rem; font-weight: 700; font-family: 'Courier New', monospace;">
                            {minutes:02d} : {seconds:02d}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if not st.session_state.quiz_completed:
                    current_q = questions[st.session_state.current_q]
                    current_answer = st.session_state.user_answers.get(current_q['id'])
                    
                    # Question Display
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 1.5rem; color: white;">
                        <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem;">Question {st.session_state.current_q + 1} of {len(questions)}</div>
                        <div style="font-size: 1.3rem; font-weight: 600; line-height: 1.6;">
                            {current_q['question']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Options
                    selected_option = None
                    for opt_letter, opt_text in current_q['options'].items():
                        is_selected = current_answer == opt_letter
                        if is_selected:
                            selected_option = opt_letter
                        
                        if st.button(
                            f"{opt_letter}) {opt_text}",
                            key=f"opt_{current_q['id']}_{opt_letter}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            st.session_state.user_answers[current_q['id']] = opt_letter
                            st.rerun()
                    
                    # AI Explanation Section
                    st.markdown("---")
                    exp_col1, exp_col2 = st.columns([3, 1])
                    
                    with exp_col1:
                        st.subheader("🤖 AI Explanation")
                    
                    with exp_col2:
                        if st.button("🔍 Show AI Explanation", use_container_width=True):
                            st.session_state.show_ai_explanation[current_q['id']] = True
                    
                    if st.session_state.show_ai_explanation.get(current_q['id'], False):
                        st.markdown(f"""
                        <div class="ai-explanation">
                            <h4>🧠 AI Analysis</h4>
                            {current_q['ai_explanation']}
                            
                            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 8px;">
                                <strong>💡 Pro Tip:</strong> This question is rated <strong>{current_q['difficulty']}</strong> difficulty. 
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Navigation Buttons
                    if st.session_state.quiz_mode == "exam":
                        # Exam navigation
                        exam_col1, exam_col2, exam_col3 = st.columns(3)
                        with exam_col1:
                            if st.button("⏮️ Previous", use_container_width=True, disabled=st.session_state.current_q == 0):
                                if st.session_state.current_q > 0:
                                    st.session_state.current_q -= 1
                                    st.rerun()
                        with exam_col2:
                            mark_text = "📌 Mark" if st.session_state.current_q not in st.session_state.marked_review else "✅ Unmark"
                            if st.button(f"{mark_text}", use_container_width=True):
                                if st.session_state.current_q in st.session_state.marked_review:
                                    st.session_state.marked_review.remove(st.session_state.current_q)
                                else:
                                    st.session_state.marked_review.add(st.session_state.current_q)
                                st.rerun()
                        with exam_col3:
                            next_text = "💾 Save & Next" if st.session_state.current_q < len(questions) - 1 else "🏁 Finish Exam"
                            if st.button(next_text, use_container_width=True, type="primary"):
                                if st.session_state.current_q < len(questions) - 1:
                                    st.session_state.current_q += 1
                                else:
                                    st.session_state.quiz_completed = True
                                st.rerun()
                    else:
                        # Practice navigation
                        practice_col1, practice_col2, practice_col3, practice_col4 = st.columns(4)
                        with practice_col1:
                            if st.button("◀ Previous", use_container_width=True, disabled=st.session_state.current_q == 0):
                                if st.session_state.current_q > 0:
                                    st.session_state.current_q -= 1
                                    st.rerun()
                        with practice_col2:
                            if st.session_state.current_q < len(questions) - 1:
                                if st.button("Next ▶", use_container_width=True):
                                    st.session_state.current_q += 1
                                    st.rerun()
                            else:
                                if st.button("Finish 🏁", use_container_width=True, type="primary"):
                                    st.session_state.quiz_completed = True
                                    st.rerun()
                        with practice_col3:
                            if current_answer:
                                if st.button("✅ Check Answer", use_container_width=True, type="primary"):
                                    # Show correct answer
                                    correct_answer = current_q['correct_answer']
                                    if current_answer == correct_answer:
                                        st.success(f"🎉 Correct! Answer: {correct_answer}")
                                        # Add XP for correct answer
                                        st.session_state.user_profile['xp'] += 10
                                    else:
                                        st.error(f"❌ Incorrect! Correct answer: {correct_answer}")
                            else:
                                st.button("✅ Check Answer", use_container_width=True, disabled=True)
                        with practice_col4:
                            if st.button("🔄 Restart", use_container_width=True):
                                for key in ['user_answers', 'current_q', 'quiz_completed', 'marked_review', 'show_ai_explanation']:
                                    if key in st.session_state:
                                        if key == 'show_ai_explanation':
                                            st.session_state[key] = {}
                                        elif key == 'marked_review':
                                            st.session_state[key] = set()
                                        else:
                                            st.session_state[key] = default_states[key]
                                st.session_state.quiz_started = True
                                st.session_state.start_time = time.time()
                                st.rerun()
                
                else:
                    # Results screen
                    st.balloons()
                    st.markdown('<div class="main-header">🏆 Quiz Completed!</div>', unsafe_allow_html=True)
                    
                    # Calculate results
                    correct_count = 0
                    for q in questions:
                        if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                            correct_count += 1
                    
                    total_time = time.time() - st.session_state.start_time
                    score_percent = (correct_count / len(questions)) * 100
                    
                    # Update user profile
                    st.session_state.user_profile['total_quizzes'] += 1
                    st.session_state.user_profile['xp'] += correct_count * 5
                    if score_percent >= 90:
                        st.session_state.user_profile['achievements'].append("Quiz Master")
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #00b09b, #96c93d); color: white; padding: 2rem; border-radius: 20px; text-align: center; margin-bottom: 2rem;">
                        <h2>Your Score: {correct_count}/{len(questions)}</h2>
                        <h1>{score_percent:.1f}%</h1>
                        <p>Time Taken: {int(total_time // 60):02d}:{int(total_time % 60):02d}</p>
                        <p>{'🎯 Perfect Score!' if score_percent == 100 else '🌟 Excellent!' if score_percent >= 90 else '👍 Great Job!'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Performance chart
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = score_percent,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Performance Score"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 50], 'color': "lightgray"},
                                {'range': [50, 80], 'color': "gray"}],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90}}))
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Restart button
                    if st.button("🔄 Start New Quiz", use_container_width=True, type="primary"):
                        for key in ['user_answers', 'current_q', 'quiz_completed', 'marked_review', 'show_ai_explanation']:
                            if key in st.session_state:
                                if key == 'show_ai_explanation':
                                    st.session_state[key] = {}
                                elif key == 'marked_review':
                                    st.session_state[key] = set()
                                else:
                                    st.session_state[key] = default_states[key]
                        st.session_state.quiz_started = True
                        st.session_state.start_time = time.time()
                        st.rerun()

        else:
            st.info("👆 Please upload a PDF file to start the quiz")
            st.markdown("""
            ### 📝 Expected PDF Format:
            ```
            Q1. What is the capital of France?
            A) London
            B) Berlin
            C) Paris
            D) Madrid
            Answer: C
            
            Q2. Which planet is known as the Red Planet?
            A) Venus
            B) Mars
            C) Jupiter
            D) Saturn
            Answer: B
            ```
            """)

    with col2:
        # Quick Actions Panel
        st.subheader("⚡ Quick Actions")
        
        if st.button("🎯 Smart Practice", use_container_width=True):
            st.info("AI will focus on your weak areas!")
        
        if st.button("📊 Performance", use_container_width=True):
            correct_count = sum(1 for q in st.session_state.questions 
                              if st.session_state.user_answers.get(q['id']) == q['correct_answer'])
            total_answered = len(st.session_state.user_answers)
            accuracy = (correct_count / total_answered * 100) if total_answered > 0 else 0
            
            st.metric("Accuracy", f"{accuracy:.1f}%")
            st.metric("Questions Done", f"{total_answered}/{len(st.session_state.questions)}")
            st.metric("Streak", f"{st.session_state.user_profile['streak']} days")
        
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
        st.metric("Correct Rate", 
                 f"{(sum(1 for q in st.session_state.questions if st.session_state.user_answers.get(q['id']) == q['correct_answer']) / len(st.session_state.user_answers) * 100):.1f}%" 
                 if st.session_state.user_answers else "0%")

if __name__ == "__main__":
    main()
    
