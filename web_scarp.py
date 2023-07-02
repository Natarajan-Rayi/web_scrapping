from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, jsonify, request
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
from webdriver_manager import chrome, firefox

app = Flask(__name__)

# Initialize the Firebase Admin SDK
cred = credentials.Certificate('./cred/surfgeo-sale.json')
firebase_admin.initialize_app(cred)

# Create a Firestore client
db = firestore.client()


@app.route("/")
def api_check():
    return "running..."


@app.route("/web-scrap", methods=['POST'])
def web_scrap():
    try:
        scarping_date = request.form.get('scarping_date')
        # Define the collection reference
        collection_ref = db.collection('web_scarp')

        # Define the field and value to check against
        field_name = 'scarping_date'

        # Query documents where the field is equal to the specified value
        query = collection_ref.where(
            field_name, '==', scarping_date).limit(1).get()

        # Iterate over the query results
        if len(query) > 0:
            query = collection_ref.where(field_name, '==', scarping_date).get()

            # Iterate over the query results
            for doc in query:
                # Access the document data
                doc_data = doc.to_dict()
                return jsonify(doc_data)
        else:
            # URL to scrape

            # Configure Chrome options
            chrome_options = Options()
            # Run Chrome in headless mode, i.e., without opening a browser window
            chrome_options.add_argument("--headless")
            # is a line of code that sets a Chrome option to
            # run the browser in headless mode. This means that the browser will run without opening a
            # visible window, which can be useful for web scraping tasks where you don't need to interact
            # with the page visually.
            chrome_options.add_argument("--headless")
            # Set window size to simulate a full-sized browser
            chrome_options.add_argument("--window-size=1920,1200")

            # Path to the ChromeDriver executable
            # Replace with the actual path to the ChromeDriver executable
            # chromedriver_path = './chromedriver_win32/chromedriver.exe'

            # Initialize ChromeDriver
            driver = webdriver.Chrome(options=chrome_options,
                                      keep_alive=firefox.DownloadManager())
            url = 'https://www.mhc.tn.gov.in/judis/clists/clists-madras/index.php'

            # Navigate to the URL
            driver.get(url)

            # Perform web scraping actions
            # Here you can use various methods provided by Selenium to interact with the webpage, find elements, extract data, etc.
            # For example, you can use driver.find_element_by_xpath(), driver.find_element_by_css_selector(),
            # driver.find_elements_by_xpath(), driver.find_elements_by_css_selector() to locate elements on the page.

            # Extract data from the page
            # For example, you can extract the page source or specific elements:
            page_source = driver.page_source
            # title_element = driver.find_element('dailylist')
            time.sleep(2)
            # Find the radio button element by its ID
            radio_button = driver.find_element(
                By.CSS_SELECTOR, 'input#dailylist')

            # Scroll the radio button into view
            driver.execute_script(
                "arguments[0].scrollIntoView();", radio_button)

            # Click the radio button via JavaScript
            driver.execute_script("arguments[0].click();", radio_button)

            # Wait for the selection to take effect
            time.sleep(2)

            select_box = Select(driver.find_element(
                By.CSS_SELECTOR, 'select#ct_date'))

            # Select the desired option by value
            select_box.select_by_value(str(scarping_date))

            time.sleep(2)

            # Find the "NEXT" button element by its ID
            next_button = driver.find_element(By.ID, 'btn_dailylist')

            # Click the "NEXT" button
            next_button.click()

            time.sleep(2)

            # Find the select box element by its ID
            select_box = driver.find_element(By.ID, 'courtnolist')

            # Initialize the Select object with the select box element
            select = Select(select_box)

            # Print the available options
            options = select.options
            for option in options:
                print(option.get_attribute("value"))

            # Find the "Submit" button element by its class name and click it
            submit_button = driver.find_element(By.CLASS_NAME, 'btn-primary')
            submit_button.click()

            # Wait for the table element to be present

            # Switch to the new window
            driver.switch_to.window(driver.window_handles[1])

            # Wait for the table element to be present
            wait = WebDriverWait(driver, 40)
            table_element = wait.until(
                EC.presence_of_element_located((By.ID, 'example')))
            time.sleep(3)
            # Scroll to the end of the table to load all rows
            driver.execute_script(
                "arguments[0].scrollIntoView(false);", table_element)

            # Wait for the table to fully load
            time.sleep(2)

            # Find all row elements within the table
            row_elements = table_element.find_elements(By.TAG_NAME, 'tr')

            time.sleep(3)

            print(row_elements)
            # Extract the text from each row
            table_data = []
            data_scarp = []
            for row_element in row_elements:
                row_data = []
                cell_text_list = []
                for cell in row_element.find_elements(By.TAG_NAME, 'td'):
                    print(cell, 'cell_value')
                    cell_text_list.append(str(cell.text))
                    cell_text = cell.text
                    print(cell_text, 'cell_text')
                    # Split the cell text by newline character '\n' and store as separate elements
                    cell_values = cell_text.split('\n')
                    row_data.extend(cell_values)
                temp_group = []
                output_array = []
                for i, element in enumerate(cell_text_list):
                    temp_group.append(element)
                    # Check if we have collected five elements or reached the end of the input array
                    if len(temp_group) == 5:
                        output_array.append(temp_group)
                        temp_group = []
                for item in output_array:
                    try:
                        data_scarp.append({'data': [{'sno': item[0]},
                                                    {'case_type': item[1].split()[0],
                                                     'number':item[1].split()[1].split('/')[0], 'year':item[1].split('/')[1]},
                                                    {'party': item[2]}, {
                            'petitioner': item[3]},
                            {'respondent': item[4]}]})
                    except:
                        data_scarp.append({'data': [{'sno': ''}, {'caseno': ''},
                                                    {'party': ''}, {
                            'petitioner': ''},
                            {'respondent': ''}]})
                print(cell_text_list, 'cell text value')
                table_data.append(row_data)
            current_timestamp = datetime.now()
            #
            # Create a DataFrame with the table data
            df = pd.DataFrame(table_data)

            # Save the DataFrame to an Excel file
            df.to_excel('table_data.xlsx', index=False)
            time.sleep(3)

            # Close the new window and switch back to the main window
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            doc_ref = db.collection('web_scarp').document()
            doc_ref.set({"data": data_scarp, "time_stamp": current_timestamp,
                        "scarping_date": scarping_date})
            # Print the extracted data
            print("Page Source:")
            print(page_source)

            print("Title:")
            # print(title_element.text)

            time.sleep(3)
            # Close the browser
            driver.quit()
        return jsonify({"message": "scarpping completed"})
    except:
        return jsonify({'status': 500, "msg": 'internal server issue'})


if __name__ == '__main__':
    app.run(debug=False)
