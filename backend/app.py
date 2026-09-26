"""Backend REST API for the Rahti deployment exercise."""

import os
import socket

import mysql.connector
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "changeme")
DB_NAME = os.getenv("DB_NAME", "appdb")

APP_VERSION = os.getenv("APP_VERSION", "dev")
POD_NAME = os.getenv("POD_NAME", socket.gethostname())

_schema_ready = False

WEATHER_LOCATION = "Oulu, Finland"
WEATHER_URL = ("https://api.open-meteo.com/v1/forecast"
               "?latitude=65.01&longitude=25.47&current_weather=true")

# WMO weather interpretation codes used by Open-Meteo
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light rain showers", 81: "Rain showers", 82: "Violent rain showers",
    85: "Light snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail", 99: "Thunderstorm with heavy hail",
}


def get_conn():
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=DB_NAME, connection_timeout=5,
    )


def ensure_schema(conn):
    global _schema_ready
    if _schema_ready:
        return
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id      BIGINT AUTO_INCREMENT PRIMARY KEY,
            pod     VARCHAR(255) NOT NULL,
            seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         BIGINT AUTO_INCREMENT PRIMARY KEY,
            author     VARCHAR(64)  NOT NULL,
            body       VARCHAR(500) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    cur.close()
    _schema_ready = True


@app.get("/api/health")
def health():
    return {"status": "ok", "pod": POD_NAME, "version": APP_VERSION}


@app.get("/api/info")
def info():
    try:
        conn = get_conn()
    except mysql.connector.Error as exc:
        return jsonify(error="database unavailable", detail=str(exc)), 503
    try:
        ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("INSERT INTO visits (pod) VALUES (%s)", (POD_NAME,))
        conn.commit()
        cur.execute("SELECT NOW()")
        db_time = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM visits")
        visits = cur.fetchone()[0]
        cur.execute("SELECT VERSION()")
        db_version = cur.fetchone()[0]
        cur.close()
    finally:
        conn.close()
    return jsonify(
        pod=POD_NAME, version=APP_VERSION,
        db_time=db_time.strftime("%Y-%m-%d %H:%M:%S"),
        db_version=db_version, visits=visits,
    )


@app.get("/api/messages")
def list_messages():
    try:
        conn = get_conn()
    except mysql.connector.Error as exc:
        return jsonify(error="database unavailable", detail=str(exc)), 503
    try:
        ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("SELECT author, body, created_at FROM messages "
                    "ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()
    return jsonify(messages=[
        {"author": a, "body": b, "created_at": c.strftime("%Y-%m-%d %H:%M:%S")}
        for a, b, c in rows
    ])


@app.post("/api/messages")
def add_message():
    payload = request.get_json(silent=True) or {}
    author = (payload.get("author") or "anonymous").strip()[:64]
    body = (payload.get("body") or "").strip()[:500]
    if not body:
        return jsonify(error="Write a message before saving it."), 400
    try:
        conn = get_conn()
    except mysql.connector.Error as exc:
        return jsonify(error="database unavailable", detail=str(exc)), 503
    try:
        ensure_schema(conn)
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (author, body) VALUES (%s, %s)",
                    (author, body))
        conn.commit()
        cur.close()
    finally:
        conn.close()
    return jsonify(status="saved", pod=POD_NAME), 201


@app.get("/api/weather")
def weather():
    try:
        res = requests.get(WEATHER_URL, timeout=5)
        res.raise_for_status()
        current = res.json()["current_weather"]
    except (requests.RequestException, ValueError, KeyError) as exc:
        return jsonify(error="weather service unavailable", detail=str(exc)), 502
    code = current.get("weathercode")
    return jsonify(
        location=WEATHER_LOCATION,
        temperature=current.get("temperature"),
        windspeed=current.get("windspeed"),
        weathercode=code,
        description=WEATHER_CODES.get(code, "Unknown conditions"),
        observed_at=current.get("time"),
        pod=POD_NAME,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)