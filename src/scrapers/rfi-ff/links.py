import re
from argparse import ArgumentParser
from pathlib import Path
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess

def make_start_urls(page_urls):
    links = set()
    for link in page_urls:
        links.add(f"{link}/")
        last_page = re.search(r"(\d+)$", link)
        if not last_page:
            continue
        links.add(re.sub(r"(/\d+/)$", "/", link))
        last_page = int(last_page.group())
        pages = {re.sub(r"(\d+)$", f"{str(page)}/", link) for page in range(last_page - 1, 1, -1)}
        links |= pages
    return list(links)

class RfiScraper(Spider):
    name = "rfi-ff-links"
    download_delay = 1
    page_urls = [
        "https://www.rfi.fr/ff/taskaramji/cellal-ko-ngalu/11",
        "https://www.rfi.fr/ff/taskaramji/%C9%93amtaare-dowri",
        "https://www.rfi.fr/ff/taskaramji/coftal-%C9%93alli-men",
        "https://www.rfi.fr/ff/taskaramji/dianke-janke",
        "https://www.rfi.fr/ff/taskaramji/dinngiral-rew%C9%93e/11",
        "https://www.rfi.fr/ff/taskaramji/faggudu-e-%C9%93amtaare-afrik/11",
        "https://www.rfi.fr/ff/taskaramji/kabaaruuji-yontere/11",
        "https://www.rfi.fr/ff/taskaramji/kiwal-taariindi/11",
        "https://www.rfi.fr/ff/taskaramji/ko%C9%97o-maw%C9%97o/11",
        "https://www.rfi.fr/ff/taskaramji/ko%C9%97o-men-hannde/48",
        "https://www.rfi.fr/ff/taskaramji/ko-mbiidon/31",
        "https://www.rfi.fr/ff/taskaramji/laawol-ganndal-e-needi/11",
        "https://www.rfi.fr/ff/taskaramji/on-tottaama-konngol/54"
        ]
    start_urls = make_start_urls(page_urls)

    def __init__(self, output_folder: str):
        self.output_folder = Path(output_folder)
        self.output_file = self.output_folder / f"{RfiScraper.name}.txt"

        
    def parse(self, response):
        with open(self.output_file, "+a") as output_file:
            for url in response.css("a.m-podcast-item__infos__edition"):
                output_file.write(f"https://www.rfi.fr{url.attrib['href']}\n")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-o", "--output_folder",
                        help="Where the output will be saved.")
    args = parser.parse_args()
    process = CrawlerProcess({
                'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +https://www.rfi.fr)'
            })
    process.crawl(RfiScraper, output_folder=args.output_folder)
    process.start()