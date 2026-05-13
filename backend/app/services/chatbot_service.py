"""
DataWizard Chatbot Service — Powered by Google Gemini 2.5 Flash (Free Tier)
Provides advanced data analysis, prediction, and natural conversation.
Completely separate from the HuggingFace AI Insights service.
"""

import os
import json
import pandas as pd
import numpy as np
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pathlib import Path

from google import genai
from google.genai import types

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

UPLOAD_FOLDER = "uploaded_files"

def get_meaningful_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Return numeric columns excluding IDs, indices, and unstructured numbers."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    meaningful = []
    ignore_kws = ['id', 'index', 'idx', 'uuid', 'unnamed', 'row']
    for col in numeric_cols:
        col_lower = str(col).lower()
        # Ensure exact match or part of word boundary for 'id' to avoid dropping valid words
        # but a simple 'in' check is okay for standard datasets if we are careful.
        if col_lower in ['id', 'index', 'idx', 'uuid'] or 'unnamed' in col_lower or 'row_id' in col_lower or 'row id' in col_lower or col_lower.endswith('_id') or col_lower.endswith('id'):
            continue
        meaningful.append(col)
    return meaningful
# ═══════════════════════════════════════════════════════════
#  Statistical Prediction Engine
# ═══════════════════════════════════════════════════════════

class PredictionEngine:
    """Pre-computes statistical predictions so Gemini narrates real numbers."""

    @staticmethod
    def detect_time_column(df: pd.DataFrame) -> Optional[str]:
        DATE_KEYWORDS = ['date', 'time', 'year', 'month', 'day', 'timestamp', 'period']
        for col in df.columns:
            if any(kw in col.lower() for kw in DATE_KEYWORDS):
                try:
                    parsed = pd.to_datetime(df[col], errors='coerce')
                    if parsed.notna().sum() > 3:
                        return col
                except Exception:
                    pass
        return None

    @staticmethod
    def compute_trends(df: pd.DataFrame, time_col: str) -> Dict[str, Any]:
        """Compute linear trends for all numeric columns over the time axis."""
        results = {}
        try:
            df_sorted = df.copy()
            df_sorted[time_col] = pd.to_datetime(df_sorted[time_col], errors='coerce')
            df_sorted = df_sorted.dropna(subset=[time_col]).sort_values(time_col)
            numeric_cols = get_meaningful_numeric_columns(df_sorted)

            x = np.arange(len(df_sorted))
            for col in numeric_cols[:8]:
                y = df_sorted[col].values.astype(float)
                mask = ~np.isnan(y)
                if mask.sum() < 3:
                    continue
                xm, ym = x[mask], y[mask]
                slope, intercept = np.polyfit(xm, ym, 1)
                mean_val = float(np.mean(ym))
                growth_pct = (slope * len(xm)) / abs(mean_val) * 100 if mean_val != 0 else 0

                # Forecast next 3 periods
                future_x = np.array([len(xm), len(xm) + 1, len(xm) + 2])
                forecasts = (slope * future_x + intercept).tolist()

                results[col] = {
                    "slope": round(float(slope), 4),
                    "intercept": round(float(intercept), 4),
                    "total_growth_pct": round(float(growth_pct), 2),
                    "trend": "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable",
                    "current_mean": round(mean_val, 2),
                    "forecast_next_3": [round(f, 2) for f in forecasts],
                    "optimistic": [round(f * 1.15, 2) for f in forecasts],
                    "pessimistic": [round(f * 0.85, 2) for f in forecasts],
                }
        except Exception as e:
            results["_error"] = str(e)
        return results

    @staticmethod
    def detect_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
        """IQR-based anomaly detection for numeric columns."""
        results = {}
        numeric_cols = get_meaningful_numeric_columns(df)
        for col in numeric_cols[:10]:
            s = df[col].dropna()
            if len(s) < 5:
                continue
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = s[(s < lower) | (s > upper)]
            if len(outliers) > 0:
                results[col] = {
                    "count": int(len(outliers)),
                    "pct": round(len(outliers) / len(s) * 100, 2),
                    "lower_bound": round(float(lower), 2),
                    "upper_bound": round(float(upper), 2),
                    "examples": [round(float(v), 2) for v in outliers.head(5).values],
                }
        return results

    @staticmethod
    def what_if_analysis(df: pd.DataFrame, target_col: str, change_pct: float) -> Dict[str, Any]:
        """Estimate downstream impact of changing target_col by change_pct."""
        results = {"target": target_col, "change_pct": change_pct, "impacts": {}}
        numeric_cols = get_meaningful_numeric_columns(df)
        if target_col not in numeric_cols:
            return results

        corr = df[numeric_cols].corr()
        for col in numeric_cols:
            if col == target_col:
                continue
            r = corr.loc[target_col, col]
            if abs(r) > 0.3:
                estimated_impact = round(r * change_pct, 2)
                results["impacts"][col] = {
                    "correlation": round(float(r), 3),
                    "estimated_change_pct": estimated_impact,
                    "direction": "same direction" if r > 0 else "opposite direction",
                }
        return results

    @classmethod
    def build_prediction_context(cls, df: pd.DataFrame, user_msg: str) -> str:
        """Build prediction context only when the user is asking about predictions."""
        msg_lower = user_msg.lower()
        prediction_kws = ['predict', 'forecast', 'future', 'trend', 'growth',
                          'توقع', 'مستقبل', 'اتجاه', 'نمو', 'next quarter',
                          'next year', 'next month', 'projection', 'estimate']
        anomaly_kws = ['anomal', 'outlier', 'unusual', 'strange', 'شاذ', 'غريب']
        whatif_kws = ['what if', 'what-if', 'scenario', 'ماذا لو', 'سيناريو', 'increase by', 'decrease by']

        sections = []

        # Trend & Forecasting
        if any(kw in msg_lower for kw in prediction_kws):
            time_col = cls.detect_time_column(df)
            if time_col:
                trends = cls.compute_trends(df, time_col)
                if trends and "_error" not in trends:
                    sections.append("\n## PRE-COMPUTED TREND ANALYSIS (use these real numbers)")
                    for col, info in trends.items():
                        sections.append(f"### {col}")
                        sections.append(f"  - Trend: {info['trend']}, Growth: {info['total_growth_pct']}%")
                        sections.append(f"  - Current mean: {info['current_mean']}")
                        sections.append(f"  - Realistic forecast (next 3 periods): {info['forecast_next_3']}")
                        sections.append(f"  - Optimistic (+15%): {info['optimistic']}")
                        sections.append(f"  - Pessimistic (-15%): {info['pessimistic']}")
            else:
                sections.append("\n## NOTE: No time-series column detected. Predictions based on distributions only.")

        # Anomaly Detection
        if any(kw in msg_lower for kw in anomaly_kws):
            anomalies = cls.detect_anomalies(df)
            if anomalies:
                sections.append("\n## PRE-COMPUTED ANOMALY DETECTION (IQR method)")
                for col, info in anomalies.items():
                    sections.append(f"- **{col}**: {info['count']} outliers ({info['pct']}%), bounds=[{info['lower_bound']}, {info['upper_bound']}], examples: {info['examples']}")

        # What-If
        if any(kw in msg_lower for kw in whatif_kws):
            numeric_cols = get_meaningful_numeric_columns(df)
            if numeric_cols:
                target = numeric_cols[0]
                whatif = cls.what_if_analysis(df, target, 20.0)
                if whatif["impacts"]:
                    sections.append(f"\n## PRE-COMPUTED WHAT-IF: {target} changes by +20%")
                    for col, info in whatif["impacts"].items():
                        sections.append(f"- {col}: estimated {info['estimated_change_pct']}% change (correlation: {info['correlation']})")

        return "\n".join(sections)


# ═══════════════════════════════════════════════════════════
#  Gemini Chatbot
# ═══════════════════════════════════════════════════════════

class GeminiChatbot:
    """Advanced data analyst chatbot powered by Google Gemini."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = "gemini-2.5-flash"

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Chatbot] Failed to initialize Gemini client: {e}")
        else:
            print("[Chatbot] GEMINI_API_KEY not set — chatbot will be unavailable.")

    def _load_dataframe(self, file_id: str, db: Session) -> Optional[pd.DataFrame]:
        """Load the uploaded file into a DataFrame."""
        from app.database import get_file
        db_file = get_file(db, file_id)
        if not db_file:
            return None

        file_found = None
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(file_id + "_"):
                file_found = filename
                break

        if not file_found:
            return None

        file_path = os.path.join(UPLOAD_FOLDER, file_found)
        try:
            if file_found.endswith('.csv'):
                return pd.read_csv(file_path)
            elif file_found.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file_path)
        except Exception as e:
            print(f"[Chatbot] Error reading file: {e}")
        return None

    def _build_rich_context(self, df: pd.DataFrame) -> str:
        """Build a comprehensive data profile for the AI."""

        info_lines = []

        # Basic info
        info_lines.append(f"## Dataset Overview")
        info_lines.append(f"- **Rows**: {len(df)}")
        info_lines.append(f"- **Columns**: {len(df.columns)}")
        info_lines.append(f"- **Column Names**: {', '.join(df.columns.tolist())}")

        # Data types
        info_lines.append(f"\n## Column Types")
        for col in df.columns:
            dtype = str(df[col].dtype)
            nunique = df[col].nunique()
            nmissing = int(df[col].isna().sum())
            info_lines.append(f"- **{col}**: type={dtype}, unique={nunique}, missing={nmissing}")

        # Numeric statistics
        numeric_cols = get_meaningful_numeric_columns(df)
        if numeric_cols:
            info_lines.append(f"\n## Numeric Statistics")
            for col in numeric_cols:
                s = df[col].dropna()
                if len(s) > 0:
                    info_lines.append(f"### {col}")
                    info_lines.append(f"  - Mean: {s.mean():.4f}, Median: {s.median():.4f}")
                    info_lines.append(f"  - Min: {s.min():.4f}, Max: {s.max():.4f}")
                    info_lines.append(f"  - Std Dev: {s.std():.4f}")
                    info_lines.append(f"  - Q1: {s.quantile(0.25):.4f}, Q3: {s.quantile(0.75):.4f}")
                    if len(s) > 2:
                        skew = float(s.skew())
                        info_lines.append(f"  - Skewness: {skew:.4f} ({'right-skewed' if skew > 0.5 else 'left-skewed' if skew < -0.5 else 'approximately symmetric'})")

        # Correlations (top pairs)
        if len(numeric_cols) > 1:
            info_lines.append(f"\n## Top Correlations")
            corr = df[numeric_cols].corr()
            pairs = []
            for i, c1 in enumerate(numeric_cols):
                for j, c2 in enumerate(numeric_cols):
                    if i < j:
                        val = corr.loc[c1, c2]
                        if not np.isnan(val):
                            pairs.append((c1, c2, val))
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            for c1, c2, val in pairs[:10]:
                strength = "strong" if abs(val) > 0.7 else "moderate" if abs(val) > 0.4 else "weak"
                direction = "positive" if val > 0 else "negative"
                info_lines.append(f"- {c1} ↔ {c2}: {val:.3f} ({strength} {direction})")

        # Categorical columns — top values
        cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        if cat_cols:
            info_lines.append(f"\n## Categorical Columns")
            for col in cat_cols[:10]:
                top5 = df[col].value_counts().head(5)
                items = ", ".join([f"{k}: {v}" for k, v in top5.items()])
                info_lines.append(f"- **{col}** (top values): {items}")

        # Time-series detection
        DATE_KEYWORDS = ['date', 'time', 'year', 'month', 'day', 'timestamp', 'period']
        time_cols = [c for c in df.columns if any(kw in c.lower() for kw in DATE_KEYWORDS)]
        if time_cols:
            info_lines.append(f"\n## Time-Series Data Detected")
            info_lines.append(f"- Time columns: {', '.join(time_cols)}")
            for tc in time_cols[:2]:
                try:
                    parsed = pd.to_datetime(df[tc], errors='coerce')
                    valid = parsed.dropna()
                    if len(valid) > 1:
                        info_lines.append(f"  - {tc}: range from {valid.min()} to {valid.max()}")
                        for nc in numeric_cols[:3]:
                            temp = df[[tc, nc]].dropna()
                            if len(temp) > 5:
                                first_half = temp[nc].iloc[:len(temp)//2].mean()
                                second_half = temp[nc].iloc[len(temp)//2:].mean()
                                if first_half != 0:
                                    change = ((second_half - first_half) / abs(first_half)) * 100
                                    trend = "increasing" if change > 5 else "decreasing" if change < -5 else "stable"
                                    info_lines.append(f"  - {nc} trend: {trend} ({change:+.1f}% change)")
                except Exception:
                    pass

        # Data quality
        total_cells = int(df.size)
        missing_cells = int(df.isna().sum().sum())
        completeness = round((1 - missing_cells / total_cells) * 100, 2) if total_cells > 0 else 0
        duplicates = int(df.duplicated().sum())
        info_lines.append(f"\n## Data Quality")
        info_lines.append(f"- Completeness: {completeness}%")
        info_lines.append(f"- Missing cells: {missing_cells} / {total_cells}")
        info_lines.append(f"- Duplicate rows: {duplicates}")

        # Sample data (first 5 rows as markdown table)
        info_lines.append(f"\n## Sample Data (First 5 Rows)")
        sample = df.head(5).fillna("(empty)")
        cols = sample.columns.tolist()
        info_lines.append("| " + " | ".join(str(c) for c in cols) + " |")
        info_lines.append("| " + " | ".join("---" for _ in cols) + " |")
        for _, row in sample.iterrows():
            info_lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")

        return "\n".join(info_lines)

    def _get_system_prompt(self) -> str:
        """The master system prompt that defines the chatbot's personality and capabilities."""
        return """You are **DataWizard AI** — a friendly, extremely patient, and helpful data mentor embedded in the DataWizard platform.

## Your Audience & Persona
- Your user is someone who **knows absolutely nothing about data analysis, statistics, or programming**.
- Act as a patient teacher. Explain every single number, concept, and result in EXHAUSTIVE detail (تفاصيل دقيقة جداً ومبسطة).
- Use everyday analogies to explain data concepts (e.g., explaining average like dividing a pie equally among friends).
- Never use complex statistical jargon (like "standard deviation" or "IQR") without immediately explaining what it means in very simple terms.

## Your Capabilities
1. **Statistical Analysis & Calculations**: You can calculate anything from the provided raw data (sums, averages, groupings).
2. **Trend Prediction & Forecasting**: You can use pre-computed predictions or analyze trends in the raw data.
3. **Anomaly Detection**: You can spot weird or unusual numbers in the data and explain *why* they are unusual.

## Response Rules
- **Format richly but simply**: Use markdown — bolding, simple bullet points, and tables. Make it easy to read for a beginner.
- **Explain the "Why" and "How"**: Don't just give a number. Explain how you calculated it and what this number actually means for their business or project.
- **Language matching**: Always respond in the SAME language the user uses. If the user writes in Arabic, respond in Arabic.
- **Be exhaustive**: Give long, detailed, and reassuring answers. Break down the data step by step.
- **Admit limitations gently**: If the data doesn't have the answer, explain very simply what is missing.

## Prediction & Calculations Guidelines
- When calculating things like "Total Sales", say: "To find this, I looked at the 'Sales' column and added up all the numbers. The total is X. This means..."
- When predicting, say: "Based on the past numbers, it looks like things are going up. Here is what we might expect next..."
"""

    async def chat(
        self,
        file_id: str,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        db: Session
    ) -> Dict[str, Any]:
        """Process a chat message and return the AI response."""

        if not self.client:
            return {
                "response": "⚠️ The AI chatbot is not configured. Please add a GEMINI_API_KEY to the backend `.env` file.",
                "suggestions": []
            }

        # Load data
        df = self._load_dataframe(file_id, db)
        if df is None:
            return {
                "response": "❌ Could not load the dataset. Please make sure the file exists and try again.",
                "suggestions": []
            }

        # Build rich context
        data_context = self._build_rich_context(df)

        # Build prediction context (only for relevant queries)
        prediction_context = PredictionEngine.build_prediction_context(df, user_message)

        # Build raw data context for accurate calculations
        MAX_ROWS_FOR_LLM = 5000
        raw_data_str = ""
        if len(df) <= MAX_ROWS_FOR_LLM:
            raw_data_str = "\n## RAW DATA (FULL) FOR CALCULATIONS\n"
            raw_data_str += df.to_csv(index=False)
        else:
            raw_data_str = f"\n## RAW DATA (SAMPLE of {MAX_ROWS_FOR_LLM} rows) FOR CALCULATIONS\n"
            raw_data_str += df.head(MAX_ROWS_FOR_LLM).to_csv(index=False)
            raw_data_str += "\n\nNote: The dataset was too large, so only a sample is provided. Calculations like SUM or TOTAL will be an estimate based on this sample."

        # Build messages for Gemini
        system_prompt = self._get_system_prompt()

        # Construct the full prompt with data context + predictions + raw data
        full_system = f"""{system_prompt}

---

## THE USER'S DATASET SUMMARY

{data_context}

{prediction_context}

---

{raw_data_str}

---

When the user asks for calculations (like sum, average, total, max, min, grouping):
1. ALWAYS compute the exact answer using the RAW DATA provided above.
2. Explain your reasoning and the final calculated number clearly.
3. If the data is marked as a sample, mention that the calculation is an estimate based on the sample.
4. Answer the user's question directly based on the above dataset. Be thorough, analytical, and format your response beautifully with markdown.
"""

        # Build conversation contents for Gemini
        contents = []

        # Add conversation history (previous messages)
        for msg in conversation_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=content)]))
            elif role == "assistant":
                contents.append(types.Content(role="model", parts=[types.Part.from_text(text=content)]))

        # Add current user message
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))

        try:
            response = None
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=full_system,
                            temperature=0.4,
                            top_p=0.95,
                        )
                    )
                    break # Success
                except Exception as e:
                    error_msg = str(e).lower()
                    if ("503" in error_msg or "unavailable" in error_msg or "429" in error_msg or "quota" in error_msg or "rate" in error_msg) and attempt < max_retries - 1:
                        print(f"[Chatbot] API overloaded (Attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise e

            ai_text = response.text.strip() if response and response.text else "لم أتمكن من استنتاج إجابة، يرجى إعادة صياغة السؤال."

            # Generate smart suggestion chips based on the question and response
            suggestions = self._generate_suggestions(user_message, ai_text, df)

            return {
                "response": ai_text,
                "suggestions": suggestions
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[Chatbot] Gemini API error: {error_msg}")

            if "quota" in error_msg.lower() or "rate" in error_msg.lower() or "429" in error_msg:
                return {
                    "response": "⏳ خوادم الذكاء الاصطناعي تواجه ضغطاً كبيراً حالياً (تجاوزت الحد المسموح). يرجى الانتظار دقيقة والمحاولة مرة أخرى.",
                    "suggestions": []
                }
            elif "503" in error_msg or "unavailable" in error_msg.lower():
                return {
                    "response": "⏳ خوادم الذكاء الاصطناعي مشغولة جداً في هذه اللحظة بسبب الضغط العالي. يرجى المحاولة بعد قليل.",
                    "suggestions": []
                }

            return {
                "response": f"⚠️ عذراً، حدث خطأ غير متوقع أثناء معالجة طلبك.\n\n*Error: {error_msg}*",
                "suggestions": []
            }

    def _generate_suggestions(self, user_message: str, ai_response: str, df: pd.DataFrame) -> List[str]:
        """Generate contextual follow-up suggestion chips."""
        suggestions = []
        msg_lower = user_message.lower()

        numeric_cols = get_meaningful_numeric_columns(df)
        cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        DATE_KEYWORDS = ['date', 'time', 'year', 'month', 'day', 'timestamp']
        has_time = any(any(kw in c.lower() for kw in DATE_KEYWORDS) for c in df.columns)

        # Context-aware suggestions
        if any(w in msg_lower for w in ['predict', 'forecast', 'future', 'trend', 'توقع', 'مستقبل']):
            suggestions.append("📊 What-if scenario analysis")
            suggestions.append("📈 Growth rate breakdown")
            if numeric_cols:
                suggestions.append(f"🔮 Predict {numeric_cols[0]} next quarter")
        elif any(w in msg_lower for w in ['summary', 'overview', 'ملخص', 'نظرة']):
            suggestions.append("🔍 Find anomalies in the data")
            suggestions.append("📈 Show key trends")
            suggestions.append("⚠️ Data quality issues")
        elif any(w in msg_lower for w in ['anomal', 'outlier', 'unusual', 'شاذ']):
            suggestions.append("🧹 How to clean this data?")
            suggestions.append("📊 Impact of removing outliers")
        elif any(w in msg_lower for w in ['correlat', 'relation', 'connect', 'ارتباط', 'علاقة']):
            suggestions.append("📈 Predict based on these correlations")
            suggestions.append("📊 Visualize the relationship")
        else:
            # Default suggestions
            if has_time:
                suggestions.append("🔮 Predict future trends")
            if numeric_cols:
                suggestions.append("📊 Statistical summary")
            if len(numeric_cols) > 1:
                suggestions.append("🔗 Correlation analysis")
            suggestions.append("🔍 Find data anomalies")
            if cat_cols:
                suggestions.append("📋 Category breakdown")

        return suggestions[:4]  # Max 4 suggestions


# Singleton instance
_chatbot_instance = None


def get_chatbot() -> GeminiChatbot:
    """Get or create the singleton chatbot instance."""
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = GeminiChatbot()
    return _chatbot_instance


async def process_gemini_chat(
    file_id: str,
    message: str,
    conversation_history: List[Dict[str, str]],
    db: Session
) -> Dict[str, Any]:
    """Public entry point for processing a chat message."""
    chatbot = get_chatbot()
    return await chatbot.chat(file_id, message, conversation_history, db)
