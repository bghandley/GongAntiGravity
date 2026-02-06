import google.generativeai as genai
import json
import re

# Config
DEFAULT_MODEL_NAME = "gemini-2.5-flash"
BRAND_NAME = "Rachael Peffer"
COACHING_STYLE = "timeless strategy, quiet power, direct feedback"
COACH_TONE = "calm, concise, direct, quiet power; no hype"

def get_gemini_client(api_key, model_name=DEFAULT_MODEL_NAME):
    """Configures and returns the Gemini client."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name) 
    return model

def _strip_code_fences(text):
    if not text:
        return ""
    cleaned = text.strip()
    cleaned = re.sub(r"```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    return cleaned.strip()

def _extract_first_json(text):
    cleaned = _strip_code_fences(text)
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        return match.group(0).strip(), cleaned
    return cleaned.strip(), cleaned

def _ensure_analysis_keys(data):
    if not isinstance(data, dict):
        return data

    defaults = {
        "summary": "",
        "topics": [],
        "sentiment_score": 0,
        "strengths": [],
        "improvements": [],
        "coaching_tips": [],
        "client_intent": {
            "occasion": "",
            "date_mentions": [],
            "decision_timing": "",
            "primary_motivation": ""
        },
        "consult_scorecard": {
            "authority_and_leadership": 0,
            "aesthetic_alignment": 0,
            "constraint_setting": 0,
            "package_pricing_clarity": 0,
            "hesitation_handling": 0,
            "decision_safety": 0,
            "next_steps_locked": 0
        },
        "conversion_risks": [],
        "missed_questions": [],
        "recommended_micro_scripts": [],
        "timeline": []
    }

    for key, value in defaults.items():
        if key not in data or data[key] is None:
            data[key] = value

    if not isinstance(data.get("client_intent"), dict):
        data["client_intent"] = defaults["client_intent"]
    else:
        for key, value in defaults["client_intent"].items():
            if key not in data["client_intent"] or data["client_intent"][key] is None:
                data["client_intent"][key] = value

    if not isinstance(data.get("consult_scorecard"), dict):
        data["consult_scorecard"] = defaults["consult_scorecard"]
    else:
        for key, value in defaults["consult_scorecard"].items():
            if key not in data["consult_scorecard"] or data["consult_scorecard"][key] is None:
                data["consult_scorecard"][key] = value

    if not isinstance(data.get("topics"), list):
        data["topics"] = defaults["topics"]
    if not isinstance(data.get("strengths"), list):
        data["strengths"] = defaults["strengths"]
    if not isinstance(data.get("improvements"), list):
        data["improvements"] = defaults["improvements"]
    if not isinstance(data.get("coaching_tips"), list):
        data["coaching_tips"] = defaults["coaching_tips"]
    if not isinstance(data.get("conversion_risks"), list):
        data["conversion_risks"] = defaults["conversion_risks"]
    if not isinstance(data.get("missed_questions"), list):
        data["missed_questions"] = defaults["missed_questions"]
    if not isinstance(data.get("recommended_micro_scripts"), list):
        data["recommended_micro_scripts"] = defaults["recommended_micro_scripts"]
    if not isinstance(data.get("timeline"), list):
        data["timeline"] = defaults["timeline"]

    return data

def _question_supported_by_transcript(transcript, question):
    if not transcript or not question:
        return False
    transcript_lower = transcript.lower()
    words = re.findall(r"[a-z0-9']+", question.lower())
    stopwords = {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "did", "do", "does",
        "for", "from", "had", "has", "have", "he", "her", "hers", "him", "his", "i",
        "if", "in", "is", "it", "its", "me", "my", "not", "of", "on", "or", "our",
        "she", "so", "that", "the", "their", "them", "they", "this", "to", "was",
        "we", "were", "what", "when", "where", "who", "why", "will", "with", "you",
        "your"
    }
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    if not keywords:
        return True
    return any(keyword in transcript_lower for keyword in keywords)

def analyze_call(api_key, transcript_text, model_name=DEFAULT_MODEL_NAME):
    """
    Sends the transcript to Gemini and requests a structured analysis.
    Returns a dictionary aligned to a bridal beauty consultation lens.
    """
    model = get_gemini_client(api_key, model_name)
    
    prompt = f"""
    You are an expert Bridal Beauty Consultation Coach for {BRAND_NAME}.
    Analyze the following bridal beauty consultation transcript between an artist and a bride/client.
    Use {COACHING_STYLE}. Voice should be {COACH_TONE}.

    Provide output in valid JSON ONLY with the following keys:
    - "summary": A concise 2-3 sentence summary of the consultation.
    - "topics": A list of main topics discussed.
    - "sentiment_score": An integer from 0 (negative) to 100 (positive) representing the overall consult sentiment.
    - "strengths": A list of strings detailing what the artist did well.
    - "improvements": A list of strings detailing areas for improvement, missed questions, or decision friction.
    - "coaching_tips": A list of actionable advice for the artist.
    - "client_intent": An object with:
        - "occasion": The occasion (e.g., wedding, elopement, rehearsal dinner) or "unknown".
        - "date_mentions": A list of any dates as mentioned.
        - "decision_timing": When the client plans to decide (or "unknown").
        - "primary_motivation": The main stated motivation (or "unknown").
    - "consult_scorecard": An object with 0-10 ratings for:
        - "authority_and_leadership"
        - "aesthetic_alignment"
        - "constraint_setting"
        - "package_pricing_clarity"
        - "hesitation_handling"
        - "decision_safety"
        - "next_steps_locked"
    - "conversion_risks": A list of objects, each with:
        - "label": Short risk label.
        - "severity": "low", "medium", or "high".
        - "evidence": Short quote or paraphrase tied to hesitations or decision friction.
        - "timestamp": Time string from transcript or null.
    - "missed_questions": A list of missed consultation questions. Use ONLY from:
        ["skin type", "inspiration/photos", "schedule", "party size", "budget range", "decision process", "trial expectations"]
    - "recommended_micro_scripts": A list of objects with:
        - "moment": Situation or timestamp.
        - "script": 1-2 sentence micro-script.
    - "timeline": A list of objects, each with:
        - "timestamp": The specific time string (e.g. "00:05:30" or "05:30") from the transcript where this event occurred.
        - "type": One of "rapport", "authority", "alignment", "pricing", "hesitation", "decision", "next_step".
        - "description": Short description of the event.

    Transcript:
    {transcript_text}
    """
    
    try:
        response = model.generate_content(prompt)
        text_response = response.text if hasattr(response, "text") else str(response)
        json_text, cleaned = _extract_first_json(text_response)
        data = json.loads(json_text)
        return _ensure_analysis_keys(data)
    except Exception as e:
        return {
            "error": f"{e}",
            "raw_response": text_response if "text_response" in locals() else ""
        }

def chat_with_coach(api_key, model_name, transcript, history, user_input):
    """
    Handles a chat turn with the AI coach.
    history: List of dicts [{"role": "user", "parts": ["..."]}, ...]
    """
    model = get_gemini_client(api_key, model_name)

    if not _question_supported_by_transcript(transcript, user_input):
        return "That isn't in the transcript."

    history_lines = []
    if history:
        for msg in history:
            role = msg.get("role")
            content = msg.get("content")
            if not content and isinstance(msg.get("parts"), list) and msg["parts"]:
                content = msg["parts"][0]
            if not content:
                continue
            if role == "user":
                history_lines.append(f"User: {content}")
            elif role == "assistant":
                history_lines.append(f"Coach: {content}")

    if user_input:
        if not history_lines or not history_lines[-1].startswith("User:"):
            history_lines.append(f"User: {user_input}")
        else:
            last_user = history[-1].get("content") if history else None
            if last_user != user_input:
                history_lines.append(f"User: {user_input}")

    conversation = "\n".join(history_lines).strip()

    system_context = f"""
    You are a Bridal Beauty Consultation Coach for {BRAND_NAME}.
    Style: {COACHING_STYLE}. Tone: {COACH_TONE}.
    Answer ONLY from the transcript provided. If the answer is not in the transcript, say: "That isn't in the transcript."
    Keep replies concise and direct.

    Transcript:
    {transcript}

    Conversation so far:
    {conversation}

    Coach response:
    """

    response = model.generate_content(system_context)
    return response.text
