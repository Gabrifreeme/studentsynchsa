import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import datetime
import time
import random
import os

# =============================================================================
# PROFILE DATA
# =============================================================================
profile_data_json = """
{
  "personal": {
    "title": "MR",
    "firstName": "John",
    "lastName": "Doe",
    "initials": "JD",
    "gender": "M",
    "idNumber": "9012315000087",
    "dateOfBirth": "1990-12-31T00:00:00Z"
  },
  "contact": {
    "email": "john.doe@example.com",
    "phone": "0831234567",
    "workPhone": "0111234567"
  },
  "address": {
    "addressLine1": "123 Main St",
    "addressLine2": "Suburbia",
    "addressLine3": "Cape Town",
    "addressLine4": "Western Cape",
    "postalCode": "0001"
  },
  "demographic": {
    "nationality": "South African",
    "homeLanguage": "E",
    "populationGroup": "4",
    "maritalStatus": "S"
  },
  "qualification": {
    "academicYear": "2024",
    "studyMode": "Full-Time"
  },
  "nextOfKin": {
    "name": "Jane Doe",
    "mobilePhone": "0827654321",
    "email": "jane.doe@example.com"
  }
}
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_date_ddmmyyyy(iso_date_str):
    if not iso_date_str: return ''
    try:
        date_only = iso_date_str.split('T')[0]
        dt_obj = datetime.datetime.strptime(date_only, '%Y-%m-%d')
        return dt_obj.strftime('%d/%m/%Y')
    except ValueError:
        return iso_date_str

def fill_form_field(driver, field_name_attr, value, timeout=10):
    if value is None: return
    try:
        time.sleep(random.uniform(0.1, 0.4))
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f"[name*='{field_name_attr}'], [id*='{field_name_attr}']"))
        )
        if element.tag_name == 'select':
            select = Select(element)
            try:
                select.select_by_value(str(value))
                print(f"Filled dropdown '{field_name_attr}' by value: {value}")
            except Exception:
                try:
                    select.select_by_visible_text(str(value))
                    print(f"Filled dropdown '{field_name_attr}' by visible text: {value}")
                except Exception as e:
                    print(f"Could not fill dropdown '{field_name_attr}': {e}")
        elif element.get_attribute('type') == 'checkbox':
            is_selected = element.is_selected()
            should_be_checked = str(value).upper() == 'Y' or value is True
            if is_selected != should_be_checked:
                element.click()
                print(f"Toggled checkbox '{field_name_attr}'")
        elif element.get_attribute('type') == 'radio':
            group_name = element.get_attribute('name')
            radios = driver.find_elements(By.CSS_SELECTOR, f"input[type='radio'][name='{group_name}']")
            for radio in radios:
                if radio.get_attribute('value').lower() == str(value).lower():
                    radio.click()
                    print(f"Selected radio '{field_name_attr}'")
                    break
        else:
            element.clear()
            element.send_keys(str(value))
            print(f"Filled input '{field_name_attr}' with: {value}")
    except Exception as e:
        print(f"Error filling '{field_name_attr}': {e}")

TARGET_FORM_URL = "https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view"
