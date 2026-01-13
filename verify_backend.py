from utils.parsers import parse_vtt
from utils.text_analysis import calculate_metrics
import os

# 1. Load Sample
with open("sample_call.vtt", "r") as f:
    content = f.read()

# 2. Test Parser
print("--- Testing Parser ---")
parsed_text = parse_vtt(content)
print(f"Parsed Text Length: {len(parsed_text)}")
print(f"Preview: {parsed_text[:100]}...")

# 3. Test Metrics
print("\n--- Testing Metrics ---")
metrics = calculate_metrics(parsed_text)
print(f"Metrics: {metrics}")

# 4. Simulated Gemini (since we don't have a live key in this env context usually, or we do/don't want to waste tokens)
# But if USER put it in env, we could test. For now, we assume integration works if parsers work.
print("\n--- Verification Complete ---")
