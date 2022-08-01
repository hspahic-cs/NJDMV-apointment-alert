import json
import urllib.request
import re
import time
import winsound

# from selenium import webdriver
# PATH = "C:\Program Files (x86)\chromedriver.exe"
# driver = webdriver.Chrome(PATH)

from bs4 import BeautifulSoup
from click import confirm
from formFill import createBrowserScript
from datetime import datetime, date

from pathlib import Path


UPDATE_DELAY = 5
RESET_DELAY = 900
SUCCESS_DELAY = 120

DEFAULT_TIMES = {0: "+0", 1: "+0", 2: "+0", 3: "+0", 4: "+0", 5: "+0", 6: "+0"} # 0 = Monday
DATE_DICTIONARY = {1:"January",  2:"February", 3:"March", 4:"April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"December"}

# Add appointment details

class DMV_Scaper:
    """ DESCRIPTION TO BE MADE
        
    Attributes:
        (string) appointment: name of appoitment to be scraped
        (string[]) locations: target DMV's for appointment
        {str: int} required_months: target months for appoitment with first interested date (format: {"July":20}) 
        {int: string} preferred_times: dictionary of preferred times for each day of the week
        format {"day": "time"} --> times can either be [ before time: -12 | after time: +6 | between time: 3-5]
    """

    def __init__(self, appointment, locations, required_months, preferred_times=DEFAULT_TIMES):
        
        self.appointment = appointment
        self.locations = locations
        self.required_months = required_months
        self.preferred_times = preferred_times
        self.url = None

    def getLocationData(self):
        """ Gets location encoding for NJDMV from json
        (str) appointment -> name of appointment type
        (str[]) locations -> list of locations to be check
        """
        location_with_array = {}
        base_url_link = ""
        with open("DMV_appointment/" + self.appointment) as jsonFile:
            data = json.load(jsonFile)
            jsonFile.close()

        for location in self.locations:
            location_with_array[location] = data['location_with_array'][location]

        base_url_link = data["base_url_link"]
        
        self.locations = location_with_array
        self.url = base_url_link

    def confirm_conditions(self, date_string, appointment_links):
        """ Helper function to clean code, parses links for all appointments in given day
            then returns whether all conditions (Month, DOM, DOW, Time) are met for appointment
            (bs4 object) date_string: 
        """    
        check = True

        # Creates date object from available appoiitment for ease of access
        parsed_appointments = [time.split('/')[-2:] for time in appointment_links]
        most_recent_apt = date.fromisoformat(parsed_appointments[0][0])

        # Check day of week (DOW)
        DOW = most_recent_apt.weekday()
        if(not(DOW in self.preferred_times)):
            return False

        # Check for required months
        if(not (bool(set(self.required_months.keys()) & set(date_string.text.split())))):
            return False
        
        # Check for day of month (DOM)
        DOM = most_recent_apt.day
        intended_date = self.required_months[DATE_DICTIONARY[most_recent_apt.month]]
        
        if(intended_date > 31 or intended_date < 0):
            raise ValueError("Intended date not valid")
        
        if(intended_date <= DOM):
            return False
        
        # If month & DOW, filter preferred time appointments
        # othewise return false
        if(check):
            check = []
            for i, appointment in enumerate(parsed_appointments):
                DOW_time = int(appointment[-1])
                
                if(self.preferred_times[DOW][0] == "+"):
                    if(DOW_time >= int(self.preferred_times[DOW][1:])):
                        check.append(appointment_links[i])

                elif(self.preferred_times[DOW][0] == "-"):
                   
                    if(DOW_time <= int(self.preferred_times[DOW][1:])):
                        check.append(appointment_links[i])
                
                else:
                    time_constraints = self.preferred_times[DOW].split("-")
                    if(DOW_time >= int(time_constraints[0]) and DOW_time <= int(time_constraints[1])):
                        check.append(appointment_links[i])

        return check
    
    def log_appointment(self, appointments):
        """ Take all successfully found appointments & adds them to continous
        csv file, along with the user's name & the current date
        """
        
        with open("appointment_logs.csv", "w") as log:
            for appointment in appointments:
                log.write(appointment)
            log.close()

    def job(self):
        """ Performs appointment scraping, continously runs until process ended.
        If appointment found, opens link providing notepad containing jscript to
        autofill form. Otherwise, keeps looking for appointments in "required_months."
        """
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        print("\n\n\nDate Time: ", dt_string, "\n\n")
        i=0
        found=0

        # Get converted locations & appointment link
        self.getLocationData()

        confirmation, reset = False, False

        # Check appointsments for each location
        for key in self.locations:
            location = key
            
            with urllib.request.urlopen(self.url+self.locations[location]) as response:
                page_html = response.read()
                soup = BeautifulSoup(page_html ,"html.parser")
                unavailable=soup.find('div',attrs={'class': 'alert-danger'})

                # If no alerts found in html, no appointments found
                if unavailable is not None:
                    print('No appointments are available in '+ location)

                # Otherwise
                else:
                    # Find the attribute attributed to potential dates
                    dates_html = soup.find('div', attrs={'class': 'col-sm-6 text-center col-md-8 col-lg-8'})
                    
                    # After recieving repeated requests, website returns "repeated usage" error page
                    # reset after recieveing said page
                    if dates_html is None:
                        reset = True
                        continue
                    
                    # date_string format: <label class="control-label">Time of Appointment for August 18, 2022: </label> 
                    date_string = dates_html.find('label',attrs={'class': 'control-label'}) 
                    appointment_links = []

                    for link in soup.find('div', id = "timeslots").find_all('a'):
                        # a href format: <a href="/njmvc/AppointmentWizard/15/198/2022-08-18/955" class="text-primary">
                        appointment_links.append(link.get('href'))
                    
                    filtered_appointments = self.confirm_conditions(date_string, appointment_links)

                    if filtered_appointments:
                        for link in filtered_appointments:
                            link = "https://telegov.njportal.com" + link
                            createBrowserScript(link, "DMV_Written_form", found)
                            found += 1
                        
                        self.log_appointment(filtered_appointments)

                        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
                        confirmation = True
                        
                    else:
                        print('No appointments during your available months at '+ location)
                        dt_string=""
                    i=i+1

        if confirmation:
            time.sleep(SUCCESS_DELAY)
            confirmation = False
        elif reset:
            time.sleep(RESET_DELAY)
            reset = False

    def __call__(self):
        while True:
            try:
                self.job()
            except Exception as exception:
                print("Error encountered", exception)
                time.sleep(UPDATE_DELAY)
            else:
                time.sleep(UPDATE_DELAY)

if __name__ == "__main__":
    DMV_Scaper(appointment="KnowledgeTest.json", locations=["North Bergen", "Lodi", "Bayonne", "Paterson", "Wayne", "Newark"], required_months={"August": 14}, preferred_times=DEFAULT_TIMES)
