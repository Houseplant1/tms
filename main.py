"""
Before you freak out because the way this code is written, keep in mind that we are talking about ms teams here
"""

from os import getenv, getcwd, remove
from typing import Union
from base64 import decodebytes
from time import sleep

from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, \
    WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from functions import load_json

# the old messages will be saved here for comparison
old_sources: dict = {}
check_again: dict = {}

# we will need it like this so that we can close and reopen the browser
driver: Union[Firefox, None] = None
wait: Union[WebDriverWait, None] = None


def initialize() -> None:
    global driver
    global wait
    driver_options = Options()
    # make the browser headless
    driver_options.add_argument("--headless")
    # get the firefox profile from the environment variables
    # firefox profile is your current firefox browser data
    # we will use this so that we don't have to log into whatsapp and teams everytime we start the script
    # it will grab the log in data from your current firefox installation
    # make sure to be logged in whatsapp and teams in firefox before starting, otherwise it will not work
    driver_profile = FirefoxProfile(getenv("FIREFOX_PROFILE"))
    driver = Firefox(executable_path="driver/geckodriver.exe", firefox_profile=driver_profile, options=driver_options)

    # we will need this in order to wait for elements to appear.
    # it will wait up to 120 seconds
    # yes, this much time, because ms teams takes sometimes very very long to load
    wait = WebDriverWait(driver, 120)


# cool stuff here
def banner():
    print(r"""
                      ___           ___           ___           ___     
      ___        /  /\         /  /\         /__/\         /  /\    
     /  /\      /  /:/_       /  /::\       |  |::\       /  /:/_   
    /  /:/     /  /:/ /\     /  /:/\:\      |  |:|:\     /  /:/ /\  
   /  /:/     /  /:/ /:/_   /  /:/~/::\   __|__|:|\:\   /  /:/ /::\ 
  /  /::\    /__/:/ /:/ /\ /__/:/ /:/\:\ /__/::::| \:\ /__/:/ /:/\:\
 /__/:/\:\   \  \:\/:/ /:/ \  \:\/:/__\/ \  \:\~~\__\/ \  \:\/:/~/:/
 \__\/  \:\   \  \::/ /:/   \  \::/       \  \:\        \  \::/ /:/ 
      \  \:\   \  \:\/:/     \  \:\        \  \:\        \__\/ /:/  
       \__\/    \  \::/       \  \:\        \  \:\         /__/:/   
                 \__\/         \__\/         \__\/         \__\/    
      ___           ___           ___           ___           ___         ___           ___     
     /  /\         /  /\         /  /\         /  /\         /  /\       /  /\         /  /\    
    /  /:/_       /  /:/        /  /::\       /  /::\       /  /::\     /  /:/_       /  /::\   
   /  /:/ /\     /  /:/        /  /:/\:\     /  /:/\:\     /  /:/\:\   /  /:/ /\     /  /:/\:\  
  /  /:/ /::\   /  /:/  ___   /  /:/~/:/    /  /:/~/::\   /  /:/~/:/  /  /:/ /:/_   /  /:/~/:/  
 /__/:/ /:/\:\ /__/:/  /  /\ /__/:/ /:/___ /__/:/ /:/\:\ /__/:/ /:/  /__/:/ /:/ /\ /__/:/ /:/___
 \  \:\/:/~/:/ \  \:\ /  /:/ \  \:\/:::::/ \  \:\/:/__\/ \  \:\/:/   \  \:\/:/ /:/ \  \:\/:::::/
  \  \::/ /:/   \  \:\  /:/   \  \::/~~~~   \  \::/       \  \::/     \  \::/ /:/   \  \::/~~~~ 
   \__\/ /:/     \  \:\/:/     \  \:\        \  \:\        \  \:\      \  \:\/:/     \  \:\     
     /__/:/       \  \::/       \  \:\        \  \:\        \  \:\      \  \::/       \  \:\    
     \__\/         \__\/         \__\/         \__\/         \__\/       \__\/         \__\/ 
    """)


def get_messages(urls: dict) -> (dict, dict):
    print(f"[DEBUG] urls:\n{urls}")
    # we will save the screenshots here
    screenshots: dict = {}
    # we will save the sources here for comparison
    sources: dict = {}
    for url in urls:
        try:
            print("[DEBUG] processing url: " + urls[url])
            # visit the site
            driver.get(urls[url])
            # teams may ask you if you want to download the teams app or open it in the browser
            wait.until(ec.element_to_be_clickable((By.ID, "openTeamsClientInBrowser"))).click()
            # find the last message and make a screenshot
            # really nice selenium feature, shoutout to the devs
            screenshot: str = wait.until(
                ec.presence_of_element_located((By.XPATH, "//div[@data-scroll-pos='0']"))).screenshot_as_base64
            print(f"[DEBUG] screenshot made in {url}")
            # save the screenshot to the dict created above
            screenshots[url] = screenshot
            try:
                source: str = wait.until(
                    ec.presence_of_element_located(
                        (By.XPATH,
                         "//div[@data-scroll-pos='0']//div[@data-tid=\"messageBodyContent\"]//div"))).get_attribute(
                    'innerText')
            except TimeoutException as e:
                print(
                    f"[ERROR] timed out while trying to find innerText of {url}:\n\t{str(e)}\n\t"
                    f"probably because there is no text in the message")
                break
            print(f"[DEBUG] source of {url}: {source}")
            sources[url] = source
        except TimeoutException as e:
            print("[ERROR] " + str(e))
            check_again[url] = urls[url]
        except ElementClickInterceptedException as e:
            print("[ERROR] " + str(e))
            check_again[url] = urls[url]
        except WebDriverException as e:
            print("[ERROR] " + str(e))
            check_again[url] = urls[url]
        if url in check_again.keys():
            check_again.pop(url)
    return screenshots, sources


def compare(old_data: dict, new_data: dict) -> Union[list, None]:
    # this will hold the data that has been changed
    changes: list = []
    n_keys = new_data.keys()
    o_keys = old_data.keys()
    # check for changes
    for key in n_keys:
        if key not in o_keys:
            break
        if new_data[key] != old_data[key]:
            changes.append(key)
            print(f"[DEBUG] found changes in {key}")
    return changes


def send_changes(changes: dict) -> None:
    driver.get("https://web.whatsapp.com")
    # find the person/group we want to send the changes too and select it
    wait.until(ec.element_to_be_clickable((By.XPATH, f"//span[@title='{getenv('RECV')}']"))).click()
    for change in changes:
        # find the attach button and click it
        wait.until(ec.element_to_be_clickable((By.XPATH, "//div[@title='Attach']"))).click()
        # we have to write the screenshot to a file in order to be able to send it
        with open("tmp.png", "wb") as fh:
            fh.write(decodebytes(changes[change].encode()))
            fh.close()
        # find the input element and attach the image
        wait.until(ec.presence_of_element_located(
            (By.XPATH, "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']"))).send_keys(
            getcwd() + "\\tmp.png")
        # find the send button and click
        wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "._3ipVb"))).click()
        # delete the temp img
        remove(getcwd() + "\\tmp.png")
        print("[DEBUG] sent change: " + change)
        sleep(2)


def main():
    # load the urls file
    urls: dict = load_json("data/urls.json")
    # it may or may not be that there are no urls
    if all(value == "" for value in urls) or list(urls.values())[0] == "FNF":
        print("[ERROR] there is no urls file or the urls are empty: " + str(list(urls.values())[1]))

    # json may error out while parsing the file
    elif list(urls.values())[0] == "JLE":
        print("[ERROR] json error while parsing urls: " + str(list(urls.values())[1]))
        return

    # load the current messages
    screenshots, sources = get_messages(urls)

    # reprocess urls that couldn't be processed
    while len(check_again) != 0:
        driver.quit()
        initialize()
        revisited_scr, revisited_sources = get_messages(check_again)
        screenshots.update(revisited_scr)
        sources.update(revisited_sources)

    # if there is no old data, copy the current data
    # this avoids sending unnecessary messages on first run
    if len(old_sources.keys()) == 0:
        old_sources.update(sources)
        return

    # compare the data
    changes: list = compare(old_sources, sources)
    screenshots_changes = {}
    if changes:
        for change in changes:
            screenshots_changes[change] = screenshots[change]
        send_changes(screenshots_changes)

    # update old_sources
    old_sources.update(sources)


if __name__ == '__main__':
    banner()
    initialize()
    while True:
        driver.get("https://teams.microsoft.com/")
        try:
            wait.until(ec.element_to_be_clickable((By.XPATH, "//button[@id='ts-waffle-button']")))
            break
        except TimeoutException:
            continue
    while True:
        main()
        print(f"[DEBUG] finished, sleeping for {getenv('REFRESH_INTERVAL')}")
        driver.quit()
        sleep(float(getenv("REFRESH_INTERVAL")) * 60)
        initialize()
