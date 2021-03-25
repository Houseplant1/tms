### Installation :floppy_disk:

---
```
git clone https://github.com/Houseplant1/tms.git
cd tms
pip install virtualenv
virtualenv env
source env/bin/activate (Linux)
env\Scripts\activate.bat (Windows)
pip install -r requirements.txt 
```

Add the urls you want to scrap from e.g.: {"name": "url"} in the src/urls.json file.

Download geckodriver and put it in src/driver/ folder. 

Create a .env file in the src directory. Parameters:

| Name                | Value                          |
| ------------------- | ------------------------------ |
| FIREFOX_PROFILE     | e.g.: C:/Users/username/AppData/Roaming/Mozilla/Firefox/Profiles/something.something   |
| RECV                | Whatsapp contact/group name    |
| REFRESH_INTERVAL    | Pause between checks in minutes|


Run the main.py file, and you are good to go!


### Attention :warning:

---

- You may have to use pip3 instead of pip
- I may or may not update this project. I don't know.
- Don't expect perfect or bug-free code.
