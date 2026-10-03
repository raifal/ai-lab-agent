# Setup ai-lab-agent

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