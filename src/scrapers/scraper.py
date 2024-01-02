from pathlib import Path
from argparse import ArgumentParser
import requests
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess
from icu_tokenizer import SentSplitter
import yaml
from bs4 import BeautifulSoup

SPLITTER = SentSplitter("ff")

class MySpider(Spider):
    name = "bible"
    output_folder = name
    with open("extra/links.yml") as links_file:
        links = yaml.safe_load(links_file)
    languages, start_urls = zip(*links.items())
    codes = [url.split(".")[-1] for url in start_urls]
    mapping = dict(zip(codes, languages))

    def download_audio(self, audio_src, output_file):
        data = requests.get(audio_src)
        with open(output_file, 'wb') as out_mp3:
            out_mp3.write(data.content)
            return True, Path(output_file).stem

    def get_audio_page(self, url):


    def parse(self, response):
        content_to_pass = {"ChapterContent_r___3KRx", "ChapterContent_label__R2PLt", "ChapterContent_note__YlDW0",
                           "ChapterContent_fr__0KsID", "ChapterContent_body__O3qjr", "ft", "w"}
        title = response.css("h1::text")
        title = title.get()
        book, chapter, code = response.url.split("/")[-1].split(".")[-3:]
        language = MySpider.mapping[code]

        output_folder = Path(f"{MySpider.output_folder}/raw/{language}")
        output_folder.mkdir(exist_ok=True, parents=True)
        output_filename = output_folder / f"{book}_{chapter}_{code}"

        with open(f"{output_folder}/{code}.books", "a+") as titles:
            titles.write(f"{book}\t{chapter}\t{title}\n")
        audio = response.css("div.pli-1:nth-child(4) > div:nth-child(1) > audio:nth-child(1)")
        if "src" in audio.attrib:
            audio = audio.attrib["src"]
            print(">>>>>>", audio)
            self.download_audio(audio, f"{output_filename}.mp3")
        with open(f"{output_filename}.txt", "w") as output_file:
            output_file.write(f"{title}\n")
            for content in response.css("div.ChapterContent_chapter__uvbXo div"):
                if content.attrib["class"] in content_to_pass:
                    continue
                spans = content.css("span span")
                if not spans:
                    text = " ".join(verse.strip() for verse in content.css("span *::text").getall())
                    text = text.strip()
                    if not text:
                        continue
                    for sent in SPLITTER.split(text):
                        output_file.write(f"{sent}\n")
                    continue
                verses = []
                for span in spans:
                    if span.attrib["class"] in content_to_pass:
                        continue
                    for verse in span.css("*::text").getall():
                        verses.append(verse.strip())
                text = " ".join(verses).strip()
                text = text.strip()
                if not text:
                    continue
                for sent in SPLITTER.split(text):
                    output_file.write(f"{sent}\n")
        next_page = response.css("div.\[pointer-events\:all\]:nth-child(2) > a:nth-child(1)")
        if next_page:
            yield Request(url=f"https://www.bible.com{next_page.attrib['href']}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-o", "--output_folder",
                        help="Where the output will be saved.")
    args = parser.parse_args()
    output_folder = args.output_folder
    process = CrawlerProcess()
    process.crawl(MySpider, name="bible-fula", output_folder=output_folder)
    process.start()