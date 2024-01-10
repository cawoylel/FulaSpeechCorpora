#!usr/bin/env python
# -*- coding: utf8 -*-
import logging
import re
from pathlib import Path
import asyncio
import sys
import requests
from urllib.parse import urlparse
from uuid import uuid4
from tqdm import tqdm
import aiohttp
import socket 

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

async def _download_audio(driver, audio_src, output_directory, filename, session):
    print(audio_src)
    async with session.get(url=audio_src, cookies=_get_selenium_cookies(driver), headers=headers) as data:
        if data.status == 200:
            output_path = Path(output_directory) / "audio"
            output_path.mkdir(exist_ok=True, parents=True)
            content = await data.content.read()
            with open(output_path / f"{filename}.mp3", 'wb') as out_mp3:
                out_mp3.write(content)

async def bounded_fetch(sem, driver, audio_src, output_directory, filename, session):
    async with sem:
        await _download_audio(driver, audio_src, output_directory, filename, session)

def get_text(response):
    print(response)

async def download_data(urls, output_directory):
    conn = aiohttp.TCPConnector(
            family=socket.AF_INET,
            verify_ssl=False,
        )
    driver = _get_selenium_driver()
    accepted = False
    batch_size = 100
    sem = asyncio.Semaphore(batch_size)  # Generally, most OS's don't allow you to make more than 1024 sockets unless you personally fine-tuned your system. 
    tasks = []
    n = len(urls)
    batches = [urls[ndx:min(ndx + batch_size, n)] for ndx in range(0, n, batch_size)]
    for batch in tqdm(batches):
        async with aiohttp.ClientSession(trust_env=True, connector=conn) as session:
            for full_url in tqdm(batch):
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
                task = asyncio.ensure_future(bounded_fetch(sem, driver, audio_src, output_directory, filename, session))
                tasks.append(task)
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
            await asyncio.gather(*tasks)



async def main(kwargs):
    # Generate URLs
    with open(kwargs["urls_file"], "r") as links:
        generated_urls = [line.strip() for line in links]
    logger.info("Generated {} URLs.".format(len(generated_urls)))

    full_output_directory = Path(kwargs["output_directory"]) / "ff"
    full_output_directory.mkdir(exist_ok=True, parents=True)
    await download_data(generated_urls, full_output_directory)


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
    asyncio.run(main(args))