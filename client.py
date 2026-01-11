#!/usr/bin/env python3
import argparse
import json
from typing import Any, Dict

import requests


def request_json(url: str) -> Dict[str, Any]:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def list_hosts(server: str) -> None:
    data = request_json(f"{server}/api/v1/hosts")
    for host in data.get("hosts", []):
        print(host)


def show_metrics(server: str, host: str) -> None:
    data = request_json(f"{server}/api/v1/metrics/{host}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def list_alerts(server: str, last_day: bool) -> None:
    url = f"{server}/api/v1/alerts"
    if last_day:
        import time

        since = int(time.time()) - 86400
        url = f"{url}?since={since}"
    data = request_json(url)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def stats(server: str, host: str, metric: str) -> None:
    data = request_json(f"{server}/api/v1/metrics/{host}")
    values = [item[metric] for item in data.get("metrics", []) if metric in item]
    if not values:
        print("No data")
        return
    print(f"min={min(values):.2f} max={max(values):.2f} avg={sum(values)/len(values):.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitoring CLI client")
    parser.add_argument("--server", default="http://localhost:8000", help="Server URL")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-hosts")

    show_metrics_parser = subparsers.add_parser("show-metrics")
    show_metrics_parser.add_argument("--host", required=True)

    alerts_parser = subparsers.add_parser("alerts")
    alerts_parser.add_argument("--last-day", action="store_true")

    stats_parser = subparsers.add_parser("stats")
    stats_parser.add_argument("--host", required=True)
    stats_parser.add_argument("--metric", required=True, choices=["cpu", "memory", "disk"])

    args = parser.parse_args()

    if args.command == "list-hosts":
        list_hosts(args.server)
    elif args.command == "show-metrics":
        show_metrics(args.server, args.host)
    elif args.command == "alerts":
        list_alerts(args.server, args.last_day)
    elif args.command == "stats":
        stats(args.server, args.host, args.metric)


if __name__ == "__main__":
    main()
