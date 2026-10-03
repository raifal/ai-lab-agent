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
                ORDER BY t.timestamp
                """,
                (start, end),
            )

            return cur.fetchall()