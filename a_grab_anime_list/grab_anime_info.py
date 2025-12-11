#!/usr/bin/env python3
"""
Grab detail info tiap anime dari otakudesu.fit.
Membaca daftar seri dari anime_series_clean.json lalu menyimpan hasil detail
ke anime_info_clean.json di folder yang sama.
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup


INPUT_FILE = Path(__file__).parent / "anime_series_clean.json"
OUTPUT_FILE = Path(__file__).parent / "anime_info_clean.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch_html(session: requests.Session, url: str, timeout: int = 15) -> str:
    """Ambil HTML dengan error handling sederhana."""
    try:
        res = session.get(url, timeout=timeout)
        res.raise_for_status()
        return res.text
    except requests.RequestException as exc:
        print(f"Gagal fetch {url}: {exc}")
        return ""


def parse_info_block(info_block: BeautifulSoup) -> Dict[str, str]:
    """Parse blok infozingle menjadi dict key/value."""
    data: Dict[str, str] = {}
    if not info_block:
        return data

    for p in info_block.find_all("p"):
        text = p.get_text(" ", strip=True)
        if ":" not in text:
            continue
        key, value = text.split(":", 1)
        key_norm = key.strip().lower()
        value = value.strip()

        # Normalisasi key ke bahasa Inggris sederhana
        if key_norm == "judul":
            data["title_detail"] = value
        elif key_norm == "japanese":
            data["title_jp"] = value
        elif key_norm in {"skor", "score"}:
            data["score"] = value
        elif key_norm in {"produser", "producers"}:
            data["producers"] = value
        elif key_norm == "tipe":
            data["type"] = value
        elif key_norm == "status":
            data["status"] = value
        elif key_norm in {"total episode", "total eps"}:
            data["total_episode"] = value
        elif key_norm == "durasi":
            data["duration"] = value
        elif key_norm in {"rilis", "release", "tanggal rilis"}:
            data["release_date"] = value
        elif key_norm == "genre":
            # gabungkan genre yang mungkin ada link terpisah
            links = [a.get_text(strip=True) for a in p.find_all("a")]
            data["genres"] = ", ".join(links) if links else value
        else:
            # simpan key lain apa adanya
            data[key_norm] = value

    return data


def parse_synopsis(soup: BeautifulSoup) -> str:
    """Ambil sinopsis dari blok sinopc."""
    sinop_block = soup.find("div", class_=re.compile(r"sinopc"))
    if not sinop_block:
        return ""
    sinop_text = sinop_block.get_text(" ", strip=True)
    return sinop_text


def parse_cover(soup: BeautifulSoup) -> str:
    """Ambil url cover bila ada."""
    cover_block = soup.find("div", class_=re.compile(r"fotoanime"))
    if not cover_block:
        return ""
    img = cover_block.find("img")
    if not img:
        return ""
    return img.get("data-src") or img.get("src") or ""


def grab_anime_info(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Iterasi daftar series dan kumpulkan detail info."""
    session = requests.Session()
    session.headers.update(HEADERS)

    results: List[Dict[str, Any]] = []

    for idx, item in enumerate(entries, 1):
        url = item.get("url", "")
        if not url:
            continue

        print(f"[{idx}/{len(entries)}] Fetch detail: {url}")
        html = fetch_html(session, url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        info_block = soup.find("div", class_=re.compile(r"infozingle"))
        info_data = parse_info_block(info_block)
        synopsis = parse_synopsis(soup)
        cover = parse_cover(soup)

        merged = {
            **item,
            **info_data,
            "synopsis": synopsis,
            "cover_url": cover or item.get("image_url", ""),
        }
        results.append(merged)
        time.sleep(1)  # simple throttle

    return results


def main() -> None:
    if not INPUT_FILE.exists():
        print(f"Input tidak ditemukan: {INPUT_FILE}")
        return

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        entries = json.load(f)

    details = grab_anime_info(entries)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(details)} items to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

