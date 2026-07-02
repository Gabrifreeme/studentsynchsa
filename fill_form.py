import json
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# --- Profile Data ---
profile_data_json = """
{
  "personal": {
    "firstName": "John",
    "lastName": "Doe",
    "initials": "JD",
    "title": "Mr",
    "gender": "Male",
    "idNumber": "9012315000087",
    "dateOfBirth": "1990-12-31T00:00:00Z"
  },
  "contact": {
    "email": "john.doe@example.com",
    "phone": "0831234567",
    "workPhone": "0111234567"
  },
  "address": {
    "address": "123 Main St",
    "addressLine2": "Suburbia",
    "province": "Gauteng",
    "postalCode": "0001"
  },
  "demographic": {
    "nationality": "South African",
    "homeLanguage": "English",
    "populationGroup": "Black",
    "maritalStatus": "Single"
  },
  "school": {
    "schoolName": "Example High School",
    "currentGrade": "12"
  },
  "results": {
    "matricYear": "2008",
    "matricType": "NSC",
    "examinationNumber": "123456789",
    "applicationLevel": "Undergraduate"
  },
  "qualification": {
    "choices": [
      {"faculty": "Engineering", "programme": "Computer Science"}
    ],
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

# --- Value Mappings ---
MAPPINGS = {
    "gender": {"Male": "M", "Female": "F"},
    "maritalStatus": {"Single": "S", "Married": "M", "Divorced": "D", "Widow/er": "W"},
    "homeLanguage": {"English": "E", "Afrikaans": "A", "Zulu": "L", "Xhosa": "K"},
    "populationGroup": {"Black": "4", "Coloured": "2", "Indian": "3", "White": "1"},
    "title": {"Mr": "MR", "Mrs": "MRS", "Ms": "MS"}
}

def format_date_ddmmyyyy(iso_date_str):
    if not iso_date_str: return ''
    try:
        date_only = iso_date_str.split('T')[0]
        dt_obj = datetime.datetime.strptime(date_only, '%Y-%m-%d')
        return dt_obj.strftime('%d/%m/%Y')
    except ValueError:
        return iso_date_str

def fill_form_field(driver, field_id, value, is_checkbox=False):
    if value is None: return
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, field_id))
        )
        if is_checkbox:
            if str(value).lower() in ['true', 'y', 'yes']:
                if not element.is_selected():
                    element.click()
                print(f"Checked checkbox '{field_id}'")
            return
        if element.tag_name == 'select':
            select = Select(element)
            try:
                select.select_by_value(str(value))
                print(f"Filled dropdown '{field_id}' with value: {value}")
            except Exception:
                try:
                    select.select_by_visible_text(str(value))
                    print(f"Filled dropdown '{field_id}' with text: {value}")
                except Exception as e:
                    print(f"Could not select '{value}' for dropdown '{field_id}': {e}")
        else:
            element.clear()
            element.send_keys(str(value))
            print(f"Filled input '{field_id}' with: {value}")
    except Exception as e:
        print(f"An error occurred filling '{field_id}': {e}")

def main():
    # IMPORTANT: Replace this with the actual URL of the form!
    target_form_url = "REPLACE_WITH_YOUR_ACTUAL_URL" 
    
    print("Starting browser...")
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # Uncomment to run without a visible window
    driver = uc.Chrome(options=options)

    try:
        driver.get(target_form_url)
        print(f"Navigated to: {target_form_url}")
        
        profile_data = json.loads(profile_data_json)

        # 1. Personal Info
        fill_form_field(driver, 'oapTitle', MAPPINGS['title'].get(profile_data['personal']['title'], profile_data['personal']['title']))
        fill_form_field(driver, 'oapInitials', profile_data['personal']['initials'])
        fill_form_field(driver, 'oapSurname', profile_data['personal']['lastName'])
        fill_form_field(driver, 'oapFirstNames', profile_data['personal']['firstName'])
        fill_form_field(driver, 'oapGender', MAPPINGS['gender'].get(profile_data['personal']['gender'], ''))
        fill_form_field(driver, 'oapBirthdate', format_date_ddmmyyyy(profile_data['personal']['dateOfBirth']))
        fill_form_field(driver, 'oapIDnumber', profile_data['personal']['idNumber'])
        fill_form_field(driver, 'oapAcceptUnderAge', 'Y', is_checkbox=True)

        # 2. Demographics
        citizen_val = 'Y' if profile_data['demographic']['nationality'] == 'South African' else 'N'
        fill_form_field(driver, 'oapCitizenType', citizen_val)
        fill_form_field(driver, 'oapMaritalStatus', MAPPINGS['maritalStatus'].get(profile_data['demographic']['maritalStatus'], ''))
        fill_form_field(driver, 'oapHomeLang', MAPPINGS['homeLanguage'].get(profile_data['demographic']['homeLanguage'], ''))
        fill_form_field(driver, 'oapEthnic', MAPPINGS['populationGroup'].get(profile_data['demographic']['populationGroup'], ''))

        # 3. Contact Info
        fill_form_field(driver, 'itsEmail', profile_data['contact']['email'])
        fill_form_field(driver, 'verifyEmail', profile_data['contact']['email'])
        fill_form_field(driver, 'oapCellInd', 'Y')
        fill_form_field(driver, 'oapSACell', profile_data['contact']['phone'])
        fill_form_field(driver, 'oapWorkPhone', profile_data['contact']['workPhone'])

        # 4. Address
        fill_form_field(driver, 'oapStreetAddr1', profile_data['address']['address'])
        fill_form_field(driver, 'oapStreetAddr2', profile_data['address']['addressLine2'])
        fill_form_field(driver, 'oapStreetAddrPCodeRq_desc', profile_data['address']['postalCode'])
        fill_form_field(driver, 'oapstudChkPostal', 'N', is_checkbox=True)

        # 5. Miscellaneous
        fill_form_field(driver, 'oapResReq', 'N')
        fill_form_field(driver, 'oapApplyDisability', 'N', is_checkbox=True)

        print("Form filling completed. Please check the browser.")
        driver.save_screenshot('form_result.png')

    except Exception as e:
        print(f"Critical error: {e}")
    finally:
        # input("Press Enter to close the browser...") # Keeps browser open so you can see the result
        # driver.quit()
        pass

if __name__ == "__main__":
    main()

