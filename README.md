# Setup ai-lab-agent

ssh-keygen -t ed25519 -C "raifal@users.noreply.github.com"
cat /root/.ssh/id_ed25519.pub

pip install ollama psycopg2-binary
pip install pydantic
pip install python-dotenv

python -m pip install ollama
python -m pip install psycopg2-binary
python -m pip install pydantic 
python -m pip install python-dotenv


Test
data = query_temperature_data("2026-10-01 06:00:00", "2026-10-01 09:00:00") 
print(data)



Was war am 3.10.2026 die maximale Temperatur von Boiler oben?

Was war die minimale Temperatur?

Wie hoch war die durchschnittliche Temperatur?

Welcher Sensor hatte am 3.10. die höchste Temperatur?

Gab es zwischen 6 und 9 Uhr ungewöhnliche Temperaturen?