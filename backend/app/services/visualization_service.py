import os
import pandas as pd
import numpy as np
from fastapi import HTTPException
from app.services.analysis_service import advanced_analysis_service
from app.utils.chart_utils import generate_purple_colors, generate_colors_palette

UPLOAD_FOLDER="uploaded_files"

def generate_chart_explanation(chart_type, column, chart_data):
    ar = ""
    en = ""
    if chart_type == "bar":
        if "datasets" in chart_data and len(chart_data["datasets"][0]["data"]) > 0:
            data_vals = chart_data["datasets"][0]["data"]
            labels = chart_data["labels"]
            max_idx = data_vals.index(max(data_vals))
            max_val = data_vals[max_idx]
            max_label = labels[max_idx]
            ar = f"هذا الرسم البياني يوضح توزيع الفئات لعمود '{column}'. الفئة الأكثر تكراراً هي '{max_label}' بتكرار {max_val} مرة."
            en = f"This chart shows the distribution of categories for '{column}'. The most frequent category is '{max_label}' appearing {max_val} times."
        else:
            ar = f"هذا الرسم يوضح توزيع الفئات في عمود '{column}'."
            en = f"This chart shows the category distribution for '{column}'."
    elif chart_type == "pie":
        if "datasets" in chart_data and len(chart_data["datasets"][0]["data"]) > 0:
            data_vals = chart_data["datasets"][0]["data"]
            labels = chart_data["labels"]
            max_idx = data_vals.index(max(data_vals))
            max_label = labels[max_idx]
            ar = f"هذا الرسم الدائري يوضح النسب المئوية للقيم في عمود '{column}'. القيمة المهيمنة هي '{max_label}'."
            en = f"This pie chart shows the percentage breakdown for '{column}'. The dominant value is '{max_label}'."
        else:
            ar = f"هذا الرسم يوضح مكونات عمود '{column}' كنسبة مئوية."
            en = f"This chart shows the percentage composition for '{column}'."
    elif chart_type == "histogram":
        stats = chart_data.get("statistics", {})
        mean_val = stats.get("mean", 0)
        ar = f"هذا الرسم يوضح التوزيع التكراري للقيم الرقمية في عمود '{column}'. متوسط القيم هو {mean_val:.2f}."
        en = f"This histogram shows the frequency distribution of numeric values in '{column}'. The average value is {mean_val:.2f}."
    elif chart_type == "line":
        ar = f"هذا الرسم يوضح التغير والاتجاه عبر الزمن لعمود '{column}'."
        en = f"This line chart displays the trend over time for '{column}'."
    elif chart_type == "scatter":
        ar = f"هذا الرسم يوضح العلاقة بين متغيرين."
        en = f"This scatter plot shows the relationship between two variables."
    return {"ar": ar, "en": en}

def prepare_bar_chart_data(column_data, column_name):
    value_counts = column_data.value_counts().head(15)
    
    return {
        "chart_type": "bar",
        "chart_title": f"Distribution of {column_name}",
        "labels": value_counts.index.tolist(),
        "datasets": [{
            "label": "Count",
            "data": value_counts.values.tolist(),
            "backgroundColor": generate_purple_colors(len(value_counts)),
            "borderColor": "#38006b",
            "borderWidth": 1
        }]
    }

def prepare_pie_chart_data(column_data, column_name):
    value_counts = column_data.value_counts().head(8)
    
    return {
        "chart_type": "pie",
        "chart_title": f"Percentage of {column_name}",
        "labels": value_counts.index.tolist(),
        "datasets": [{
            "data": value_counts.values.tolist(),
            "backgroundColor": generate_purple_colors(len(value_counts)),
            "hoverBackgroundColor":generate_colors_palette(len(value_counts))
        }]
    }

def prepare_histogram_data(column_data, column_name):
    if not pd.api.types.is_numeric_dtype(column_data):
        raise ValueError(f"Column '{column_name}' is not numeric")
    
    clean_data = column_data.dropna()
    data_points = len(clean_data)
    
    if data_points < 2:
        raise ValueError("Need at least 2 data points to create a histogram")
    
    bins = max(2, int(np.sqrt(data_points)))
    hist, bin_edges = np.histogram(clean_data, bins=bins)
    
    labels = [f"{bin_edges[i]:.1f}-{bin_edges[i+1]:.1f}" for i in range(len(bin_edges)-1)]
    
    return {
        "chart_type": "histogram",
        "chart_title": f"Distribution of {column_name}",
        "statistics": {
            "data_points": data_points,
            "bins_used": bins,
            "min": float(clean_data.min()),
            "max": float(clean_data.max()),
            "mean": float(clean_data.mean()),
            "median": float(clean_data.median()),
            "std": float(clean_data.std()),
            "variance": float(clean_data.var()),
            "q1": float(clean_data.quantile(0.25)),
            "q3": float(clean_data.quantile(0.75)),
            "iqr": float(clean_data.quantile(0.75) - clean_data.quantile(0.25))
        },
        "labels": labels,
        "datasets": [{
            "label": "Frequency",
            "data": hist.tolist(),
            "backgroundColor": "rgba(106, 27, 154, 0.7)",  
            "borderColor": "#4a148c",
            "borderWidth": 1
        }]
    }

def prepare_line_chart_data(df, column_name):
    date_keywords=['date', 'time', 'year', 'month']
    date_columns = []
    
    for col in df.columns:
        if any(keyword in col.lower() for keyword in date_keywords):
            date_columns.append(col)
            
    col_data=df[column_name]
    
    if date_columns and pd.api.types.is_numeric_dtype(df[column_name]):
        x_column = date_columns[0]
        sorted_df = df.sort_values(by=x_column)
        labels = sorted_df[x_column].astype(str).tolist()
        data = sorted_df[column_name].tolist()
        title = f"{column_name} Over Time"
    else:
        labels = list(range(len(df)))
        data = df[column_name].tolist()
        title = f"{column_name} Trend"
    
    clean_data = col_data.dropna()
    
    return {
        "chart_type": "line",
        "chart_title": title,
        "statistics": {
            "data_points": len(clean_data),
            "min": float(clean_data.min()) if len(clean_data) > 0 else None,
            "max": float(clean_data.max()) if len(clean_data) > 0 else None,
            "mean": float(clean_data.mean()) if len(clean_data) > 0 else None,
            "total": float(clean_data.sum()) if pd.api.types.is_numeric_dtype(clean_data) else None
        },
        "labels": labels,
        "datasets": [{
            "label": column_name,
            "data": data,
            "borderColor": "#6a1b9a",
            "backgroundColor": "rgba(106, 27, 154, 0.1)",
            "fill": True,
            "tension": 0.1
        }]
    }

def prepare_scatter_data(df, col1, col2):
    if col1 not in df.columns or col2 not in df.columns:
        raise ValueError("Columns not found")
    
    # errors='coerce' 
    temp_col1 = pd.to_numeric(df[col1], errors='coerce')
    temp_col2 = pd.to_numeric(df[col2], errors='coerce')
    clean_df = pd.concat([temp_col1, temp_col2], axis=1).dropna()
    if len(clean_df) < 2:
       raise ValueError("Not enough numeric data for a scatter plot")
    data_points = [
        {"x": float(x), "y": float(y)} 
        for x, y in zip(clean_df[col1], clean_df[col2])
    ]
    
    correlation = None
    if len(clean_df) > 1:
        correlation = float(clean_df.corr().iloc[0, 1])
    
    return {
        "chart_type": "scatter",
        "chart_title": f"{col1} vs {col2}",
        "statistics": {
            "data_points": len(data_points),
            "correlation": round(correlation, 3) if correlation else None,
            "correlation_strength": (
                "very strong" if abs(correlation) > 0.8
                else "strong" if abs(correlation) > 0.6
                else "medium" if abs(correlation) > 0.4
                else "weak" if correlation
                else "undefined"
            ) if correlation else None,
            "x_mean": float(clean_df[col1].mean()),
            "y_mean": float(clean_df[col2].mean())
        },
        "datasets": [{
            "label": f"{col1} vs {col2}",
            "data": data_points,
            "backgroundColor": "#6a1b9a",
            "pointRadius": 5,
            "pointHoverRadius": 8
        }]
    }

async def get_visualization_data_service(file_id: str, chart_type: str = None,
                                         column: str = None, column2: str = None, db=None):
   
    from app.database import get_analysis
    analyses = get_analysis(db, file_id)
    
    analysis = None
    if analyses:
        for a in analyses:
            if getattr(a, "analyze_type", "") == "advanced_analysis" and "chart_suggestion" in a.result:
                analysis = a.result
                break
            # Fallback if analyze_type isn't properly set but it has suggestions
            elif "chart_suggestion" in a.result:
                analysis = a.result
                break

    if not analysis:
        # No advanced analysis saved yet — run it first so we have chart suggestions
        analysis = await advanced_analysis_service(file_id, db)

    file_found = None
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.startswith(file_id + "_"):
            file_found = filename
            break
    if not file_found:
        raise HTTPException(404, "File not found")
    
    file_path = os.path.join(UPLOAD_FOLDER, file_found)
    try:
        if file_found.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_found.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {str(e)}")
    
    df = df.fillna("")

    if chart_type and column:
        if column not in df.columns:
            raise HTTPException(400, f"Column '{column}' not found in data")
        
        if chart_type == "bar":
            return prepare_bar_chart_data(df[column], column)
        elif chart_type == "pie":
            return prepare_pie_chart_data(df[column], column)
        elif chart_type == "histogram":
            return prepare_histogram_data(df[column], column)
        elif chart_type == "line":
            return prepare_line_chart_data(df, column)
        elif chart_type == "scatter":
            if not column2:
                raise HTTPException(400, "Scatter chart requires column2 parameter")
            return prepare_scatter_data(df, column, column2)
        else:
            raise HTTPException(400, f"Chart type '{chart_type}' not supported")

    visualization_options = []
    for suggestion in analysis.get("chart_suggestion", []):
        chart_type = suggestion.get("chart_type")
        column = suggestion.get("column")
        
        chart_data = None
        explanation = {"en": "", "ar": ""}
        
        try:
            if chart_type and column and column in df.columns:
                if chart_type == "bar":
                    chart_data = prepare_bar_chart_data(df[column], column)
                elif chart_type == "pie":
                    chart_data = prepare_pie_chart_data(df[column], column)
                elif chart_type == "histogram":
                    chart_data = prepare_histogram_data(df[column], column)
                elif chart_type == "line":
                    chart_data = prepare_line_chart_data(df, column)
                
                if chart_data:
                    explanation = generate_chart_explanation(chart_type, column, chart_data)
        except Exception as e:
            print(f"Error generating chart data for {column} ({chart_type}): {e}")
            pass

        if chart_data:
            visualization_options.append({
                "chart_type": chart_type,
                "column": column,
                "reason": suggestion.get("reason", ""),
                "data": chart_data,
                "explanation": explanation,
                "ready_for_frontend": True
            })

    return {
        "file_id": file_id,
        "file_name": file_found,
        "available_columns": list(df.columns),
        "visualization_options": visualization_options,
        "message": "Use ?chart_type=bar&column=column_name to get specific chart data"
    }