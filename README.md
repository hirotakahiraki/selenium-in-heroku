# selenium-in-heroku

scrape some websites with Selenium in Python, hosted on Heroku.

with SlackDriver and Deepl, you can translate the information from the website into your language and push notification to slack channel.

check:
$ heroku buildpacks

if python buildpacks don't exist, add it using
$ heroku buildpacks:add heroku/python

$ python main.py
