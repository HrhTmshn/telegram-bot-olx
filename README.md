# OLX Telegram Bot

A Python bot that scrapes OLX website based on a given URL with selected filters (category, query, city, price, condition, etc.) and monitors for new listings, notifying the user when a new listing is available.

## Important Notes

>⚠️ Disclaimer: This project was created for personal automation purposes. Some functionality may not be suitable for multi-user environments.
> - This bot was designed primarily for personal use and currently supports **only one user at a time**. If you plan to adapt it for multi-user support, additional work is required (e.g., user management, session handling).
> - Ensure you have a stable internet connection while running the script, as it relies on external requests to the OLX website.
> - The bot will notify the user in Telegram whenever a new listing matching the specified filters is found.

#### Stack:

- [Python](https://www.python.org/downloads/)
- [Beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [lxml](https://pypi.org/project/lxml/)
- [fake-useragent](https://pypi.org/project/fake-useragent/)
- [pyTelegramBotAPI](https://pypi.org/project/pyTelegramBotAPI/)
- [requests](https://pypi.org/project/requests/)
- [Pyinstaller](https://www.pyinstaller.org/)

## Local Developing

All actions should be executed from the source directory of the project and only after installing all requirements.

1. Firstly, create and activate a new virtual environment:
   ```bash
   python3.7 -m venv venv
   .\venv\Scripts\activate
   ```

2. Install packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Create a `config.json` file in the root directory of the project with the following content::
   ```json
   {
      "TOKEN": "your_token",
      "ADMIN_ID": 000000000000,
      "password": "password"
   }
   ```

   - TOKEN: Your Telegram bot token.
   - ADMIN_ID: The Telegram user ID you want to assign as the bot's admin.
   - password: The password required for users to start the bot's parsing functionality.

4. Run the script:
   ```bash
   python main.py
   ```

## Creating an Executable

To create an executable of the bot, follow these steps:

1. Make sure PyInstaller is installed:
   ```bash
   pip install pyinstaller
   ```

2. Run PyInstaller with the spec file:
   ```bash
   pyinstaller exe/olx.spec
   ```

This will generate an executable in the dist folder, using the spec file located in the exe folder.