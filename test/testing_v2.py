import socket
import unittest

#from flask import request
from time import sleep
from datetime import datetime
from datetime import timedelta

import logging

import dialogflow
from gevent import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import io
import urllib.request
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


class Testing_ChatBot_v2(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()

    def  test_v2(self):
        driver = self.driver
        server_url = "http://160.85.252.47:5000"
        driver.get(server_url)
        test = open("test_v2.txt", "r")
        elem = driver.find_element_by_id("input_message")

        questions = ["Anything else?", "Would you like to specify any other requirement?",
                     "What else should I take into consideration?", "What else do you want to include?"]
        answers = ["no thanks", "no", "that's all", "nothing"]

        i = 0
        for line in test:
            if len(line) > 1 and '#' not in line:
                elem.send_keys(line)
                sleep(2)
                elem.send_keys(Keys.ENTER)
                sleep(2)

            if len(line) <= 1:
                for question in questions:
                    if elem2[len(elem2) - 1].text.__contains__(question):
                        idx = questions.index(question)
                        elem.send_keys(answers[idx])
                        sleep(2)
                        elem.send_keys(Keys.ENTER)
                        sleep(2)
                i += 1

            elem2 = driver.find_elements_by_css_selector(".bot-message")
            self.assertIsNotNone(elem2)
            sleep(2)

        test.close()

        assert "No results found." not in driver.page_source


    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
