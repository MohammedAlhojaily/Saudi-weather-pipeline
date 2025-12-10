from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import psycopg2
import os


API_KEY = os.getenv("OPENWEATHER_API_KEY")


SAUDI_CITIES = [
    {"name": "Riyadh", "lat": 24.7136, "lon": 46.6753},
    {"name": "Jeddah", "lat": 21.4858, "lon": 39.1925},
    {"name": "Mecca", "lat": 21.3891, "lon": 39.8579},
    {"name": "Medina", "lat": 24.5247, "lon": 39.5692},
    {"name": "Dammam", "lat": 26.3927, "lon": 49.9777},
    {"name": "Khobar", "lat": 26.2777, "lon": 50.2083},
    {"name": "Taif", "lat": 21.4373, "lon": 40.5127},
    {"name": "Tabuk", "lat": 28.3839, "lon": 36.5662},
    {"name": "Abha", "lat": 18.2164, "lon": 42.5053},
    {"name": "Hail", "lat": 27.5114, "lon": 41.7208},
]


def fetch_weather(lat, lon, city_name):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()
    weather = {
        "city": city_name,
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"],
        "date": datetime.utcnow().date(),
    }
    return weather


def store_weather():
    import logging

    conn = psycopg2.connect(
        host="postgres",
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    cur = conn.cursor()

    for city in SAUDI_CITIES:
        try:

            weather = fetch_weather(city["lat"], city["lon"], city["name"])
            logging.info(f"Fetched weather for {city['name']}: {weather}")

            insert_query = """
            INSERT INTO weather (city, temperature, humidity, weather_description, date)
            VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(
                insert_query,
                (
                    weather["city"],
                    weather["temperature"],
                    weather["humidity"],
                    weather["description"],
                    weather["date"],
                ),
            )

            logging.info(f"Inserted weather for {city['name']} successfully.")
        except Exception as e:
            logging.error(f"Error with {city['name']}: {e}")

    conn.commit()
    cur.close()
    conn.close()


default_args = {
    "start_date": datetime(2024, 1, 1),
}


with DAG(
    dag_id="weather_etl",
    schedule_interval="@daily",
    default_args=default_args,
    catchup=False,
) as dag:

    store_weather_task = PythonOperator(
        task_id="store_weather", python_callable=store_weather
    )

    store_weather_task
