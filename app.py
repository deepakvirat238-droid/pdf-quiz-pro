import streamlit as st
import pdfplumber
import re

def parse_pdf_content(pdf_file):
    questions = []
    
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    
    question_blocks = re.split(r'Q\d+\.', text)
    
    for i, block in enumerate(question_blocks[1:], 1):
        try:
            question_match = re.search(r'^(.*?)(?=A\)|Answer:)', block, re.DOTALL)
            if not question_match: continue
            
            question_text = question_match.group(1).strip()
            
            options = {}
            # 4-5 options support (A-E)
            option_matches = re.findall(r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|Answer:|$)', block)
            for opt_letter, opt_text in option_matches:
                options[opt_letter] = opt_text.strip()
            
            # Correct answer A-E
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
    st.set_page_config(page_title="PDF Quiz PRO", page_icon="🚀")
    st.title("🚀 PDF Quiz PRO")
    st.markdown("Advanced PDF Quiz with 4-5 options support!")
    
    with st.expander("📋 Expected Format (4-5 Options)"):
        st.code("""
Q1. What is the capital of France?
A) London
B) Berlin  
C) Paris
D) Madrid
E) Rome
Answer: C
        """)
    
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file:
        questions = parse_pdf_content(uploaded_file)
        
        if not questions:
            st.error("No questions found. Check format.")
            return
        
        st.success(f"Found {len(questions)} questions!")
        
        if 'user_answers' not in st.session_state:
            st.session_state.user_answers = {}
        if 'current_q' not in st.session_state:
            st.session_state.current_q = 0
        if 'show_answer' not in st.session_state:
            st.session_state.show_answer = {}
        
        # Navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("◀ Previous") and st.session_state.current_q > 0:
                st.session_state.current_q -= 1
                st.rerun()
        with col3:
            if st.session_state.current_q < len(questions)-1:
                if st.button("Next ▶"):
                    st.session_state.current_q += 1
                    st.rerun()
            else:
                if st.button("Finish 🏁"):
                    # Calculate score
                    correct = 0
                    for q in questions:
                        if st.session_state.user_answers.get(q['id']) == q['correct_answer']:
                            correct += 1
                    st.session_state.score = correct
                    st.session_state.quiz_completed = True
        
        # Current question
        q = questions[st.session_state.current_q]
        st.subheader(f"Q{st.session_state.current_q+1}. {q['question']}")
        
        user_answer = st.radio(
            "Select your answer:",
            options=list(q['options'].keys()),
            format_func=lambda x: f"{x}) {q['options'][x]}",
            key=f"q_{q['id']}"
        )
        
        st.session_state.user_answers[q['id']] = user_answer
        
        # Check Answer Button
        if st.button("Check Answer ✅", key=f"check_{q['id']}"):
            st.session_state.show_answer[q['id']] = True
        
        # Show answer if checked
        if st.session_state.show_answer.get(q['id']):
            if user_answer == q['correct_answer']:
                st.success("🎉 Correct! Well done!")
            else:
                st.error(f"❌ Incorrect! Correct answer is {q['correct_answer']}) {q['options'][q['correct_answer']]}")
        
        # Progress
        st.progress((st.session_state.current_q + 1) / len(questions))
        st.write(f"Progress: {st.session_state.current_q + 1}/{len(questions)}")
        
        # Show results if completed
        if hasattr(st.session_state, 'quiz_completed') and st.session_state.quiz_completed:
            st.balloons()
            st.success(f"🎉 Your Score: {st.session_state.score}/{len(questions)}")
            
            if st.button("🔄 Restart Quiz"):
                for key in ['user_answers', 'current_q', 'show_answer', 'quiz_completed', 'score']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()
