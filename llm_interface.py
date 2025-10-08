import google.generativeai as genai
from dotenv import load_dotenv
import os


# Warnungen und gRPC-Logmeldungen unterdrücken
import warnings
import logging
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_TRACE"] = "none"
logging.getLogger("google").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")


class LLMInterface:
    def __init__(self, model="models/gemini-2.5-flash", temperature=0.2, top_p=1.0):
        load_dotenv()
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model)
        self.temperature = temperature
        self.top_p = top_p

    def query(self, prompt: str) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": self.temperature,
                "top_p": self.top_p
            }
        )
        return response.text

if __name__ == "__main__":
    print("Starte LLM Interface...")
    llm = LLMInterface()
    print("LLM Interface bereit!")