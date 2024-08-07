# Job Bot

Job Bot is a Python script that automates job acceptance on a standard job portal website. It uses Selenium WebDriver to interact with the website and BeautifulSoup for HTML parsing. The script logs into the website, searches for jobs matching specific criteria, and accepts them if they meet the criteria.

## Prerequisites

1. **Google Chrome**: Ensure you have Google Chrome installed.
2. **ChromeDriver**: ChromeDriver must be compatible with the version of Google Chrome installed.
3. **Python**: Make sure you have Python 3.6+ installed.
4. **Virtual Environment**: It's recommended to use a virtual environment to manage dependencies.

## Setup

### Step 1: Clone the Repository

```sh
git clone https://github.com/yemeen/jobbot.git
cd jobbot
```

### Step 2: Set Up the Virtual Environment

Set up a virtual environment to manage dependencies:

```sh
python -m venv jobbot
source jobbot/bin/activate  # On Windows use `jobbot\Scripts\activate`
```

### Step 3: Install Dependencies

Install the required Python packages:

```sh
pip install -r requirements.txt
```

_Note: If `requirements.txt` is not available, you can install the necessary packages individually:_

```sh
pip install selenium webdriver-manager beautifulsoup4 python-dotenv
```

### Step 4: Download and Install Google Chrome

Download the latest stable release of Google Chrome from the official [Google Chrome download page](https://www.google.com/chrome/).

For Debian-based systems:

```sh
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
```

### Step 5: Set Up Environment Variables

Create a `.env` file in the project directory and add your Website credentials:

```sh
USERNAME=your_username
PASSWORD=your_password
```

### Step 6: Create the Initial Job Count File

Create a `job_count.json` file in the project directory to keep track of the number of jobs accepted:

```json
{
  "jobs_accepted": 0
}
```

## Running the Script

To run the script, use the following command:

```sh
python job_bot.py
```

### Common Issues

1. **ChromeDriver Compatibility**: Ensure that the version of ChromeDriver matches the installed version of Google Chrome. Use `webdriver-manager` to manage ChromeDriver versions automatically.
2. **No Such Element Exception**: Ensure the XPath or CSS selectors used in the script are correct and match the current structure of the website. The specific error in the logs indicates that an element with `xpath=".//td[2]"` was not found. Verify the correctness of the selectors.

## Logs

Logs are written to `job_bot.log` and the console. The script logs important events such as successful logins, job searches, job acceptances, and periodic status updates to indicate that the script is running.

### Log Rotation

The script uses a rotating file handler for logging. Log files are automatically rotated when they reach 5 MB, and up to 5 backup files are kept.

## Troubleshooting

1. **Permission Denied**: Ensure that the script has the necessary permissions to access the required files and directories.
2. **Updating Selenium**: If you encounter issues related to Selenium, ensure you are using the latest version:

   ```sh
   pip install --upgrade selenium
   ```

3. **Uninstall and Reinstall Selenium**: If issues persist, try uninstalling and reinstalling Selenium:

   ```sh
   pip uninstall selenium
   pip install selenium
   ```

4. **ChromeDriver Path**: If ChromeDriver is not found, specify the path explicitly in the script:

   ```python
   driver = webdriver.Chrome(executable_path='/path/to/chromedriver', options=options)
   ```

## Contributing

If you find any issues or have suggestions for improvements, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
