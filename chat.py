from llm_interface import LLMInterface
import os
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import warnings
warnings.filterwarnings("ignore")


llm = LLMInterface()
history = []

print("Gemini 2.5 Flash – Chatmodus (Tippe 'exit' zum Beenden)\n")

while True:
    user_input = input("Du: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Chat beendet.")
        break

    # Kontext anhängen
    history.append(f"User: {user_input}")
    prompt = "\n".join(history) + "\nAI:"

    answer = llm.query(prompt)
    print(f"Gemini: {answer}\n")

    # Antwort im Verlauf speichern
    history.append(f"AI: {answer}")

