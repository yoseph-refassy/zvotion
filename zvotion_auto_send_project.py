import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = "7893642419:AAGVX9WoWwDedz5vG7qhm-2kqqv_vO4PAK0"
CHANNEL_ID = "@zvotion"
BASE_URL = "https://rehobot.org/category/z-votion/"

def print_error(message):
    print(f"[ERROR] {message}")

def send_to_telegram(message: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"[SENT] {response.status_code} - Message sent successfully.")
    except requests.RequestException as e:
        print_error(f"Gagal mengirim ke Telegram: {e}")

def send_audio_to_telegram(audio_url: str, title: str, performer: str = "Z-Votion"):
    try:
        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()

        filename = "zvotion_audio.mp3"
        with open(filename, "wb") as f:
            f.write(audio_response.content)

        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
        with open(filename, "rb") as audio_file:
            files = {"audio": audio_file}
            data = {
                "chat_id": CHANNEL_ID,
                "title": title,
                "performer": performer
            }
            response = requests.post(telegram_url, data=data, files=files)
            response.raise_for_status()
            print(f"[SENT AUDIO] Audio terkirim: {title}")

        os.remove(filename)

    except requests.RequestException as e:
        print_error(f"Gagal mengirim audio: {e}")
    except Exception as e:
        print_error(f"Kesalahan umum saat kirim audio: {e}")

def extract_article_content(url: str) -> str:
    try:
        res = requests.get(url)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        content_div = soup.select_one("div.entry-content")
        paragraphs = content_div.find_all("p")
        return "\n\n".join(p.get_text(separator="\n", strip=True) for p in paragraphs)
    except Exception as e:
        print_error(f"Gagal mengambil konten dari {url}: {e}")
        return ""

def extract_audio_url(soup: BeautifulSoup) -> str:
    audio_tag = soup.find("audio")
    return audio_tag['src'] if audio_tag and audio_tag.has_attr("src") else ""

def format_message(date: datetime, category: str, link: str, content: str) -> str:
    return (
        f"<i>{category} — {date.strftime('%d %B %Y')}</i>\n"
        f"{link}\n\n"
        f"{content}"
    )

def process_article(article, label: str, require_today: bool = False) -> None:
    date_tag = article.select_one("time.entry-date")
    link_tag = article.select_one("h2.entry-title a")

    if not date_tag or not date_tag.has_attr("datetime") or not link_tag:
        print_error(f"Artikel tidak lengkap untuk {label}")
        return

    article_date = datetime.fromisoformat(date_tag['datetime']).date()
    if require_today and article_date != datetime.today().date():
        print(f"[SKIP] Tidak ada renungan hari ini untuk {label}")
        return

    article_link = link_tag['href']
    try:
        detail_res = requests.get(article_link)
        detail_res.raise_for_status()
        soup = BeautifulSoup(detail_res.text, 'html.parser')

        # Ambil konten
        content = extract_article_content(article_link)
        message = format_message(article_date, label, article_link, content)
        send_to_telegram(message)

        # Kirim audio jika ada
        audio_url = extract_audio_url(soup)
        if audio_url:
            send_audio_to_telegram(
                audio_url,
                title=f"{label} - {article_date.strftime('%d %B %Y')}"
            )

    except Exception as e:
        print_error(f"Gagal memproses artikel {label}: {e}")

def fetch_devotions():
    try:
        res = requests.get(BASE_URL)
        res.raise_for_status()
    except requests.RequestException as e:
        print_error(f"Gagal mengakses halaman utama: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.select("article")

    if len(articles) < 2:
        print_error("Artikel tidak cukup ditemukan (minimal 2 diperlukan).")
        return

    process_article(articles[0], "Z-Votion", require_today=True)
    process_article(articles[1], "Z-Votion (English)")

if __name__ == "__main__":
    fetch_devotions()
