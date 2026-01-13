import streamlit as st
import os
import plotly.express as px
import pandas as pd
from utils.parsers import parse_transcript
from utils.gemini_client import analyze_call, chat_with_coach
from utils.text_analysis import calculate_metrics
from utils.report_generator import generate_pdf_report

# Page Config
st.set_page_config(
    page_title="Gong Clone - AI Sales Coach",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for "Gong-like" feel
st.markdown("""
<style>
    .main {
        background-color: #f9f9f9;
        color: #333333;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #6C5CE7;
    }
    h1 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #2D3436;
    }
    h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #636e72;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://Placehold.co/200x60/6C5CE7/ffffff?text=Gong+Clone", use_column_width=True)
    st.title("Settings")
    
    # Navigation added here
    page_selection = st.radio("Go to", ["Upload", "Dashboard", "Coach Chat", "Reference"])
    st.divider()

    
    # API Key Handling (Secrets > Manual)
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
        st.success("API Key loaded from secrets", icon="🔒")
    else:
        api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API Key here.")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            st.success("API Key saved!", icon="✅")
        else:
            st.warning("Enter API Key to enable AI.", icon="⚠️")
    
    st.divider()
    
    # Model Selection
    # Mapping display names to API names (making assumptions on API keys based on standard Gemini versioning)
    model_options = {
        "Gemini 3 Pro (Preview)": "gemini-3.0-pro-preview", 
        "Gemini 3 Flash (Preview)": "gemini-3.0-flash-preview", 
        "Gemini 2.5 Pro": "gemini-2.5-pro", 
        "Gemini 2.5 Flash": "gemini-2.5-flash",
        "Gemini 2.5 Flash-Lite": "gemini-2.5-flash-lite"
    }
    
    selected_display_name = st.selectbox(
        "Select AI Model",
        list(model_options.keys()),
        index=3, # Default to 2.5 Flash
        help="Choose the specific Gemini model version."
    )
    model_name = model_options[selected_display_name]
        
    st.divider()
    if page_selection == "Upload":
        st.info("Upload a transcript to get started.")

# Main Layout
st.title("🎙️ Sales Call Analyzer")

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = None
if 'raw_transcript_text' not in st.session_state:
    st.session_state.raw_transcript_text = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

# Conditional Rendering based on Sidebar Selection

if page_selection == "Upload":
    st.markdown("Upload your call transcripts to get AI-powered insights, feedback, and analytics.")
    st.header("Upload Transcript")
    uploaded_file = st.file_uploader("Choose a file (txt, vtt, srt)", type=['txt', 'vtt', 'srt'])
    
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split('.')[-1]
        
        if st.button("Analyze Transcript"):
            if not os.environ.get("GOOGLE_API_KEY"):
                st.error("Please enter your Gemini API Key in the sidebar settings first.")
            else:
                with st.spinner(f"Parsing and analyzing with {selected_display_name}..."):
                    try:
                        # 1. Parse
                        clean_text, raw_text = parse_transcript(uploaded_file, file_ext)
                        st.session_state.transcript_text = clean_text
                        st.session_state.raw_transcript_text = raw_text
                        
                        # 2. Text Metrics (use clean text)
                        mets = calculate_metrics(clean_text)
                        st.session_state.metrics = mets
                        
                        # 3. AI Analysis (use RAW text for timestamps)
                        analysis = analyze_call(os.environ["GOOGLE_API_KEY"], raw_text, model_name=model_name)
                        
                        if "error" in analysis:
                            st.error(f"Gemini API Error: {analysis['error']}")
                        else:
                            st.session_state.analysis_result = analysis
                            st.success("Analysis Complete! Go to the 'Dashboard' page.")
                            
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

elif page_selection == "Dashboard":
    st.markdown("Detailed analytics and coaching feedback.")
    st.header("Call Analytics")
    
    if not st.session_state.analysis_result:
        st.info("Upload and analyze a transcript in the 'Upload' page to see insights here.")
    else:
        analy = st.session_state.analysis_result
        mets = st.session_state.metrics
        
        # Action Buttons (Report Download)
        col_dl, _ = st.columns([1, 4])
        with col_dl:
            # Generate PDF
            from utils.report_generator import generate_pdf_report
            pdf_data = generate_pdf_report(analy, mets)
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_data,
                file_name="coach_report.pdf",
                mime="application/pdf"
            )
        
        st.divider()
        
        # Summary Section
        st.subheader("📝 Executive Summary")
        st.write(analy.get("summary", "No summary available."))
        
        st.divider()
        
        # TIMELINE VISUALIZATION
        if "timeline" in analy and analy["timeline"]:
            st.subheader("⏳ Conversation Timeline")
            
            # Convert timeline data to DataFrame for Plotly
            timeline_data = analy["timeline"]
            df_timeline = pd.DataFrame(timeline_data)
            
            # Simple data cleaning to ensure we have columns
            if not df_timeline.empty and "timestamp" in df_timeline.columns:
                # Color mapping
                color_map = {"positive": "#00CC96", "negative": "#EF553B"}
                
                fig = px.scatter(
                    df_timeline, 
                    x="timestamp", 
                    y=[1] * len(df_timeline), # Dummy y-axis to put them in a line
                    color="sentiment",
                    color_discrete_map=color_map,
                    hover_data=["description"],
                    size=[10] * len(df_timeline), # Fixed size dots
                    title="Key Moments (Strengths vs Improvements)",
                    height=200
                )
                
                fig.update_yaxes(visible=False, showticklabels=False)
                fig.update_layout(
                    xaxis_title="Time", 
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend_title_text='Sentiment'
                )
                
                st.plotly_chart(fig, use_column_width=True)
            else:
                st.info("Timeline data found but could not be plotted.")
        
        st.divider()

        # Metrics Row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sentiment Score", f"{analy.get('sentiment_score', 'N/A')}/100")
        with col2:
            st.metric("Word Count", mets.get("word_count", 0))
        with col3:
            st.metric("Est. Duration", f"{mets.get('estimated_duration_mins', 0)} mins")
            
        st.divider()
        
        # FEEDBACK SECTION (The Core "Gong" Value)
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### 🟢 What Went Well")
            for item in analy.get("strengths", []):
                st.success(item, icon="✅")

        with c2:
            st.markdown("### 🟠 Areas for Improvement")
            for item in analy.get("improvements", []):
                st.warning(item, icon="⚠️")
                
        st.divider()
        
        # Coaching Tips
        st.subheader("💡 Coaching Tips")
        for tip in analy.get("coaching_tips", []):
            st.info(tip, icon="🎓")

        # Topics Visualization (Simple)
        if "topics" in analy:
            st.subheader("Topic Detected")
            st.write(", ".join(analy["topics"]))

elif page_selection == "Coach Chat":
    st.header("💬 Chat with AI Coach")
    if not st.session_state.raw_transcript_text:
         st.info("Please upload and analyze a transcript first.")
    else:
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Ask a question about this call (e.g., 'Was I empathetic?')"):
            # Add user message to state
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response_text = chat_with_coach(
                        os.environ["GOOGLE_API_KEY"], 
                        model_name,
                        st.session_state.raw_transcript_text, 
                        st.session_state.chat_messages, 
                        prompt
                    )
                    st.markdown(response_text)
            
            # Add assistant message to state
            st.session_state.chat_messages.append({"role": "assistant", "content": response_text})

elif page_selection == "Reference":
    st.header("Sales Playbook & Best Practices")
    st.markdown("""
    ### 🏆 Discovery Questions
    - "What is the biggest challenge you are facing right now?"
    - "How are you currently solving this problem?"
    
    ### 🛑 Objection Handling
    - **Price**: "Focus on ROI and value, not just cost."
    - **Timing**: "Ask what will change in 3 months vs now."
    """)

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit & Google Gemini")
