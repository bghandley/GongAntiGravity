def calculate_metrics(transcript_text):
    """
    Calculates basic metrics from the text.
    """
    words = transcript_text.split()
    word_count = len(words)
    
    # Average speaking rate (approx 130-150 words per minute)
    # This is a rough estimation since we don't have audio length in pure text
    estimated_duration_minutes = round(word_count / 140, 2)
    
    return {
        "word_count": word_count,
        "estimated_duration_mins": estimated_duration_minutes
    }
