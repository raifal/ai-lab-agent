import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def query_temperature_data(start, end):
    with psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=5432,
        database="hsm",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    ) as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.name AS sensor_name,
                    t.temperature,
                    t.timestamp,
                    s."sensorAddress"
                FROM public.sensors s
                JOIN public.temperature_measurements t
                  ON s."sensorAddress" = t.sensor_address
                WHERE t.timestamp >= %s
                  AND t.timestamp <= %s
                  AND s.active IS TRUE
                ORDER BY t.timestamp
                """,
                (start, end),
            )

            return cur.fetchall()


def analyze_temperature(start, end, sensor, operation):
    """
    Analysiert Temperaturmesswerte eines bestimmten Sensors.

    Unterstützte Operationen:
        min
        max
        min_max
        average
    """

    allowed_operations = {
        "min": "MIN(t.temperature)",
        "max": "MAX(t.temperature)",
        "average": "AVG(t.temperature)",
    }

    if operation == "min_max":
        select_clause = """
            MIN(t.temperature) AS min_temperature,
            MAX(t.temperature) AS max_temperature
        """
    elif operation in allowed_operations:
        select_clause = allowed_operations[operation]
    else:
        raise ValueError(
            f"Ungültige Operation: {operation}. "
            "Erlaubt sind: min, max, min_max, average"
        )

    with psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=5432,
        database="hsm",
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    ) as conn:

        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    {select_clause}
                FROM public.sensors s
                JOIN public.temperature_measurements t
                  ON s."sensorAddress" = t.sensor_address
                WHERE t.timestamp >= %s
                  AND t.timestamp <= %s
                  AND s.active IS TRUE
                  AND s.name = %s
                """,
                (start, end, sensor),
            )

            result = cur.fetchone()

            if result is None:
                return None

            if operation == "min_max":
                return {
                    "sensor": sensor,
                    "min_temperature": result[0],
                    "max_temperature": result[1],
                }

            return {
                "sensor": sensor,
                "operation": operation,
                "temperature": result[0],
            }

