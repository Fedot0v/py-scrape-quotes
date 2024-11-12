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
    author_url: str


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
        author_url = (
                BASE_URL + quote.select_one("a[href^='/author/']").get("href")
        )
        quotes.append(Quote(
            text=quote.select_one(".text").text,
            author=quote.select_one(".author").text,
            tags=[tag.text for tag in quote.select(".tag")],
            author_url=author_url,
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


def get_author_biography(author_url: str) -> Author:
    response = safe_request(author_url)
    if not response:
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    name = soup.select_one(".author-title").text.strip()
    biography = soup.select_one(".author-description").text.strip()
    birth_date = soup.select_one(".author-born-date").text.strip()
    birth_place = soup.select_one(".author-born-location").text.strip()
    return Author(name, biography, birth_date, birth_place)


def write_authors_to_csv(
        authors: dict[str, Author],
        output_csv_path: str
) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["name", "biography", "birth_date", "birth_place"])
        writer.writeheader()
        for author in authors.values():
            writer.writerow(
                {"name": author.name,
                 "biography": author.biography,
                 "birth_date": author.birth_date,
                 "birth_place": author.birth_place
                 }
            )


def get_all_quotes() -> list[Quote]:
    quotes = []
    num_pages = get_num_pages()
    for i in range(1, num_pages + 1):
        response = safe_request(f"{BASE_URL}page/{i}")
        if not response:
            continue

        quotes.extend(parse_single_page(response.content))
    return quotes


def main(output_csv_path: str, output_authors_csv: str) -> None:
    quotes = get_all_quotes()

    with open(
            output_csv_path,
            mode="w",
            encoding="utf-8",
            newline=""
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["text", "author", "tags"]
        )
        writer.writeheader()

        for quote in quotes:
            writer.writerow(
                {
                    "text": quote.text,
                    "author": quote.author,
                    "tags": ", ".join(quote.tags)
                }
            )

    authors = {}
    for quote in quotes:
        if quote.author not in authors:
            author_data = get_author_biography(quote.author_url)
            if author_data:
                authors[quote.author] = author_data

    write_authors_to_csv(authors, output_authors_csv)


if __name__ == "__main__":
    main("quotes.csv", "authors.csv")
