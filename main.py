from classes.bot import Bot
import json


def get_params(name_file: str):
    with open(name_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


if __name__ == '__main__':
    try:
        config = get_params('config.json')
    except FileNotFoundError:
        print(f'Create a config.json file in the root directory of the project with the following content:/n"TOKEN": "your_token",/n"ADMIN_ID": 000000000000,/n"password": "password"')
    else:    
        messages = get_params('messages.json')
        bot = Bot(
            TOKEN=config["TOKEN"],
            DB_PATH="database.db",
            messages=messages,
            password=config["password"],
            ADMIN_ID=config["ADMIN_ID"],
        )
        bot.run()
