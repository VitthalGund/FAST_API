import openai
from fastapi import HTTPException
from ChatApp.constants import OPEN_AI_KEY
import os
from langchain.llms import ChatOpenAI
from langchain.agents import ChainAgent

openai.api_key = os.environ.get("OPENAI_API_KEY")


def call_gpt(prompt: str) -> str:
    try:
        chat = QAAgent(openai_api_key=OPEN_AI_KEY)
        return chat.answer_question(prompt)
        # return response.choices[0].text
    except openai.error.Error as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {e}")


class QAAgent(ChainAgent):
    def __init__(self, openai_api_key):
        super().__init__()
        self.chat_gpt35 = ChatOpenAI(
            model_name="chat-gpt-3.5",
            openai_api_key=openai_api_key,
            temperature=0.7,  # Adjust temperature for desired response style
        )

    def answer_question(self, question):
        prompt = f"Answer the question: {question}"
        response = self.chat_gpt35(prompt)
        return response.text
