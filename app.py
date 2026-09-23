"""
Campus EcoTrack AI - Smart Campus Waste Management & Circular Economy Assistant
Author: Senior Full-Stack Python and AI Engineer
"""

import streamlit as st
import json
import os
from PIL import Image
from google import genai
from google.genai import types

# ==========================================
# PAGE CONFIGURATION & CUSTOM CSS (THEMING)
# ==========================================
st.set_page_config(
    page_title="Campus EcoTrack AI",
    page_icon="♻️",
    layout="centered",
    initial_sidebar_state="expanded"
)
# --- कस्टम डार्क CSS जोड़ना ---
st.markdown("""
    <style>
    /* 1. पूरे ऐप का बैकग्राउंड और टेक्स्ट का रंग */
    .stApp {
        background-color: #0b132b !important;
        color: #f8fafc !important;
    }

    /* 2. साइडबार का बैकग्राउंड */
    [data-testid="stSidebar"] {
        background-color: #1c2541 !important;
    }

    /* 3. मुख्य हेडिंग और सब-टाइटल का रंग */
    h1, h2, h3, h4, p, label {
        color: #ffffff !important;
    }

    /* 4. बटन्स की स्टाइलिंग (ग्रीन थीम) */
    .stButton > button {
        background-color: #22c55e !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: 0.3s !important;
    }
    .stButton > button:hover {
        background-color: #16a34a !important;
        transform: scale(1.02);
    }

    /* 5. रिजल्ट कार्ड्स (डार्क कार्ड्स) */
    .card {
        background-color: #1e293b !important;
        border-radius: 10px !important;
        padding: 16px !important;
        margin-bottom: 15px !important;
        border-left: 5px solid #22c55e !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* 6. इनपुट बॉक्स का रंग */
    input, textarea {
        background-color: #1e293b !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
<div class="card">
    <h4>🌱 रीसाइक्लिंग सुझाव:</h4>
    <p>इस कचरे को कंपोस्ट पिट में डालकर जैविक खाद बनाई जा सकती है।</p>
</div>
""", unsafe_allow_html=True)

# Green Sustainability Theme CSS
st.markdown("""
<style>
    /* Main Background & Text */
    .stApp {
        background-color: #f4fdf4;
    }
    h1, h2, h3 {
        color: #2e7d32 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Metric Cards / Info Blocks */
    .eco-card {
        background-color: #ffffff;
        border-left: 5px solid #4caf50;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .eco-card-title {
        color: #2e7d32;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .eco-card-text {
        color: #333333;
        font-size: 1rem;
    }
    /* Danger/Warning Card for Hazardous Waste */
    .eco-card-danger {
        background-color: #fff5f5;
        border-left: 5px solid #d32f2f;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .eco-card-danger-title {
        color: #d32f2f;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# SYSTEM PROMPT & LLM CONFIGURATION
# ==========================================
SYSTEM_INSTRUCTION = """
You are "EcoTrack AI", an intelligent Campus Waste Management and Circular Economy Assistant.
Your objective is to analyze any input (waste name in text OR an uploaded image) and deliver actionable recycling, upcycling, and smart disposal instructions tailored for a college campus environment.

RULES & BEHAVIOR:
1. LANGUAGE FLEXIBILITY:
   - Accept input in Hindi, English, or Hinglish.
   - If an image is provided, accurately detect the waste item.
   - Output language MUST be clear, easy-to-read Hindi with key technical/standard English terms in brackets for professional context.

2. DOMAIN CONTEXT (CAMPUS ECOSYSTEM):
   - Prioritize on-campus circularity: Can the cafeteria turn this into compost? Can the electronics lab reuse it? Can fine-arts students use it?
   - Categorize strictly into: "गीला कचरा (Wet/Organic)", "सूखा कचरा (Dry/Recyclable)", "ई-वेस्ट (E-Waste)", or "खतरनाक/विशेष कचरा (Hazardous/Sanitary)".

3. STRICT OUTPUT FORMAT:
   Return ONLY a valid JSON object. Do not include markdown code block formatting (never wrap in ```json or ```). Do not include any conversational pleasantries.
   
Use this exact JSON schema:
{
  "item_identified": "पहचाने गए कचरे का नाम (Identified Item Name)",
  "category": "कचरे का प्रकार (Wet / Dry / E-Waste / Hazardous)",
  "correct_bin": "सही डस्टबिन (जैसे: हरा बिन / नीला बिन / ई-वेस्ट बॉक्स)",
  "campus_reuse_solution": "कैंपस के अंदर तुरंत उपयोग का तरीका (खाद, लैब रीयूज़, आर्ट प्रोजेक्ट)",
  "upcycling_product_idea": "इससे बाहर या इंडस्ट्री में क्या नया प्रोडक्ट बनाया जा सकता है",
  "safe_handling_note": "सावधानी या सुरक्षित निस्तारण निर्देश (Safe Disposal Tip)"
}
"""

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_api_key():
    # 1. पहले Streamlit secrets में चेक करें (बिना क्रैश हुए)
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    
    # 2. अगर secrets नहीं है, तो साइडबार में इनपुट बॉक्स दिखाएं
    api_key = st.sidebar.text_input("Gemini API Key डालें:", type="password")
    return api_key

def clean_and_parse_json(raw_text: str) -> dict:
    """Safely strips markdown formatting and parses JSON."""
    try:
        # Clean potential markdown ticks just in case the LLM disobeys the prompt
        cleaned_text = raw_text.strip()
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.split("\n", 1)[-1]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text.rsplit("\n", 1)[0]
        cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI response into JSON. Raw response was: \n{raw_text}\nError: {str(e)}")

def analyze_waste(api_key: str, text_input: str, image_input: Image.Image = None) -> dict:
    """Calls Gemini API to analyze waste and return structured data."""
    try:
        client = genai.Client(api_key=api_key)
        
        # Build contents array
        contents = []
        if image_input:
            contents.append(image_input)
        if text_input:
            contents.append(text_input)
        else:
            contents.append("Identify this waste item and provide recycling instructions as per the system prompt.")
            
        # Call Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2, # Low temperature for more deterministic/structured JSON output
                response_mime_type="application/json" # Enforce JSON return
            )
        )
        
        # Parse the JSON response safely
        return clean_and_parse_json(response.text)
        
    except Exception as e:
        raise Exception(f"API Error: {str(e)}")

# ==========================================
# UI COMPONENTS & MAIN APP LOGIC
# ==========================================
def render_results(data: dict):
    """Renders the parsed JSON data into beautiful UI blocks."""
    st.markdown("---")
    st.markdown(f"## ♻️ Analysis Complete: {data.get('item_identified', 'Unknown Item')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="eco-card">
            <div class="eco-card-title">🗑️ Category</div>
            <div class="eco-card-text">{data.get('category', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
        <div class="eco-card">
            <div class="eco-card-title">✅ Correct Bin</div>
            <div class="eco-card-text">{data.get('correct_bin', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="eco-card">
        <div class="eco-card-title">🏫 Campus Reuse Solution</div>
        <div class="eco-card-text">{data.get('campus_reuse_solution', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="eco-card">
        <div class="eco-card-title">🏭 Upcycling Product Idea</div>
        <div class="eco-card-text">{data.get('upcycling_product_idea', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)

    # Highlight Safe Handling Note in red if hazardous, else normal warning
    is_hazardous = "खतरनाक" in data.get('category', '') or "Hazardous" in data.get('category', '')
    card_class = "eco-card-danger" if is_hazardous else "eco-card"
    title_class = "eco-card-danger-title" if is_hazardous else "eco-card-title"
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="{title_class}">⚠️ Safe Handling Note</div>
        <div class="eco-card-text">{data.get('safe_handling_note', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.title("🌱 Campus EcoTrack AI")
    st.markdown("Your intelligent **Campus Waste Management** and **Circular Economy** Assistant.")
    
    # Initialize API Key
    api_key = get_api_key()
    
    # Input Mechanism
    st.markdown("### How would you like to identify the waste?")
    tab1, tab2, tab3 = st.tabs(["📝 Text Input", "📷 Live Camera", "📂 Upload Image"])
    
    waste_text = ""
    waste_image = None
    
    with tab1:
        text_val = st.text_input("Describe the waste (Hindi, English, or Hinglish):", placeholder="e.g. purani battery, खराब कीबोर्ड, plastic wrappers")
        if text_val:
            waste_text = text_val
            
    with tab2:
        cam_val = st.camera_input("Take a picture of the waste")
        if cam_val:
            try:
                waste_image = Image.open(cam_val)
                st.image(waste_image, caption="Captured Image", width=300)
            except Exception as e:
                st.error(f"Error processing camera image: {str(e)}")
                
    with tab3:
        upload_val = st.file_uploader("Upload an image of the waste", type=["jpg", "jpeg", "png", "webp"])
        if upload_val:
            try:
                waste_image = Image.open(upload_val)
                st.image(waste_image, caption="Uploaded Image", width=300)
            except Exception as e:
                st.error(f"Error reading uploaded file: {str(e)}")

    # Analyze Button
    analyze_clicked = st.button("🔍 Analyze & Guide", use_container_width=True, type="primary")
    
    if analyze_clicked:
        if not api_key:
            st.error("Please provide a valid Google Gemini API Key in the sidebar or via secrets.")
            st.stop()
            
        if not waste_text and not waste_image:
            st.warning("Please provide either text description or an image of the waste to analyze.")
            st.stop()
            
        with st.spinner("EcoTrack AI is analyzing the waste..."):
            try:
                # Call AI processing logic
                result_data = analyze_waste(api_key, text_input=waste_text, image_input=waste_image)
                
                # Render UI
                render_results(result_data)
                st.balloons() # Small celebration for successful eco-tracking!
                
            except Exception as e:
                st.error("An error occurred during analysis. Please try again.")
                st.error(f"Developer Details: {str(e)}")

if __name__ == "__main__":
    main()
