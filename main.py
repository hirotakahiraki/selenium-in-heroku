from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv
from time import sleep

class Selenium:
    posts = []
    def __init__(self, url1, url2, ID, PASS):
        driver_path = '/app/.chromedriver/bin/chromedriver'
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
    
        driver = webdriver.Chrome(options=options, executable_path=driver_path)

        # Basic Authentication
        driver.get(url1)

        # Single Sign On
        driver.find_element_by_id("edit-name").send_keys(ID)
        driver.find_element_by_id("edit-pass").send_keys(PASS)
        driver.find_element_by_id('edit-submit').click()
        
        # Get URL for scraping
        driver.get(url2)
        html = driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        table = soup.findAll("table", {"class":"sticky-enabled sticky-table"})[0]
        tbody = table.find("tbody")
        trs = tbody.find_all("tr")
        for tr in trs:
            post = [td.text for td in tr.find_all(["td"])]
            post.append(tr.select('a[href]')[0].get("href"))
            post.append(False)
            if post[1][-4:] == " new":
                post[1] = post[1][:-4]
                post[6] = True
            print(post)
            self.posts.append(post)
        driver.quit()

class SlackDriver:

    def __init__(self, _token, _channel):

        self._headers = {"Authorization": "Bearer {}".format(_token)}
        self._channel = _channel

    def send_message(self, message):
        params = {"channel": self._channel, "text": message}
        slack_url = 'https://slack.com/api/chat.postMessage'

        r = requests.post(slack_url,
                          headers=self._headers,
                          params=params)
        print("return ", r.json())

class Deepl:
    def __init__(self, url, key, target_lang):
        self.url = url
        self.auth_key = key
        self.target_lang = target_lang
    
    def translate(self, text):
        
        params = {
            "auth_key":self.auth_key,
            "text": text,
            "target_lang":self.target_lang
        }
        res = requests.post(self.url, params=params).json()
        print(res)
        return res["translations"][0]["text"]

if __name__ == '__main__':
    # load env
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    
    # selenium
    access_url = os.environ.get("ACCESS_URL")

    url1 = os.environ.get("URL1")
    url2 = os.environ.get("URL2")
    ID = os.environ.get("ID")
    PASS = os.environ.get("PASS")

    posts = Selenium(url1, url2, ID, PASS).posts

    # slack setting
    token = os.environ.get("SLACKTOKEN")
    channel = os.environ.get("SLACKCHANNEL")
    slack = SlackDriver(token, channel)

    # deepl setting
    deepl_url = os.environ.get("DEEPLURL")
    deepl_key = os.environ.get("DEEPLKEY")
    target_lang = "EN"
    deepl = Deepl(deepl_url, deepl_key, target_lang)
    
    for post in posts:
        split = post[4].split(" ")
        if int(split[0]) == 1 and split[1]=="day" :
            post_en = deepl.translate(post[1]) # deepl 
            message = "-------------------\n"
            if post[6]:
                message += "[`New`] |"
            message += post[1].replace("【","【 *").replace("】","* 】")
            message += "\n[*EN*] " + post_en + "\n"
            message += "<" + access_url+post[5] + ">"
            slack.send_message(message) # Post to Slack
            sleep(3)
