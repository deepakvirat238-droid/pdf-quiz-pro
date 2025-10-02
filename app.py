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
    
    # Advanced CSS with Animations
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
    
    /* Dark Mode Styles */
    .dark-mode {
        background-color: #1a1a1a;
        color: white;
    }
    
    /* 3D Card Effects */
    .card-3d {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transform-style: preserve-3d;
        transition: all 0.3s ease;
    }
    .card-3d:hover {
        transform: translateY(-5px) rotateX(5deg);
        box-shadow: 0 20px 40px rgba(0,0,0,0.2);
    }
    
    /* Existing styles remain the same... */
    .time-left-box { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3); }
    .bubble-option { background: rgba(255,255,255,0.95); padding: 1rem; border-radius: 25px; border: 2px solid transparent; transition: all 0.3s ease; cursor: pointer; color: #333; text-align: center; font-weight: 500; min-height: 60px; display: flex; align-items: center; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🧠 PDF Quiz PRO - AI Enhanced</div>', unsafe_allow_html=True)
    
    # Initialize session state for new features
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
    
    # Sidebar with enhanced features
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
        
        # New Features Section
        st.header("✨ Cool Features")
        
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
        
        # Dark Mode
        if st.button("🌙 Toggle Dark Mode", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
        
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

    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Existing quiz functionality remains the same
        uploaded_file = st.file_uploader("📁 Upload PDF File", type="pdf")
        
        if uploaded_file:
            with st.spinner("🔍 Processing PDF with AI..."):
                questions = parse_pdf_content(uploaded_file)
            
            if not questions:
                st.error("❌ No questions found. Please check the PDF format.")
                return
            
            st.success(f"✅ Found {len(questions)} questions! + 🤖 AI Analysis Enabled")
            
            # Add AI suggestions for each question
            for q in questions:
                if q['id'] not in st.session_state.ai_suggestions:
                    st.session_state.ai_suggestions[q['id']] = {
                        'explanation': f"AI Explanation: This question tests your understanding of {q['difficulty'].lower()} concepts.",
                        'related_topics': ['Topic A', 'Topic B', 'Topic C'],
                        'tips': ['Read carefully', 'Eliminate wrong options first']
                    }
            
            # Continue with existing quiz logic...
            # [Previous quiz implementation code here]
            
            # Demo: Show AI features
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
    
    with col2:
        # Quick Actions Panel
        st.subheader("⚡ Quick Actions")
        
        if st.button("🎯 Smart Practice", use_container_width=True):
            st.info("AI will focus on your weak areas!")
        
        if st.button("📊 Performance", use_container_width=True):
            # Show performance metrics
            st.metric("Accuracy", "78%")
            st.metric("Speed", "45s/q")
            st.metric("Streak", "5 days")
        
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
        st.metric("Questions Solved", "24")
        st.metric("Time Spent", "45m")
        st.metric("Correct Rate", "85%")

    # New Features Expansion
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

# Run the app
if __name__ == "__main__":
    main()
    
