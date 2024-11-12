import csv
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://quotes.toscrape.com/"


def safe_request(url: str) -> requests.Response:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


@dataclass
class Author:
    name: str
    biography: str
    birth_date: str
    birth_place: str


def parse_single_page(page_content: str) -> list[Quote]:
    soup = BeautifulSoup(page_content, "html.parser")
    quotes = []
    for quote in soup.select(".quote"):
        quotes.append(Quote(
            text=quote.select_one(".text").text,
            author=quote.select_one(".author").text,
            tags=[tag.text for tag in quote.select(".tag")],
        ))
    return quotes


def get_num_pages() -> int:
    page_number = 1

    while True:
        response = safe_request(f"{BASE_URL}page/{page_number}")
        if not response:
            break

        soup = BeautifulSoup(response.content, "html.parser")
        if not soup.select_one(".next"):
            break
        page_number += 1
    return page_number


def write_to_csv(data: list, output_csv_path: str, fieldnames: list) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            writer.writerow(item)


def get_all_quotes() -> list[Quote]:
    quotes = []
    num_pages = get_num_pages()
    for i in range(1, num_pages + 1):
        response = safe_request(f"{BASE_URL}page/{i}")
        if not response:
            continue
        quotes.extend(parse_single_page(response.content))
    return quotes


def main(output_csv_path: str) -> None:
    quotes = get_all_quotes()

    quotes_data = [
        {
            "text": quote.text,
            "author": quote.author,
            "tags": ", ".join(quote.tags)
        }
        for quote in quotes
    ]
    write_to_csv(quotes_data, output_csv_path, ["text", "author", "tags"])


if __name__ == "__main__":
    main("quotes.csv")
