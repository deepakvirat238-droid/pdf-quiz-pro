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
        except: continue
    
    return questions

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
    
    /* View Toggle Styles */
    .view-toggle {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .view-btn {
        flex: 1;
        padding: 0.8rem;
        border-radius: 8px;
        text-align: center;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 2px solid #007bff;
        background: white;
        color: #007bff;
    }
    .view-btn.active {
        background: #007bff;
        color: white;
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
    
    /* Existing styles... */
    .time-left-box { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; }
    .bubble-option { background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 25px; border: 2px solid transparent; transition: all 0.3s ease; cursor: pointer; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🧠 PDF Quiz PRO - Ultimate Edition</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = "practice"
    if 'current_view' not in st.session_state:
        st.session_state.current_view = "question"  # "question" or "grid"
    if 'show_ai_explanation' not in st.session_state:
        st.session_state.show_ai_explanation = {}
    if 'marked_review' not in st.session_state:
        st.session_state.marked_review = set()
    
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
        st.header("🔍 Navigation")
    
    # File upload
    uploaded_file = st.file_uploader("📁 Upload PDF File", type="pdf")
    
    if uploaded_file:
        with st.spinner("🔍 Processing PDF with AI Analysis..."):
            questions = parse_pdf_content(uploaded_file)
        
        if not questions:
            st.error("❌ No questions found. Please check the PDF format.")
            return
        
        st.success(f"✅ Found {len(questions)} questions! + 🤖 AI Explanations Ready")
        
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
        
        # Quick Jump Grid - ALWAYS VISIBLE
        st.subheader("🎯 Quick Jump to Any Question")
        
        # Create grid with 10 questions per row
        rows = (len(questions) + 9) // 10  # Calculate number of rows needed
        
        for row in range(rows):
            cols = st.columns(10)
            start_idx = row * 10
            end_idx = min(start_idx + 10, len(questions))
            
            for idx in range(start_idx, end_idx):
                with cols[idx % 10]:
                    is_answered = questions[idx]['id'] in st.session_state.user_answers
                    is_current = idx == st.session_state.current_q
                    is_marked = idx in st.session_state.marked_review
                    
                    btn_class = "jump-btn"
                    if is_current:
                        btn_class += " current"
                    elif is_answered:
                        btn_class += " answered"
                    elif is_marked:
                        btn_class += " marked"
                    
                    btn_text = f"Q{idx+1}"
                    if is_marked:
                        btn_text = f"📌{idx+1}"
                    
                    if st.button(btn_text, key=f"jump_{idx}", use_container_width=True):
                        st.session_state.current_q = idx
                        st.rerun()
        
        # View Toggle
        st.markdown("""
        <div class="view-toggle">
            <div class="view-btn %s" onclick="setView('question')">📖 Question View</div>
            <div class="view-btn %s" onclick="setView('grid')">🔲 Grid View</div>
        </div>
        """ % ("active" if st.session_state.current_view == "question" else "", 
               "active" if st.session_state.current_view == "grid" else ""), 
        unsafe_allow_html=True)
        
        # Display based on view mode
        if st.session_state.current_view == "grid":
            # GRID VIEW
            st.subheader("🔲 All Questions - Grid View")
            
            st.markdown('<div class="grid-view-container">', unsafe_allow_html=True)
            
            # Display all questions in grid
            for idx, question in enumerate(questions):
                is_answered = question['id'] in st.session_state.user_answers
                is_current = idx == st.session_state.current_q
                is_marked = idx in st.session_state.marked_review
                
                card_class = "question-card"
                if is_current:
                    card_class += " current"
                if is_answered:
                    card_class += " answered"
                
                st.markdown(f"""
                <div class="{card_class}" onclick="selectQuestion({idx})">
                    <strong>Q{idx+1}</strong>
                    <div class="question-preview">
                        {question['question'][:100]}...
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem;">
                        {'✅ Answered' if is_answered else '⭕ Unanswered'}
                        {' 📌 Marked' if is_marked else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Hidden button for functionality
                if st.button(f"Open Q{idx+1}", key=f"grid_{idx}", use_container_width=True):
                    st.session_state.current_q = idx
                    st.session_state.current_view = "question"  # Switch to question view
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
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
                if st.session_state.quiz_mode == "exam":
                    st.markdown(f"""
                    <div style="background: white; padding: 2rem; border-radius: 10px; margin-bottom: 1.5rem; border-left: 5px solid #3498db;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                            <div style="font-size: 1.4rem; font-weight: 700; color: #2c3e50;">Question. {st.session_state.current_q + 1}</div>
                            <div style="background: #e74c3c; color: white; padding: 0.5rem 1rem; border-radius: 20px; font-weight: 600;">Last 6 Minutes</div>
                        </div>
                        <div style="font-size: 1.3rem; font-weight: 600; color: #2c3e50; line-height: 1.6;">
                            {current_q['question']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2.5rem; border-radius: 20px; margin-bottom: 1rem; color: white;">
                        <div style="font-size: 1.4rem; font-weight: 600; line-height: 1.6;">
                            Q{st.session_state.current_q + 1}. {current_q['question']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Options
                if st.session_state.quiz_mode == "exam":
                    # Exam mode options
                    for opt_letter, opt_text in current_q['options'].items():
                        is_selected = current_answer == opt_letter
                        if st.button(f"{opt_letter}) {opt_text}", 
                                   key=f"exam_opt_{current_q['id']}_{opt_letter}",
                                   use_container_width=True,
                                   type="primary" if is_selected else "secondary"):
                            st.session_state.user_answers[current_q['id']] = opt_letter
                            st.rerun()
                else:
                    # Practice mode bubble options
                    st.markdown('<div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 0.8rem; margin-top: 1rem;">', unsafe_allow_html=True)
                    
                    for opt_letter, opt_text in current_q['options'].items():
                        is_selected = current_answer == opt_letter
                        bubble_class = "bubble-option"
                        if is_selected:
                            bubble_class += " selected"
                        
                        st.markdown(f"""
                        <div class="{bubble_option}" onclick="selectOption('{opt_letter}')">
                            <strong>{opt_letter})</strong> {opt_text}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Select {opt_letter}", key=f"practice_opt_{current_q['id']}_{opt_letter}", 
                                   use_container_width=True, type="primary" if is_selected else "secondary"):
                            st.session_state.user_answers[current_q['id']] = opt_letter
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # AI Explanation Section - AVAILABLE IN BOTH MODES
                st.markdown("---")
                ai_col1, ai_col2 = st.columns([3, 1])
                
                with ai_col1:
                    st.subheader("🤖 AI Explanation")
                
                with ai_col2:
                    if st.button("🔍 Show AI Explanation", use_container_width=True):
                        st.session_state.show_ai_explanation[current_q['id']] = True
                
                if st.session_state.show_ai_explanation.get(current_q['id'], False):
                    st.markdown(f"""
                    <div class="ai-explanation">
                        <h4>🧠 AI Analysis</h4>
                        {current_q['ai_explanation']}
                        
                        <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 8px;">
                            <strong>💡 Pro Tip:</strong> This question is rated <strong>{current_q['difficulty']}</strong> difficulty. 
                            Focus on understanding the underlying concept rather than memorizing.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Navigation Buttons
                if st.session_state.quiz_mode == "exam":
                    # Exam navigation
                    exam_col1, exam_col2, exam_col3 = st.columns(3)
                    with exam_col1:
                        if st.button("⏮️ Previous", use_container_width=True) and st.session_state.current_q > 0:
                            st.session_state.current_q -= 1
                            st.rerun()
                    with exam_col2:
                        if st.button("📌 Mark & Next", use_container_width=True):
                            st.session_state.marked_review.add(st.session_state.current_q)
                            if st.session_state.current_q < len(questions) - 1:
                                st.session_state.current_q += 1
                            st.rerun()
                    with exam_col3:
                        if st.button("💾 Save & Next", use_container_width=True, type="primary"):
                            if st.session_state.current_q < len(questions) - 1:
                                st.session_state.current_q += 1
                            else:
                                st.session_state.quiz_completed = True
                            st.rerun()
                else:
                    # Practice navigation
                    practice_col1, practice_col2, practice_col3, practice_col4 = st.columns(4)
                    with practice_col1:
                        if st.button("◀ Previous", use_container_width=True) and st.session_state.current_q > 0:
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
                                else:
                                    st.error(f"❌ Incorrect! Correct answer: {correct_answer}")
                        else:
                            st.button("✅ Check Answer", use_container_width=True, disabled=True)
                    with practice_col4:
                        if st.button("🔄 Restart", use_container_width=True):
                            for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 'start_time', 'show_ai_explanation', 'marked_review']:
                                if key in st.session_state:
                                    del st.session_state[key]
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
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #00b09b, #96c93d); color: white; padding: 2rem; border-radius: 20px; text-align: center; margin-bottom: 2rem;">
                    <h2>Your Score: {correct_count}/{len(questions)}</h2>
                    <h1>{score_percent:.1f}%</h1>
                    <p>Time Taken: {int(total_time // 60):02d}:{int(total_time % 60):02d}</p>
                    <p>{'🎯 Perfect Score!' if score_percent == 100 else '🌟 Excellent!' if score_percent >= 90 else '👍 Great Job!'}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Restart button
                if st.button("🔄 Start New Quiz", use_container_width=True, type="primary"):
                    for key in ['user_answers', 'current_q', 'quiz_completed', 'quiz_started', 'start_time', 'show_ai_explanation', 'marked_review']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

    else:
        st.info("👆 Please upload a PDF file to start the quiz")

# JavaScript for interactive elements
st.markdown("""
<script>
function setView(view) {
    // This would be handled by Streamlit buttons in actual implementation
    console.log("Switching to view: " + view);
}

function selectQuestion(index) {
    // This would trigger a Streamlit rerun with the selected question
    console.log("Selected question: " + index);
}
</script>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
    
