import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    print("Available models:")
    for model in genai.list_models():
        print(f"  - {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"    Supported methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
