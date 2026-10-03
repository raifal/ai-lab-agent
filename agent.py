import json
import ollama

from database import query_temperature_data


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_temperature_data",
            "description": (
                "Liest Temperaturmesswerte aus der Heizungsdatenbank. "
                "Verwende das Tool, wenn konkrete Temperaturdaten "
                "für einen bestimmten Zeitraum benötigt werden."
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
    }
]


def execute_tool(tool_name, arguments):
    if tool_name == "query_temperature_data":
        return query_temperature_data(
            arguments["start"],
            arguments["end"],
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

    question = input("> ")

    answer = ask_agent(question)

    print()
    print(answer)                