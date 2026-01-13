# Gong Clone - Sales Call Analyzer

A Streamlit application that uses Google Gemini to analyze sales call transcripts and provide coaching feedback, similar to Gong.io.

## Features
- **Transcript Upload**: Supports `.txt`, `.vtt`, and `.srt` files.
- **AI Analysis**: Uses Google Gemini (gemini-2.5-flash) to identify strengths, weaknesses, and coaching tips.
- **Metrics**: Sentiment scoring, word counts, and estimated duration.
- **Dashboard**: "Gong-style" interface for reviewing calls.

## Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd GongAntiGravity
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**:
   ```bash
   streamlit run app.py
   ```

## Usage
1. Open the app in your browser (usually `http://localhost:8501`).
2. Enter your **Google Gemini API Key** in the sidebar settings.
3. Go to the "Upload" tab and drop a transcript file.
4. Click "Analyze Transcript" and wait for the results.
5. View insights in the "Dashboard" tab.

## Deployment on Streamlit Cloud
1. Push this code to GitHub.
2. Login to [Streamlit Cloud](https://streamlit.io/cloud).
3. Connect your GitHub repo.
4. In the "Advanced Settings" of the deployment, add your secrets:
   - `GOOGLE_API_KEY` = "your-api-key-here" (Optional, or users can enter it in the UI).
5. Click **Deploy**.
