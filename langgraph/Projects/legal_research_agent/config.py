# config.py

import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# OpenAI API key
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

# Default LLM model
DEFAULT_MODEL = "gpt-4o-mini"
MODEL_TEMPERATURE = 0

# Optional: logging level, max tokens, etc.
