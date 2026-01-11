#!/usr/bin/env python3
import argparse
import json
import os
import signal
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

LOCKFILE_PATH = os.path.join(tempfile.gettempdir(), "monitor_agent.lock")


def ensure_single_instance(lockfile: str = LOCKFILE_PATH) -> None:
    os.makedirs(os.path.dirname(lockfile), exist_ok=True)
    if os.path.exists(lockfile):
        with open(lockfile, "r", encoding="utf-8") as handle:
            contents = handle.read().strip()
        if contents:
            try:
                existing_pid = int(contents)
            except ValueError:
                existing_pid = None
            if existing_pid and os.path.exists(f"/proc/{existing_pid}"):
                raise RuntimeError(f"Agent already running with pid {existing_pid}")
    with open(lockfile, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))


def cleanup_lockfile(lockfile: str = LOCKFILE_PATH) -> None:
    if os.path.exists(lockfile):
        os.remove(lockfile)


def daemonize() -> None:
    if os.fork() > 0:
        sys.exit(0)
    os.setsid()
    if os.fork() > 0:
        sys.exit(0)
    sys.stdout.flush()
    sys.stderr.flush()
    with open("/dev/null", "r") as dev_null:
        os.dup2(dev_null.fileno(), sys.stdin.fileno())
    with open("/dev/null", "a+") as dev_null:
        os.dup2(dev_null.fileno(), sys.stdout.fileno())
        os.dup2(dev_null.fileno(), sys.stderr.fileno())


@dataclass
class AgentConfig:
    server_url: str
    host: str
    interval: int = 10
    token: Optional[str] = None


class MetricsCollector:
    @staticmethod
    def _get_cpu_percent() -> float:
        try:
            load_1, _, _ = os.getloadavg()
            cpu_count = os.cpu_count() or 1
            return min(100.0, (load_1 / cpu_count) * 100.0)
        except (AttributeError, OSError):
            return 0.0

    @staticmethod
    def _get_memory_percent() -> float:
        try:
            page_size = os.sysconf("SC_PAGE_SIZE")
            phys_pages = os.sysconf("SC_PHYS_PAGES")
            avail_pages = os.sysconf("SC_AVPHYS_PAGES")
        except (ValueError, OSError, AttributeError):
            return 0.0
        total = page_size * phys_pages
        available = page_size * avail_pages
        if total == 0:
            return 0.0
        used = total - available
        return (used / total) * 100.0

    @staticmethod
    def _get_disk_percent() -> float:
        try:
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            available = stat.f_bavail * stat.f_frsize
        except OSError:
            return 0.0
        if total == 0:
            return 0.0
        used = total - available
        return (used / total) * 100.0

    def collect(self) -> Dict[str, float]:
        return {
            "cpu": round(self._get_cpu_percent(), 2),
            "memory": round(self._get_memory_percent(), 2),
            "disk": round(self._get_disk_percent(), 2),
        }


def load_config(path: str) -> AgentConfig:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return AgentConfig(
        server_url=data["server_url"].rstrip("/"),
        host=data.get("host") or os.uname().nodename,
        interval=int(data.get("interval", 10)),
        token=data.get("token"),
    )


def post_metrics(config: AgentConfig, metrics: Dict[str, float]) -> None:
    payload: Dict[str, Any] = {
        "host": config.host,
        "metrics": metrics,
        "timestamp": int(time.time()),
    }
    headers = {}
    if config.token:
        headers["Authorization"] = f"Bearer {config.token}"
    response = requests.post(
        f"{config.server_url}/api/v1/metrics",
        json=payload,
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()


def run_agent(config: AgentConfig) -> None:
    collector = MetricsCollector()

    def handle_exit(signum: int, frame: Any) -> None:
        cleanup_lockfile()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    ensure_single_instance()
    while True:
        metrics = collector.collect()
        post_metrics(config, metrics)
        time.sleep(config.interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Monitoring agent")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.daemon:
        daemonize()
    run_agent(config)


if __name__ == "__main__":
    main()
