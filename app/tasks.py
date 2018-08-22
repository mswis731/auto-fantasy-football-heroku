from app import app, db, celery
from models import User, Team

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

def login_user(username, password):
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
        web_teams = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//li[@class='teams fantasy']/div/ul/li[@class='team']/a[@itemprop='url']")))
    except:
        web_teams = None

    return driver if web_teams else None

@celery.task
def verify_user_task(username, password):
    driver = login_user(username, password)
    return 0 if driver else 1 # 0: login successful, 1: login failed

@celery.task
def update_teams_task(user_id):
    user = User.query.get(user_id)
    if not user:
        return -1 # user does not exist

    username = user.username
    password = User.decrypt_password(user.password)
    driver = login_user(username, password)
    web_teams = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//li[@class='teams fantasy']/div/ul/li[@class='team']/a[@itemprop='url']")))

    old_teams = { team.external_id: team.name for team in user.teams }
    new_teams = {}
    for team in web_teams:
        name = team.find_element_by_xpath(".//span[@class='link-text']").get_attribute('innerHTML')
        url = team.get_attribute("href")
        external_id = Team.parse_url(url)
        new_teams[external_id] = name
    old_team_set = set(old_teams.keys())
    new_team_set = set(new_teams.keys())

    teams_to_remove = old_team_set - new_team_set
    teams_to_update = filter(lambda key: old_teams[key] != new_teams[key], old_team_set & new_team_set)
    teams_to_create = new_team_set - old_team_set

    for external_id in teams_to_remove:
        team = Team.query.filter_by(external_id=external_id).first()
        if team:
            db.session.delete(team)
    for external_id in teams_to_update:
        name = new_teams[external_id]
        team = Team.query.filter_by(external_id=external_id).first()
        if team:
            team.name = name
    for external_id in teams_to_create:
        name = new_teams[external_id]
        team = Team(name=name, external_id=external_id, user_id=user_id)
        db.session.add(team)

    db.session.commit()

    return 0
