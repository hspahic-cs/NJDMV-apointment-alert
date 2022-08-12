import json
import webbrowser
from bs4 import BeautifulSoup
import urllib.request

from os.path import exists
from pathlib import Path

def getFields(url):
    try:
        urllib.request.urlopen(url)
    except Exception as exception:
        print(f"{url} was already closed")

    with urllib.request.urlopen(url) as form:
        page_html = form.read()
        soup = BeautifulSoup(page_html, "html.parser")

        text_fields = soup.find_all('input', attrs={'type':'text'})
        text_values = {}

        for field in text_fields:
            print(f"For {field['id']} ~ {field['data-val-required']}")
            text_values[field['id']] = field['value']

        with open('fields/text-fields.json', 'w') as f:
            json.dump(text_values, f)
            f.close()

        select_fields = soup.find_all('select')
        select_values = {}

        for i, field in enumerate(select_fields):
            select_id = field['id']
            select_fields[i] = field.select('option[value]')
            select_values[select_id] = {}
            for option in select_fields[i]:
                if(option.has_attr('disabled')):
                    print(option['value'])
                else:
                    select_values[select_id][option['value']] = False

        with open('fields/select-fields.json', 'w') as f:
            json.dump(select_values, f)
            f.close()

        print(select_values)

        #radio_fields = soup.find_all('input', attrs={'type':'radio'})
        checked_fields = soup.find_all('input', attrs={'type':'checkbox'})
        checked_values = {}

        for field in checked_fields:
            if(field.has_attr('data-val-required')):
                print(f"For {field['id']} ~ {field['data-val-required']}")
            checked_values[field['name']] = field['value']

        with open('fields/check-fields.json', 'w') as f:
            json.dump(checked_values, f)
            f.close()

def createBrowserScript(url, title, notepad_open, name):
    
    copied_name = []

    if(not exists(f"{title}.txt")):
        Path(f'{title}.txt').touch()
        
        script = [] 

        with open("fields/text-fields.json", "r") as f:
            text_fields = json.load(f)
            for key in text_fields:
                script.append(f"document.getElementById('{key}').value = '{text_fields[key]}'")
                if key == "firstName" or key == "lastName":
                    copied_name.append(text_fields[key])
                
            f.close()

        with open("fields/select-fields.json", "r") as f:
            select_fields = json.load(f)
            found = False
            for selection in select_fields.keys():
                for i, key in enumerate(select_fields[selection]):
                    if (select_fields[selection][key] and not found):
                        script.append(f"document.getElementById('{selection}').selectedIndex = {i + 1}")
                        found = True
                        break
                if(not found):
                    script.append(f"document.getElementById('{selection}').selectedIndex = {0}")
                found = False
            f.close()


        with open("fields/check-fields.json", "r") as f:
            check_fields = json.load(f)
            for key in check_fields:
                script.append(f"document.getElementsByName('{key}')[0].checked = {check_fields[key]}")
            f.close()

        with open(f"{title}.txt", "w+") as script_file:
            for cmd in script:
                cmd += "\n"
                script_file.write(cmd)
            lines = script_file.readlines()
            for line in lines:
                print(line)
        script_file.close()

    # If form already exist & name doesnt, get name
    elif(not name):
        with open("fields/text-fields.json", "r") as f:
            text_fields = json.load(f)
            for key in text_fields:
                if key == "firstName" or key == "lastName":
                    copied_name.append(text_fields[key])
                
            f.close()

    if(not notepad_open):
        webbrowser.open(f"{title}.txt")
    webbrowser.open(url, new=2)

    return copied_name

if __name__ == "__main__":
    #getFields("https://telegov.njportal.com/njmvc/AppointmentWizard/19/267/2022-09-13/1115")
    createBrowserScript("https://telegov.njportal.com/njmvc/AppointmentWizard/15/186/2022-10-04/1345", "DMV_Written_form", True, "Default")