# app/services/llm_client.py

import os

import openai


# ensure you have set OPENAI_API_KEY in your environment
openai.api_key = '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'


async def send_to_llm(prompt: str) -> str:
    """
    Send a prompt to the ChatGPT-4o mini model using the new v1 client
    and return its reply text.
    """
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content