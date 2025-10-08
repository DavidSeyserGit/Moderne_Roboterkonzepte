# LLM Interface & Hyperparameter


## Zielsetzung

Hier wurde ein Interface zu einem Large Language Model (LLM) entwickelt,  
welches im Gesamtprojekt als Sprachmodul für den Chatbot und das RAG-System dient.  

## Hauptziele:
- Einbindung eines kostenfreien LLM (Google Gemini 2.5 Flash)  
- Aufbau eines Python-Interfaces zur Nutzung im Projekt  
- Untersuchung und Dokumentation der wichtigsten Hyperparameter (`temperature`, `top_p`)  
- Bereitstellung einer konfigurierbaren API, die später einfach in das Gesamtsystem integrierbar ist



## Voraussetzungen

   ## Umgebung & Setup

   1. Python-Version: 3.12 oder neuer  
   2. Benötigte Pakete:
      pip install google-generativeai python-dotenv
   3. API-Key ↓↓


###  API-Key einrichten

Für den Zugriff auf das LLM (Google Gemini 2.5 Flash) wird ein persönlicher API-Key benötigt!

1. API-Key erstellen:
   - Gehe zu https://aistudio.google.com/app/apikey
   - Melde dich mit deinem Google-Konto an.  
   - Klicke auf „Create API key“.  
   - Kopiere den angezeigten Schlüssel.

2. API-Key lokal speichern: 
   Im Projektverzeichnis muss eine Datei mit dem Namen `.env` angelegt werden. 
   Hierfür kann man einfach die Datei `dummy.env` umbenennen zu `.env` und den zuvor generierten API-Key darin einfügen.


## Verwendung
Das LLM kann direkt über das Skript chat.py gestartet werden.
Dieses Skript verwendet intern das LLMInterface und ermöglicht eine einfache Kommunikation mit dem Modell. Jedenfalls benötigt wird ein API-Key! 

python chat.py


  ## Beispielausgabe:

   Gemini 2.5 Flash – Chatmodus (Strg + C zum Beenden)

   Du: Hallo!
   Gemini: Hallo! Wie kann ich Ihnen helfen?

   


### Programmintegration (für andere Projektteile)
```python

Das Interface kann von anderen Modulen direkt importiert und genutzt werden:

from llm_interface import LLMInterface

llm = LLMInterface()
antwort = llm.query("Was macht der Roboter gerade? Sind wir bereit?")
print(antwort)
