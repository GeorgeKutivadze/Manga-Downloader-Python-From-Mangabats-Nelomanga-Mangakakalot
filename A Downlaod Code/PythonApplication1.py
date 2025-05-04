import os
import re
import sys
import io
import time
import random
import logging
import tempfile
import subprocess
import zipfile
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from difflib import get_close_matches
from urllib.parse import urljoin, urlparse, quote_plus, parse_qs
from httpx import request
import requests
import cloudscraper
import pyautogui
from scipy.datasets import download_all
import tqdm
from PIL import Image, UnidentifiedImageError
from bs4 import BeautifulSoup
from mdurl import URL
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from tqdm import tqdm
from datetime import datetime
from urllib.parse import urljoin, quote_plus
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from PIL import Image
from PIL import UnidentifiedImageError
from urllib.parse import quote_plus
import urllib.parse
from urllib.parse import urlparse, parse_qs
from zipfile import ZipFile
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.adapters import HTTPAdapter, Retry
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException, ReadTimeout
from urllib3.util.retry import Retry
from typing import Optional, Dict
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException
)


# Base directory for manga storage
base_dir = r"E:\Z Mangas" # Write Path Here TO save It where You Wish
seven_zip_path = r"C:\Program Files\7-Zip\7z.exe"  # This is essential for creating CBZ files in Correct Format to Work in Kavita As well, without it it may work but kavita won't register it
chromedriver_path = r"C:\\chromedriver\\chromedriver.exe"
User_Agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"






def headers(manga_url_main: str | None = None, base_url: str | None = None, image_path: str | None = None, image_url: str | None = None,) -> dict:
    """Returns full HTTP headers dynamically based on manga_url_main."""
    if manga_url_main and image_url:
        
        header_dict = {
            "Authority":base_url,
            "Method": "GET",
            "Path": image_path,
            "scheme": "https",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,ka-GE;q=0.8,ka;q=0.7,ru-RU;q=0.6,ru;q=0.5",
            "Dnt": "1",
            "Priority": "i",
            "Referer": manga_url_main,
            "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-Storage-Access": "active",            
            "User-Agent": User_Agent,


            "Request URL": image_url,
            "Request Method": "GET",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

    else:
        header_dict = {}
        header_dict["User-Agent"]=User_Agent
        header_dict["Referer"] = ""


    return header_dict

def split_image_url(img_url: str) -> tuple[str, str]:

    if not img_url.startswith("https://"):
        raise ValueError("Only https:// URLs are supported")

    # Remove 'https://' for easier splitting
    stripped_url = img_url[len("https://"):]
    parts = stripped_url.split("/", 1)

    if len(parts) != 2:
        raise ValueError("URL format invalid, missing path after domain")

    domain, path = parts
    base_url = f"{domain}"
    image_path = f"/{path}"

    return base_url, image_path






def init_selenium():
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)


    chromedriver_path1 = chromedriver_path
    service = Service(chromedriver_path1)

    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": User_Agent
    })

    return driver

def human_like_interaction(driver):
    time.sleep(random.uniform(2, 5))  # Random delay between 2-5 seconds
    
    # Simulate scrolling
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(1, 3))
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(random.uniform(2, 5))

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def clean_title_for_search(title):
    # Step 1: Remove content along with brackets: [], (), {}
    title = re.sub(r"\[.*?\]|\(.*?\)|\{.*?\}", "", title)
    # Step 2: Replace non-alphanumeric characters (except spaces, dashes, and apostrophes) with spaces
    title = re.sub(r"[^\w\s\'-]", " ", title)
    # Step 3: Replace dashes with spaces to avoid word merging (e.g., "Sss-Class" -> "Sss Class")
    title = title.replace("-", " ")
    # Step 4: Normalize spaces and convert to lowercase
    title = re.sub(r"\s+", " ", title).strip().lower()
    # Step 5: Use urllib.parse.quote to encode the title for URL
    return urllib.parse.quote(title)

def normalize_text(text):
    """Normalize text by removing accents and converting to lowercase."""
    return unicodedata.normalize('NFKC', text).strip().lower()

def save_url(manga_dir, url):
    url_file_path = os.path.join(manga_dir, "url.txt")
    with open(url_file_path, "w", encoding="utf-8") as url_file:
        url_file.write(url)
    print(f"URL saved to {url_file_path}")

def update_combined_log():
    combined_log_path = os.path.join(base_dir, "combined_download_log.txt")

    with open(combined_log_path, "w", encoding="utf-8") as combined_log:
        combined_log.write(f"{'Manga Title':<30} {'Total Chapters':<15} {'Last Updated':<25}\n")
        combined_log.write("="*70 + "\n")
        
        for manga_folder in os.listdir(base_dir):
            manga_path = os.path.join(base_dir, manga_folder)
            if os.path.isdir(manga_path):
                log_file = os.path.join(manga_path, "download_log.txt")
                
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as individual_log:
                        chapters = individual_log.readlines()
                        if chapters:
                            last_updated = chapters[-1].strip().split("\t")[-1]
                            combined_log.write(f"{manga_folder:<30} {len(chapters):<15} {last_updated:<25}\n")

def log_error(manga_dir, error_message):
    error_log_path = os.path.join(manga_dir, "error_log.txt")
    with open(error_log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{datetime.now().isoformat()} - {error_message}\n")
    print(f"Error logged to {error_log_path}")




def save_html_as_txt(manga_dir, html_content):
    html_file_path = os.path.join(manga_dir, "page_content.txt")
    with open(html_file_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_content)
    return html_file_path

def extract_alternative_titles_from_file(manga_dir):
    """Extract alternative manga titles from the page_content.txt file."""
    page_content_path = os.path.join(manga_dir, "page_content.txt")
    
    if not os.path.exists(page_content_path):
        print(f"page_content.txt not found in {manga_dir}")
        return []

    # Read the content of the page_content.txt file
    with open(page_content_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML to extract alternative titles 
    soup = BeautifulSoup(html_content, 'html.parser')
    alternative_titles_tag = soup.find('h2', class_='story-alternative')
            
    if alternative_titles_tag:
        titles_text = alternative_titles_tag.text.strip()
                
        # Handle multiple delimiters: semicolon, comma, etc.
        delimiters = [';', ',']
        for delimiter in delimiters:
            if delimiter in titles_text:
                alternative_titles = [title.strip() for title in titles_text.split(delimiter)]
                return alternative_titles

    print("No alternative titles found in page_content.txt.")
    return []

def extract_alternative_titles(html_content):
    """Extract alternative manga titles from the HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    alternative_titles_tag = soup.find('td', class_='table-label', string='Alternative')

    if alternative_titles_tag:
        alternative_titles_value = alternative_titles_tag.find_next_sibling('td', class_='table-value')
        if alternative_titles_value:
            titles_text = alternative_titles_value.get_text(separator=';')
            alternative_titles = [title.strip() for title in titles_text.split(';') if title.strip()]
            return alternative_titles

    return []

def extract_and_download_cover(manga_dir, html_file_path, base_url, manga_title, alt_site_url, manga_url_main):
    success = search_mangadex_and_download_cover_selenium(manga_title, manga_dir, alt_site_url)  # Use Selenium-based search
    if success:
        return

    print("Falling back to original method to download cover image.")
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    cover_img_tag = soup.find('div', class_='manga-info-pic') 
    
    if not cover_img_tag or not cover_img_tag.get('src'):
        log_error(manga_dir, "Cover image tag not found or missing 'src' attribute.")
        return

    cover_img_url = cover_img_tag.get('src')


    img_name = f"cover.jpg"  # Custom filename
    img_file_path = os.path.join(manga_dir, img_name)

    img_file = requests.get(cover_img_url, headers=headers(manga_url_main), stream=True)
    # Check if request was successful
    if img_file.status_code == 200:
        with open(img_file_path, "wb") as file:
            for chunk in img_file.iter_content(1024):  # Download in chunks
                file.write(chunk)








def search_mangadex_and_download_cover_selenium(manga_title, manga_dir, alt_site_url):

    if os.path.exists(os.path.join(manga_dir, "cover.jpg")):
        print(f"Cover already exists for {manga_title}. Skipping download.")
        return True
    else:
        driver = None  # Initialize driver to None for better exception handling
        try:
            driver = init_selenium()  # Initialize Selenium driver
            cleaned_title = clean_title_for_search(manga_title)
            search_url = f"https://mangadex.org/search?q={cleaned_title}"
            print(f"Searching for {manga_title} on MangaDex using Selenium: {search_url}")
        
            driver.get(search_url)
            human_like_interaction(driver)  # Simulate human behavior on the page

            # Try to find the first manga card that has an image
            first_manga_card = driver.find_element(By.CSS_SELECTOR, 'div.grid.gap-2 img.rounded.shadow-md')
            if not first_manga_card:
                print(f"No results found on MangaDex for {manga_title}. Falling back to alternative titles...")
                return search_using_alternative_titles_from_file(manga_title, manga_dir)

            # Get the cover image URL
            cover_img_url = first_manga_card.get_attribute('src').rsplit('.', 2)[0]
            print(f"Found cover image via Selenium: {cover_img_url}")

            # Download and save the image using Selenium
            driver.get(cover_img_url)
            time.sleep(2)  # Wait for the image to fully load
            save_path = os.path.join(manga_dir, "cover.jpg")

            # Save the image as a screenshot
            with open(save_path, "wb") as file:
                file.write(driver.find_element(By.TAG_NAME, "img").screenshot_as_png)

            print(f"Image downloaded and saved at: {save_path}")
            return True

        except Exception as e:
            log_error(manga_dir, f"Error searching or downloading cover using Selenium: {e}")
            # Fall back to alternative titles if there was an error
            return search_using_alternative_titles_from_file(manga_title, manga_dir)

        finally:
            if driver:
                driver.quit()  

def search_using_alternative_titles_from_file(manga_title, manga_dir):
    global save_title_for_later
    alternative_titles = extract_alternative_titles_from_file(manga_dir)

    if alternative_titles:
        print(f"Alternative titles found in page_content.txt: {alternative_titles}")
        for alt_title in alternative_titles:
            if download_cover_from_mangadex(alt_title, manga_dir):
                print(f"CCC Cover image downloaded using alternative title: {alt_title}")
                save_title_for_later = alt_title
                return True

    print("Failed to download cover image using alternative titles.")
    return False

def download_cover_from_mangadex(manga_title, manga_dir):
    """Attempt to download the cover image from MangaDex using Selenium."""
    driver = init_selenium()
    try:
        search_url = f"https://mangadex.org/search?q={manga_title.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(3)  # Allow time for page load

        first_manga_card = driver.find_element(By.CSS_SELECTOR, 'div.grid.gap-2 img.rounded.shadow-md')
        if first_manga_card:
            cover_img_url = first_manga_card.get_attribute('src').rsplit('.', 2)[0]

            # Download and save the image using Selenium
            driver.get(cover_img_url)
            time.sleep(2)  # Wait for the image to fully load
            save_path = os.path.join(manga_dir, "cover.jpg")

            # Save the image as a screenshot
            with open(save_path, "wb") as file:
                file.write(driver.find_element(By.TAG_NAME, "img").screenshot_as_png)

            return True

        else:
            print(f"No cover image found for {manga_title} on MangaDex.")
            return False

    except Exception as e:
        print(f"Error downloading cover from MangaDex: {e}")
        return False

    finally:
        driver.quit()


















def create_cbz_file(manga_title, chapter_title, manga_dir, chapter_images, chapter_url):
    global seven_zip_path
    # Sanitize the chapter title by removing anything after a colon

    match = re.search(r'Chapter (\d+(\.\d+)?)', chapter_title)
    if match:
        chapter_number = match.group(1)
        if '.' in chapter_number:
            chapter_number = chapter_number.replace('.', 'p')
        else:
            chapter_number = f"{int(chapter_number):02}"

    cbz_name = f"{manga_title} Chapter {chapter_number}.cbz"
    cbz_path = os.path.join(manga_dir, cbz_name)

    # Remove any existing empty CBZ file
    if os.path.exists(cbz_path) and os.path.getsize(cbz_path) == 0:
        print(f"Removing empty CBZ file: {cbz_path}")
        os.remove(cbz_path)

    # Create CBZ file using 7-Zip
    try:
        # Prepare the list of images for the CBZ
        valid_images = [image for image in chapter_images if os.path.exists(image)]
        if not valid_images:
            print("No valid images found to create the CBZ file.")
        else:
            # Run the 7-Zip command
            command = [seven_zip_path, 'a', '-tzip', cbz_path] + valid_images
            result = subprocess.run(command, capture_output=True, text=True)
        
            # Check the result of the subprocess call
            if result.returncode == 0:
                print(f"CBZ file created successfully: {cbz_path}")
                return
            else:
                print(f"Failed to create CBZ file. Error: {result.stderr}")
    except Exception as e:
        print(f"An error occurred: {e}")

def add_cover_to_cbz(manga_title, chapter_title, cbz_name, manga_dir):

    match = re.search(r'Chapter (\d+(\.\d+)?)', chapter_title)
    if match:
        chapter_number = match.group(1)
        if '.' in chapter_number:
            chapter_number = chapter_number.replace('.', 'p')
        else:
            chapter_number = f"{int(chapter_number):02}"

    cbz_name = f"{manga_title} Chapter {chapter_number}.cbz"
    cbz_path = os.path.join(manga_dir, cbz_name)

    cover_image_path = os.path.join(manga_dir, "cover.jpg")

    # Check if the CBZ file exists
    if not os.path.exists(cbz_path):
        print(f"CBZ file for '{manga_title}' not found.")
        return

    # Append the cover image to the CBZ file as '000.jpg'
    print("Adding cover image to the CBZ file as '000.jpg'.")
    
    with ZipFile(cbz_path, 'a', ZIP_DEFLATED) as cbz_file:
        cbz_file.write(cover_image_path, '000.jpg')
    
    print(f"Cover image added to '{cbz_name}' as '000.jpg'.")



#MangaUpdates Help searching close titles
def find_closest_match2(search_title, manga_titles):
    """
    Find the closest match for a given title.
    First, look for an exact match; if none, use difflib.get_close_matches to find the closest title.
    """
    # Normalize the search title
    search_title = normalize_text(search_title)
    # Normalize and clean the manga titles
    manga_titles_clean = [normalize_text(title) for title in manga_titles]
    
    # Debugging output
    print(f"Normalized search title: {search_title}")
    print(f"Normalized manga titles: {manga_titles_clean}")

    # First, check for an exact match
    if search_title in manga_titles_clean:
        exact_index = manga_titles_clean.index(search_title)
        print(f"Exact match found: {manga_titles[exact_index]}")
        return manga_titles[exact_index]  # Return the original title (unmodified)
    
    # If no exact match, find the closest match using difflib
    closest_matches = get_close_matches(search_title, manga_titles_clean, n=1, cutoff=0.6)
    if closest_matches:
        closest_index = manga_titles_clean.index(closest_matches[0])
        print(f"Closest match found: {manga_titles[closest_index]}")
        return manga_titles[closest_index]  # Return the original title

    print("No match found.")
    return None

def find_and_extract_closest_match(txt_file_path, manga_title):
    """Search the text file for the closest title match and extract the corresponding link."""
    if not os.path.exists(txt_file_path):
        print(f"File {txt_file_path} not found.")  # Debugging
        return None, None
    
    with open(txt_file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Extract titles and links using the updated regex-based functions
    titles = extract_titles_from_content(content)
    links = extract_links_from_content(content)
    
    print(f"Extracted {len(titles)} titles and {len(links)} links")  # Debugging
    
    # Check if the number of titles matches the number of links
    if len(titles) != len(links):
        print(f"Mismatch between number of titles and links: {len(titles)} titles, {len(links)} links.")
        return None, None

    if titles:
        # Find the closest matching title (using the cleaned title list for matching)
        closest_title = find_closest_match2(manga_title, titles)
        if closest_title:
            # Normalize titles to find the index of the closest match
            normalized_titles = [title.strip().lower() for title in titles]
            match_index = normalized_titles.index(closest_title.strip().lower())  # Use normalized title for lookup
            print(f"Closest title found: {titles[match_index]}, at index: {match_index}")  # Return the original title and index
            return titles[match_index], links[match_index]  # Return the original title and the link

    # Return None if no match was found
    print("No match found.")  # Debugging
    return None, None

def extract_titles_from_content(content):
    """Extract all manga titles from the downloaded content."""
    # Adjusted regex to match <a title="Click for Series Info" and extract the title inside <span>
    return re.findall(r'<a[^>]*title="Click for Series Info"[^>]*><span[^>]*>(.*?)</span></a>', content)

def extract_links_from_content(content):
    """Extract all manga info links from the downloaded content."""
    # Adjusted regex to extract the href attribute from <a title="Click for Series Info">
    return re.findall(r'<a\s+title="Click for Series Info"\s+href="(.*?)"', content)

manga_title3 = None
manga_title4 = None
#MangaUpdates
def search_manga_and_download_html_mangaupdates(manga_title, manga_dir):
    """Search for a manga on MangaUpdates and download the HTML of the Series Info page."""
    txt_file_path = os.path.join(manga_dir, "Mangaupdates_SearchResults.txt")
    global save_title_for_later  # Fallback title
    global manga_title3

    # Check if file exists without including the manga title yet
    existing_file = [f for f in os.listdir(manga_dir) if f.startswith("Mangaupdates_Metadata")]
    if existing_file:
        print(f"File {existing_file} already exists. Skipping download.")
        return existing_file


    # Construct the search URL 

    cleaned_title = re.sub(r"[!$@#%&*\(\)\-+=\[\]{}|;:'\"<>\?/.,]", "", manga_title)
    search_title = cleaned_title.replace(" ", "+")
    encoded_title = urllib.parse.quote(search_title)
    search_url = f"https://www.mangaupdates.com/site/search/result?search={encoded_title}"
    
    try:
        # Fetch the static content from the URL
        response = requests.get(search_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Get content type
        content_type = response.headers.get('Content-Type')

        # Ensure directory exists
        if not os.path.exists(manga_dir):
            os.makedirs(manga_dir)

        # Determine file extension based on content type
        mode = 'w' if 'text' in content_type else 'wb'  # Text or binary mode
        content = response.text if mode == 'w' else response.content

        # Save the content into the appropriate file
        with open(txt_file_path, mode, encoding='utf-8' if mode == 'w' else None) as file:
            file.write(content)

        print(f"Content successfully saved to {txt_file_path}")

        # Find the closest match in the downloaded file
        closest_title, manga_link = find_and_extract_closest_match(txt_file_path, manga_title)

        if closest_title:
            print(f"Found closest match: {closest_title}")

            # Use Selenium to load the manga info page
            driver = init_selenium()
            try:
                driver.get(manga_link)
                time.sleep(3)  # Wait for the page to load


                manga_title3 = driver.find_element(By.CLASS_NAME, 'releasestitle').text
                manga_title3 = sanitize_filename(manga_title3)
                if manga_title3.endswith("."):
                    manga_title3 = manga_title3[:-1]
                html_file_path = os.path.join(manga_dir, f"Mangaupdates_Metadata_{manga_title3}.txt")

                # Save the HTML content of the manga info page
                html_content = driver.page_source
                with open(html_file_path, "w", encoding="utf-8") as html_file:
                    html_file.write(html_content)
                print(f"HTML content saved to {html_file_path}")

                return html_file_path
            finally:
                # Clean up the search results file after successful match
                if os.path.exists(txt_file_path):
                    os.remove(txt_file_path)
                driver.quit()
        else:
            print(f"No close match found for '{manga_title}'. Deleting {txt_file_path}.")
            if os.path.exists(txt_file_path):
                os.remove(txt_file_path)

            # Retry with alternative title if available
            if save_title_for_later:
                print(f"Trying alternative title: {save_title_for_later}")
                return search_manga_and_download_html_mangaupdates2(save_title_for_later, manga_dir)
            else:
                print("No alternative title available to fall back on.")
                return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the content: {e}")
        return None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

        # Retry with alternative title if available
        try:
            if save_title_for_later:
                print(f"Trying alternative title: {save_title_for_later}")
                return search_manga_and_download_html_mangaupdates2(save_title_for_later, manga_dir)
            else:
                print("No alternative title available to fall back on.")
                return None
        except Exception as e:
            print(f"Failed with alternative title: {e}. Trying alternative title search V2...")
            return search_manga_and_download_html_mangaupdates3(manga_dir)

def search_manga_and_download_html_mangaupdates2(manga_title, manga_dir):
    """Search for a manga on MangaUpdates and download the HTML of the Series Info page."""
    txt_file_path = os.path.join(manga_dir, "Mangaupdates_SearchResults.txt")

    global manga_title3

    # Check if file exists without including the manga title yet
    existing_file = [f for f in os.listdir(manga_dir) if f.startswith("Mangaupdates_Metadata")]
    if existing_file:
        print(f"File {existing_file} already exists. Skipping download.")
        return existing_file

    # Construct the search URL 
    cleaned_title = re.sub(r"[!$@#%&*\(\)\-+=\[\]{}|;:'\"<>\?/.,]", "", manga_title)
    search_title = cleaned_title.replace(" ", "+")
    encoded_title = urllib.parse.quote(search_title)
    search_url = f"https://www.mangaupdates.com/site/search/result?search={encoded_title}"



    try:
        # Fetch the static content from the URL
        response = requests.get(search_url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Get content type
        content_type = response.headers.get('Content-Type')

        # Ensure directory exists
        if not os.path.exists(manga_dir):
            os.makedirs(manga_dir)

        # Save the content based on type (text or binary)
        mode = 'w' if 'text' in content_type else 'wb'
        content = response.text if mode == 'w' else response.content

        # Save the search results into the appropriate file
        with open(txt_file_path, mode, encoding='utf-8' if mode == 'w' else None) as file:
            file.write(content)

        print(f"Content successfully saved to {txt_file_path}")

        # Find the closest match in the downloaded file
        closest_title, manga_link = find_and_extract_closest_match(txt_file_path, manga_title)

        if closest_title:
            print(f"Found closest match: {closest_title}")

            # Use Selenium to load the manga info page
            driver = init_selenium()
            try:
                driver.get(manga_link)
                time.sleep(3)  # Wait for the page to load

                manga_title3 = driver.find_element(By.CLASS_NAME, 'releasestitle').text
                manga_title3 = sanitize_filename(manga_title3)
                if manga_title3.endswith("."):
                    manga_title3 = manga_title3[:-1]
                html_file_path = os.path.join(manga_dir, f"Mangaupdates_Metadata_{manga_title3}.txt")



                # Save the HTML content of the manga info page
                html_content = driver.page_source
                with open(html_file_path, "w", encoding="utf-8") as html_file:
                    html_file.write(html_content)

                print(f"HTML content saved to {html_file_path}")
                return html_file_path
            finally:
                # Ensure the driver quits and clean up the text file
                driver.quit()
                if os.path.exists(txt_file_path):
                    os.remove(txt_file_path)
        else:
            print(f"No close match found for '{manga_title}'. Deleting {txt_file_path}.")
            if os.path.exists(txt_file_path):
                os.remove(txt_file_path)
            return None

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while downloading the content: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def search_manga_and_download_html_mangaupdates3(manga_dir):
    """Search for a manga on MangaUpdates using alternative titles and download the HTML of the Series Info page."""
    global manga_title3
    # Extract multiple alternative titles from the file
    alternative_titles = extract_alternative_titles_from_file2(manga_dir)
    txt_file_path = os.path.join(manga_dir, "Mangaupdates_SearchResults.txt")
    
    if not alternative_titles:
        print("No valid alternative titles found.")
        return None

    

    # Check if file exists without including the manga title yet
    existing_file = [f for f in os.listdir(manga_dir) if f.startswith("Mangaupdates_Metadata")]
    if existing_file:
        print(f"File {existing_file} already exists. Skipping download.")
        return existing_file

    try:
        # Iterate through the alternative titles to find the closest match
        for manga_title in alternative_titles:
            # Construct the search URL 

            cleaned_title = re.sub(r"[!$@#%&*\(\)\-+=\[\]{}|;:'\"<>\?/.,]", "", manga_title)
            search_title = cleaned_title.replace(" ", "+")
            encoded_title = urllib.parse.quote(search_title)
            search_url = f"https://www.mangaupdates.com/site/search/result?search={encoded_title}"

            
            print(f"Searching for: {manga_title}")

            try:
                # Fetch the static content from the URL
                response = requests.get(search_url, stream=True)
                response.raise_for_status()  # Raise an exception for HTTP errors

                # Get content type
                content_type = response.headers.get('Content-Type')

                # Ensure directory exists
                if not os.path.exists(manga_dir):
                    os.makedirs(manga_dir)

                # Determine file extension based on content type
                mode = 'w' if 'text' in content_type else 'wb'
                content = response.text if mode == 'w' else response.content

                # Save the content into the appropriate file
                with open(txt_file_path, mode, encoding='utf-8' if mode == 'w' else None) as file:
                    file.write(content)

                print(f"Content successfully saved to {txt_file_path}")

                # Find the closest match in the downloaded file
                closest_title, manga_link = find_and_extract_closest_match(txt_file_path, manga_title)

                if closest_title:
                    print(f"Found closest match: {closest_title}")

                    # Use Selenium to load the manga info page
                    driver = init_selenium()  # Initialize the driver only when needed
                    try:
                        driver.get(manga_link)
                        time.sleep(3)  # Wait for the page to load

                        manga_title3 = driver.find_element(By.CLASS_NAME, 'releasestitle').text
                        manga_title3 = sanitize_filename(manga_title3)
                        if manga_title3.endswith("."):
                           manga_title3 = manga_title3[:-1]
                        html_file_path = os.path.join(manga_dir, f"Mangaupdates_Metadata_{manga_title3}.txt")



                        # Save the HTML content of the manga info page
                        html_content = driver.page_source
                        with open(html_file_path, "w", encoding="utf-8") as html_file:
                            html_file.write(html_content)
                        print(f"HTML content saved to {html_file_path}")
                        
                        return html_file_path  # Return after successful save
                    finally:
                        driver.quit()  # Ensure driver quits properly
                        if os.path.exists(txt_file_path):
                            os.remove(txt_file_path)  # Clean up text file after successful search
                else:
                    print(f"No close match found for '{manga_title}'. Deleting {txt_file_path}.")
                    if os.path.exists(txt_file_path):
                        os.remove(txt_file_path)  # Clean up if no match
                    continue  # Try the next title

            except requests.exceptions.RequestException as e:
                print(f"An error occurred while downloading the content: {e}")
                continue  # Continue to the next alternative title if there's a network issue

            except TimeoutException as e:
                print(f"Timeout while searching for '{manga_title}': {e}")
                continue  # Continue to the next alternative title if there's a timeout

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    print("Exhausted all alternative titles without finding a match.")
    return None

# Mangadex
def search_manga_and_download_html(manga_title, manga_dir):
    """
    Search for a manga on MangaDex and download the HTML if it doesn't exist already.
    If this fails, try searching via the alternative title stored in `save_title_for_later`.
    """
    global save_title_for_later
    global manga_title4

    
    # Check if file exists without including the manga title yet
    existing_file = [f for f in os.listdir(manga_dir) if f.startswith("Mangadex_Metadata")]
    if existing_file:
        print(f"File {existing_file} already exists. Skipping download.")
        return existing_file


    driver = init_selenium()  # Assumes you have an init_selenium() function
    cleaned_title = clean_title_for_search(manga_title)
    search_url = f"https://mangadex.org/search?q={cleaned_title}"
    driver.get(search_url)

    try:
        # Wait for the manga card to load, with retries in case of failures
        first_manga_card = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.grid.gap-2 a.manga-card-dense'))
        )
        first_manga_card.click()
        time.sleep(3)


        manga_title4 = driver.find_element(By.CLASS_NAME, 'title').find_element(By.TAG_NAME, 'p').text
        manga_title4 = sanitize_filename(manga_title4)
        if manga_title4.endswith("."):
            manga_title4 = manga_title4[:-1]
        html_file_path = os.path.join(manga_dir, f"Mangadex_Metadata_{manga_title4}.txt")

        # Save the current page's HTML as a .txt file
        html_content = driver.page_source
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)
        print(f"HTML content saved to {html_file_path}")
        return html_file_path
    except Exception as e:
        print(f"Error searching manga with title '{manga_title}': {e}")

        # Retry with alternative title if available
        try:
            if save_title_for_later:
                print(f"Trying alternative title: {save_title_for_later}")
                return search_manga_and_download_html2(save_title_for_later, manga_dir)
            else:
                print("No alternative title available to fall back on.")
                return None
        except Exception as e:
            print(f"Failed with alternative title: {e}. Trying alternative title search V2...")
            return search_manga_and_download_html3(manga_dir)
        finally:
            driver.quit()
    finally:
        driver.quit()

def search_manga_and_download_html2(manga_title, manga_dir):
    """
    Search for a manga on MangaDex and download the HTML if it doesn't exist already.
    If this fails, retry by using alternative titles from `page_content.txt` one at a time.
    """
    global manga_title4

    
    # Check if file exists without including the manga title yet
    existing_file = [f for f in os.listdir(manga_dir) if f.startswith("Mangadex_Metadata")]
    if existing_file:
        print(f"File {existing_file} already exists. Skipping download.")
        return existing_file


    driver = init_selenium()
    search_url = f"https://mangadex.org/search?q={manga_title.replace(' ', '+')}"
    driver.get(search_url)

    try:
        # Wait for the first manga card to load
        first_manga_card = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.grid.gap-2 a.manga-card-dense'))
        )
        first_manga_card.click()
        time.sleep(3)  # Allow the page to load

        manga_title4 = driver.find_element(By.CLASS_NAME, 'title').find_element(By.TAG_NAME, 'p').text
        manga_title4 = sanitize_filename(manga_title4)
        if manga_title4.endswith("."):
           manga_title4 = manga_title4[:-1]
        
        html_file_path = os.path.join(manga_dir, f"Mangadex_Metadata_{manga_title4}.txt")

        # Save the page's HTML as a .txt file
        html_content = driver.page_source
        with open(html_file_path, "w", encoding="utf-8") as html_file:
            html_file.write(html_content)
        print(f"HTML content saved to {html_file_path}")
        return html_file_path

    except Exception as e:
        print(f"Error searching manga with title '{manga_title}': {e}")

        # Retry with alternative titles from the file
        alternative_titles = extract_alternative_titles_from_file2(manga_dir)
        if not alternative_titles:
            print("No alternative titles available.")
            return None

        for alt_title in alternative_titles:
            print(f"Trying alternative title: {alt_title}")
            html_file_path = search_manga_and_download_html3(alt_title, manga_dir)
            if html_file_path:
                return html_file_path  # Stop if a match is found

        print("No matching titles found, even with alternative titles.")
        return None

    finally:
        driver.quit()

def search_manga_and_download_html3(manga_dir):
    """
    Search for a manga on MangaDex and download the HTML if it doesn't exist already.
    This is the final fallback method with no further retries.
    """
    global manga_title4

    
    # Check if file exists without including the manga title yet
    existing_file = [f for f in os.listdir(manga_dir) if f.startswith("Mangadex_Metadata")]
    if existing_file:
        print(f"File {existing_file} already exists. Skipping download.")
        return existing_file

    # Extract multiple alternative titles from the file
    alternative_titles = extract_alternative_titles_from_file2(manga_dir)
    
    if not alternative_titles:
        print("No valid alternative titles found.")
        return None

    driver = init_selenium()

    try:
        # Loop through each alternative title to find a match
        for manga_title in alternative_titles:
            search_url = f"https://mangadex.org/search?q={quote_plus(manga_title)}"
            print(f"Searching for: {manga_title}")
            driver.get(search_url)

            try:
                # Wait for the first manga card to appear
                first_manga_card = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.grid.gap-2 a.manga-card-dense'))
                )
                first_manga_card.click()

                time.sleep(3)  # Allow the page to load

                manga_title4 = driver.find_element(By.CLASS_NAME, 'title').find_element(By.TAG_NAME, 'p').text
                manga_title4 = sanitize_filename(manga_title4)
                if manga_title4.endswith("."):
                   manga_title4 = manga_title4[:-1]

                html_file_path = os.path.join(manga_dir, f"Mangadex_Metadata_{manga_title4}.txt")

                # Save the HTML content of the page
                html_content = driver.page_source
                with open(html_file_path, "w", encoding="utf-8") as html_file:
                    html_file.write(html_content)
                print(f"HTML content saved to {html_file_path}")
                return html_file_path

            except TimeoutException as e:
                print(f"Timeout while searching for '{manga_title}': {e}")
                continue  # Try the next title in the list

        print("Exhausted all alternative titles without finding a match.")
        return None

    except Exception as e:
        print(f"Error occurred: {e}")
        return None

    finally:
        driver.quit()


#Comicinfo.xml
def extract_metadata_from_txt_mangaupdates(manga_dir):

    if manga_title3 is None:
        metadata_files = [os.path.join(manga_dir, f) for f in os.listdir(manga_dir) if f.startswith("Mangaupdates_Metadata")]
        if not metadata_files:
            print(f"Error: No Mangaupdates_Metadata.txt found in {manga_dir}")
            return {}
        page_content_path = metadata_files[0]  # Select the first file
    elif manga_title3 is not None:
        page_content_path = os.path.join(manga_dir, f"Mangaupdates_Metadata_{manga_title3}.txt")
        if not os.path.exists(page_content_path):
            print(f"Error: {page_content_path} not found.")
            return {}

    # Read the content of the .txt file (HTML)
    with open(page_content_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Initialize empty metadata dictionary
    metadata = {
        'Authors': [],
        'Artists': [],
        'Publishers': [],
        'Genres': [],
        'Year': [],
        'Alternative Titles': [],
        'Summary': []
    }
    
    # Extract Authors
    authors_section = soup.find('div', {'data-cy': 'info-box-authors'})
    if authors_section:
        metadata['Authors'] = [span.text.strip() for span in authors_section.find_all('span', class_='linked-name_name_underline__QgZKK')]
    else:
        metadata['Authors'] = None

    # Extract Artists
    artists_section = soup.find('div', {'data-cy': 'info-box-artists'})
    if artists_section:
        metadata['Artists'] = [span.text.strip() for span in artists_section.find_all('span', class_='linked-name_name_underline__QgZKK')]
    else:
        metadata['Artists'] = None

    # Extract Genres
    genres_section = soup.find('div', {'data-cy': 'info-box-genres'})

    if genres_section:
        genre_links = genres_section.find_all('a', href=True)
        # Filter out unwanted "Search for series of same genre(s)" links
        metadata['Genres'] = [
            link.text.strip() 
            for link in genre_links 
            if not 'Search for series of same genre(s)' in link.text
        ]
    else:
        metadata['Genres'] = None

    # Extract Publishers
    publishers_section = soup.find('div', {'data-cy': 'info-box-original_publisher'})
    if publishers_section:
        publisher_names = publishers_section.find_all('span', class_='linked-name_name_underline__QgZKK')
        metadata['Publishers'] = [pub.text.strip() for pub in publisher_names]
    else:
        metadata['Publishers'] = None

    # Extract Year
    year_section = soup.find('div', {'data-cy': 'info-box-year'})
    if year_section:
        year_text = year_section.text.strip()
        if re.match(r'\d{4}', year_text):
            metadata['Year'] = year_text
        else:
            metadata['Year'] = None
    else:
            metadata['Year'] = None
    

    # Extract Alternative Titles
    alt_titles_section = soup.find('div', {'data-cy': 'info-box-associated'})
    if alt_titles_section:
        alt_titles = [div.text.strip() for div in alt_titles_section.find_all('div')]
        metadata['Alternative Titles'] = alt_titles
    else:
            metadata['Alternative Titles'] = None

    print(f"Extracted Mangaupdates Metadata: {metadata}")


    # Find the specific class containing the summary
    summary_section = soup.find('div', {'class': 'mu-markdown_mu_markdown__pqmRi'})

    # Extract the text from the summary section, excluding unwanted parts
    if summary_section:
        # Remove specific parts like "Original Webtoon"
        for p in summary_section.find_all('p'):
            if 'Original Webtoon' in p.get_text():
                p.decompose()
    
        # Join the remaining text as the summary
        summary = ' '.join(p.get_text(strip=True) for p in summary_section.find_all('p'))
    else:
        summary = None

    # Output metadata
    metadata['Summary'] = summary
    

    return metadata

def extract_metadata_from_txt(manga_dir):
    """Extract metadata from Mangadex_Metadata.txt."""

    if manga_title4 is None:
        metadata_files = [os.path.join(manga_dir, f) for f in os.listdir(manga_dir) if f.startswith("Mangadex_Metadata")]
        if not metadata_files:
            print(f"Error: No Mangadex_Metadata.txt found in {manga_dir}")
            return {}
        page_content_path = metadata_files[0]  # Select the first file
    elif manga_title4 is not None:
         page_content_path = os.path.join(manga_dir, f"Mangadex_Metadata_{manga_title4}.txt")
    if not os.path.exists(page_content_path):
        print(f"Error: {page_content_path} not found.")
        return {}

    # Read the content of the .txt file (HTML)
    with open(page_content_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    
    # Find the container holding the authors.
    authors_container = soup.find('div', class_='flex gap-2 flex-wrap')
    if authors_container:
        # Extract all <span> tags within the <a> tags for authors.
        extracted_authors = [
            span.get_text(strip=True)
            for span in authors_container.find_all('span')
        ]
    
        # Join the author names with commas if any are found.
        if extracted_authors:
            writer = ', '.join(extracted_authors)
        else:
            writer = None
    else:
            writer = None 



    # Find the container holding the artist names
    artists_container = soup.find('div', class_='flex gap-2 flex-wrap')
    if artists_container:
        # Extract all <span> tags within the <a> tags for artists
        extracted_artists = [
            span.get_text(strip=True)
            for span in artists_container.find_all('span')
        ]
    
        # Join the artist names with commas if any are found
        if extracted_artists:
            Artist = ', '.join(extracted_artists)
        else:
            Artist = None
    else:
            Artist = None

    # Extract Genres
    genre_tags = soup.find_all('a', class_='tag bg-accent')
    genres = [genre_tag.text for genre_tag in genre_tags] if genre_tags else None

    # Extract Tags
    tag_elements = soup.find_all('span', class_='tag text-white bg-status-yellow')
    tags = [tag_element.text for tag_element in tag_elements] if tag_elements else None


    # Find the container holding the content
    summary_tag = soup.find('div', class_='md-md-container')
    if not summary_tag:
        return 'No summary available.'
    
    # Initialize an empty list to store paragraphs
    paragraphs = []
    
    # Traverse the elements inside the container
    for element in summary_tag.contents:
        if element.name == 'hr':
            # Stop processing if <hr> is encountered (links section starts here)
            break
        if element.name == 'p':
            # Add only text content from <p> tags
            paragraphs.append(element.get_text(strip=True))
    
    # Join paragraphs with line breaks and return the cleaned summary
    summary = "\n\n".join(paragraphs)
    if not summary:
        summary = None

    alt_titles_elements = soup.find_all('div', class_='alt-title')
    alt_titles = [alt_title.find('span').text.strip() for alt_title in alt_titles_elements] if alt_titles_elements else None
    # If the list is empty after extraction, assign None
    alt_titles = alt_titles if alt_titles else None


    # Find the span that contains the publication year
    publication_span = soup.find('span', text=lambda t: t and 'Publication:' in t)

    # Extract the year
    if publication_span:
        # Split the text to isolate the year
        publication_text = publication_span.text
        year = publication_text.split('Publication: ')[1].split(',')[0].strip()
        Year = year if year else None


    metadata = {
        'Writer': writer,
        'Artist': Artist,
        'Genres': genres,
        'Tags': tags,
        'Summary': summary,
        'Alternative Titles': alt_titles,
        'Year': Year
    }

    print(f"Extracted MangaDex Metadata: {metadata}")
    return metadata

def extract_alternative_titles_from_file2(manga_dir):

    page_content_path = os.path.join(manga_dir, "page_content.txt")
    
    if not os.path.exists(page_content_path):
        print(f"Error: page_content.txt not found in {manga_dir}")
        return []

    # Read the content of the page_content.txt file
    with open(page_content_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    alternative_titles_tag = soup.find('h2', class_='story-alternative')
            
    if alternative_titles_tag:
        titles_text = alternative_titles_tag.text.strip()
        # Handle multiple delimiters robustly
        delimiters = [';', ',']
        for delimiter in delimiters:
            if delimiter in titles_text:
                alternative_titles = [title.strip() for title in titles_text.split(delimiter)]
                return alternative_titles

        # Return the text as a single title if no delimiter is found
        return [titles_text]

    print("No alternative titles found or malformed HTML in page_content.txt.")
    return []

def merge_metadata(metadata1, metadata2, manga_dir):
    """Merge two metadata dictionaries into one."""
    merged_metadata = {}

    # Merge Genres lists from metadata1 and metadata2, handling None values
    genres1 = metadata1.get('Genres') or []  # Default to empty list if None
    genres2 = metadata2.get('Genres') or []  # Default to empty list if None
    merged_metadata['Genres'] = list(set(genres1 + genres2))

    # Allowed genres list
    allowed_genres = {
        "Action", "Adult", "Adventure", "Comedy", "Cooking", "Doujinshi", "Drama",
        "Ecchi", "Erotica", "Fantasy", "Gender Bender", "Harem", "Historical", 
        "Horror", "Isekai", "Josei", "Martial arts", "Mature", "Mecha", "Medical", 
        "Mystery", "Pornographic", "Psychological", "Romance", "School life", 
        "Sci fi", "Sci-fi", "Shoujo ai", "Shounen ai", "Slice of life", "Smut", "Sports", 
        "Supernatural", "Tragedy", "Yaoi", "Yuri"
    }

    # Filter and de-duplicate genres to include only allowed genres
    genres_from_metadata = merged_metadata['Genres']
    filtered_genres = [genre for genre in genres_from_metadata if genre in allowed_genres]
    merged_metadata['Genres'] = list(dict.fromkeys(filtered_genres))

    # Move any genre not in allowed genres to 'Tags'
    extra_tags = [genre for genre in genres_from_metadata if genre not in allowed_genres]
    tags = (metadata2.get('Tags') or []) + extra_tags  # Handle None in Tags with or []
    merged_metadata['Tags'] = list(dict.fromkeys(tags))

    # Authors list from metadata1
    authors1 = metadata1.get('Authors', [])

    # Writer from metadata2, always treated as a list for consistency
    writer2 = metadata2.get('Writer')
    authors2 = [writer2] if writer2 and writer2 != 'Unknown' else []

    def normalize_name(name):
        return re.sub(r'\s+|\(.*?\)', '', name)

    normalized_authors = {normalize_name(author): author for author in authors1}
    normalized_writer = {normalize_name(writer): writer for writer in authors2}

    merged_authors = []
    merged_authors.extend(normalized_authors.values())

    for norm_writer, original_writer in normalized_writer.items():
        if norm_writer not in normalized_authors:
            merged_authors.append(original_writer)
        else:
            existing_author = normalized_authors[norm_writer]
            if len(original_writer) > len(existing_author):
                merged_authors = [original_writer if author == existing_author else author for author in merged_authors]

    def remove_shorter_versions(authors):
        detailed_authors = {}
        for author in authors:
            normalized = normalize_name(author)
            if normalized not in detailed_authors or len(author) > len(detailed_authors[normalized]):
                detailed_authors[normalized] = author
        return list(detailed_authors.values())

    merged_authors = remove_shorter_versions(merged_authors)

    flattened_authors = []
    for item in merged_authors:
        if isinstance(item, list):
            flattened_authors.extend(str(sub_item) for sub_item in item)
        else:
            flattened_authors.append(str(item))

    merged_metadata['Authors'] = flattened_authors if flattened_authors else []

    artists1 = metadata1.get('Artists', [])
    artist2 = metadata2.get('Artist')
    artists2 = [artist2] if artist2 and artist2 != 'Unknown' else []

    normalized_artists1 = {normalize_name(artist): artist for artist in artists1}
    normalized_artists2 = {normalize_name(artist): artist for artist in artists2}

    merged_artists = []
    merged_artists.extend(normalized_artists1.values())

    for norm_artist, original_artist in normalized_artists2.items():
        if norm_artist not in normalized_artists1:
            merged_artists.append(original_artist)
        else:
            existing_artist = normalized_artists1[norm_artist]
            if len(original_artist) > len(existing_artist):
                merged_artists = [original_artist if artist == existing_artist else artist for artist in merged_artists]

    merged_artists = remove_shorter_versions(merged_artists)

    flattened_artists = []
    for item in merged_artists:
        if isinstance(item, list):
            flattened_artists.extend(str(sub_item) for sub_item in item)
        else:
            flattened_artists.append(str(item))

    merged_metadata['Artists'] = flattened_artists if flattened_artists else []

    merged_metadata['Publishers'] = list(set(metadata1.get('Publishers') or []))

    # Ensure metadata1 and metadata2 have a properly merged 'Summary'
    summary2 = metadata2.get('Summary', None)
    if summary2 is None:
        summary2 = metadata1.get('Summary', None)
    if isinstance(summary2, list):
        summary2 = "\n".join(summary2)
    elif not isinstance(summary2, str):
        summary2 = str(summary2)

    merged_metadata['Summary'] = "\n" + summary2

    merged_metadata['Year'] = metadata1.get('Year') or metadata2.get('Year') or []

    try:
        file_alternative_titles = extract_alternative_titles_from_file2(manga_dir)
        file_alternative_titles = file_alternative_titles or []
        merged_titles = (file_alternative_titles + 
                         metadata1.get('Alternative Titles', []) + 
                         metadata2.get('Alternative Titles', []))
        merged_titles = [str(title) if isinstance(title, list) else title for title in merged_titles]
        merged_metadata['Alternative Titles'] = list(set(merged_titles)) or []
    except Exception:
        merged_metadata['Alternative Titles'] = []

    merged_metadata['Alternative Titles'] = clean_alternative_titles(merged_metadata['Alternative Titles'])
    
    return merged_metadata

def extract_chapter_number_from_cbz(cbz_name):
    # Use regex to extract numbers from the CBZ file name (e.g., "One Piece Chapter 123.cbz")
    match = re.search(r'\bChapter (\d+)', cbz_name, re.IGNORECASE)
    return match.group(1) if match else "Unknown"

def count_images_in_cbz(cbz_file_path):
    try:
        with zipfile.ZipFile(cbz_file_path, 'r') as cbz_file:
            # List only image files inside the archive
            image_files = [file for file in cbz_file.namelist() if file.endswith(('.jpg', '.png', '.jpeg', '.webp'))]
            return len(image_files)
    except Exception as e:
        print(f"Error counting images in {cbz_file_path}: {e}")
        return "Unknown"   

def clean_alternative_titles(alternative_titles):
    """
    Clean alternative titles by removing unwanted <br/> tags, trimming spaces,
    and removing duplicates while preserving order.
    """
    cleaned_titles = []
    for title in alternative_titles:
        # Remove <br/> tags and trim spaces
        clean_title = title.replace('<br/>', '').strip()
        # Add to cleaned list if not already present
        if clean_title and clean_title not in cleaned_titles:
            cleaned_titles.append(clean_title)

    return cleaned_titles

def create_comicinfo_xml(manga_dir, metadata, manga_title, chapter_url, cbz_name, image_tags=None):
    """Create a ComicInfo.xml file using the merged metadata and save it in the specified manga directory."""
    
    # Extract chapter number from the cbz file name
    chapter_number = extract_chapter_number_from_cbz(cbz_name)

    # Full path to the cbz file
    cbz_file_path = os.path.join(manga_dir, cbz_name)

    # Determine page count based on image_tags or fallback to counting images in the cbz
    if image_tags and len(image_tags):  
        page_count = len(image_tags) + 1  # Add 1 for the cover image
    else:
        page_count = count_images_in_cbz(cbz_file_path)



    # Create the root of the XML structure
    root = ET.Element("ComicInfo")
    ET.SubElement(root, "Series").text = f"{manga_title};"
    ET.SubElement(root, "LocalizedSeries").text = ", ".join(metadata.get('Alternative Titles', [])) if metadata.get('Alternative Titles') else ''
    ET.SubElement(root, "Number").text = chapter_number  # Ensure chapter_number is a string
    ET.SubElement(root, "Writer").text = ", ".join(metadata.get('Authors', [])) if metadata.get('Authors') else 'Unknown'
    ET.SubElement(root, "Artists").text = ", ".join(metadata.get('Artists', [])) if metadata.get('Artists') else 'Unknown'
    ET.SubElement(root, "Publisher").text = ", ".join(metadata.get('Publishers', [])) if metadata.get('Publishers') else 'Unknown'
    ET.SubElement(root, "Year").text = metadata.get('Year', []) if metadata.get('Year') else 'Unknown'
    ET.SubElement(root, "Genre").text = ", ".join(metadata.get('Genres', [])) if metadata.get('Genres') else 'Not Available'
    ET.SubElement(root, "Tags").text = ", ".join(metadata.get('Tags', [])) if metadata.get('Tags') else 'Not Available'
    ET.SubElement(root, "Summary").text = metadata.get('Summary', 'No summary available')
    ET.SubElement(root, "Web").text = chapter_url
    ET.SubElement(root, "LanguageISO").text = "en"
    ET.SubElement(root, "PageCount").text = str(page_count)
    ET.SubElement(root, "Format").text = "CBZ"

    # Save the ComicInfo.xml file
    xml_file_path = os.path.join(manga_dir, "ComicInfo.xml")
    tree = ET.ElementTree(root)
    tree.write(xml_file_path, encoding="utf-8", xml_declaration=True)
    print(f"ComicInfo.xml created at {xml_file_path}")

    return xml_file_path

def insert_comicinfo_into_cbz(manga_dir, cbz_name, xml_file_path):
    """Insert ComicInfo.xml into CBZ file."""
    cbz_file_path = os.path.join(manga_dir, cbz_name)

    if not os.path.exists(cbz_file_path):
        print(f"Error: {cbz_file_path} does not exist.")
        return False

    with zipfile.ZipFile(cbz_file_path, 'a') as cbz_file:
        cbz_file.write(xml_file_path, "ComicInfo.xml")
        print(f"ComicInfo.xml inserted into {cbz_name}")

    return True



total_download_size_multiple = 0
def download_manga(url, manga_title = None):


    if url.startswith("https://www.mangabats.com/"):
        manga_url_main="https://www.mangabats.com/"

    elif url.startswith("https://www.nelomanga.net/"):
        manga_url_main="https://www.nelomanga.net/"

    elif url.startswith("https://www.mangakakalot.gg/"):
        manga_url_main="https://www.mangakakalot.gg/"
    else: manga_url_main = None


    global total_download_size_multiple
    global seven_zip_path
    global Check_idx


    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch the manga page. Error: {e}")
        return

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract manga title if not provided
    if not manga_title:
        title_tag = soup.find('ul', class_='manga-info-text').find('li').find('h1')
        manga_title = title_tag.text.strip()

    manga_title = sanitize_filename(manga_title)

    if manga_title.endswith("."):
        manga_title = manga_title[:-1]

    print(f"Processing Manga: {manga_title}")
    
    # Create directory for the manga
    manga_dir = os.path.join(base_dir, manga_title)
    os.makedirs(manga_dir, exist_ok=True)

    # Save URL and HTML content if not already saved
    save_url(manga_dir, url)
    html_file_path = save_html_as_txt(manga_dir, html_content)
    print(f"HTML content saved to {html_file_path}")

    # Extract and download cover with alternative titles
    alt_site_url = "https://manganelo.com/manga-hero-x-demon-queen"
    extract_and_download_cover(manga_dir, html_file_path, url, manga_title, alt_site_url, manga_url_main)
    # Process chapters


    chapter_list = soup.find('div', class_='chapter-list')

    if not chapter_list:
        print("No chapter list found on the page.")
        exit()

    # Extract links from each row
    chapter_links = chapter_list.find_all('div', class_='row')


    print(f"Number of chapters found: {len(chapter_links)}")

    log_file_path = os.path.join(manga_dir, "download_log.txt")

    # Load existing download log to avoid re-downloading
    existing_log = {}
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            for line in log_file:
                chapter_url, chapter_title, last_updated = line.strip().split("\t")
                existing_log[chapter_url] = (chapter_title, last_updated)

    total_download_size = 0


    for chapter_item in chapter_links:
        chapter_item = str(chapter_item) 

        soup = BeautifulSoup(chapter_item, 'html.parser')  # Parse HTML

        # Find the <a> tag inside <span>
        a_tag = soup.find('a')  # Store in a different variable to avoid overwriting

        chapter_url = a_tag["href"].strip()  # Extract URL
        chapter_title = a_tag.text.strip()  # Extract title


        # Skip chapters that are already logged as downloaded
        if chapter_url in existing_log:
            print(f"Chapter {chapter_title} already downloaded. Skipping...")
            continue

        print(f"Processing Chapter: {chapter_title} | URL: {chapter_url}")

        match = re.search(r'Chapter (\d+(\.\d+)?)', chapter_title)
        if match:
            chapter_number = match.group(1)
            if '.' in chapter_number:
                chapter_number = chapter_number.replace('.', 'p')
            else:
                chapter_number = f"{int(chapter_number):02}"
            # Generate the CBZ filename and save the file
            cbz_filename = f"{manga_title} Chapter {chapter_number}.cbz"
            cbz_path = os.path.join(manga_dir, cbz_filename)
        else:
            cbz_filename = f"{manga_title} {sanitize_filename(chapter_title)}.cbz"
            cbz_path = os.path.join(manga_dir, cbz_filename)


        if os.path.exists(cbz_path) and os.path.getsize(cbz_path) > 0:
            print(f"Chapter {chapter_title} already exists as {cbz_filename}. Skipping...")
            continue

        chapter_response = requests.get(chapter_url)
        chapter_response.raise_for_status()
        chapter_soup = BeautifulSoup(chapter_response.text, 'html.parser')

        # Find the image container
        image_container = chapter_soup.find('div', class_='container-chapter-reader')

        if not image_container:
            print(f"No image container found for chapter: {chapter_title}. Skipping...")
            return 0

        image_tags = image_container.find_all('img')
            
        if not image_tags:
            print(f"No images found in chapter: {chapter_title}. Skipping...")
            return 0

        print(f"Found {len(image_tags)} images in chapter: {chapter_title}")
            
        img_url_list = []
        # Assuming image_tags is a list of img tags
        for img_tag in image_tags:
            img_url = img_tag.get('src')  # Get the 'src' attribute from the img tag
            if img_url:  # Only append if img_url is not None or empty
                img_url_list.append(img_url)


        def get_retry_session(max_retries=5, backoff_factor=1.5, status_forcelist=(500, 502, 503, 504, 520, 522, 524)):
                session = requests.Session()
                retry = Retry(
                    total=max_retries,
                    read=max_retries,
                    connect=max_retries,
                    backoff_factor=backoff_factor,
                    status_forcelist=status_forcelist,
                    raise_on_status=False,
                    respect_retry_after_header=True,
                )
                adapter = HTTPAdapter(max_retries=retry)
                session.mount('http://', adapter)
                session.mount('https://', adapter)
                return session

        def save_image(file_path, content):
            with open(file_path, "wb") as f:
                for chunk in content:
                    if chunk:  # make sure it's not a keep-alive chunk
                        f.write(chunk)


        def download_image(img_url, img_name, manga_dir, headers, progress, lock, img_url_img_fail, img_url_img_fail_set, TRY2=False):
            img_file_path = os.path.join(manga_dir, img_name)
            session = get_retry_session()

            max_attempts = 10 if TRY2 else 2

            for attempt in range(max_attempts):
                try:
                    if TRY2:
                        response = requests.get(img_url, headers=headers)
                    else:
                        response = session.get(img_url, headers=headers)

                    if response.status_code == 200:
                        if attempt > 0:
                            print(f"\nRecovered: {img_name} on attempt {attempt + 1}.")
                        save_image(img_file_path, response.iter_content(8192))
                        with lock:
                            progress.update(1)
                        session.close()
                        return img_name

                    elif response.status_code in (500, 502, 503, 504, 520, 522, 524):
                        print(f"\n[HTTP {response.status_code}] Attempt {attempt + 1}: {img_name}. Retrying...")
                        if TRY2:
                            session.close()
                            session = get_retry_session()
                        continue

                    else:
                        print(f"[HTTP {response.status_code}] {img_name}. Not retrying.")
                        break

                except (RequestException, ReadTimeout) as e:
                    print(f"[Request Error] Attempt {attempt + 1}: {img_name} - {str(e)}")
                    if TRY2:
                        session.close()
                        session = get_retry_session()

            fail_entry = (img_url, img_name)
            with lock:
                if fail_entry not in img_url_img_fail_set:
                    img_url_img_fail.append(fail_entry)
                    img_url_img_fail_set.add(fail_entry)

            session.close()
            return None




        downloaded_count = 0
        lock = threading.Lock()
        progress = tqdm(total=len(img_url_list), desc=f"Downloading {chapter_title}", unit="file")

        img_url_img_fail = []         # List of failed downloads
        img_url_img_fail_set = set()  # Set for quick lookup

        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = {}
            for i, img_url in enumerate(img_url_list):
                base_url, image_path = split_image_url(img_url)
                request_headers = headers(manga_url_main, base_url, image_path, img_url)
                future = executor.submit(
                    download_image,
                    img_url,
                    f"{i+1:03}.webp",
                    manga_dir,
                    request_headers,
                    progress,
                    lock,
                    img_url_img_fail,
                    img_url_img_fail_set,
                    TRY2=False
                )
                futures[future] = img_url

            for future in as_completed(futures):
                if future.result():
                    downloaded_count += 1

        progress.close()
        print(f"\nDownloaded {downloaded_count}/{len(img_url_list)} images for {chapter_title}.")

        if img_url_img_fail:
            second_downloaded_count = 0
            print(f"\nRetrying {len(img_url_img_fail)} failed downloads...")

            failed_progress = tqdm(total=len(img_url_img_fail), desc="Retrying failed downloads", unit="file")
            second_fail_list = []
            second_fail_set = set()

            with ThreadPoolExecutor(max_workers=10) as retry_executor:
                retry_futures = {}
                for img_url, img_name in img_url_img_fail:
                    base_url, image_path = split_image_url(img_url)
                    request_headers = headers(manga_url_main, base_url, image_path, img_url)
                    future = retry_executor.submit(
                        download_image,
                        img_url,
                        img_name,
                        manga_dir,
                        request_headers,
                        failed_progress,
                        lock,
                        second_fail_list,
                        second_fail_set,
                        TRY2=True
                    )
                    retry_futures[future] = img_url

                for retry_future in as_completed(retry_futures):
                    if retry_future.result():
                        downloaded_count += 1
                        second_downloaded_count += 1

            failed_progress.close()

            # --- Final Report ---
            print(f"\nFinal: Downloaded {downloaded_count-second_downloaded_count}/{len(img_url_list)} images for {chapter_title}.")

            if second_fail_list:
                print(f"\nStill failed {len(second_fail_list)} images after retry.")
                with open(os.path.join(manga_dir, "failed_downloads.txt"), "w", encoding="utf-8") as fail_file:
                    for img_url, img_name in second_fail_list:
                        fail_file.write(f"{img_name} - {img_url}\n")
                print("\nSaved failed image URLs to 'failed_downloads.txt'.")
            else:
                print("\nAll images downloaded successfully after retry.")



        chapter_size = 0
        i = 0
        for i, img_url in enumerate(img_url_list):  # Correctly unpack the tuple
            img_name = f"{i+1:03}.webp"  # Ensures filenames are 001.jpg, 002.jpg, etc.
            img_file_path = os.path.join(manga_dir, img_name)
            
            if os.path.exists(img_file_path):  # Prevents errors if file is missing
                chapter_size += os.path.getsize(img_file_path)
            else:
                print(f"Warning: {img_file_path} not found.")

        print(f"Estimated size for {chapter_title}: {chapter_size / (1024 * 1024):.2f} MB")
        total_download_size += chapter_size

        # Extract chapter number using regex
        match = re.search(r'Chapter (\d+(\.\d+)?)', chapter_title)
        if match:
            chapter_number = match.group(1)
            if '.' in chapter_number:
                chapter_number = chapter_number.replace('.', 'p')
            else:
                chapter_number = f"{int(chapter_number):02}"

        # Generate the CBZ filename and save the file
        cbz_filename = f"{manga_title} Chapter {chapter_number}.cbz"
        cbz_path = os.path.join(manga_dir, cbz_filename)

        with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
            for i, img_url in enumerate(img_url_list):
                img_name = f"{i+1:03}.webp"
                img_file_path = os.path.join(manga_dir, img_name)
                
                # Ensure the file exists before adding it to the archive
                if os.path.exists(img_file_path):
                    cbz.write(img_file_path, arcname=img_name)  # Fix: Use img_name, not 'file'
                    os.remove(img_file_path)  # Remove after adding to CBZ
            

        # Add cover, metadata, and update logs
        cbz_name = f"{manga_title} Chapter {chapter_number}.cbz"
        add_cover_to_cbz(manga_title, chapter_title, cbz_name, manga_dir)
                                 
        # Download and extract metadata from MangaUpdates
        html_file_path_mangaupdates = search_manga_and_download_html_mangaupdates(manga_title, manga_dir)
        if html_file_path_mangaupdates is None:
            print("Failed to download MangaUpdates metadata.")
        metadata_mangaupdates = extract_metadata_from_txt_mangaupdates(manga_dir)

        # Download and extract metadata from MangaDex
        html_file_path_mangadex = search_manga_and_download_html(manga_title, manga_dir)
        if html_file_path_mangadex is None:
            print("Failed to download MangaDex metadata.")
        metadata_mangadex = extract_metadata_from_txt(manga_dir)

        # Merge metadata from both sources
        merged_metadata = merge_metadata(metadata_mangaupdates, metadata_mangadex, manga_dir)

        # Create ComicInfo.xml using the merged metadata
        xml_file_path = create_comicinfo_xml(manga_dir, merged_metadata, manga_title, chapter_url, cbz_name, image_tags)

        # Insert ComicInfo.xml into the CBZ file
        insert_comicinfo_into_cbz(manga_dir, cbz_name, xml_file_path)


        cbz_filename = f"{manga_title} Chapter {chapter_number}.cbz"
        cbz_path = os.path.join(manga_dir, cbz_filename)
        
        # Step 1: Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            # Step 2: Use 7z to extract the CBZ file
            subprocess.run([seven_zip_path, 'x', cbz_path, f'-o{temp_extract_dir}'], check=True)

            # Step 3: Delete the original CBZ file
            os.remove(cbz_path)

            # Step 4: Use 7z to re-compress files into a new CBZ file with the original structure
            new_cbz_path = os.path.join(manga_dir, cbz_filename)
            subprocess.run([seven_zip_path, 'a', '-tzip', new_cbz_path, f'{temp_extract_dir}/*'], check=True)


        # Log the successful download
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"{chapter_url}\t{chapter_title}\t{datetime.now().isoformat()}\n")
    else:
        print(f"Failed to extract chapter number from title '{chapter_title}'. Skipping...")


    total_download_size_multiple += total_download_size
    total_download_size_in_mb = total_download_size / (1024 * 1024)

    print(f"Total estimated download size: {total_download_size_in_mb:.2f} MB")
    update_combined_log()

total_update_size = 0
def update_manga(url=None, manga_title = None):
    global total_update_size
    global seven_zip_path
    global Check_idx
    if url:
        if url.startswith("https://www.mangabats.com/"):
            manga_url_main="https://www.mangabats.com/"
            manga_url_search="https://www.nelomanga.com/search/story/"

        elif url.startswith("https://www.nelomanga.net/"):
            manga_url_main="https://www.nelomanga.net/"
            manga_url_search="https://www.nelomanga.net/search/story/"

        elif url.startswith("https://www.mangakakalot.gg/"):
            manga_url_main="https://www.mangakakalot.gg/"
            manga_url_search="https://www.mangakakalot.gg/search/story/"
    
    else: 
            manga_url_main="https://www.nelomanga.com/"
            manga_url_search="https://www.nelomanga.com/search/story/"


    if url:
        try:
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch the manga page. Error: {e}")
            return

        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract manga title if not provided
        if not manga_title:
            title_tag = soup.find('ul', class_='manga-info-text').find('li').find('h1')
            manga_title = title_tag.text.strip()


    manga_title = sanitize_filename(manga_title)

    if manga_title.endswith("."):
        manga_title = manga_title[:-1]

    print(f"Processing Manga: {manga_title}")
    
    # Create directory for the manga
    manga_dir = os.path.join(base_dir, manga_title)
    os.makedirs(manga_dir, exist_ok=True)





    try:
        chapter_list = soup.find('div', class_='chapter-list')
        chapter_links = chapter_list.find_all('div', class_='row')
        print("Chapter links found.")
        
    except:
        driver = init_selenium()

        try:
            # Attempt to encode and decode to UTF-8, replacing unreadable characters
            manga_title = manga_title.encode('utf-8', 'replace').decode('utf-8')
        except UnicodeDecodeError:
            # Fallback for non-UTF-8 characters
            manga_title = manga_title.encode('ascii', 'replace').decode('ascii')

        # Remove all non-ASCII characters (including �, �, etc.)
        manga_title = re.sub(r'[^\x00-\x7F]', '', manga_title)

        # Remove other unwanted special characters
        cleaned_title = re.sub(r'[!$@#%&*\(\)\-+=\[\]{}|;:\'"<>\?/.,~]', '', manga_title, flags=re.UNICODE)

        # Convert to lowercase
        cleaned_title = cleaned_title.lower()

        # Replace spaces with underscores
        search_title = cleaned_title.replace(" ", "_")

        # Remove consecutive underscores and leading/trailing underscores
        search_title = re.sub(r"_+", "_", search_title).strip("_")

        # URL encode the final search title
        search_title = urllib.parse.quote(search_title)

        # Construct the search URL
        search_url = f"{manga_url_search}{search_title}"

        # Navigate to the search URL
        driver.get(search_url)

        # Wait for the page to load
        time.sleep(5)  # Adjust as needed for slow connections

        # Locate search results
        search_items = driver.find_elements(By.CSS_SELECTOR, '.panel_story_list .story_item')
        if not search_items:
            raise Exception("No search results found.")

        # Extract the first manga link
        for item in search_items:
                
            link_tag = item.find_element(By.CSS_SELECTOR, 'a')
            manga_link = link_tag.get_attribute('href')
            if manga_link:
                print(f"Manga URL found: {manga_link}")
                # Save the URL to a file
                manga_dir = os.path.join(base_dir, manga_title)
                os.makedirs(manga_dir, exist_ok=True)
                url_file_path = os.path.join(manga_dir, 'url.txt')

                with open(url_file_path, 'w') as url_file:
                    url_file.write(manga_link)
                print(f"URL updated in: {url_file_path}")         
                driver.quit()
                

                try:
                    response = requests.get(manga_link, headers=headers)
                    response.raise_for_status()
                    html_content = response.text
                except requests.exceptions.RequestException as e:
                    print(f"Failed to fetch the manga page. Error: {e}")
                    return

                soup = BeautifulSoup(html_content, 'html.parser')

                chapter_list = soup.find('div', class_='chapter-list')
                chapter_links = chapter_list.find_all('div', class_='row')
                print("Chapter links found")
                continue 
            else:
                print("No matching manga found.")
                driver.quit()
                continue




          
                        
    print(f"Number of chapters found: {len(chapter_links)}")

    log_file_path = os.path.join(manga_dir, "download_log.txt")
    existing_log = {}
    if os.path.exists(log_file_path):
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            for line in log_file:
                chapter_url, chapter_title, last_updated = line.strip().split("\t")
                existing_log[chapter_url] = (chapter_title, last_updated)

    total_download_size = 0

    for chapter_item in chapter_links:
        chapter_item = str(chapter_item) 

        soup = BeautifulSoup(chapter_item, 'html.parser')  # Parse HTML

        # Find the <a> tag inside <span>
        a_tag = soup.find('a')  # Store in a different variable to avoid overwriting

        chapter_url = a_tag["href"].strip()  # Extract URL
        chapter_title = a_tag.text.strip()  # Extract title


        # Skip chapters that are already logged as downloaded
        if chapter_url in existing_log:
            print(f"Chapter {chapter_title} already downloaded. Skipping...")
            continue

        print(f"Processing Chapter: {chapter_title} | URL: {chapter_url}")

        match = re.search(r'Chapter (\d+(\.\d+)?)', chapter_title)
        if match:
            chapter_number = match.group(1)
            if '.' in chapter_number:
                chapter_number = chapter_number.replace('.', 'p')
            else:
                chapter_number = f"{int(chapter_number):02}"
            # Generate the CBZ filename and save the file
            cbz_filename = f"{manga_title} Chapter {chapter_number}.cbz"
            cbz_path = os.path.join(manga_dir, cbz_filename)
        else:
            cbz_filename = f"{manga_title} {sanitize_filename(chapter_title)}.cbz"
            cbz_path = os.path.join(manga_dir, cbz_filename)


        if os.path.exists(cbz_path) and os.path.getsize(cbz_path) > 0:
            print(f"Chapter {chapter_title} already exists as {cbz_filename}. Skipping...")
            continue



        chapter_response = requests.get(chapter_url)
        chapter_response.raise_for_status()
        chapter_soup = BeautifulSoup(chapter_response.text, 'html.parser')

        # Find the image container
        image_container = chapter_soup.find('div', class_='container-chapter-reader')

        if not image_container:
            print(f"No image container found for chapter: {chapter_title}. Skipping...")
            return 0

        image_tags = image_container.find_all('img')
            
        if not image_tags:
            print(f"No images found in chapter: {chapter_title}. Skipping...")
            return 0

        print(f"Found {len(image_tags)} images in chapter: {chapter_title}")
            
        img_url_list = []
        # Assuming image_tags is a list of img tags
        for img_tag in image_tags:
            img_url = img_tag.get('src')  # Get the 'src' attribute from the img tag
            if img_url:  # Only append if img_url is not None or empty
                img_url_list.append(img_url)


        def get_retry_session(max_retries=5, backoff_factor=1.5, status_forcelist=(500, 502, 503, 504, 520, 522, 524)):
            session = requests.Session()
            retry = Retry(
                total=max_retries,
                read=max_retries,
                connect=max_retries,
                backoff_factor=backoff_factor,
                status_forcelist=status_forcelist,
                raise_on_status=False,
                respect_retry_after_header=True,
            )
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            return session

        def save_image(file_path, content):
            with open(file_path, "wb") as f:
                for chunk in content:
                    if chunk:  # make sure it's not a keep-alive chunk
                        f.write(chunk)


        def download_image(img_url, img_name, manga_dir, headers, progress, lock, img_url_img_fail, img_url_img_fail_set, TRY2=False):
            img_file_path = os.path.join(manga_dir, img_name)
            session = get_retry_session()

            max_attempts = 10 if TRY2 else 2

            for attempt in range(max_attempts):
                try:
                    if TRY2:
                        response = requests.get(img_url, headers=headers)
                    else:
                        response = session.get(img_url, headers=headers)

                    if response.status_code == 200:
                        if attempt > 0:
                            print(f"\nRecovered: {img_name} on attempt {attempt + 1}.")
                        save_image(img_file_path, response.iter_content(8192))
                        with lock:
                            progress.update(1)
                        session.close()
                        return img_name

                    elif response.status_code in (500, 502, 503, 504, 520, 522, 524):
                        print(f"\n[HTTP {response.status_code}] Attempt {attempt + 1}: {img_name}. Retrying...")
                        if TRY2:
                            session.close()
                            session = get_retry_session()
                        continue

                    else:
                        print(f"[HTTP {response.status_code}] {img_name}. Not retrying.")
                        break

                except (RequestException, ReadTimeout) as e:
                    print(f"[Request Error] Attempt {attempt + 1}: {img_name} - {str(e)}")
                    if TRY2:
                        session.close()
                        session = get_retry_session()

            fail_entry = (img_url, img_name)
            with lock:
                if fail_entry not in img_url_img_fail_set:
                    img_url_img_fail.append(fail_entry)
                    img_url_img_fail_set.add(fail_entry)

            session.close()
            return None




        downloaded_count = 0
        lock = threading.Lock()
        progress = tqdm(total=len(img_url_list), desc=f"Downloading {chapter_title}", unit="file")

        img_url_img_fail = []         # List of failed downloads
        img_url_img_fail_set = set()  # Set for quick lookup

        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = {}
            for i, img_url in enumerate(img_url_list):
                base_url, image_path = split_image_url(img_url)
                request_headers = headers(manga_url_main, base_url, image_path, img_url)
                future = executor.submit(
                    download_image,
                    img_url,
                    f"{i+1:03}.webp",
                    manga_dir,
                    request_headers,
                    progress,
                    lock,
                    img_url_img_fail,
                    img_url_img_fail_set,
                    TRY2=False
                )
                futures[future] = img_url

            for future in as_completed(futures):
                if future.result():
                    downloaded_count += 1

        progress.close()
        print(f"\nDownloaded {downloaded_count}/{len(img_url_list)} images for {chapter_title}.")

        if img_url_img_fail:
            second_downloaded_count = 0
            print(f"\nRetrying {len(img_url_img_fail)} failed downloads...")

            failed_progress = tqdm(total=len(img_url_img_fail), desc="Retrying failed downloads", unit="file")
            second_fail_list = []
            second_fail_set = set()

            with ThreadPoolExecutor(max_workers=10) as retry_executor:
                retry_futures = {}
                for img_url, img_name in img_url_img_fail:
                    base_url, image_path = split_image_url(img_url)
                    request_headers = headers(manga_url_main, base_url, image_path, img_url)
                    future = retry_executor.submit(
                        download_image,
                        img_url,
                        img_name,
                        manga_dir,
                        request_headers,
                        failed_progress,
                        lock,
                        second_fail_list,
                        second_fail_set,
                        TRY2=True
                    )
                    retry_futures[future] = img_url

                for retry_future in as_completed(retry_futures):
                    if retry_future.result():
                        downloaded_count += 1
                        second_downloaded_count += 1

            failed_progress.close()

            # --- Final Report ---
            print(f"\nFinal: Downloaded {downloaded_count-second_downloaded_count}/{len(img_url_list)} images for {chapter_title}.")

            if second_fail_list:
                print(f"\nStill failed {len(second_fail_list)} images after retry.")
                with open(os.path.join(manga_dir, "failed_downloads.txt"), "w", encoding="utf-8") as fail_file:
                    for img_url, img_name in second_fail_list:
                        fail_file.write(f"{img_name} - {img_url}\n")
                print("\nSaved failed image URLs to 'failed_downloads.txt'.")
            else:
                print("\nAll images downloaded successfully after retry.")



        chapter_size = 0
        i = 0
        for i, img_url in enumerate(img_url_list):  
            img_name = f"{i+1:03}.webp"  
            img_file_path = os.path.join(manga_dir, img_name)
            
            if os.path.exists(img_file_path): 
                chapter_size += os.path.getsize(img_file_path)
            else:
                print(f"Warning: {img_file_path} not found.")

        print(f"Estimated size for {chapter_title}: {chapter_size / (1024 * 1024):.2f} MB")
        total_download_size += chapter_size

        # Extract chapter number using regex
        match = re.search(r'Chapter (\d+(\.\d+)?)', chapter_title)
        if match:
            chapter_number = match.group(1)
            if '.' in chapter_number:
                chapter_number = chapter_number.replace('.', 'p')
            else:
                chapter_number = f"{int(chapter_number):02}"

        # Generate the CBZ filename and save the file
        cbz_filename = f"{manga_title} Chapter {chapter_number}.cbz"
        cbz_path = os.path.join(manga_dir, cbz_filename)

        with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
            for i, img_url in enumerate(img_url_list):
                img_name = f"{i+1:03}.webp"
                img_file_path = os.path.join(manga_dir, img_name)
                
                # Ensure the file exists before adding it to the archive
                if os.path.exists(img_file_path):
                    cbz.write(img_file_path, arcname=img_name)  # Fix: Use img_name, not 'file'
                    os.remove(img_file_path)  # Remove after adding to CBZ
            

        # Add cover, metadata, and update logs
        cbz_name = f"{manga_title} Chapter {chapter_number}.cbz"
        add_cover_to_cbz(manga_title, chapter_title, cbz_name, manga_dir)
                                 
        # Download and extract metadata from MangaUpdates
        html_file_path_mangaupdates = search_manga_and_download_html_mangaupdates(manga_title, manga_dir)
        if html_file_path_mangaupdates is None:
            print("Failed to download MangaUpdates metadata.")
        metadata_mangaupdates = extract_metadata_from_txt_mangaupdates(manga_dir)

        # Download and extract metadata from MangaDex
        html_file_path_mangadex = search_manga_and_download_html(manga_title, manga_dir)
        if html_file_path_mangadex is None:
            print("Failed to download MangaDex metadata.")
        metadata_mangadex = extract_metadata_from_txt(manga_dir)

        # Merge metadata from both sources
        merged_metadata = merge_metadata(metadata_mangaupdates, metadata_mangadex, manga_dir)

        # Create ComicInfo.xml using the merged metadata
        xml_file_path = create_comicinfo_xml(manga_dir, merged_metadata, manga_title, chapter_url, cbz_name, image_tags)

        # Insert ComicInfo.xml into the CBZ file
        insert_comicinfo_into_cbz(manga_dir, cbz_name, xml_file_path)


        cbz_filename = f"{manga_title} Chapter {chapter_number}.cbz"
        cbz_path = os.path.join(manga_dir, cbz_filename)
        
        # Step 1: Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_extract_dir:
            # Step 2: Use 7z to extract the CBZ file
            subprocess.run([seven_zip_path, 'x', cbz_path, f'-o{temp_extract_dir}'], check=True)

            # Step 3: Delete the original CBZ file
            os.remove(cbz_path)

            # Step 4: Use 7z to re-compress files into a new CBZ file with the original structure
            new_cbz_path = os.path.join(manga_dir, cbz_filename)
            subprocess.run([seven_zip_path, 'a', '-tzip', new_cbz_path, f'{temp_extract_dir}/*'], check=True)


        # Log the successful download
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"{chapter_url}\t{chapter_title}\t{datetime.now().isoformat()}\n")
    else:
        print(f"Failed to extract chapter number from title '{chapter_title}'. Skipping...")


    # Update total download size
    total_update_size += total_download_size
    total_download_size_in_mb = total_download_size / (1024 * 1024)
    print(f"Total estimated update size: {total_download_size_in_mb:.2f} MB")
    update_combined_log()   





#For Code development Just Ignore It also Ignore txtnamedownlaod, check_links I'll Fix it Later
'''
def  txtnamedownlaod(txt_filepath):
    with open(txt_filepath, 'r', encoding='utf-8') as file:
        all_titles = [line.strip() for line in file if line.strip()]  
    total_titles = len(all_titles)

    if "mangabats" in os.path.basename(txt_filepath):
        main_url =  "https://www.mangabats.com/search/story/"
    elif "nelomanga" in os.path.basename(txt_filepath):
        main_url =  "https://www.nelomanga.com/search/story/"
    elif "mangakakalot" in os.path.basename(txt_filepath):
        main_url =  "https://www.mangakakalot.gg/search/story/"

    try:
        # Open the text file for reading
        with open(txt_filepath, 'r', encoding='utf-8') as file:

            line_count = 0  # Initialize a line counter
            processed_count = 0  # Counter for processed lines
            for line in file:
                line_count += 1  # Increment line count
                manga_title = line.strip()
                if manga_title:
                    try:
                        processed_count += 1  # Increment processed lines count
                        print(f"Processing line {line_count}, Remaining Titles {total_titles - processed_count}: {manga_title}")
                        # Clean and format the manga title
                        manga_title = manga_title.encode('utf-8', 'replace').decode('utf-8')
                        manga_title = re.sub(r'[^\x00-\x7F]', '', manga_title)
                        manga_title = re.sub(r'[!$@#%&*\(\)\-+=\[\]{}|;:\'"<>\?/.,~]', '', manga_title, flags=re.UNICODE)
                        cleaned_title = manga_title.lower().replace(" ", "_")
                        search_title = re.sub(r"_+", "_", cleaned_title).strip("_")
                        search_title = urllib.parse.quote(search_title)

                        driver = init_selenium()
                        # Construct the search URL and navigate to it
                        search_url = f"{main_url}{search_title}"
                        driver.get(search_url)
                        time.sleep(5)  # Wait for the page to load



                        search_items = driver.find_elements(By.CSS_SELECTOR, '.panel_story_list .story_item')
                        manga_link = None

                        # Iterate through items and find the first valid manga link
                        for item in search_items:
                            try:
                                link_tag = item.find_element(By.CSS_SELECTOR, 'a')
                                manga_link = link_tag.get_attribute('href')
                                if manga_link:
                                    break  # Stop once a valid link is found
                            except Exception as e:
                                print(f"Error finding link: {e}")

                        driver.quit()

                        # Process the manga link
                        if manga_link:
                            print(f"Manga URL found: {manga_link}")
                            print(f"Downloading manga from: {manga_link}")  # Placeholder for download logic
                            download_manga(manga_link)
                        else:
                            print(f"No results found for: {manga_title}")
                    except Exception as e:
                        print(f"An error occurred while processing '{manga_title}': {e}")
    except FileNotFoundError:
        print(f"Error: File not found at {txt_filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")

def  txturldownlaod(txt_filepath):
    with open(txt_filepath, 'r', encoding='utf-8') as file:
        all_titles = [line.strip() for line in file if line.strip()]  
    total_titles = len(all_titles)

    if "mangabats" in os.path.basename(txt_filepath):
        main_url =  "https://www.mangabats.com/search/story/"
    elif "nelomanga" in os.path.basename(txt_filepath):
        main_url =  "https://www.nelomanga.com/search/story/"
    elif "mangakakalot" in os.path.basename(txt_filepath):
        main_url =  "https://www.mangakakalot.gg/search/story/"

    try:
        # Open the text file for reading
        with open(txt_filepath, 'r', encoding='utf-8') as file:
            
            line_count = 0  # Initialize a line counter
            processed_count = 0  # Counter for processed lines

            for line in file:
                line_count += 1  # Increment line count 
                parts = line.strip().split("\t")  # Split by tab

                if len(parts) > 1 and parts[0].startswith("http"):  # Ensure there's a URL
                    url_title = unicodedata.normalize("NFKC", parts[0]).strip()  # Extract URL
                    manga_title = unicodedata.normalize("NFKC", parts[1]).strip() if len(parts) > 1 else None
                elif line.strip().startswith("http"):
                    url_title = line.strip()
                    manga_title = None
                else:
                    manga_title = line.strip()
                    manga_title2 = line.strip()
                    print(f"Finding Url for  {manga_title}:")
                    try:
                        # Clean and format the manga title
                        manga_title2 = manga_title2.encode('utf-8', 'replace').decode('utf-8')
                        manga_title2 = re.sub(r'[^\x00-\x7F]', '', manga_title2)
                        manga_title2 = re.sub(r'[!$@#%&*\(\)\-+=\[\]{}|;:\'"<>\?/.,~]', '', manga_title2, flags=re.UNICODE)
                        cleaned_title = manga_title2.lower().replace(" ", "_")
                        search_title = re.sub(r"_+", "_", cleaned_title).strip("_")
                        search_title = urllib.parse.quote(search_title)

                        driver = init_selenium()
                        # Construct the search URL and navigate to it
                        search_url = f"{main_url}{search_title}"
                        driver.get(search_url)
                        time.sleep(5)  # Wait for the page to load

                        search_items = driver.find_elements(By.CSS_SELECTOR, '.panel_story_list .story_item')
                        url_title = None
                        # Iterate through items and find the first valid manga link
                        for item in search_items:
                            try:
                                link_tag = item.find_element(By.CSS_SELECTOR, 'a')
                                url_title = link_tag.get_attribute('href')
                                if url_title:
                                    print(f"Url has been found for {manga_title}\t{url_title}\n")
                                    break  # Stop once a valid link is found
                            except Exception as e:
                                print(f"Error finding link: {e}")

                        driver.quit()
                    except Exception as e:
                        print(f"An error occurred while processing '{manga_title2}': {e}")


                if manga_title == None:
                    headers['Referer'] = url_title
                    try:
                        response = requests.get(url_title)
                        response.raise_for_status()
                        html_content = response.text
                        soup = BeautifulSoup(html_content, 'html.parser')
                        title_tag = soup.find('ul', class_='manga-info-text').find('li').find('h1')
                        manga_title = title_tag.text.strip()
                        manga_title = sanitize_filename(manga_title)
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to fetch the manga page. Error: {e}")
                        return

                log_file_path = os.path.join(base_dir, "Download_Progress_url.txt")

                # Format title for logging
                max_length = 50
                max_length2 = 40

                # Normalize text to ensure consistent spacing
                manga_title = unicodedata.normalize("NFKC", manga_title).strip()
                url_title = unicodedata.normalize("NFKC", url_title).strip()

                # Apply consistent padding
                formatted_title = manga_title[:max_length].ljust(max_length)
                formatted_title2 = url_title

                log_entry = f"{formatted_title2}\t{formatted_title}\t{datetime.now().isoformat()}\n"

                # Append to log file
                with open(log_file_path, "a", encoding="utf-8") as log_file:
                    log_file.write(log_entry)

                if url_title:
                   processed_count += 1  # Increment processed lines count
                   print(f"Processing line {line_count}, Remaining Titles {total_titles - processed_count}:")
                   download_manga(url_title)

    except FileNotFoundError:
        print(f"Error: File not found at {txt_filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")

def check_links(base_dir):

    manga_folders =  [folder for folder in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, folder))]
    invalid_manga = []

    print(f"Found {len(manga_folders)} manga folders.")

    for index, folder in enumerate(manga_folders, 1):
        if index == len(manga_folders) or index % 100 == 0:
            print(f"Checking {index} out of {len(manga_folders)}")
        else:
            print(f"Checking {index} out of {len(manga_folders)}",  end="\r")

        manga_folder_path = os.path.join(base_dir, folder)
        url_file = os.path.join(manga_folder_path, "url.txt")
    
        with open(url_file, "r", encoding="utf-8") as file:
           url = file.readline().strip()

        try:
            response = requests.get(url, timeout=5, headers=headers)
            if response.status_code >= 400 or response.status_code == 404 or "<title>404" in response.text or "Page Not Found" in response.text:
                print(f"Error occured while Checking for {index} {folder}")
                invalid_manga.append(f'{index} {folder}')
                continue  # No need to check further links for this manga
        except (requests.RequestException, requests.Timeout) as e:
            print(f"Error while Checking {index} {folder}")
            print(f"Error occured for {url}: {e}")
            invalid_manga.append(f'{index} {folder}')
            continue


    return invalid_manga
'''



 



def list_manga_folders():
    manga_folders = [folder for folder in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, folder))]
    print("Available Manga Titles:")
    for index, folder in enumerate(manga_folders, 1):
        print(f"{index}. {folder}")
    return manga_folders

def select_and_update_folders():
    manga_folders = list_manga_folders()
    print("Enter 'all' to update all folders.")
    selected_numbers = input("Enter the numbers of the manga folders to update (comma-separated): ").split(',')
    
    if 'all' in selected_numbers:
        selected_numbers = range(1, len(manga_folders) + 1)
    else:
        selected_numbers = [int(num.strip()) for num in selected_numbers]

    for num in selected_numbers:
        if 1 <= num <= len(manga_folders):
            manga_folder = manga_folders[num-1]
            manga_folder_path = os.path.join(base_dir, manga_folder)
            url_file_path = os.path.join(manga_folder_path, "url.txt")

            if os.path.exists(url_file_path):
                with open(url_file_path, "r", encoding="utf-8") as url_file:
                    manga_page_url = url_file.read().strip()
                print(f"Updating folder: {manga_folder}")
                update_manga(manga_page_url, manga_title=manga_folder)
            else:
                update_manga(None, manga_title=manga_folder)
        else:
            print(f"Invalid selection: {num}. Skipping...")



def handle_user_input():
    # Ask for initial input: '1', 'many', or 'update'
    user_input = input("Type '1' to download one manga title, 'many' for multiple manga titles, 'txt' from via text file format,  'check' for check if links work  or 'update' to select folders for update: ").strip().lower()

    if user_input == 'update':
        # Handle the update case
        select_and_update_folders()
        total_update_size_in_mb = total_update_size / (1024 * 1024)
        print(f"Total estimated update size: {total_update_size_in_mb:.2f} MB")

    elif user_input == 'many':
        # Interactive mode for entering multiple URLs
        print("Enter as many URLs as you wish. Type 'done' when finished.")
        url_list = []
        url_count = 1

        while True:
            user_input = input(f"Count {url_count}. Enter URL or 'done' to finish: ").strip()

            if user_input.lower() == 'done':
                break
    
            url_count += 1

            # Handle potential entry of multiple URLs in a single line
            urls = [url.strip() for url in user_input.split(',') if url.strip()]
            url_list.extend(urls)

        if not url_list:
            print("No valid URLs were provided.")
            return

        total_titles = len(url_list)
        for i, url in enumerate(url_list, start=1):
            remaining = total_titles - i
            print(f"Downloading {i} out of {total_titles} manga titles. Remaining files: {remaining}")
            download_manga(url)

        total_download_size_multiple_in_mb = total_download_size_multiple / (1024 * 1024)

        # Check if the size exceeds 1024 MB (1 GB)
        if total_download_size_multiple_in_mb >= 1024:
            # Convert to GB and print
            total_download_size_multiple_in_gb = total_download_size_multiple_in_mb / 1024
            print(f"Total estimated Download size: {total_download_size_multiple_in_gb:.2f} GB")
        else:
            # Print in MB
            print(f"Total estimated Download size: {total_download_size_multiple_in_mb:.2f} MB")

    elif user_input == '1':
        # Single URL download
        url = input("Enter the URL for the manga title: ").strip()

        if url:
            download_manga(url)
        else:
            print("No valid URL provided.")

    elif user_input == 'txt':
        name = input("Do you wish to downlaod via 'name' or 'url'?: ").strip().lower()
        if name == 'name':
            txt_filepath = input("Enter the path to the text file which has only names of manga titles: ")
            txtnamedownlaod(txt_filepath)
        else:
            txt_filepath = input("Enter the path to the text file which has only urls of mangas: ")
            txturldownlaod(txt_filepath)

    elif user_input == 'check':
        invalid_titles = check_links(base_dir)
        if invalid_titles:
            print("Manga folders with invalid links:")
            for title in invalid_titles:
                print(title)
        else:
             print("No manga folders found with invalid links:")

    else:
        print("Invalid input. Please enter '1', 'many', or 'update' 'Check' or 'txt'")
        return

    if user_input in ['update', 'many', '1', 'txt']:
    # Final messages after download or update
        print("All selected chapters downloaded and saved in their respective directories.")
        print(f"Combined log file updated and saved at {os.path.join(base_dir, 'combined_download_log.txt')}")

    # Wait for user input to exit
    input("Press Enter to exit...")


handle_user_input()



