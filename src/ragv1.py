import json
import re
from datetime import datetime
from memory import load_memory, save_to_memory
from chromadb_store import ChromaStore
from llm_client import generate_llm_response

store = ChromaStore("./chroma_db")

def classify_user_query(user_input, history):
    history_snippet = "\n".join(
        f"User: {h[0]}\nAssistant: {h[1]}" for h in history[-3:]
    )
    prompt = f"""You are a system that classifies user questions.

History:
{history_snippet}

New input:
{user_input}

Classify as one of: 'refinement', 'new_query', or 'chitchat'."""
    return generate_llm_response(prompt).strip().lower()

def build_query(history, user_input):
    if not history:
        return user_input
    return f"Previously: {history[-1][0]}\nNow: {user_input}"

def retrieve_context(query):
    results = store.query(query)
    if results and "documents" in results:
        return "\n---\n".join(results["documents"][0])
    return ""

def should_generate_graph(user_input, context):
    prompt = f"""Given this query: {user_input}\nAnd context: {context}\nShould a chart be generated? Answer Yes or No."""
    answer = generate_llm_response(prompt)
    return "yes" in answer.lower()

def generate_graph_code(user_input, context):
    prompt = f"""Given the following user_query: {user_input} and context: {context}, generate:
1. Python code using matplotlib to create an appropriate chart.
2. The chart type (e.g., bar, line).
3. The chart title.
4. X and Y axis labels.
Format your response as a JSON like:
{{
  "code": "...",
  "chart_type": "...",
  "title": "...",
  "x_label": "...",
  "y_label": "..."
}}"""
    return generate_llm_response(prompt)

def extract_code_block(json_text):
    try:
        code_block = json.loads(json_text)
        return code_block.get("code", ""), code_block
    except Exception as e:
        return "", {}

def try_execute_code(code):
    try:
        local_vars = {}
        exec(code, {"__builtins__": __builtins__, "plt": __import__('matplotlib.pyplot'), "io": __import__('io')}, local_vars)
        return local_vars.get("buf").getvalue() if "buf" in local_vars else None
    except Exception as e:
        return str(e)

def answer_query(user_input, session_id):
    history = load_memory(session_id)
    q_type = classify_user_query(user_input, history)
    if q_type == "chitchat":
        return "Happy to chat!"
    refined_query = build_query(history, user_input) if q_type == "refinement" else user_input
    context = retrieve_context(refined_query)
    prompt = f"""
    You are an expert assistant helping the user understand complex documents.

    Answer the following user query clearly and accurately:
    "{refined_query}"

    Use the provided context below. Prioritize summarizing key findings, relationships, or facts — do not copy-paste large blocks of text.

    Context:
    {context}

    Your response should be direct, concise, and focused on insight.
    """
    answer = generate_llm_response(prompt)

    image = None
    if should_generate_graph(user_input, context):
        graph_json = generate_graph_code(user_input, context)
        code, parsed = extract_code_block(graph_json)
        execution_result = try_execute_code(code)

        # Self-heal if execution failed
        if isinstance(execution_result, str):
            heal_prompt = f"Fix this code:\n{code}\nError: {execution_result}"
            fixed_json = generate_llm_response(heal_prompt)
            code, parsed = extract_code_block(fixed_json)
            execution_result = try_execute_code(code)

        image = execution_result if not isinstance(execution_result, str) else None

    save_to_memory(session_id, datetime.utcnow().isoformat(), user_input, answer)
    return answer, image
