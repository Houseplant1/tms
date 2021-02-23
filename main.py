"""
Before you freak out because the way this code is written, keep in mind that we are talking about ms teams here
"""

from os import getenv, getcwd, remove
from typing import Union
from base64 import decodebytes
from time import sleep

from selenium.common.exceptions import JavascriptException, TimeoutException, ElementClickInterceptedException, \
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
    # we will save the screenshots here
    screenshots: dict = {}
    # we will save the sources here for comparison
    sources: dict = {}
    for url in urls:
        while True:
            try:
                print("[DEBUG] processing url: " + urls[url])
                # visit the site
                driver.get(urls[url])
                # teams may ask you if you want to download the teams app or open it in the browser
                wait.until(ec.element_to_be_clickable((By.ID, "openTeamsClientInBrowser"))).click()
                # remove the date from the message
                # because if the message is 1 day old, it shows yesterday + time as date
                # if the date is older it shows a normal date
                # this makes this script that a message is new even though it is not
                while True:
                    # because of how shitty m$ teams is, it may be that the messages appear
                    # then disappear again, this causes the script to continue
                    # although the message is not visible anymore
                    try:
                        driver.execute_script(
                            "var elements = document.getElementsByClassName(\"timestamp-column\");elements.item("
                            "  elements.length-1).remove();")
                        # remove the scroll handle, it causes issues
                        driver.execute_script(
                            "var list = document.getElementsByClassName(\"drag-handle\");" +
                            "for(var i=0; i < list.length; i++) {list[i].remove() }")
                        print(f"[DEBUG] removed handle and time in {url}")
                        break
                    except JavascriptException:
                        continue
                # find the last message and make a screenshot
                # really nice selenium feature, shoutout to the devs
                screenshot: str = wait.until(
                    ec.presence_of_element_located((By.XPATH, "//div[@data-scroll-pos='0']"))).screenshot_as_base64
                print("[DEBUG] screenshot made in {de}")
                # save the screenshot to the dict created above
                screenshots[url] = screenshot
                source: str = wait.until(
                    ec.presence_of_element_located(
                        (By.XPATH,
                         "//div[@data-scroll-pos='0']//div[@data-tid=\"messageBodyContent\"]//div"))).get_attribute(
                    'innerText')
                print(f"[DEBUG] source of {url}: {source}")
                sources[url] = source
                break
            except TimeoutException as e:
                print("[ERROR] " + str(e))
                continue
            except ElementClickInterceptedException as e:
                print("[ERROR] " + str(e))
                continue
            except WebDriverException as e:
                print("[ERROR] " + str(e))
                continue
    return screenshots, sources


def compare(old_data: dict, new_data: dict) -> Union[list, None]:
    # this will hold the data that has been changed
    changes: list = []
    # check for changes
    for key in new_data.keys():
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

    # if there is no old data, copy the current data
    # this avoids sending unnecessary messages on first run
    if len(old_sources.keys()) == 0:
        old_sources.update(sources)
        return

    # compare the data
    changes: list = compare(old_sources, sources)
    screenshots_changes = {}
    for change in changes:
        screenshots_changes[change] = screenshots[change]
    if changes:
        send_changes(screenshots_changes)

    # update old_sources
    old_sources.update(sources)


if __name__ == '__main__':
    while True:
        driver.get("https://teams.microsoft.com/")
        try:
            wait.until(ec.element_to_be_clickable((By.XPATH, "//div[@class='teams-title']")))
            break
        except TimeoutException:
            continue
    while True:
        main()
        sleep(float(getenv("REFRESH_INTERVAL")) * 60)
