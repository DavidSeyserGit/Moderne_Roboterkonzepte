# Moderne_Roboterkonzepte

# GUI
Für das GUI selbst wird Chainlit verwendet Hiermeit bekommen wir eine schöne, Chat GPT ähnliche Chatoberfläche im Browser
- https://docs.chainlit.io/get-started/overview

Zum Ausführen des Chatbots mit GUI zunächst die requirements aus `requirements.txt` installieren.   
Anschließend bitte den API key mithilfe dieses befhels setzen `$env:OPENROUTER_API_KEY="<API_KEY>"`unter windows in Anaconda `set OPENROUTER_API_KEY=<API KEY>`

Mit `chainlit run main.py -w` kann das programm nun ausgeführt werden.
Es sollte sich nun ein browserfenster mti der chatbot oberfläche öffnen.

## model_fetcher
Der Model fetcher ruft die API von openrouter auf und extrahiert von dort alle verfügmaren modelle als .json  
```python
(Zeile 37) response = requests.get(self.API_URL)
(Zeile 41) models = response.json().get("data", [])
```
Diese json wir nun nach bestimmten parametern die die einzelnen modelle unterstüzen durchsucht.  

Es wird einerseits nach dem priceing gefilterd (in unserem fall welche modelle gratis sind (diese funktionalität kann ausgeschaltet werden)), und nach allen support_parametern z.b. die unterstüzung von tools.  
Alle support parameter findet man hier: https://openrouter.ai/docs/overview/models alle implementierten in `model_fetcher` zeilen `14` bis `24`.

Wenn alle gewünschten funktionen im modell vorhanden sind werden diese in die filtered_models liste aufgenommen.
Die filtered_models liste wird dann ausgegeben sobald alle modelle durchsucht wurden.

## Chatbot

Diese Klasse implementiert einen Chatbot auf Basis von LangChain und OpenRouter.
Sie erlaubt es, verschiedene Sprachmodelle dynamisch zu nutzen, ein Gespräch im Speicher zu halten und flexibel zwischen Modellen zu wechseln.



### Importierte Module:

```python
from langchain_openai import ChatOpenAI
```
→ Importiert die ChatOpenAI-Klasse, die als Schnittstelle zwischen LangChain und OpenRouter dient. Damit kann OpenRouter wie eine OpenAI-kompatible API genutzt werden.
```python
from langchain.chains import ConversationChain
```
→ Importiert die ConversationChain aus LangChain. Sie verknüpft ein Sprachmodell (llm) und ein Gedächtnis (memory), um eine fortlaufende Konversation zu ermöglichen.
```python
from langchain.memory import ConversationBufferMemory
```
→ Importiert die ConversationBufferMemory, die als einfacher Zwischenspeicher für den Gesprächsverlauf dient. Sie speichert alle bisherigen Nachrichten, damit das Modell Kontext hat.

#### Klassendefinition:
```python
class Chatbot:
```
→ Definiert die Klasse `Chatbot`, die alle wichtigen Funktionen des Chatbots kapselt:
- das aktive Sprachmodell
- den Konversationsspeicher
- sowie Methoden zur Eingabeverarbeitung und Modellumschaltung.

#### Konstruktor:
```python
def init(self, api_key: str, model: str):
```
→ Initialisiert ein neues Chatbot-Objekt.  
Parameter:
- `api_key`: Dein OpenRouter-API-Schlüssel
- `model`: Die ID des zu verwendenden Sprachmodells
```python
self.model_name = model
```
→ Speichert den aktuellen Modellnamen intern.
```python
self.llm = ChatOpenAI(...)
```
→ Erstellt ein LLM-Objekt (Language Learning Model) mit dem angegebenen Modellnamen. Der API-Endpunkt ist auf OpenRouter gesetzt, sodass du Modelle von OpenRouter nutzen kannst.
```python
self.memory = ConversationBufferMemory(return_messages=True)
```
→ Erstellt einen Chat-Speicher. Dieser speichert den bisherigen Gesprächsverlauf, um den Kontext über mehrere Nachrichten hinweg zu behalten.
```python
self.chain = ConversationChain(llm=self.llm, memory=self.memory, verbose=False)
```
→ Erstellt eine LangChain-Konversationskette. Diese verbindet das Modell (llm) und den Speicher (memory) und verwaltet den Ablauf der Kommunikation.

#### Dynamischer Modellwechsel:
```python
def update_model(self, api_key: str, model: str):
```
→ Diese Methode erlaubt den Wechsel des aktiven Modells während der Laufzeit.
```python
self.model_name = model
```
→ Aktualisiert den Modellnamen intern.
```python
self.llm = ChatOpenAI(...)
```
→ Erstellt ein neues Modell-Objekt mit denselben Zugangsdaten, aber anderer Modell-ID.
```python
self.chain.llm = self.llm
```
→ Weist der bestehenden Konversationskette das neue Modell zu. Dadurch bleibt der bisherige Gesprächsverlauf erhalten, das Modell wird jedoch aktualisiert.

#### Antwortverarbeitung:
```python
def get_response(self, user_input: str) -> str:
```
→ Diese Methode verarbeitet eine Benutzereingabe und gibt eine Modellantwort zurück.
```python
response = self.chain.run(input=user_input)
```
→ Führt die Konversationskette aus: Das Modell erhält die aktuelle Eingabe und den bisherigen Gesprächsverlauf. Die Antwort wird generiert und automatisch im Speicher abgelegt.
```python
return response.strip()
```
→ Entfernt überflüssige Leerzeichen und gibt die bereinigte Antwort als Text zurück.

### Kurzfassung / Zusammenfassung:

`ChatOpenAI`: Schnittstelle zwischen LangChain und OpenRouter  
`ConversationBufferMemory`: Speichert den bisherigen Gesprächsverlauf  
`ConversationChain`: Verknüpft Modell und Speicher zu einem vollständigen Dialogsystem  
`update_model()`: Ermöglicht den Wechsel des Sprachmodells während des Chats  
`get_response()`: Sendet Nutzereingaben an das Modell und liefert Antworten zurück  
