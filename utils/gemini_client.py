import google.generativeai as genai
import os
import json

def get_gemini_client(api_key, model_name='gemini-2.5-flash'):
    """Configures and returns the Gemini client."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name) 
    return model

def analyze_call(api_key, transcript_text, model_name='gemini-2.5-flash'):
    """
    Sends the transcript to Gemini and requests a structured analysis.
    Returns a dictionary with 'summary', 'strengths', 'improvements', 'sentiment'.
    """
    model = get_gemini_client(api_key, model_name)
    
    prompt = f"""
    You are an expert Sales Coach and Manager, similar to the insights provided by Gong.io.
    Analyze the following sales call transcript.
    
    Provide the output in valid JSON format with the following keys:
    - "summary": A concise 2-3 sentence summary of the call.
    - "topics": A list of main topics discussed.
    - "sentiment_score": An integer from 0 (negative) to 100 (positive) representing the overall call sentiment.
    - "strengths": A list of strings detailing what the sales rep did well.
    - "improvements": A list of strings detailing areas for improvement or missed opportunities.
    - "coaching_tips": A list of actionable advice for the rep.
    - "timeline": A list of objects, each with:
        - "timestamp": The specific time string (e.g. "00:05:30" or "05:30") from the transcript where this event occurred.
        - "sentiment": "positive" or "negative".
        - "description": Short description of the event (e.g. "Good empathy", "Missed upsell").
    
    Transcript:
    {transcript_text}
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean up code blocks if Gemini returns markdown ```json ... ```
        text_response = response.text
        if "```json" in text_response:
            text_response = text_response.replace("```json", "").replace("```", "")
        
        return json.loads(text_response)
    except Exception as e:
        return {"error": str(e)}

def chat_with_coach(api_key, model_name, transcript, history, user_input):
    """
    Handles a chat turn with the AI coach.
    history: List of dicts [{"role": "user", "parts": ["..."]}, ...]
    """
    model = get_gemini_client(api_key, model_name)
    
    # We construct a chat session. 
    # To keep it simple and stateless for Streamlit, we might just use generate_content with a consolidated prompt 
    # OR use start_chat if we were persisting the object properly. 
    # For MVP Streamlit, sending the context each time is safer.
    
    system_context = f"""
    You are a helpful Sales Coach. The user is asking questions about a specific sales call transcript.
    Answer their questions based ONLY on the transcript provided below.
    Be encouraging but honest.
    
    Transcript:
    {transcript}
    """
    
    # Convert simple history to Gemini format if needed, 
    # but for a single-turn completion with context, we can just append.
    # Let's try to use the chat object for better multi-turn handling if possible.
    
    chat = model.start_chat(history=[])
    
    # Prime with context
    chat.send_message(system_context)
    
    # Replay history (simplified)
    for msg in history:
        # Streamlit history is typically {"role": "user"/"assistant", "content": "..."}
        if msg["role"] == "user":
            chat.send_message(msg["content"])
        elif msg["role"] == "assistant":
            # We can't easily force the model's history without hacking, 
            # so for this simple implementation, we might just trust the LLM with the full context in the prompt 
            # or rely on the fact that we are starting a fresh chat each time for the "logic" but that's inefficient.
            # OPTION B: Just send the latest question with the transcript context.
            pass
            
    response = chat.send_message(user_input)
    return response.text
