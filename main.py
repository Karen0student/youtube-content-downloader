import yt_dlp
from pydub import AudioSegment
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import time
import tkinter as tk
from datetime import datetime

def get_playlist_info(url):
    ydl_opts = {
        'quiet': True,  # Suppress yt-dlp output
        'extract_flat': True,  # Only get metadata, not download
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except yt_dlp.utils.DownloadError as e:
        error_message = str(e).lower()
        if 'sign in' in error_message or 'private' in error_message:
            print("Authentication or special permissions required to access this content.")
        elif '403' in error_message:
            print("Access forbidden. This content may require authentication.")
        else:
            print(f"Download error: {e}")
    except yt_dlp.utils.ExtractorError as e:
        print(f"Extractor error: {e}")
    except yt_dlp.utils.UnsupportedError as e:
        print(f"Unsupported URL error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None


def create_directory(directory_name): # album directories
    try:
        if not os.path.exists(f"./downloads/{directory_name}"):
            os.makedirs(f"./downloads/{directory_name}")
            print(f"Directory ./downloads/{directory_name} created.")
        else:
            print(f"Directory ./downloads/{directory_name} already exists.")
    except Exception as e:
        print(f"An error occurred while creating the directory: {e}")


def download_youtube_video(url, download_type, download_path):
    ydl_opts = {}

    if download_type == "video":
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
        }
    elif download_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:
        print("Invalid download type. Choose 'video' or 'audio'.")
        return

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"{download_type.capitalize()} downloaded to {download_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("retrying")
        download_youtube_video(url, download_type, download_path) # recall same function if error
        

def main():
    playlist = []
    if os.path.exists(f"./youtube_link.txt"):
        with open('./youtube_link.txt', 'r') as file:
            playlist = file.readlines()
    else:
        #playlist = str(sys.stdin.readline('Enter youtube playlist url and video count separated by one "space": '))
        playlist.append(str(input('Enter youtube playlist url and video count separated by one "space": ')))
    
    download_type = input("Do you want to download 'video' or 'audio'? (press Enter to use default 'audio'): ") or 'audio'
    
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/chromium-browser'  # Path to the Chromium browser
    driver = webdriver.Chrome(options=chrome_options)
    download_path = "./downloads"
    if not os.path.exists(download_path): # main directory
        os.makedirs(download_path)
    scrapped_path = "./scraped_urls.txt" # create folder to save urls
    if not os.path.exists(scrapped_path):
        os.makedirs(scrapped_path)
        
    for index in range(len(playlist)):
        download_path = "./downloads" # reseting because adding ./downloads/{new_playlist}
        if playlist is None: # if end of file reached
            print("FINISH")
            break
        parts = playlist[index].split() # playlist is list
        if not parts:
            break
        playlist_url = str(parts[0])
        # create album folder by playlist name
        title = get_playlist_info(playlist_url)
        if title: #and 'title' in title:
            playlist_name = title.get('title', 'Unknown Playlist')
            print(f"Playlist name: {playlist_name}")
            create_directory(str(playlist_name))
            download_path += f"/{playlist_name}"
        else:
            print("ERROR, can't get playlist title, exiting")
            break
        # Open YouTube video
        driver.get(playlist_url)
        with open(scrapped_path, 'a') as file: ######## optional
                file.write(f"Playlist url: {playlist_url} {str(datetime.now())}\n")
        
        for count in range(int(parts[1])):
            print("Wait for the page to load")
            time.sleep(4)
            print("working...")
            try:
                # Check for sign-in requirement
                if driver.find_element(By.CSS_SELECTOR, 'button[class="yt-spec-button-shape-next yt-spec-button-shape-next--tonal yt-spec-button-shape-next--mono yt-spec-button-shape-next--size-m yt-spec-button-shape-next--icon-leading"]'):
                    driver.find_element(By.CSS_SELECTOR, 'button[class="yt-spec-button-shape-next yt-spec-button-shape-next--tonal yt-spec-button-shape-next--mono yt-spec-button-shape-next--size-m yt-spec-button-shape-next--icon-leading"]').click()
            except:
                print("ERROR, SKIPPING")
                time.sleep(3) # for youtube's autonext algorithm
                continue

            # Wait for the share menu to appear
            time.sleep(2)

            copy_button = driver.find_element(By.CSS_SELECTOR, 'button[class="yt-spec-button-shape-next yt-spec-button-shape-next--filled yt-spec-button-shape-next--call-to-action yt-spec-button-shape-next--size-m"]')
            copy_button.click()

            # Wait for the link to be copied
            time.sleep(1)

            root = tk.Tk()
            root.withdraw()  # Hide the main window
            copied_link = root.clipboard_get()

            # Save the copied link to a .txt file
            with open(scrapped_path, 'a') as file:######## optional (remove count)
                file.write(f"{str(count + 1)}. {copied_link}\n")

            print(f"The link: {copied_link} has been copied and saved to scraped_urls.txt")
            
            # downloader segment
            download_youtube_video(copied_link, download_type, download_path)
            # ---------------
            close_button = driver.find_element(By.CSS_SELECTOR, 'yt-icon[class="style-scope ytd-unified-share-panel-renderer"]')
            close_button.click()
            time.sleep(1)
            if count == range(int(parts[1]) - 1): # Do not click the "Next" button if you have reached the end
                break
            next_button = driver.find_element(By.CSS_SELECTOR, 'a[class="ytp-next-button ytp-button"]')
            next_button.click()
        
        with open(scrapped_path, 'a') as file: # newline in file ######## optional
                file.write("\n")
            
    # Close the browser
    driver.quit()
    print("FINISHED")

if __name__ == "__main__":
    main()