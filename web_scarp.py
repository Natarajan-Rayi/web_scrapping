from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask import Flask, jsonify, request, redirect, url_for, session
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
from webdriver_manager import chrome

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
        desired_court_number = request.form.get('court_no')

        # Define the collection reference
        collection_ref = db.collection('web_scarp')

        # Define the field and value to check against
        field_name = 'details.scarping_date'

        # Query documents where the field is equal to the specified value
        query = collection_ref.where(
            field_name, '==', scarping_date).where(
            "details.court_no", '==', desired_court_number).limit(1).get()

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
            chromedriver_path = './chromedriver_win32/chromedriver.exe'

            # Initialize ChromeDriver
            driver = webdriver.Chrome(options=chrome_options,
                                      keep_alive=chrome.ChromeDriverManager().install())
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

            select.select_by_value(desired_court_number)
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
            court_name = driver.find_element(
                By.CSS_SELECTOR, 'h2[style="text-align: center; color:#555; margin-bottom:0;"]')

            # Get the text content of the <h2> tag
            court_text = court_name.text
            time.sleep(2)
            # Find all <h2> elements on the page
            h2_element = driver.find_element(
                By.CSS_SELECTOR, 'h2[style="text-align: center; color:#555; margin-top:0;"]')

            # Extract the text of the <h2> element
            cause_list_text = h2_element.text.split('-')[1]

            # Find the element with the class "head_judge"
            head_judge_element = driver.find_element(
                By.CLASS_NAME, 'head_judge')

            # Get the inner HTML of the element
            head_judge_html = head_judge_element.get_attribute('innerHTML')

            # Split the HTML content by "<br>" tags
            br_splits = head_judge_html.split('<br>')

            # Check if there are at least two "<br>" tags
            if len(br_splits) >= 3:
                # Get the text after the second "<br>" tag
                second_break_text = br_splits[2].strip()
                print(second_break_text)
            else:
                print("Insufficient <br> tags found in the head_judge element.")
            time.sleep(2)
            # Find all row elements within the table
            tbody_element = table_element.find_element(By.ID, 'tbl')

            # row_elements = table_element.find_elements(By.TAG_NAME, 'tr')
            # Find all row elements within the <tbody> element
            row_elements = tbody_element.find_elements(By.TAG_NAME, 'tr')

            time.sleep(3)

            print(row_elements)
            # Extract the text from each row
            table_data = []
            data_scarp = []
            stagename_text = ''
            for row_element in row_elements:
                row_data = []
                cell_text_list = []
                # stagename_element = row_element.find_element(
                #     By.CLASS_NAME, 'stagename_heading')
                # Get the text content of the element
                for cell in row_element.find_elements(By.TAG_NAME, 'td'):
                    print(cell, 'cell_value')
                    cell_text_list.append(str(cell.text))
                    cell_text = cell.text
                    print(cell_text, 'cell_text')
                    # Split the cell text by newline character '\n' and store as separate elements
                    cell_values = cell_text.split('\n')
                    row_data.extend(cell_values)
                if row_element.get_attribute('class') == 'stagename':
                    stagename_element = row_element.find_element(
                        By.CLASS_NAME, 'stagename_heading')
                    stagename_text = stagename_element.text.strip()
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
                        data_scarp.append({'sno': item[0],
                                           'case_type': item[1].split()[0],
                                           'number': item[1].split()[1].split('/')[0], 'year': item[1].split('/')[1],
                                           'caseid': "".join(item[1].split()),
                                           'petitioner': item[2].split("VS", 1)[0],
                                           'respondent': item[2].split("VS", 1)[1],
                                           'petitioner_advocates': item[3],
                                           'respondent_advocates': item[4],
                                           'case_category': stagename_text,
                                           'important': '',
                                           })
                    except:
                        data_scarp.append({'sno': '', 'caseno': '',
                                           'party': '',
                                           'caseid': '',
                                           'petitioner': '',
                                           'respondent': ''})
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
            doc_ref.set({"daily_cases": data_scarp, "details": {"time_stamp": current_timestamp,
                        "scarping_date": scarping_date, 'court_no': desired_court_number, "judge_name": second_break_text, "court_name": court_text,
                                                                "date": cause_list_text.strip(), "link": ""}})
            document_id = doc_ref.id
            # Splitting the name by space
            name_parts = second_break_text.split()

            # Extracting the desired part
            desired_part = ' '.join(name_parts[-1:])
            time.sleep(3)
            # Close the browser
            driver.quit()

            data = {'doc_id': document_id, 'judge_name': desired_part}
            print("Data complete", document_id)
            # Redirect to the second API endpoint with the data
            return redirect(url_for('scraplink', **data))
    except:
        return jsonify({'status': 500, "msg": 'internal server issue'})


@app.route("/scraplink", methods=['GET'])
def scraplink():
    try:
        # Use eval to convert string to dictionary
        # Store the data in session
        data = request.args
        print(data, 'document id')
        document_id = data.get('doc_id')
        judge_name_get = data.get('judge_name')
        print(data, document_id, 'document id')
        # document_id = data[]
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
        chromedriver_path = './chromedriver_win32/chromedriver.exe'

        # Initialize ChromeDriver
        driver = webdriver.Chrome(options=chrome_options,
                                  keep_alive=chrome.ChromeDriverManager().install())

        # Open the webpage
        driver.get("https://mhc.tn.gov.in/vclink/vclink.php")

        # Wait for the page to load
        time.sleep(3)

        # Fill the form fields
        select_bench = Select(driver.find_element(By.ID, "bench"))
        # Select "High Court Madras" from the dropdown
        select_bench.select_by_value("1")

        time.sleep(1)

        select_date = Select(driver.find_element(By.ID, "cdate"))
        # Select the second option from the dropdown (index 1)
        select_date.select_by_index(1)

        # Click the "Search" button
        search_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Search')]")
        search_button.click()

        # Wait for the search results to load
        time.sleep(3)

        # Perform further actions with the search results, such as scraping data or interacting with the elements
        # Find the table rows containing the judge names and links
        table_rows = driver.find_elements(
            By.XPATH, "//table[@border='1']/tbody/tr[not(th)]")

        # Iterate over the table rows and extract the link for a specific judge name
        desired_judge_name = judge_name_get
        desired_link = None

        for row in table_rows:
            judge_name = row.find_element(By.XPATH, "./td[2]").text
            link_element = row.find_element(By.XPATH, "./td[3]/a")

            if desired_judge_name in judge_name:
                desired_link = link_element.get_attribute("href")
                update_data = {"details.link": desired_link}

                # Update the document
                doc_ref = db.collection(
                    "web_scarp").document(document_id)
                doc_ref.update(update_data)
                break

        # Print the link for the desired judge name
        if desired_link:
            print("Link for", desired_judge_name, ":", desired_link)
        else:
            print("No link found for", desired_judge_name)

        # Close the browser window
        driver.quit()

        return jsonify({"message": "scarpping completed"})
    except:
        return jsonify({'status': 500, "msg": 'internal server issue'})


@app.route('/scraping-results', methods=['GET'])
def query_results():
    # Initialize Firestore client
    scarping_date = request.form.get('scarping_date')
    desired_court_number = request.form.get('court_no')

    # Specify the collection to query
    collection_ref = db.collection('web_scarp')

    # Define the conditions
    condition1 = ('details.scarping_date', '==', scarping_date)
    condition2 = ('details.court_no', '==', desired_court_number)

    # Build the query
    query = collection_ref.where(*condition1).where(*condition2)

    # Execute the query and get the results
    results = query.get()

    # Convert the results to a list of dictionaries
    data = []
    for doc in results:
        data.append({
            'id': doc.id,
            'data': doc.to_dict()
        })

    # Return the results as JSON response
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=False)
