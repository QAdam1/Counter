import time
import smtplib
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from email.mime.text import MIMEText

# Email Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "adamuran10@gmail.com"  # Replace with your email
EMAIL_PASSWORD = "dszmooobohzdfnsv"  # Replace with your app-specific password
TO_EMAIL = "adirov9@gmail.com"

# URL and message to check
URL = "https://www.eventer.co.il/artists/%D7%A2%D7%95%D7%A4%D7%A8_%D7%A0%D7%99%D7%A1%D7%99%D7%9D"
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
        print(f"Email sent to {TO_EMAIL}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to monitor the webpage
def monitor_page():
    # Set up headless Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Monitor for 48 hours
    end_time = datetime.now() + timedelta(hours=48)
    try:
        driver.get(URL)
        try:
            # Wait for the page to load and check for the message
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{MESSAGE}')]"))
            )
            print(f"{datetime.now()}: Message found. Checking again in 1 minute.")
        except:
            print(f"{datetime.now()}: Message not found! Sending email notification.")
            send_email()
        time.sleep(60)  # Wait 1 minute before checking again
    finally:
        driver.quit()

if __name__ == "__main__":
    monitor_page()