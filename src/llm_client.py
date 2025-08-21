import requests
from config import LLM_PROVIDER, TOGETHER_API_KEY, LLM_MODEL

def generate_llm_response(prompt: str) -> str:
    if LLM_PROVIDER == "together":
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": LLM_MODEL,
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.3,
        }
        response = requests.post("https://api.together.xyz/v1/completions", headers=headers, json=data)
        return response.json()["choices"][0]["text"].strip()

    # elif LLM_PROVIDER == "openai":
    #     import openai
    #     openai.api_key = OPENAI_API_KEY
    #     response = openai.ChatCompletion.create(
    #         model="gpt-4o",
    #         messages=[{"role": "user", "content": prompt}]
    #     )
    #     return response.choices[0].message["content"]

    else:
        raise ValueError("Unsupported LLM_PROVIDER")