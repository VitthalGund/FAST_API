import openai
from fastapi import HTTPException
import os


openai.api_key = os.environ.get("OPENAI_API_KEY")


def call_gpt(prompt: str) -> str:
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1024,
            temperature=0.7,
        )
        return response.choices[0].text
    except openai.error.Error as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {e}")
