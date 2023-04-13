from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests
import os
from os.path import join, dirname
from dotenv import load_dotenv
from time import sleep
from datetime import datetime, timezone, timedelta

class Selenium:
    def __init__(self, url1, access_url):
        self.posts = []
        self.url1 = url1
        self.access_url = access_url
        
        driver_path = '/app/.chromedriver/bin/chromedriver'
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')

        driver = webdriver.Chrome(options=options, executable_path=driver_path)
        self.driver = driver

    def get_posts(self, url2, ID, PASS):
        # Basic Authentication
        self.driver.get(url1)

        # Single Sign On
        self.driver.find_elements(By.ID, "edit-name")[0].send_keys(ID)
        self.driver.find_elements(By.ID, "edit-pass")[0].send_keys(PASS)
        self.driver.find_elements(By.ID, 'edit-submit')[0].click()
        

        # Get URL for scraping
        self.driver.get(url2)
        html = self.driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        table = soup.findAll(
            "table", {
                "class": "sticky-enabled sticky-table"})[0]
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
        # self.driver.quit()
        return self.posts

    def get_post_message(self, url_node, format_to_slack=True):
        url_node_with_ba = self.url1 + url_node
        self.url_node = self.access_url+url_node
        self.url_node_with_ba = url_node_with_ba
        self.driver.get(url_node_with_ba)
        html = self.driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find('h2', class_='content-title').get_text()
        content = soup.find("div", class_="node").get_text()
        
        if format_to_slack:
            thread_message = self.formatting_to_slack(title, content)
            return thread_message
        else:
            return title +"\n"+ content + "\n" + self.url_node
    
    def formatting_to_slack(self, text, content):
        return "------------------------------\n\n"+"*"+text +"*"+ "\n" + content + "\n" + self.url_node
        
        

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
        return r.json()
    
    def send_message_to_chile_thread(self, message, parent_ts):
        params = {"channel": self._channel, "text": message, "thread_ts": parent_ts}
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
            "auth_key": self.auth_key,
            "text": text,
            "target_lang": self.target_lang
        }
        res = requests.post(self.url, params=params).json()
        print(res)
        return res["translations"][0]["text"]

if __name__ == '__main__':
    #  JSTでAM 9:00から9:15の間であれば実行
    if datetime.now(timezone(timedelta(hours=+9), 'JST')).hour != 9 or datetime.now(timezone(timedelta(hours=+9), 'JST')).minute > 15:
        exit()
        
    # load env
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)

    # selenium
    access_url = os.environ.get("ACCESS_URL")

    url1 = os.environ.get("URL1")
    url2 = os.environ.get("URL2")
    ID = os.environ.get("ID")
    PASS = os.environ.get("PASS")

    selenium_driver = Selenium(url1, access_url)
    posts = selenium_driver.get_posts(url2, ID, PASS)

    # slack setting
    token = os.environ.get("SLACKTOKEN")
    channel = os.environ.get("SLACKCHANNEL")
    slack = SlackDriver(token, channel)

    # deepl setting
    # deepl_url = os.environ.get("DEEPLURL")
    # deepl_key = os.environ.get("DEEPLKEY")
    # target_lang = "EN"
    # deepl = Deepl(deepl_url, deepl_key, target_lang)

    for post in posts:
        split = post[4].split(" ")
        print(split, post)
        # 1日前のもののみを投稿
        if int(split[0]) == 1 and split[1] == "day":
        
            message_thread = selenium_driver.get_post_message(post[5][1:])
            slack.send_message(message_thread)
            
            print("posted.")
            sleep(1)
        
