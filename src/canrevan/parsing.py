import re
from typing import List

from bs4 import BeautifulSoup, SoupStrainer

import canrevan.utils as utils


def extract_article_urls(document: str) -> List[str]:
    document = document[document.find('<ul class="type06_headline">') :]

    # Extract article url containers.
    list1 = document[: document.find("</ul>")]
    list2 = document[document.find("</ul>") + 5 :]
    list2 = list2[: list2.find("</ul>")]

    document = list1 + list2

    # Extract all article urls from the containers.
    article_urls = []
    while "<dt>" in document:
        document = document[document.find("<dt>") :]
        container = document[: document.find("</dt>")]

        if not container.strip():
            continue

        article_urls.append(re.search(r'<a href="(.*?)"', container).group(1))
        document = document[document.find("</dt>") :]

    return article_urls


def parse_article_content(document: str) -> str:
    strainer = SoupStrainer("div", attrs={"id": "articleBodyContents"})
    metadata = BeautifulSoup(document, "lxml")
    document = BeautifulSoup(document, "lxml", parse_only=strainer)
    content = document.find("div")

    # Get headline & datetime
    headline = metadata.select_one("#articleTitle").text.strip()
    datetime = metadata.select_one(
        "#main_content > div.article_header > div.article_info > div > span.t11"
    ).text.strip()
    category = metadata.select_one("#lnb > ul > li.on > a > span.tx").text.strip()
    url = metadata.find("a", class_="naver-splugin").get("data-url").strip()

    # Skip invalid articles which do not contain news contents.
    if content is None:
        raise ValueError("there is no any news article content.")

    # Remove unnecessary tags except `<br>` elements for preserving line-break
    # characters.
    for child in content.find_all():
        if child.name != "br":
            child.clear()

    content = content.get_text(separator="\n").strip().replace("\t", " ")

    # Skip the contents which contain too many non-Korean characters.
    if utils.korean_character_ratio(content) < 0.5:
        raise ValueError("there are too few Korean characters in the content.")

    content = "\\n".join(
        [
            line.strip()
            for line in content.splitlines()
            if line.strip() and utils.korean_character_ratio(line) > 0.5
        ]
    )
    content = "\t".join([url, datetime, category, headline, content])

    return content
