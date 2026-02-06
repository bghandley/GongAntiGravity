"""
Bridal beauty consultation coach for Rachael Peffer.
Analyzes consultation transcripts with a bridal consult lens (alignment, pricing, hesitation handling, next steps).
Example usage: streamlit run app.py, then upload a transcript.
"""
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
    page_title="Bridal Beauty Consultation Coach",
    page_icon="B",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Rachael Peffer brand aesthetic (light + dark mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Source+Sans+3:wght@300;400;500;600&display=swap');

    :root {
        /* Brand Primary - Burnt Terracotta */
        --rp-terracotta: #BD4F3C;

        /* Brand Neutrals */
        --rp-charcoal: #1A1A1A;
        --rp-slate: #4A4A4A;
        --rp-white: #FFFFFF;
        --rp-border: #E0E0E0;
        --rp-ivory: #FAF7F4;
        --rp-card: #FFFFFF;
    }

    /* Dark mode overrides (OS-level) */
    @media (prefers-color-scheme: dark) {
        :root {
            --rp-terracotta: #D86A57;
            --rp-charcoal: #F3EEE9;
            --rp-slate: #D1C7C0;
            --rp-white: #0E0C0A;
            --rp-border: #2A2622;
            --rp-ivory: #12100E;
            --rp-card: #181512;
        }
    }

    /* Dark mode overrides (Streamlit theme) */
    html[data-theme="dark"], body[data-theme="dark"], .stApp[data-theme="dark"] {
        --rp-terracotta: #D86A57;
        --rp-charcoal: #F3EEE9;
        --rp-slate: #D1C7C0;
        --rp-white: #0E0C0A;
        --rp-border: #2A2622;
        --rp-ivory: #12100E;
        --rp-card: #181512;
    }

    .stApp {
        background-color: var(--rp-ivory);
        color: var(--rp-charcoal);
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
        color: var(--rp-terracotta);
        font-family: "Cormorant Garamond", serif;
    }

    h1, h2, h3, h4 {
        font-family: "Cormorant Garamond", serif;
        color: var(--rp-charcoal);
        letter-spacing: 0.3px;
    }

    p, li, label, textarea, input, .stMarkdown, .stText {
        font-family: "Source Sans 3", sans-serif;
        color: var(--rp-slate);
    }

    div[data-testid="stSidebar"] {
        background-color: var(--rp-white);
        border-right: 1px solid var(--rp-border);
    }

    .stButton > button {
        background-color: var(--rp-terracotta);
        color: var(--rp-white);
        border: 1px solid var(--rp-terracotta);
        border-radius: 6px;
        font-family: "Cormorant Garamond", serif;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #A64535;
        border-color: #A64535;
    }

    .stDownloadButton > button {
        background-color: transparent;
        color: var(--rp-slate);
        border: 1px solid var(--rp-border);
        border-radius: 6px;
        font-family: "Source Sans 3", sans-serif;
        font-weight: 500;
    }

    .css-1d391kg {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://Placehold.co/200x60/6C5CE7/ffffff?text=Rachael+Peffer", width=200)
    st.title("Settings")

    # Navigation added here
    page_selection = st.radio("Go to", ["Upload", "Dashboard", "Coach Chat", "Reference"])
    st.divider()

    # API Key Handling (Secrets > Manual)
    api_key_from_secrets = None
    secrets_paths = [
        os.path.expanduser("~/.streamlit/secrets.toml"),
        os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
    ]
    if any(os.path.exists(path) for path in secrets_paths):
        try:
            api_key_from_secrets = st.secrets.get("GOOGLE_API_KEY")
        except Exception:
            api_key_from_secrets = None

    if api_key_from_secrets:
        os.environ["GOOGLE_API_KEY"] = api_key_from_secrets
        st.success("API Key loaded from secrets")
    else:
        api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API Key here.")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            st.success("API Key saved!")
        else:
            st.warning("Enter API Key to enable AI.")

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
        st.info("Upload a consultation transcript to get started.")

# Main Layout
st.title("Bridal Beauty Consultation Analyzer - Rachael Peffer")

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = None
if "raw_transcript_text" not in st.session_state:
    st.session_state.raw_transcript_text = None
if "metrics" not in st.session_state:
    st.session_state.metrics = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Conditional Rendering based on Sidebar Selection

if page_selection == "Upload":
    st.markdown("Upload consultation transcripts to get AI-powered insights, feedback, and analytics.")
    st.header("Upload Transcript")
    uploaded_file = st.file_uploader("Choose a file (txt, vtt, srt)", type=["txt", "vtt", "srt"])

    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1]

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
    st.header("Consultation Analytics")

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
                label="Download PDF Report",
                data=pdf_data,
                file_name="coach_report.pdf",
                mime="application/pdf"
            )

        st.divider()

        # Summary Section
        st.subheader("Executive Summary")
        st.write(analy.get("summary", "No summary available."))

        st.divider()

        # TIMELINE VISUALIZATION
        if "timeline" in analy and analy["timeline"]:
            st.subheader("Conversation Timeline")

            # Convert timeline data to DataFrame for Plotly
            timeline_data = analy["timeline"]
            df_timeline = pd.DataFrame(timeline_data)

            # Simple data cleaning to ensure we have columns
            if not df_timeline.empty and "timestamp" in df_timeline.columns:
                # Color mapping
                type_color_map = {
                    "rapport": "#00A896",
                    "authority": "#457B9D",
                    "alignment": "#E9C46A",
                    "pricing": "#F4A261",
                    "hesitation": "#E76F51",
                    "decision": "#8E9AAF",
                    "next_step": "#264653"
                }
                sentiment_color_map = {"positive": "#00CC96", "negative": "#EF553B"}
                color_field = "type" if "type" in df_timeline.columns else "sentiment"
                color_map = type_color_map if color_field == "type" else sentiment_color_map

                fig = px.scatter(
                    df_timeline,
                    x="timestamp",
                    y=[1] * len(df_timeline), # Dummy y-axis to put them in a line
                    color=color_field,
                    color_discrete_map=color_map,
                    hover_data=["description"],
                    size=[10] * len(df_timeline), # Fixed size dots
                    title="Key Moments (Consultation Flow)",
                    height=200
                )

                fig.update_yaxes(visible=False, showticklabels=False)
                fig.update_layout(
                    xaxis_title="Time",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend_title_text="Moment Type" if color_field == "type" else "Sentiment"
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

        # FEEDBACK SECTION
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### What Went Well")
            for item in analy.get("strengths", []):
                st.success(item)

        with c2:
            st.markdown("### Areas for Improvement")
            for item in analy.get("improvements", []):
                st.warning(item)

        st.divider()

        # Coaching Tips
        st.subheader("Coaching Tips")
        for tip in analy.get("coaching_tips", []):
            st.info(tip)

        # Topics Visualization (Simple)
        if "topics" in analy:
            st.subheader("Topics Detected")
            st.write(", ".join(analy["topics"]))

elif page_selection == "Coach Chat":
    st.header("Chat with AI Coach")
    if not st.session_state.raw_transcript_text:
         st.info("Please upload and analyze a transcript first.")
    else:
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Ask a question about this consultation (e.g., 'Did I clarify the package?')"):
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
    st.header("Bridal Consultation Playbook")
    st.markdown("""
    ### Consultation Questions
    - "What is your wedding date, location, and ceremony timeline?"
    - "What is your skin type and coverage preference?"
    - "Do you have inspiration photos or a mood board?"
    - "How many people need services and what time is the ceremony?"
    - "What is your budget range for beauty services?"
    - "How do you plan to make the decision and by when?"
    - "What are your expectations for a trial?"

    ### Hesitation Handling
    - **Pricing**: "Name the package, anchor the value, and confirm fit."
    - **Timing**: "Clarify decision timing and explain how the date is held with a deposit."
    - **Aesthetic fit**: "Mirror their vision, then state your signature clearly."
    """)

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and Google Gemini")
