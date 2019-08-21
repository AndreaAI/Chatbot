import socket
import unittest
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import io

class Testing_ChatBot_v1(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()

    def test_v1(self):
        driver = self.driver
        server_url = "http://160.85.252.47:5000"  ## the local url obtained web launching the flask app
        driver.get(server_url)
        test = open("test_v1.txt", "r")
        elem = driver.find_element_by_id("input_message")
        for line in test:
            if len(line) > 1:
                elem.send_keys(line)
                sleep(2)
                elem.send_keys(Keys.ENTER)
                sleep(2)

        assert "No results found." not in driver.page_source


    def tearDown(self):
        self.driver.close()

if __name__ == "__main__":
    unittest.main()
