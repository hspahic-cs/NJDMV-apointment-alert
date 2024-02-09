from subprocess import TimeoutExpired
from this import d
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

import os
import time

URL = "https://www27.state.nj.us/tc/driverlogin.do?url=njmvcdtclient"
PATH = "C:\Program Files (x86)\chromedriver"

class RD_Scraper:
    """
    DESCRIPTION: Class dedicated for continously monitoring open NJMVC road tests
    in the hope of getting an earlier appointment. Different from dl-alert, due to
    different registration page system.

    Attributes:
    (string) Drivers License Number [DLN]  -> letter + 14 digit number necessary for page access
    (string) Permit Validation Numbeer [PVN]  -> 5-digit number necessary for page access
    (string) zip -> zipcode closest to user's desired location
    preferred_times -> ??? not sure yet
    (bs4 object) current_page -> copy of the current pages html 

    """

    def __init__(self, DLN, PVN, preferred_times, zip, soup=None):
        self.DLN = DLN
        self.PVN = PVN
        self.preferred_times = preferred_times
        self.zip = zip

        self.soup = soup
        self.driver = webdriver.Chrome(PATH)

        # Clear terminal outputs
        os.system("clear")

        # Load login page
        try:
            self.driver.get(URL)
            time.sleep(10);
            # self.driver.set_page_load_timeout(30)
        except TimeoutException:
            print("Unable to load login page", TimeoutException)
            exit()

        print("Successfully loaded page")

    def login(self):
        """Attempt to login to rescheduling website"""

        # Fill DLN cred
        select_DLN_text = self.driver.find_element(By.NAME, "licenseNumber")
        select_DLN_text.clear()
        select_DLN_text.send_keys(self.DLN)

        # Fill PVN cred
        select_PVN_text = self.driver.find_element(By.NAME, "permitNumber")
        select_PVN_text.clear()
        select_PVN_text.send_keys(self.PVN)
        
        # Wait for page to load
        try:
            # Submit login information
            self.driver.find_element(By.CLASS_NAME, "button").click()
            self.driver.set_page_load_timeout(30)
        except Exception as exc:
            print("Unable to login", exc)
            self.end_prgm()

        time.sleep(3)


        # Success
        print("Login Successful!")

    def reschedule(self):
        """
        Selects reschedule for page, enters neccessary location information
        """
        
        # Select to reschedule
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'Reschedule')]").click()
            time.sleep(1)
        except Exception as exc:
            print("Unable to select [Reschedule] option :: ", exc)
            self.end_prgm()
    
        # Select zipcode
        try: 
            zip_form = self.driver.find_element(By.NAME, "location_zip")
            zip_form.clear()
            zip_form.send_keys(self.zip)

            # submit zipcode search
            self.driver.find_element(By.XPATH, "//input[@type='button' and @value='Search']").click()
            time.sleep(1)
        except Exception as exc:
            print("Unable to enter zipcode :: ", exc)
            self.end_prgm()

        # Load appointments page for next available location
        try: 
            but = self.driver.find_element(By.XPATH, "//input[@type='button' and @value='Next']")
            print(but)
            but.click()
            time.sleep(3)
        except Exception as exc:
            print("Unable to load appointments page :: ", exc)
            self.end_prgm()

        # Success
        print("Selection sucessful")

    def search_apmt(self):
        """
        Main function, continously monitor dates upto 3 weeks in advance for new appointments
        """

        # Get information for changing weeks (next & previius)


        # Note: Reason why this was so hard to debug was because actual html different from html displayed on google devtools
        try: 
            print("Writing to file")
            with open("test.txt", 'w') as f:
                f.write(self.driver.page_source)
                # html = self.driver.execute_script("return document.getElementsByTagName('html')").;
                # print(html)
                # f.write(html)
                f.close()
            #prev_week = self.driver.find_element(By.XPATH, "//input[@type='button' and @value='Back']")
            #next_week = self.driver.find_element(By.XPATH, "//input[@type='button' and @value='Next']")      
            #prev_week.click()
           
            #next_week.click()
            #time.sleep(3)
        
        except Exception as exc:
            print("Unable to locate prev / next buttons", exc)
            self.end_prgm()

        #current = self.driver.find_element(By.CLASS_NAME, "f24b").getText()
        #print(current)

    def end_prgm(self): 
        self.driver.close()
        quit()

    def __call__(self):
        self.login()
        self.reschedule()
        self.search_apmt()        