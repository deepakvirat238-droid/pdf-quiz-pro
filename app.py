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
    
    # ✅ DEBUG CODE START - Yeh add karna hai
    st.subheader("🔍 DEBUG INFORMATION")
    st.write("### 📊 Text Extraction Summary")
    st.write(f"**Total text length:** {len(text)} characters")
    st.write(f"**First 500 characters:**")
    st.code(text[:500] if text else "No text extracted")
    
    st.write("### 🔍 Pattern Matching Analysis")
    
    # Check for question patterns
    question_patterns = [
        r'Q\d+\.',
        r'Question\s*\d+',
        r'\d+\.\s*[A-Z]'
    ]
    
    for pattern in question_patterns:
        matches = re.findall(pattern, text)
        if matches:
            st.write(f"**Pattern `{pattern}` found:** {len(matches)} matches")
            st.write(f"Matches: {matches[:5]}")  # First 5 matches
    
    # Check for answer patterns
    answer_matches = re.findall(r'Answer:\s*[A-E]', text, re.IGNORECASE)
    st.write(f"**Answer patterns found:** {len(answer_matches)}")
    if answer_matches:
        st.write(f"Answer matches: {answer_matches[:5]}")
    
    # Original parsing logic
    question_blocks = re.split(r'Q\d+\.', text)
    st.write(f"**Question blocks after splitting:** {len(question_blocks)}")
    
    for i, block in enumerate(question_blocks[1:], 1):
        try:
            st.write(f"--- Processing Block {i} ---")
            
            question_match = re.search(r'^(.*?)(?=A\)|Answer:)', block, re.DOTALL)
            if not question_match: 
                st.write("❌ No question match in this block")
                st.code(f"Block content: {block[:200]}...")
                continue
            
            question_text = question_match.group(1).strip()
            st.write(f"✅ Question found: {question_text[:50]}...")
            
            options = {}
            option_matches = re.findall(r'([A-E])\)\s*(.*?)(?=\s*[A-E]\)|Answer:|$)', block)
            st.write(f"Options found: {option_matches}")
            
            for opt_letter, opt_text in option_matches:
                options[opt_letter] = opt_text.strip()
            
            answer_match = re.search(r'Answer:\s*([A-E])', block)
            if not answer_match: 
                st.write("❌ No answer found in this block")
                continue
            
            correct_answer = answer_match.group(1)
            st.write(f"✅ Correct answer: {correct_answer}")
            
            questions.append({
                "id": i,
                "question": question_text,
                "options": options,
                "correct_answer": correct_answer
            })
            
            st.success(f"✅ Question {i} parsed successfully!")
            
        except Exception as e:
            st.error(f"Error in block {i}: {str(e)}")
            continue
    
    st.write("### 📋 FINAL RESULT")
    st.write(f"**Total questions parsed:** {len(questions)}")
    
    return questions

def main():
    st.set_page_config(
        page_title="PDF Quiz PRO - DEBUG", 
        page_icon="🐛",
        layout="wide"
    )
    
    st.markdown('<div style="color: red; font-size: 2rem;">🔧 DEBUG MODE ACTIVE</div>', unsafe_allow_html=True)
    
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
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🚀 PDF Quiz PRO - DEBUG</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Debugging PDF Parsing Issues</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📁 Upload PDF File for Debugging", type="pdf")
    
    if uploaded_file:
        st.warning("🔍 Debug information will show below. Check what's being extracted from your PDF.")
        
        with st.spinner("🔍 Processing PDF with DEBUG mode..."):
            questions = parse_pdf_content(uploaded_file)
        
        if not questions:
            st.error("❌ No questions could be parsed. Check the debug info above to see what's wrong.")
        else:
            st.success(f"✅ Successfully parsed {len(questions)} questions!")
            
            # Show parsed questions
            st.subheader("📖 Parsed Questions Preview")
            for i, q in enumerate(questions[:3]):  # Show first 3
                st.write(f"**Q{q['id']}:** {q['question'][:100]}...")
                st.write(f"**Options:** {q['options']}")
                st.write(f"**Correct:** {q['correct_answer']}")
                st.write("---")

if __name__ == "__main__":
    main()
