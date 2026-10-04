# Setup ai-lab-agent

## Setup in vscode terminal

```
ssh-keygen -t ed25519 -C "raifal@users.noreply.github.com"
cat /root/.ssh/id_ed25519.pub

pip install ollama psycopg2-binary
pip install pydantic
pip install python-dotenv

python -m pip install ollama
python -m pip install psycopg2-binary
python -m pip install pydantic 
python -m pip install python-dotenv
```

## Example prompts

Welche aktiven sensoren hat die Heizungsanlage? Bitte nur die Namen auflisten

Was war am 3.10.2026 die maximale Temperatur von Boiler oben?

Was war die minimale Temperatur?

Wie hoch war die durchschnittliche Temperatur?

Welcher Sensor hatte am 3.10. die höchste Temperatur?

Gab es zwischen 6 und 9 Uhr ungewöhnliche Temperaturen?

Gab es zwischen 6 und 9 Uhr ungewöhnliche Temperaturen? am 2.10.2026 am sensor boiler oben?


## Setup User für postgres datenbank
```sql
-- Read-only User für den AI-Agenten
CREATE ROLE ai_agent
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 3
    PASSWORD '### password here ###';

-- Zugriff auf die Datenbank
GRANT CONNECT ON DATABASE hsm TO ai_agent;

-- Zugriff auf das Schema
GRANT USAGE ON SCHEMA public TO ai_agent;

-- Nur die beiden Tabellen, die der Agent benötigt
GRANT SELECT ON TABLE
    public.sensors,
    public.temperature_measurements
TO ai_agent;

-- Sicherheitsnetz:
-- Keine Schreibrechte auf diesen Tabellen
REVOKE INSERT, UPDATE, DELETE, TRUNCATE
ON TABLE
    public.sensors,
    public.temperature_measurements
FROM ai_agent;
```
