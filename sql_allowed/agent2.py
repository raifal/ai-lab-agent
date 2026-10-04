import json
import os
import re

import ollama
import psycopg2
from dotenv import load_dotenv


load_dotenv()


# ---------------------------------------------------------
# Ollama
# ---------------------------------------------------------

client = ollama.Client(
    host=os.getenv("OLLAMA_HOST")
)


# ---------------------------------------------------------
# PostgreSQL
# ---------------------------------------------------------

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": 5432,
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


# ---------------------------------------------------------
# Tools
# ---------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_readonly_sql",
            "description": (
                "Führt eine einzelne schreibgeschützte SQL-SELECT-Abfrage "
                "auf der Heizungsdatenbank aus. "
                "Verwende dieses Tool, wenn konkrete Daten aus der "
                "Datenbank benötigt werden. "
                "INSERT, UPDATE, DELETE, DROP, ALTER, CREATE und andere "
                "ändernde SQL-Befehle sind nicht erlaubt."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": (
                            "Eine einzelne PostgreSQL SELECT-Abfrage. "
                            "Verwende nur die Tabellen sensors und "
                            "temperature_measurements."
                        ),
                    }
                },
                "required": ["sql"],
            },
        },
    }
]


# ---------------------------------------------------------
# SQL Sicherheitsprüfung
# ---------------------------------------------------------

def validate_sql(sql):
    """
    Sehr konservative Prüfung für SQL,
    bevor die Abfrage an PostgreSQL geht.
    """

    sql = sql.strip()

    if not sql:
        raise ValueError("SQL-Abfrage ist leer.")

    # Keine mehreren Statements
    if ";" in sql.rstrip(";"):
        raise ValueError(
            "Mehrere SQL-Statements sind nicht erlaubt."
        )

    # Optionales Semikolon am Ende entfernen
    sql = sql.rstrip(";").strip()

    # Muss mit SELECT oder WITH beginnen
    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise ValueError(
            "Nur SELECT-Abfragen sind erlaubt."
        )

    # Explizit verbotene SQL-Befehle
    forbidden = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "GRANT",
        "REVOKE",
        "COPY",
        "VACUUM",
        "ANALYZE",
        "CALL",
        "DO",
        "SET",
        "RESET",
        "COMMENT",
        "LOCK",
    ]

    for keyword in forbidden:
        if re.search(
            rf"\b{keyword}\b",
            sql,
            re.IGNORECASE,
        ):
            raise ValueError(
                f"SQL enthält nicht erlaubten Befehl: {keyword}"
            )

    # Nur unsere beiden Tabellen erlauben
    allowed_tables = {
        "sensors",
        "temperature_measurements",
    }

    # Sehr einfache FROM/JOIN-Prüfung
    referenced_tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
        sql,
        re.IGNORECASE,
    )

    for table in referenced_tables:
        table_name = table.split(".")[-1].lower()

        if table_name not in allowed_tables:
            raise ValueError(
                f"Tabelle nicht erlaubt: {table}"
            )

    return sql


# ---------------------------------------------------------
# SQL ausführen
# ---------------------------------------------------------

def execute_readonly_sql(sql):

    sql = validate_sql(sql)

    with psycopg2.connect(**DB_CONFIG) as conn:

        with conn.cursor() as cur:

            # Zusätzliche Schutzschicht.
            # Selbst wenn die SQL-Prüfung versagt,
            # darf diese Transaktion nichts verändern.
            cur.execute(
                "SET TRANSACTION READ ONLY"
            )

            # Maximal 5 Sekunden pro Query
            cur.execute(
                "SET LOCAL statement_timeout = '5s'"
            )

            cur.execute(sql)

            rows = cur.fetchall()

            columns = [
                description[0]
                for description in cur.description
            ]

            result = [
                dict(zip(columns, row))
                for row in rows
            ]

            return result


# ---------------------------------------------------------
# Tool Dispatcher
# ---------------------------------------------------------

def execute_tool(tool_name, arguments):

    if tool_name == "execute_readonly_sql":

        return execute_readonly_sql(
            arguments["sql"]
        )

    raise ValueError(
        f"Unbekanntes Tool: {tool_name}"
    )


# ---------------------------------------------------------
# Agent
# ---------------------------------------------------------

def ask_agent(question):

    messages = [
        {
            "role": "system",
            "content": """
Du bist ein Assistent zur Analyse einer Heizungsanlage.

Du hast Zugriff auf eine PostgreSQL-Datenbank.

WICHTIG:
- Erfinde niemals Daten.
- Wenn Daten benötigt werden, verwende das SQL-Tool.
- Du darfst nur SELECT-Abfragen erzeugen.
- Verwende ausschließlich die Tabellen sensors und
  temperature_measurements.
- Verwende keine INSERT-, UPDATE-, DELETE-, DROP-,
  ALTER- oder CREATE-Befehle.
- Verwende nur aktive sensoren mit active is true
- "sensorAddress" muss immer in quotes gesetzt werden.
Datenbankschema:

Tabelle public.sensors:

    name
    "sensorAddress"
    active

Tabelle public.temperature_measurements:

    sensor_address
    temperature
    timestamp

Verknüpfung:

    sensors."sensorAddress"
        =
    temperature_measurements.sensor_address

Beispiel:

SELECT
    s.name,
    MIN(t.temperature) AS min_temperature,
    MAX(t.temperature) AS max_temperature
FROM public.sensors s
JOIN public.temperature_measurements t
    ON s."sensorAddress" = t.sensor_address
WHERE s.name = 'Boiler oben'
  AND s.active IS TRUE
  AND t.timestamp >= '2026-10-03 00:00:00'
  AND t.timestamp <= '2026-10-03 23:59:59';

Wenn du viele Messwerte abfragst,
verwende nach Möglichkeit LIMIT.

Bevor du eine Antwort gibst:
- Prüfe die Ergebnisse des SQL-Tools.
- Verwende nur Werte, die tatsächlich aus
  dem Tool-Ergebnis stammen.
- Wenn keine Daten gefunden wurden, sage das.
""",
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    while True:

        response = client.chat(
            model="qwen2.5:3b",
            messages=messages,
            tools=TOOLS,
        )

        messages.append(response["message"])

        tool_calls = response["message"].get(
            "tool_calls"
        )

        if not tool_calls:
            return response["message"]["content"]

        for tool_call in tool_calls:

            tool_name = tool_call["function"]["name"]

            arguments = tool_call["function"]["arguments"]

            print(
                f"Tool: {tool_name}"
            )

            print(
                f"SQL: {arguments['sql']}"
            )

            try:

                result = execute_tool(
                    tool_name,
                    arguments,
                )

                print(
                    f"Ergebnis: {result}"
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

            except Exception as e:

                error_message = {
                    "error": str(e)
                }

                print(
                    f"SQL-Fehler: {e}"
                )

                messages.append(
                    {
                        "role": "tool",
                        "content": json.dumps(
                            error_message
                        ),
                    }
                )


# ---------------------------------------------------------
# Chat
# ---------------------------------------------------------

if __name__ == "__main__":

    print("Heizungs-Agent gestartet.")
    print(
        "Beenden mit 'exit', 'quit' oder Strg+C."
    )
    print()

    while True:

        try:

            question = input("> ").strip()

            if not question:
                continue

            if question.lower() in [
                "exit",
                "quit",
            ]:
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

