from app import app, db, celery
from models import User, Team, Transaction

import time, traceback
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains


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


@celery.task
def transactions_task(team_id):
    print("Team %i: Starting transactions task" % team_id)

    team = Team.query.get(team_id)
    if not team:
        return 1 # team does not exist
    user = User.query.get(team.user_id)
    if not user:
        return 2 # user does not exist

    username = user.username
    password = User.decrypt_password(user.password)
    driver = login_user(username, password)
    if not driver:
        return 3 # user login failed

    print("Team %i: Login successful" % team_id)

    web_teams = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//li[@class='teams fantasy']/div/ul/li[@class='team']/a[@itemprop='url']")))
    found_team = False
    team_url = None
    for web_team in web_teams:
        name = web_team.find_element_by_xpath(".//span[@class='link-text']").get_attribute('innerHTML')
        if name == team.name:
            team_url = web_team.get_attribute("href")
            found_team = True
            break
    if not found_team:
        return 4 # team was not found

    fantasy_tab = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//li[@class='pillar logo fantasy fantasy']/a")))
    ActionChains(driver).move_to_element(fantasy_tab).perform()

    print("Team %i: Fantasy team found and team page accessible" % team_id)

    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//li[@class='teams fantasy']/div/ul/li[@class='team']/a[@href='{}']".format(team_url)))).click()
    FANTASY_TEAM_HOMEPAGE = driver.current_url

    transactions = Transaction.query.filter_by(team_id=team.id, status=Transaction.Status.PENDING)

    print("Team %i: Running through %i transaction(s)" % (team_id, transactions.count()))

    for transaction in transactions:
        if driver.current_url != FANTASY_TEAM_HOMEPAGE:
            driver.get(FANTASY_TEAM_HOMEPAGE)

        drop_player = transaction.drop_player
        add_player = transaction.add_player

        print("Team %i, Transaction %i: Starting <%s, %s>" % (team_id, transaction.id, drop_player, add_player))

        drop_available = False
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.LINK_TEXT, drop_player)))
            drop_available = True
        except:
            print("Team %i, Transaction %i: %s (DROP) not found" % (team_id, transaction.id, drop_player))
            traceback.print_exc()

        if not drop_available:
            transaction.status = Transaction.Status.FAILED
            db.session.commit()

            continue

        # Click Add Player -> All
        add_players_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//ul[@id='games-subnav-links']/li[@class=' games-subnav-drop-btn']/a")))
        ActionChains(driver).move_to_element(add_players_element).perform()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.LINK_TEXT, "All"))).click()
        # Type in add player into search bar
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@id='lastNameInput'][@type='text']"))).send_keys(add_player)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@class='lastNameFilterButton'][@type='button']"))).click()

        driver.refresh()
        add_available = False
        try:
            player_table = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//table[@id='playertable_0']")))
            player_name_link = WebDriverWait(player_table, 5).until(EC.presence_of_element_located((By.LINK_TEXT, add_player)))
            player_row = player_name_link.find_element_by_xpath("../..")
            add_available = True
        except:
            print("Team %i, Transaction %i: %s (ADD) not found" % (team_id, transaction.id, add_player))
            traceback.print_exc()

        if not add_available:
            transaction.status = Transaction.Status.FAILED
            db.session.commit()

            continue

        WAIT_TIME = 60
        MAX_TRIES = 100
        transaction_button = None
        step = 0
        claim_not_present = False
        while True:
            step += 1
            if step > MAX_TRIES:
                break

            transaction_button = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "transactionButton")))[0]
            transaction_type = transaction_button.get_attribute("title")

            if transaction_type == "Claim":
                print("Team %i, Transaction %i: Still on claim. Retrying...%i" % (team_id, transaction.id, step))
                time.sleep(WAIT_TIME)
                continue
            claim_not_present = True
            break

        if not claim_not_present:
            print("Team %i, Transaction %i: Waiver claims still present after max tries" % (team_id, transaction.id))
            transaction.status = Transaction.Status.ERRORED
            db.session.commit()

            continue


        transaction_button.click()

        transaction_successful = False
        try:
            drop_player_elem = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, drop_player)))
            checkbox = drop_player_elem.find_element_by_xpath("../..//td[@class='playertableCheckbox']")
            driver.execute_script("return arguments[0].scrollIntoView();", checkbox)
            checkbox.click()
            submit_roster_btn = driver.find_element_by_xpath("//input[@value='Submit Roster']")
            driver.execute_script("return arguments[0].scrollIntoView();", submit_roster_btn)
            submit_roster_btn.click()
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@value='Confirm']"))).click()
            transaction_successful = True
        except:
            print("Team %i, Transaction %i: Confirm transaction failed" % (team_id, transaction.id))
            traceback.print_exc()

        if not transaction_successful:
            transaction.status = Transaction.Status.ERRORED
            db.session.commit()

            continue

        transaction.status = Transaction.Status.COMPLETE
        db.session.commit()

        print("Team %i, Transaction %i: Transaction successful" % (team_id, transaction.id))

    print("Team %i: Finishing transactions task" % team_id)

    return 0
