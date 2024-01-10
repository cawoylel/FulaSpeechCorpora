#!usr/bin/env python
# -*- coding: utf8 -*-
import logging
import re
from pathlib import Path
import sys
import requests
from urllib.parse import urlparse
from uuid import uuid4
from tqdm import tqdm
from scrapy import Request

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


logger = logging.getLogger(__name__)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

def _get_selenium_cookies(driver):
    driver_cookies = driver.get_cookies()
    cookies = {cookie['name']:cookie['value'] for cookie in driver_cookies}
    return cookies


def _get_selenium_driver():
    driver = webdriver.Firefox()
    return driver

def _download_audio(driver, audio_src, output_directory, filename):
    parsed_url = urlparse(audio_src)
    # Get filename
    print("REUESTING...")
    data = requests.get(audio_src, cookies=_get_selenium_cookies(driver), headers=headers, stream=True)
    print("REUESTING FINISHED")
    if data.status_code == 200:
        output_path = Path(output_directory) / "audio"
        output_path.mkdir(exist_ok=True, parents=True)
        with open(output_path / f"{filename}.mp3", 'wb') as out_mp3:
            out_mp3.write(data.content)

def get_text(response):
    print(response)

def download_data(urls, output_directory, skip_done):
    driver = _get_selenium_driver()
    accepted = False
    for full_url in tqdm(urls):
        filename = str(uuid4())
        filename = re.sub("-", "_", filename)
        driver.get(full_url)
        if not accepted:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'//button[@id="didomi-notice-agree-button"]'))).click()
            accepted = True
        audio_element = driver.find_element(By.XPATH, "//button[@class='m-cta m-cta--rounded m-cta--play-pause a-picto-play-pause--play']")
        ActionChains(driver).move_to_element(audio_element).click().perform()
        # Download audio
        audio_player = driver.find_element(By.XPATH, '/html/body/audio')
        audio_src = audio_player.get_attribute('src')
        _download_audio(driver, audio_src, output_directory, filename)
        text_element = driver.find_element(By.XPATH, "//p[@class='t-content__chapo']")
        title_element = driver.find_element(By.XPATH, "//h1[@class='a-page-title']")
        text_path = output_directory / "text"
        text_path.mkdir(exist_ok=True, parents=True)
        title_path = output_directory / "title"
        title_path.mkdir(exist_ok=True, parents=True)
        with open(text_path / f"{filename}.txt", "w") as output_text:
            output_text.write(text_element.text)
        with open(title_path / f"{filename}.title", "w") as output_text:
            output_text.write(title_element.text)

def get_bible_language_data(urls_file, output_directory, skip_done):

    # Generate URLs
    with open(urls_file, "r") as links:
        generated_urls = [line.strip() for line in links]
    logger.info("Generated {} URLs.".format(len(generated_urls)))

    full_output_directory = Path(output_directory) / "ff"
    full_output_directory.mkdir(exist_ok=True, parents=True)
    download_data(generated_urls, full_output_directory, skip_done)


def main(**kwargs):
    get_bible_language_data(**kwargs)


def _parse_args(argv):
    import argparse

    parser = argparse.ArgumentParser(description='Download Bible.is data.')
    parser.add_argument('--urls_file', required=True,
                        help='File containing the urls')
    parser.add_argument('--output-directory', default='.',
                        help="Path where the output directory should be store. Default: '.'.")
    parser.add_argument('--skip-done', action="store_true", default=False,
                        help="If --skip-done, existing files are skipped rather than re-downloaded.")
    args = parser.parse_args(argv)

    return vars(args)


if __name__ == '__main__':
    import sys
    pgrm_name, argv = sys.argv[0], sys.argv[1:]
    args = _parse_args(argv)

    logging.basicConfig(level=logging.INFO)
    main(**args)