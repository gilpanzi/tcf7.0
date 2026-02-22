from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--window-size=1920,1080')
driver = webdriver.Chrome(options=options)

driver.get('http://localhost:5000/orders')
time.sleep(3) # Wait for charts to load

# Try clicking the first SE
se_row = driver.find_elements(By.XPATH, "//strong[text()='SAB']")
if se_row:
    # Need to click the parent div that actually has the onClick handler
    clickable = se_row[0].find_element(By.XPATH, "../../..")
    
    # Use javascript click to bypass any weird overlays
    driver.execute_script("arguments[0].click();", clickable)
    
    time.sleep(1) # wait for modal animation
    
    driver.save_screenshot(r"C:\Users\farze\.gemini\antigravity\brain\89001a77-5b9c-4ad4-b47a-9e4c54882ae3\se_drilldown_with_customer_1771610999.png")
    print("Success")
else:
    print("Could not find SE SAB")

driver.quit()
