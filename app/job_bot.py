import os
import dotenv
import time
import logging
import random
import threading
from logging.handlers import RotatingFileHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException, NoSuchWindowException,
    StaleElementReferenceException
)
from selenium.webdriver.common.action_chains import ActionChains
from job_data import load_job_count, save_job_count


dotenv.load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt="%m/%d/%Y %I:%M:%S %p %Z",
    handlers=[
        RotatingFileHandler("job_bot.log",
                            maxBytes=5*1024*1024, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JobBot:
    def __init__(self, config: dict):
        self.login_url = config['LOGIN_URL']
        self.jobs_url = config['JOBS_URL']
        self.username = config['USERNAME']
        self.password = config['PASSWORD']
        self.job_radius = config['JOB_RADIUS']
        self.job_check_interval = config['JOB_CHECK_INTERVAL']
        self.status_update_interval = config['STATUS_UPDATE_INTERVAL']
        self.job_count_file = config['JOB_COUNT_FILE']
        self.testing = config['TESTING']
        self.job_query = config['JOB_QUERY']
        self.driver = self.initialize_driver()
        self.job_count = load_job_count(self.job_count_file)
        self.status_counter = 0
        self.stop_flag = threading.Event()

    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        if not self.testing:
            options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        driver_path = ChromeDriverManager().install()
        logger.info(f"Using ChromeDriver at {driver_path}")
        driver = webdriver.Chrome(service=Service(
            driver_path), options=options)
        return driver

    def login(self):
        try:
            self.driver.get(self.login_url)
            self.driver.find_element(By.NAME, 'email').send_keys(self.username)
            self.driver.find_element(
                By.NAME, 'password').send_keys(self.password)
            self.driver.find_element(
                By.CSS_SELECTOR, 'button[type="submit"]').click()
            WebDriverWait(self.driver, 10).until(EC.url_to_be(self.jobs_url))
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table-responsive")))
        except TimeoutException:
            logger.error(
                "Timed out waiting for the jobs page to load after logging in.")
        except Exception as e:
            logger.error(f"An error occurred while logging in: {str(e)}")

    def navigate_to_last_job_page(self):
        try:
            last_button = self.driver.find_element(
                By.ID, "DataTables_Table_0_last")
            if "disabled" not in last_button.get_attribute("class"):
                last_button.click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "table-responsive")))
            else:
                logger.info(
                    "The 'LAST' button is disabled, indicating only one page of results.")
        except NoSuchElementException:
            logger.info(
                "The 'LAST' button is not present, indicating only one page of results.")
        except ElementClickInterceptedException:
            logger.info(
                "The 'LAST' button was intercepted by another element, trying again.")
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", last_button)
            last_button.click()
        except TimeoutException:
            logger.error(
                "Timed out waiting for the 'LAST' button to become clickable.")

    def search_for_jobs(self):

        attempts = 0
        max_attempts = 5
        search_input = None

        while attempts < max_attempts and search_input is None:
            try:
                search_input = self.driver.find_element(
                    By.CSS_SELECTOR, 'input[type="search"]')
                search_input.clear()
                search_input.send_keys(query)
                WebDriverWait(self.driver, 10).until(lambda d: d.find_element(
                    By.CSS_SELECTOR, 'input[type="search"]').get_attribute('value') == query)
                break
            except (NoSuchElementException, TimeoutException):
                attempts += 1
                self.driver.refresh()
                time.sleep(1)
                logger.error(
                    f"Attempt {attempts}: Unable to locate search input. Retrying...")

        if attempts == max_attempts:
            logger.info(
                "Failed to find the search input after several attempts.")
            return False

        return True

    def find_acceptable_job(self):
        try:
            job_listings = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, "//table/tbody/tr")))
        except TimeoutException:
            logger.error("Timed out waiting for job listings to be present.")
            return None, None

        for job_row in job_listings:
            if "No matching records found" not in job_row.text:
                try:
                    system = job_row.find_element(By.XPATH, ".//td[2]").text
                    distance_text = job_row.find_element(
                        By.XPATH, ".//td[5]").text
                    distance = float(distance_text)
                    if system == self.job_query and distance < self.job_radius:
                        return job_row, distance
                    if system == self.job_query:
                        logger.info(
                            f"Job with distance {distance} is too far away.")
                except NoSuchElementException:
                    logger.error("Necessary elements not found in job row.")
                except ValueError:
                    logger.error(
                        f"Could not convert distance text to float: {distance_text}")
        return None, None

    def accept_job(self, job):
        try:
            accept_button_element = job.find_element(
                By.XPATH, ".//a[contains(@class, 'btn-primary')]")
            accept_button_element.click()
            logger.info("Clicked the 'Accept' button.")
        except NoSuchElementException:
            logger.error("No 'Accept' button found for the job.")
        except ElementClickInterceptedException:
            logger.error(
                "The 'Accept' button was intercepted by another element, trying again.")
            ActionChains(self.driver).move_to_element(
                accept_button_element).click().perform()
        except Exception as e:
            logger.error(
                f"An error occurred while trying to click the 'Accept' button: {str(e)}")

    def finalize_acceptance(self):
        attempt_count = 0
        max_attempts = 5
        success = False

        while attempt_count < max_attempts and not success:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "frm")))
                radio_buttons = self.driver.find_elements(
                    By.XPATH, '//input[@type="radio" and contains(@name, "appttime")]')
                if radio_buttons:
                    ActionChains(self.driver).move_to_element(
                        radio_buttons[-1]).click().perform()
                    if not self.testing:
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.NAME, "accept_button"))).click()
                        success = True
            except StaleElementReferenceException:
                attempt_count += 1
                logger.error(
                    f"Attempt {attempt_count}: Encountered a stale element; retrying.")
                time.sleep(1)
            except Exception as e:
                logger.error(
                    f"An error occurred during acceptance finalization: {str(e)}")
                break

        if not success:
            logger.error("Failed to finalize acceptance after 5 attempts.")

    def run(self):
        logger.info(f"Starting with {self.job_count} jobs accepted.")

        while not self.stop_flag.is_set():
            try:
                self.login()
                logger.info("Successfully logged in.")
                while not self.stop_flag.is_set():
                    if self.search_for_jobs():
                        job_to_accept, lowest_distance = self.find_acceptable_job()
                        if job_to_accept:
                            logger.info(
                                f"Found a suitable job {job_to_accept, lowest_distance}, accepting...")
                            self.accept_job(job_to_accept)
                            self.finalize_acceptance()
                            logger.info("Job accepted successfully!")
                            self.job_count += 1
                            save_job_count(self.job_count_file, self.job_count)
                            logger.info(
                                f"Job accepted successfully! Total jobs accepted: {self.job_count}")
                            self.driver.get(self.jobs_url)
                        else:
                            logger.info("No suitable job found to accept.")
                        jittered_interval = self.job_check_interval * \
                            random.randint(1, 2)
                        if not self.stop_flag.wait(jittered_interval):
                            self.driver.refresh()
                    else:
                        logger.error(
                            "Failed to search for jobs.")
                        break

                    self.status_counter += 1
                    if self.status_counter >= self.status_update_interval:
                        logger.info(
                            "Script is running and checking for new jobs.")
                        self.status_counter = 0

            except TimeoutException:
                logger.error(
                    "Timed out waiting for an element to load. Attempting to re-login.")
                continue
            except NoSuchWindowException:
                logger.error(
                    "Browser window was closed. Re-initializing the driver.")
                self.driver.quit()
                self.driver = self.initialize_driver()
            except KeyboardInterrupt:
                logger.info("Script canceled by user. Exiting...")
                break
            except Exception as e:
                logger.error(f"An error occurred: {str(e)}")
                break
        self.driver.quit()

    def stop(self):
        self.stop_flag.set()

    def check_status(self):
        if self.stop_flag:
            status = 'Stopped'
        else:
            status = 'Running'
        return {
            "status": status,
            "job_count": self.job_count
        }


if __name__ == "__main__":
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')
    bot = JobBot(username, password)
    bot.run()
