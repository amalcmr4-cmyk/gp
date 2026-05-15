import os
import json
import re
from google import genai
from google.genai import types
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import add_chat_suggestion, get_analysis
from dotenv import load_dotenv
from pathlib import Path


env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def extract_json(text: str):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return None
        return None


class BusinessInsightsGenerator:

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            print("GEMINI_API_KEY is not set in environment variables.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-2.5-flash"

    def prepare_business_context(self, analysis_result: Dict[str, Any]) -> str:

        if not analysis_result or analysis_result.get("basic_info", {}).get("total_rows", 0) == 0:
            return "No data available in the dataset."

        return f"""
BUSINESS DATA SUMMARY:

Basic Info:
- Rows: {analysis_result.get('basic_info', {}).get('total_rows', 0)}
- Columns: {analysis_result.get('basic_info', {}).get('total_columns', 0)}

Numeric Statistics:
{json.dumps(analysis_result.get('numeric_statistics', {}), indent=2, ensure_ascii=False)}

Correlations:
{json.dumps(analysis_result.get('correlation', {}), indent=2, ensure_ascii=False)}

Data Quality:
- Completeness: {analysis_result.get('data_quality', {}).get('completeness_percentage', 0)}%
"""

    def generate_structured_prompt(self, context: str, lang: str = "en") -> str:
        lang_instruction = ""
        if lang == "ar":
            lang_instruction = "\nCRITICAL INSTRUCTION: You MUST translate and write ALL the generated JSON values in the ARABIC language.\n"
            
        return f"""
You are a senior business analyst.

Analyze the business data below and return ONLY valid JSON.{lang_instruction}

Return this exact structure:

{{
  "summary": "",
  "pricing_strategy": "",
  "growth_opportunities": "",
  "customer_strategy": "",
  "risk_alerts": "",
  "global_comparison": "",
  "forecast_message": "",
  "chart_suggestion": ""
}}

Chart selection rules:
- histogram: Use for distribution analysis
- bar: Use for category comparisons
- line: Use for time-based trends
- pie: Use for percentage breakdown (less than 6 categories)
- scatter: Use for relationships between two numeric variables

Rules:
- If no time-based column exists, set forecast_message to:
  "No time-based data detected for forecast"
- Return only valid JSON.
- Do NOT include explanations outside JSON.

Business Data:
{context}
"""

    def generate_comprehensive_insights(
        self,
        analysis_result: Dict[str, Any],
        db: Session,
        file_id: str,
        lang: str = "en"
    ) -> Dict[str, Any]:

        try:
            if not self.client:
                return {"error": "Gemini client not initialized. Check API key."}

            context = self.prepare_business_context(analysis_result)

            if context.startswith("No data"):
                return {"message": "No data available to generate business insights."}

            prompt = self.generate_structured_prompt(context, lang)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json"
                )
            )

            raw_text = response.text

            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            insights_data = extract_json(clean_text)

            #fallback if parsing failed
            if not insights_data:
                insights_data = {
                    "summary": "AI response parsing failed.",
                    "pricing_strategy": "",
                    "growth_opportunities": "",
                    "customer_strategy": "",
                    "risk_alerts": "",
                    "global_comparison": "",
                    "forecast_message": "No time-based data detected for forecast",
                    "chart_suggestion": "bar"
                }

            #ensure all required keys exist
            required_keys = [
                "summary",
                "pricing_strategy",
                "growth_opportunities",
                "customer_strategy",
                "risk_alerts",
                "global_comparison",
                "forecast_message",
                "chart_suggestion"
            ]

            for key in required_keys:
                if key not in insights_data:
                    insights_data[key] = ""

            #validate chart type
            allowed_charts = ["bar", "line", "pie", "scatter", "histogram"]

            if insights_data.get("chart_suggestion") not in allowed_charts:
                insights_data["chart_suggestion"] = "bar"

            insights = {
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
                "business_insights": insights_data,
                "disclaimer": "AI-generated insights based on your data and general market knowledge"
            }

            insights_json = json.dumps(insights, ensure_ascii=False)

            # Look up the actual Analyze record ID (integer) for this file_id
            analyses = get_analysis(db, file_id)
            if analyses:
                add_chat_suggestion(
                    db=db,
                    analyze_id=analyses[0].id,
                    suggestion_text=insights_json
                )

            return insights

        except Exception as e:
            return {
                "error": f"Failed to generate insights: {str(e)}",
                "suggestion": "Please check your Gemini API key and try again."
            }

    def chat_with_data(self, analysis_result: Dict[str, Any], user_message: str) -> str:
        try:
            if not self.client:
                return "عذراً، خدمة الذكاء الاصطناعي غير مفعلة حالياً."

            context = self.prepare_business_context(analysis_result)

            if context.startswith("No data"):
                return "لا توجد بيانات متاحة للإجابة على سؤالك."

            prompt = f"""
You are a helpful and professional data assistant for the DataWizard platform.
Answer the user's question based ONLY on the following Business Data Summary.
Do not invent information that is not present in the data.
If the data does not contain the answer, politely state that you cannot find the answer in the current dataset.
Respond in the same language as the user's question (e.g., if the user asks in Arabic, respond in Arabic).

BUSINESS DATA SUMMARY:
{context}

USER QUESTION: {user_message}

ANSWER:
"""
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3
                )
            )

            return response.text.strip()

        except Exception as e:
            print(f"Chat error: {str(e)}")
            return "عذراً، حدث خطأ أثناء معالجة سؤالك. يرجى المحاولة مرة أخرى."


async def get_business_insights(
    file_id: str,
    db: Session,
    analysis_result: Dict[str, Any] = None,
    lang: str = "en"
):

    if not analysis_result:
        from app.services.analysis_service import advanced_analysis_service
        analysis_result = await advanced_analysis_service(file_id, db)

    generator = BusinessInsightsGenerator()

    return generator.generate_comprehensive_insights(
        analysis_result,
        db,
        file_id,
        lang
    )

async def process_chat_message(
    file_id: str,
    message: str,
    db: Session,
):
    from app.services.analysis_service import advanced_analysis_service
    # Re-fetch analysis to get context
    analysis_result = await advanced_analysis_service(file_id, db)
    
    generator = BusinessInsightsGenerator()
    response_text = generator.chat_with_data(analysis_result, message)
    
    return {"response": response_text}


async def translate_texts(texts: dict, target_lang: str = "ar"):
    """Translate a dict of insight texts to the target language using Gemini.
    This does NOT re-analyze data — it simply translates the existing text."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[translate_texts] ERROR: GEMINI_API_KEY not set")
        return {"error": "Gemini API key not configured."}

    # Filter out empty texts
    clean_texts = {k: v for k, v in texts.items() if v and str(v).strip()}
    if not clean_texts:
        return {"error": "No texts provided to translate."}

    print(f"[translate_texts] Translating {len(clean_texts)} cards to '{target_lang}'")

    client = genai.Client(api_key=api_key)
    lang_name = "Arabic" if target_lang == "ar" else "English"

    # Build compact JSON input so Gemini knows exactly what to translate
    texts_json = json.dumps(clean_texts, ensure_ascii=False, indent=2)

    prompt = f"""You are a professional translator.

Translate EVERY value in the JSON below to {lang_name}. Keep the keys exactly as they are.
Return ONLY valid JSON, no explanation, no markdown, no code fences.

Input JSON:
{texts_json}

Translated JSON:"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1)
        )

        raw = response.text.strip()
        print(f"[translate_texts] Raw response (first 300 chars): {raw[:300]}")

        # Strip markdown code fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()

        translated = extract_json(raw)

        if not translated:
            print(f"[translate_texts] ERROR: Could not parse JSON from response: {raw[:200]}")
            return {"error": "Failed to parse translation response.", "raw": raw[:200]}

        print(f"[translate_texts] SUCCESS: translated {len(translated)} keys")
        return {"translated": translated, "target_lang": target_lang}

    except Exception as e:
        print(f"[translate_texts] EXCEPTION: {str(e)}")
        return {"error": f"Translation failed: {str(e)}"}
