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
from functions import load_json, save_json

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


def get_messages(urls: dict) -> dict:
    # we will save the screenshots here
    screenshots: dict = {}
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
                        break
                    except JavascriptException:
                        continue
                # find the last message and make a screenshot
                # really nice selenium feature, shoutout to the devs
                screenshot: str = wait.until(
                    ec.presence_of_element_located((By.XPATH, "//div[@data-scroll-pos='0']"))).screenshot_as_base64
                # save the screenshot to the dict created above
                screenshots[url] = screenshot
                break
            except TimeoutException:
                continue
            except ElementClickInterceptedException:
                continue
            except WebDriverException:
                continue
    return screenshots


def compare(old_data: dict, new_data: dict) -> Union[dict, None]:
    # this will hold the data that has been changed
    changes: dict = {}

    o_keys = old_data.keys()
    n_keys = new_data.keys()
    for key in n_keys:
        # check if the key exists in the old data
        if key in o_keys:
            if old_data[key] != new_data[key]:
                changes[key] = new_data[key]
                print(f"[DEBUG] found changes in {key}")
        else:
            print(f"[DEBUG] {key} was not found in old messages, don't worry, it will get added")
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
    data: dict = get_messages(urls)
    # load the old messages
    old_messages: dict = load_json("data/old_messages.json")
    # it may or may not be that there are no messages
    if all(value == "" for value in old_messages) or list(old_messages.values())[0] == "FNF":
        save_json("data/old_messages.json", data)
        print("[ERROR] occurred and handled: " + str(list(old_messages.values())[1]))
        return

    # json may error out while parsing the file
    elif list(old_messages.values())[0] == "JLE":
        print("[ERROR] unhandled json error: " + str(list(old_messages.values())[1]))
        return

    # compare the data
    changes: dict = compare(old_messages, data)
    save_json("data/old_messages.json", data)
    if changes:
        send_changes(changes)


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
        driver.close()
        sleep(float(getenv("REFRESH_INTERVAL")) * 60)
        driver = Firefox(executable_path="driver/geckodriver.exe", firefox_profile=driver_profile, options=driver_options)
