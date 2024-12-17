import logging
import os
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Tuple

import dotenv
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.devtools.v131.dom import scroll_into_view_if_needed
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.expected_conditions import presence_of_all_elements_located
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

#  Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

dotenv.load_dotenv()

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

logging.info(f'***********using secrets************\n' +
             f'email: {EMAIL_ADDRESS}, \n' +
             f'password: {EMAIL_PASSWORD}, \n' +
             f'toMail: {TO_EMAIL}')

# URL and message to check
URL = "https://www.eventer.co.il/artists/%D7%A2%D7%95%D7%A4%D7%A8_%D7%A0%D7%99%D7%A1%D7%99%D7%9D"
# URL = "https://www.eventer.co.il/artists/jimbo_j" #DEMO
MESSAGE = "ברגע זה אין אירועים של עופר ניסים"  # Text indicating no events

# Function to send an email notification
def send_email():
    try:
        subject = "החלה המכירה"
        body = f"The sale has started! Check it here: {URL}"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = TO_EMAIL

        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, TO_EMAIL, msg.as_string())
        logging.info(f"Email sent to {TO_EMAIL}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


def buyTickets(driver: WebDriver, wait: WebDriverWait):
    # screen 1 - artist events
    by_btn_event: Tuple[str, str] = (By.CSS_SELECTOR, '#eventContainerEvents > a:nth-child(1)')

    wait.until(presence_of_all_elements_located((By.CSS_SELECTOR, "#eventContainerEvents > a:nth-child(1)")))
    element = driver.find_elements(By.CSS_SELECTOR, "#eventContainerEvents > a:nth-child(1)")[0]
    link = element.get_attribute('href')
    print(link)
    driver.get(link)

    # screen 2 - choose tickets
    # by_event_type_row = (By.XPATH, '(//*[contains(@rnd-id,"purchase_ticket")])[1]')
    # by_select_amount = (By.XPATH, './/*[@id="tickets_amount0"]')
    by_select_amount = (By.XPATH, '(//*[contains(@class, "mobilePlusMinusBtn")])[1]')
    by_txt_total_price = (By.CSS_SELECTOR, '[aria-labelledby="TOTAL_PRICE"]')
    by_btn_go_to_checkout = (By.CSS_SELECTOR, '[rnd-id="lp_finish_tickets"]')

    # event_type_row = wait.until(EC.visibility_of_element_located(by_event_type_row))
    # select_amount: Select = Select(event_type_row.find_element(by_select_amount[0], by_select_amount[1]))
    # select_amount.select_by_value('2')
    btn_plus_tickets = wait.until(EC.visibility_of_element_located((by_select_amount[0], by_select_amount[1])))

    scroll_into_view_if_needed(btn_plus_tickets.location_once_scrolled_into_view)

    for i in range(2):
        btn_plus_tickets.click()

    # price = wait.until(EC.visibility_of_element_located(by_txt_total_price)).text
    wait.until(EC.element_to_be_clickable(by_btn_go_to_checkout)).click()

    # screen 3 - order details
    by_input_full_name = (By.NAME, 'name')
    by_input_id_number = (By.NAME, 'sid')
    by_input_phone = (By.NAME, 'phone')
    by_input_email = (By.NAME, 'email')
    by_input_age = (By.NAME, 'age')
    by_btn_danger = (By.CSS_SELECTOR, '[class*="btn-danger"]')
    by_cbox_read_the_rules = (By.CSS_SELECTOR, '#purchase_terms_toggle > button > div > div.md-container > div')
    by_cbox_above_18 = (By.XPATH, '//*[contains(text(), "גיל 18")]/../../..')
    by_btn_go_to_payment = (By.CSS_SELECTOR, '[rnd-id="navigate_to_transaction"]')

    wait.until(EC.visibility_of_element_located(by_input_full_name)).send_keys(os.getenv('FULL_NAME'))
    wait.until(EC.visibility_of_element_located(by_input_id_number)).send_keys(os.getenv('ID_NUMBER'))
    wait.until(EC.visibility_of_element_located(by_input_phone)).send_keys(os.getenv('PHONE'))
    wait.until(EC.visibility_of_element_located(by_input_email)).send_keys(TO_EMAIL)
    wait.until(EC.visibility_of_element_located(by_input_age)).send_keys(os.getenv('AGE'))

    cbox = wait.until(EC.element_to_be_clickable(by_cbox_read_the_rules))
    scroll_into_view_if_needed(cbox.location_once_scrolled_into_view)
    cbox.click()

    ActionChains(driver=driver).click(
        driver.find_element(by_cbox_read_the_rules[0], by_cbox_read_the_rules[1])).perform()

    try:
        wait.until(EC.element_to_be_clickable(by_cbox_above_18)).click()
    except:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="btn-danger"]'))).click()
        ActionChains(driver=driver).click(driver.find_element(by_cbox_read_the_rules[0], by_cbox_read_the_rules[1])).perform()
        wait.until(EC.element_to_be_clickable(by_cbox_above_18)).click()
    wait.until(EC.element_to_be_clickable(by_btn_go_to_payment)).click()

    # screen 4 - payment details
    by_iframe = (By.ID, 'pp_iframe')
    by_input_card_number = (By.ID, 'credit-card-input')
    by_select_expiration_year = (By.ID, 'expiration-date-year')
    by_select_expiration_month = (By.ID, 'expiration-date-month')
    by_input_cvv = (By.ID, 'cvv-input')
    by_card_holder_id_number = (By.ID, 'holder-identifier')
    by_btn_pay = (By.ID, 'checkout-button')

    iframe = wait.until(EC.presence_of_element_located(by_iframe))
    driver.switch_to.frame(iframe)

    wait.until(EC.visibility_of_element_located(by_input_card_number)).send_keys(os.getenv('CARD_NUMBER'))
    Select(driver.find_element(by_select_expiration_year[0], by_select_expiration_year[1])).select_by_value(
        os.getenv('CARD_YEAR'))
    Select(driver.find_element(by_select_expiration_month[0], by_select_expiration_month[1])).select_by_value(
        os.getenv('CARD_MONTH'))
    wait.until(EC.visibility_of_element_located(by_input_cvv)).send_keys(os.getenv('CARD_CVV'))
    wait.until(EC.visibility_of_element_located(by_card_holder_id_number)).send_keys(os.getenv('ID_NUMBER'))
    wait.until(EC.element_to_be_clickable(by_btn_pay)).click()


# Function to monitor the webpage
def monitor_page():
    # Set up headless Chrome
    mobile_emulation = {
        "deviceMetrics": {"width": 400, "height": 472, "pixelRatio": 3.0},
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile Safari/535.19"}
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    driver: WebDriver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait: WebDriverWait = WebDriverWait(driver=driver, timeout=10)

    # Monitor for 6 hours
    end_time = datetime.now() + timedelta(hours=6)
    try:
        while datetime.now() < end_time:
            logging.info("Checking the webpage for updates...")
            driver.get(URL)
            try:
                # Wait for the page to load and check for the message
                wait.until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{MESSAGE}')]"))
                )
                logging.info(f"{datetime.now()}: Message found. Checking again in 30 sec.")
            except:
                logging.info(f"{datetime.now()}: Message not found! Sending email notification.")
                send_email()
                buyTickets(driver, wait)
                break
            time.sleep(30)  # Wait 30 sec before checking again
    finally:
        driver.quit()
        logging.info("Monitoring session ended.")


if __name__ == "__main__":
    monitor_page()
