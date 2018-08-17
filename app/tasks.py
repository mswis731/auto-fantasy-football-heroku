from app import app, celery

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.by import By


def get_driver():
    GOOGLE_CHROME_BIN = app.config["GOOGLE_CHROME_BIN"]

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = GOOGLE_CHROME_BIN
    chrome_options.add_argument("headless")
    chrome_options.add_argument("window-size=1200x600")
    driver = webdriver.Chrome(chrome_options=chrome_options)
    driver.implicitly_wait(10)
    return driver

@celery.task
def verify_user_task(username, password):
    driver = get_driver()
    driver.get("http://www.espn.com/fantasy/football/")

    user_tab = driver.find_element_by_xpath("(//a)[@id='global-user-trigger']")
    user_tab.click()

    user_div = driver.find_element_by_xpath("//div[@class='global-user']")
    login = user_div.find_element_by_link_text("Log In")
    login.click()

    WebDriverWait(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,"//iframe[@name='disneyid-iframe']")))
    username_input = driver.find_element_by_xpath("(//input)[@ng-model='vm.username']")
    password_input = driver.find_element_by_xpath("(//input)[@ng-model='vm.password']")
    login_button = driver.find_element_by_xpath("(//button)[@ng-click='vm.submitLogin()']")
    username_input.send_keys(username)
    password_input.send_keys(password)

    login_button.click()
    driver.switch_to_default_content()

    try:
        fantasy_teams = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//li[@class='teams fantasy']/div/ul/li[@class='team']/a[@itemprop='url']")))
    except:
        fantasy_teams = None

    return 0 if fantasy_teams else 1
