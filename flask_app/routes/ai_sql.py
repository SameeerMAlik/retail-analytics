"""
Enterprise Retail Analytics Engine — AI SQL Route
Natural Language to SQL using Google Gemini
"""
import logging
from flask import Blueprint, render_template, request, jsonify
from services.gemini_service import gemini_service
from services.snowflake_service import snowflake_service

log = logging.getLogger(__name__)
ai_sql_bp = Blueprint("ai_sql", __name__)

# Pre-built example questions to guide users
EXAMPLE_QUESTIONS = [
    "Show top 5 customers by revenue",
    "What are the monthly revenue trends for 2024?",
    "Which product categories have the highest profit margin?",
    "Compare revenue by region",
    "Show customers who haven't ordered in 90+ days",
    "What is the average order value by payment method?",
    "Which products are priced above competitors?",
    "Show revenue by age group",
]


@ai_sql_bp.route("/")
def ai_sql_page():
    """AI SQL generator page."""
    return render_template(
        "ai_sql.html",
        active_page="ai_sql",
        example_questions=EXAMPLE_QUESTIONS,
        ai_available=gemini_service.is_available(),
        is_demo=not snowflake_service.is_connected()
    )


@ai_sql_bp.route("/generate", methods=["POST"])
def generate_sql():
    """
    AJAX endpoint: receives natural language question,
    returns generated SQL + query results.

    Request JSON: { "question": "..." }
    Response JSON: { "sql": "...", "columns": [...], "rows": [...], "error": null }
    """
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Missing 'question' in request body"}), 400

    question = data["question"].strip()
    if len(question) < 5:
        return jsonify({"error": "Question too short. Please be more specific."}), 400
    if len(question) > 500:
        return jsonify({"error": "Question too long (max 500 chars)"}), 400

    log.info("AI SQL request: %s", question)

    # Step 1: Generate SQL via Gemini
    generated_sql, gen_error = gemini_service.generate_sql(question)

    if gen_error:
        return jsonify({"error": gen_error, "sql": None, "rows": [], "columns": []}), 422

    # Step 2: Validate & Execute query on Snowflake
    result_df, exec_error = snowflake_service.execute_safe_query(generated_sql)

    if exec_error:
        return jsonify({
            "error":   exec_error,
            "sql":     generated_sql,
            "rows":    [],
            "columns": []
        }), 422

    # Step 3: Return results
    response = {
        "sql":     generated_sql,
        "columns": result_df.columns.tolist() if len(result_df) > 0 else [],
        "rows":    result_df.values.tolist()  if len(result_df) > 0 else [],
        "count":   len(result_df),
        "error":   None,
        "truncated": len(result_df) >= 500
    }

    log.info("AI SQL returned %d rows", response["count"])
    return jsonify(response)
