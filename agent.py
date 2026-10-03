import json
import ollama

from database import query_temperature_data, analyze_temperature

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_temperature_data",
            "description": (
                "Liest einzelne Temperaturmesswerte aus der "
                "Heizungsdatenbank. Verwende dieses Tool, wenn "
                "konkrete Messwerte und Zeitpunkte benötigt werden."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": (
                            "Startzeit im Format "
                            "YYYY-MM-DD HH:MM:SS"
                        ),
                    },
                    "end": {
                        "type": "string",
                        "description": (
                            "Endzeit im Format "
                            "YYYY-MM-DD HH:MM:SS"
                        ),
                    },
                },
                "required": ["start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_temperature",
            "description": (
                "Analysiert Temperaturmesswerte eines bestimmten "
                "Sensors innerhalb eines Zeitraums. Verwende dieses "
                "Tool für Fragen nach minimaler, maximaler oder "
                "durchschnittlicher Temperatur. "
                "Für minimale und maximale Temperatur gleichzeitig "
                "verwende die Operation 'min_max'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": (
                            "Startzeit im Format "
                            "YYYY-MM-DD HH:MM:SS"
                        ),
                    },
                    "end": {
                        "type": "string",
                        "description": (
                            "Endzeit im Format "
                            "YYYY-MM-DD HH:MM:SS"
                        ),
                    },
                    "sensor": {
                        "type": "string",
                        "description": (
                            "Name des Sensors, zum Beispiel "
                            "'Boiler oben', 'Boiler unten', "
                            "'Heizung VL' oder 'Warmwasser VL'."
                        ),
                    },
                    "operation": {
                        "type": "string",
                        "enum": [
                            "min",
                            "max",
                            "min_max",
                            "average"
                        ],
                        "description": (
                            "Art der Analyse: "
                            "'min' für minimale Temperatur, "
                            "'max' für maximale Temperatur, "
                            "'min_max' für minimale und maximale "
                            "Temperatur und "
                            "'average' für Durchschnittstemperatur."
                        ),
                    },
                },
                "required": [
                    "start",
                    "end",
                    "sensor",
                    "operation",
                ],
            },
        },
    },
]


def execute_tool(tool_name, arguments):
    if tool_name == "query_temperature_data":
        return query_temperature_data(
            arguments["start"],
            arguments["end"],
        )
    if tool_name == "analyze_temperature":
        return analyze_temperature(
            arguments["start"],
            arguments["end"],
            arguments["sensor"],
            arguments["operation"],
        )    

    raise ValueError(f"Unbekanntes Tool: {tool_name}")

def ask_agent(question):

    messages = [
        {
            "role": "system",
            "content": """
Du bist ein Assistent für die Analyse einer Heizungsanlage.

Du hast Zugriff auf Temperaturmessdaten.

Wenn du konkrete Messdaten benötigst,
verwende das dafür bereitgestellte Tool.

Erfinde niemals Temperaturwerte.
Wenn du keine ausreichenden Daten hast,
sage das offen.
""",
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    while True:

        client = ollama.Client( host="http://ollama:11434" )
        response = client.chat(
            model="qwen2.5:3b",
            messages=messages,
            tools=TOOLS,
        )

        messages.append(response["message"])

        # Hat das Modell ein Tool aufgerufen?
        if not response["message"].get("tool_calls"):
            return response["message"]["content"]

        # Tool(s) ausführen
        for tool_call in response["message"]["tool_calls"]:

            tool_name = tool_call["function"]["name"]

            arguments = tool_call["function"]["arguments"]

            print(f"Tool: {tool_name}")
            print(f"Argumente: {arguments}")

            result = execute_tool(
                tool_name,
                arguments,
            )

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(
                        result,
                        default=str,
                    ),
                }
            )

if __name__ == "__main__":
    print("Heizungs-Agent gestartet.")
    print("Beenden mit 'exit', 'quit' oder Strg+C.")
    print()

    while True:
        try:
            question = input("> ").strip()

            if not question:
                continue

            if question.lower() in ["exit", "quit"]:
                print("Agent beendet.")
                break

            answer = ask_agent(question)

            print()
            print(answer)
            print()

        except KeyboardInterrupt:
            print("\nAgent beendet.")
            break

        except Exception as e:
            print(f"Fehler: {e}")
             