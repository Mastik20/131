"""Utilities for scraping text content and classifying cybersecurity-related texts."""
from __future__ import annotations

from typing import Dict, List

OLLAMA_URL = "http://localhost:11434/api/chat"


def extract_visible_text(url: str) -> List[str]:
    """
    Load a dynamic page and extract visible text lines.

    The function avoids executing custom JavaScript in ``evaluate``
    and instead relies on Playwright's ``all_inner_texts`` helper.
    Playwright is imported lazily to prevent mandatory dependency
    failures when the function is not used.
    """

    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("Playwright must be installed to extract text") from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=60_000)
        raw_texts = page.locator("body").all_inner_texts()

        cleaned: List[str] = []
        for block in raw_texts:
            for line in block.split("\n"):
                normalized_line = " ".join(line.split()).strip()
                if normalized_line:
                    cleaned.append(normalized_line)

        browser.close()
        return cleaned


def classify_cybersecurity(texts: List[str]) -> List[Dict[str, str]]:
    """
    Classify whether each text relates to cybersecurity topics.

    The function sends each text to an Ollama chat model and returns a
    structured list that includes both the raw model response and a
    normalized label (``"да"`` or ``"нет"``).
    """

    try:
        import requests
    except ModuleNotFoundError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError("The 'requests' package is required to classify text") from exc

    system_prompt = (
        "Ты получаешь один текст. "
        "Нужно определить, связан ли он с кибербезопасностью "
        "(атаки, взломы, DDoS, вирусы, уязвимости, безопасность сетей, "
        "шифрование, защита данных, пароли, фишинг, SOC, malware и т.п.).\n\n"
        "Если текст связан с кибербезопасностью — отвечай СТРОГО: да\n"
        "Если не связан — СТРОГО: нет\n\n"
        "Не добавляй никаких пояснений, только одно слово: да или нет."
    )

    results: List[Dict[str, str]] = []

    for text in texts:
        payload = {
            "model": "deepseek-r1:8b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "stream": False,
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        ai_raw = str(data["message"]["content"]).strip().lower()

        if ai_raw.startswith("да"):
            label = "да"
        elif ai_raw.startswith("нет"):
            label = "нет"
        else:
            label = "да" if "кибербез" in ai_raw or "cyber" in ai_raw else "нет"

        results.append({"text": text, "ai_raw": ai_raw, "label": label})

    return results
