#!usr/bin/env python
# -*- coding: utf8 -*-
import logging
import re
from pathlib import Path
import asyncio
import sys
import requests
from uuid import uuid4
from tqdm import tqdm
import aiohttp
# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
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
    try:
        async with session.get(url=audio_src, cookies=_get_selenium_cookies(driver), headers=headers) as data:
            if data.status == 200:
                output_path = Path(output_directory) / "audio"
                output_path.mkdir(exist_ok=True, parents=True)
                content = await data.content.read()
                with open(output_path / f"{filename}.mp3", 'wb') as out_mp3:
                    out_mp3.write(content)
    except:
        print(f"Unable to download {audio_src}")
async def bounded_fetch(sem, driver, audio_src, output_directory, filename, session):
    async with sem:
        await _download_audio(driver, audio_src, output_directory, filename, session)

async def download_data(urls, output_directory):
    driver = _get_selenium_driver()
    errors = []
    accepted = False
    batch_size = 200
    sem = asyncio.Semaphore(batch_size)  # Generally, most OS's don't allow you to make more than 1024 sockets unless you personally fine-tuned your system. 
    tasks = []
    n = len(urls)
    batches = [urls[ndx:min(ndx + batch_size, n)] for ndx in range(0, n, batch_size)]
    for idx, batch in tqdm(list(enumerate(batches))):
        async with aiohttp.ClientSession(trust_env=True) as session:
            for full_url in tqdm(batch, desc=f"{idx}/{len(batches)}"):
                filename = str(uuid4())
                filename = re.sub("-", "_", filename)
                driver.get(full_url)
                try:
                    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//h1[@class="a-page-title"]')))
                except:
                    print()
                    print(f"Empty page {full_url}.")
                    continue
                if not accepted:
                    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH,'//button[@id="didomi-notice-agree-button"]'))).click()
                    accepted = True
                try:
                    audio_element = driver.find_element(By.XPATH, "//button[@class='m-cta m-cta--rounded m-cta--play-pause a-picto-play-pause--play']")
                except:
                    print()
                    print(f"Unable to find audio boutton {full_url}")
                    continue
                ActionChains(driver).move_to_element(audio_element).click().perform()
                # Download audio
                try:
                    audio_player = driver.find_element(By.XPATH, '/html/body/audio')
                    audio_src = audio_player.get_attribute('src')
                except:
                    errors.append(full_url)
                    print()
                    print(f"No audio source for {full_url}")
                    continue
                if not audio_src:
                    print()
                    print(f"Empty link {audio_src}")
                    continue
                task = asyncio.ensure_future(bounded_fetch(sem, driver, audio_src, output_directory, filename, session))
                tasks.append(task)
                try:
                    text_element = driver.find_element(By.XPATH, "//p[@class='t-content__chapo']")
                    title_element = driver.find_element(By.XPATH, "//h1[@class='a-page-title']")
                except:
                    print(f"No content for the url {full_url}")
                    continue
                # We can possibly do this in a multiprocess way
                text_path = output_directory / "text"
                text_path.mkdir(exist_ok=True, parents=True)
                title_path = output_directory / "title"
                title_path.mkdir(exist_ok=True, parents=True)
                with open(text_path / f"{filename}.txt", "w") as output_text:
                    output_text.write(text_element.text)
                with open(title_path / f"{filename}.title", "w") as output_text:
                        output_text.write(title_element.text)
            await asyncio.gather(*tasks)
    with open("errors.txt", "+a") as errors_file:
        errors_file.write("\n".join(errors))

async def main(kwargs):
    # Generate URLs
    with open(kwargs["urls_file"], "r") as links:
        generated_urls = [line.strip() for line in links]
    logger.info("Generated {} URLs.".format(len(generated_urls)))

    full_output_directory = Path(kwargs["output_directory"])
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