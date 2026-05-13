import os
from dotenv import load_dotenv
from pathlib import Path
from huggingface_hub import InferenceClient

load_dotenv(Path('c:/Users/Dell/Desktop/gpp/backend/.env'))
client = InferenceClient(api_key=os.getenv('HUGGINGFACE_API_KEY'))

prompt = """
You are a senior business analyst.

Analyze the business data below and return ONLY valid JSON.

Return this exact structure:

{
  "summary": "",
  "pricing_strategy": "",
  "growth_opportunities": "",
  "customer_strategy": "",
  "risk_alerts": "",
  "global_comparison": "",
  "forecast_message": "",
  "chart_suggestion": ""
}

Business Data:
Rows: 100
Columns: 5
Completeness: 100%
"""
res = client.chat_completion(messages=[{'role': 'user', 'content': prompt}], model='meta-llama/Meta-Llama-3-8B-Instruct', max_tokens=1500, temperature=0.4)
print("RAW TEXT:")
print(res.choices[0].message.content)
