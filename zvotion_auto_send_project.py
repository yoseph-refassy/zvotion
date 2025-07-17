import requests
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = "7893642419:AAGVX9WoWwDedz5vG7qhm-2kqqv_vO4PAK0"
CHANNEL_ID = "@zvotion"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    res = requests.post(url, json=payload)
    print("Status:", res.status_code)
    print("Response:", res.text)

def format_message(date, category, link, content):
    timestamp = datetime.now().strftime('%H:%M:%S')
    return (
        f"[{timestamp}]\n"
        f"<i>{category} — {date.strftime('%d %B %Y')}</i>\n"
        f"{link}\n\n"
        f"{content}"
    )

def fetch_devotions():
    base_url = "https://rehobot.org/category/z-votion/"
    try:
        res = requests.get(base_url, headers=HEADERS, timeout=10)
        res.raise_for_status()
    except Exception as e:
        send_to_telegram(f"❌ Gagal mengakses halaman utama: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    articles = soup.select("article")
    if len(articles) < 2:
        send_to_telegram("❌ Artikel kurang dari dua, tidak bisa fetch renungan.")
        return

    # Bahasa Indonesia
    indo_article = articles[0]
    indo_date_tag = indo_article.select_one("time.entry-date")
    indo_date = datetime.fromisoformat(indo_date_tag['datetime']).date() if indo_date_tag and indo_date_tag.has_attr("datetime") else datetime.today().date()
    indo_link_tag = indo_article.select_one("h2.entry-title a")
    indo_link = indo_link_tag['href']

    indo_detail = requests.get(indo_link, headers=HEADERS, timeout=10)
    indo_soup = BeautifulSoup(indo_detail.text, 'html.parser')
    indo_content_div = indo_soup.select_one("div.entry-content")
    indo_paragraphs = indo_content_div.find_all("p")
    indo_content = "\n\n".join(p.get_text(separator="\n", strip=True) for p in indo_paragraphs)

    indo_message = format_message(
        indo_date,
        "Z-Votion",
        indo_link,
        indo_content
    )
    send_to_telegram(indo_message)

    # Bahasa Inggris
    eng_article = articles[1]
    eng_date_tag = eng_article.select_one("time.entry-date")
    eng_date = datetime.fromisoformat(eng_date_tag['datetime']).date() if eng_date_tag and eng_date_tag.has_attr("datetime") else datetime.today().date()
    eng_link_tag = eng_article.select_one("h2.entry-title a")
    eng_link = eng_link_tag['href']

    eng_detail = requests.get(eng_link, headers=HEADERS, timeout=10)
    eng_soup = BeautifulSoup(eng_detail.text, 'html.parser')
    eng_content_div = eng_soup.select_one("div.entry-content")
    eng_paragraphs = eng_content_div.find_all("p")
    eng_content = "\n\n".join(p.get_text(separator="\n", strip=True) for p in eng_paragraphs)

    eng_message = format_message(
        eng_date,
        "Z-Votion (English)",
        eng_link,
        eng_content
    )
    send_to_telegram(eng_message)

if __name__ == "__main__":
    fetch_devotions()
