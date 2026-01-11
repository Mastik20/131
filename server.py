#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, redirect, render_template, request, url_for

DATABASE_PATH = os.environ.get("MONITOR_DB", "monitoring.db")


@dataclass
class ServerConfig:
    token: Optional[str] = None
    thresholds: Optional[Dict[str, float]] = None


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                cpu REAL NOT NULL,
                memory REAL NOT NULL,
                disk REAL NOT NULL,
                FOREIGN KEY(host_id) REFERENCES hosts(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                host_id INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY(host_id) REFERENCES hosts(id)
            )
            """
        )


def load_config(path: Optional[str]) -> ServerConfig:
    if not path:
        return ServerConfig()
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return ServerConfig(
        token=data.get("token"),
        thresholds=data.get("thresholds"),
    )


def authenticate_request(config: ServerConfig) -> bool:
    if not config.token:
        return True
    auth_header = request.headers.get("Authorization", "")
    return auth_header == f"Bearer {config.token}"


def get_or_create_host(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM hosts WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    cursor = conn.execute("INSERT INTO hosts (name) VALUES (?)", (name,))
    return int(cursor.lastrowid)


def check_alerts(
    conn: sqlite3.Connection,
    host_id: int,
    metrics: Dict[str, float],
    thresholds: Optional[Dict[str, float]],
    timestamp: int,
) -> None:
    if not thresholds:
        return
    for metric, value in metrics.items():
        threshold = thresholds.get(metric)
        if threshold is None:
            continue
        if value >= threshold:
            message = f"{metric} usage {value:.2f}% exceeded {threshold:.2f}%"
            conn.execute(
                "INSERT INTO alerts (host_id, timestamp, message) VALUES (?, ?, ?)",
                (host_id, timestamp, message),
            )


@app.route("/")
def index() -> Any:
    return redirect(url_for("hosts"))


@app.route("/hosts")
def hosts() -> Any:
    with get_db() as conn:
        rows = conn.execute("SELECT name FROM hosts ORDER BY name").fetchall()
    host_list = [row["name"] for row in rows]
    return render_template("hosts.html", hosts=host_list)


@app.route("/hosts/<host>")
def host_detail(host: str) -> Any:
    return render_template("host_detail.html", host=host)


@app.route("/alerts")
def alerts_page() -> Any:
    return render_template("alerts.html")


@app.route("/api/v1/metrics", methods=["POST"])
def api_metrics() -> Any:
    config: ServerConfig = app.config["SERVER_CONFIG"]
    if not authenticate_request(config):
        return jsonify({"error": "unauthorized"}), 401
    data = request.get_json(silent=True) or {}
    host = data.get("host")
    metrics = data.get("metrics")
    timestamp = int(data.get("timestamp", time.time()))
    if not host or not metrics:
        return jsonify({"error": "host and metrics are required"}), 400
    with get_db() as conn:
        host_id = get_or_create_host(conn, host)
        conn.execute(
            """
            INSERT INTO metrics (host_id, timestamp, cpu, memory, disk)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                host_id,
                timestamp,
                float(metrics.get("cpu", 0.0)),
                float(metrics.get("memory", 0.0)),
                float(metrics.get("disk", 0.0)),
            ),
        )
        check_alerts(conn, host_id, metrics, config.thresholds, timestamp)
    return jsonify({"status": "ok"})


@app.route("/api/v1/hosts", methods=["GET"])
def api_hosts() -> Any:
    with get_db() as conn:
        rows = conn.execute("SELECT name FROM hosts ORDER BY name").fetchall()
    return jsonify({"hosts": [row["name"] for row in rows]})


@app.route("/api/v1/metrics/<host>", methods=["GET"])
def api_host_metrics(host: str) -> Any:
    limit = int(request.args.get("limit", 50))
    with get_db() as conn:
        row = conn.execute("SELECT id FROM hosts WHERE name = ?", (host,)).fetchone()
        if not row:
            return jsonify({"metrics": []})
        host_id = row["id"]
        rows = conn.execute(
            """
            SELECT timestamp, cpu, memory, disk
            FROM metrics
            WHERE host_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (host_id, limit),
        ).fetchall()
    metrics_data = [
        {
            "timestamp": row["timestamp"],
            "cpu": row["cpu"],
            "memory": row["memory"],
            "disk": row["disk"],
        }
        for row in rows
    ]
    return jsonify({"metrics": list(reversed(metrics_data))})


@app.route("/api/v1/alerts", methods=["GET"])
def api_alerts() -> Any:
    since = request.args.get("since")
    with get_db() as conn:
        if since:
            rows = conn.execute(
                """
                SELECT hosts.name, alerts.timestamp, alerts.message
                FROM alerts
                JOIN hosts ON hosts.id = alerts.host_id
                WHERE alerts.timestamp >= ?
                ORDER BY alerts.timestamp DESC
                """,
                (int(since),),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT hosts.name, alerts.timestamp, alerts.message
                FROM alerts
                JOIN hosts ON hosts.id = alerts.host_id
                ORDER BY alerts.timestamp DESC
                """,
            ).fetchall()
    alerts = [
        {
            "host": row["name"],
            "timestamp": row["timestamp"],
            "message": row["message"],
        }
        for row in rows
    ]
    return jsonify({"alerts": alerts})


def build_host_chart_data(metrics: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    labels = [m["timestamp"] for m in metrics]
    return {
        "labels": labels,
        "cpu": [m["cpu"] for m in metrics],
        "memory": [m["memory"] for m in metrics],
        "disk": [m["disk"] for m in metrics],
    }


def create_app(config: ServerConfig) -> Flask:
    app.config["SERVER_CONFIG"] = config
    init_db()
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitoring server")
    parser.add_argument("--config", help="Path to JSON config")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()

    config = load_config(args.config)
    create_app(config)
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
