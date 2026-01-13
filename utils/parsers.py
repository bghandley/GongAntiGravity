import re

def parse_txt(content: str) -> str:
    """Simply returns the content of a text file."""
    return content

def parse_vtt(content: str) -> str:
    """
    Parses a VTT file content and extracts the spoken text.
    Removes headers, timestamps, and metadata.
    """
    lines = content.splitlines()
    text_content = []
    
    # Simple state machine or regex could work. 
    # VTT typically has "WEBVTT" header, then blocks with timestamps.
    # 00:00:00.000 --> 00:00:05.000
    # Hello world
    
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{3}\s-->\s\d{2}:\d{2}:\d{2}\.\d{3}')
    
    for line in lines:
        if "WEBVTT" in line:
            continue
        if line.strip() == "":
            continue
        if timestamp_pattern.match(line):
            continue
        # Also skip simple numbers often found in SRT/VTT as block IDs
        if line.strip().isdigit():
            continue
            
        text_content.append(line.strip())
        
    return " ".join(text_content)

def parse_srt(content: str) -> str:
    """
    Parses an SRT file content and extracts the spoken text.
    Removes block numbers and timestamps.
    """
    lines = content.splitlines()
    text_content = []
    
    # Files often look like:
    # 1
    # 00:00:01,000 --> 00:00:04,000
    # Hello
    
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2},\d{3}\s-->\s\d{2}:\d{2}:\d{2},\d{3}')
    
    for line in lines:
        if line.strip() == "":
            continue
        if line.strip().isdigit():
            continue
        if timestamp_pattern.match(line):
            continue
            
        text_content.append(line.strip())
        
    return " ".join(text_content)

def parse_transcript(file_obj, file_extension):
    """
    Main entry point for parsing. 
    file_obj is the UploadedFile object from Streamlit.
    Returns: (clean_text, raw_content)
    """
    # Streamlit UploadedFile.read() returns bytes, need to decode
    content = file_obj.read().decode("utf-8")
    
    clean_text = ""
    if file_extension == 'txt':
        clean_text = parse_txt(content)
    elif file_extension == 'vtt':
        clean_text = parse_vtt(content)
    elif file_extension == 'srt':
        clean_text = parse_srt(content)
    else:
        raise ValueError("Unsupported file format")
        
    return clean_text, content
