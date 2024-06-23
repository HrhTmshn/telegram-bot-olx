import telebot
from telebot import types
from classes.category import Category
from classes.parse import Parse
from classes.db import DataBase
from typing import Union
import random
import string
from time import sleep, time
from datetime import datetime


class Bot:
    def __init__(
        self,
        TOKEN: str,
        DB_PATH: str,
        messages: dict,
        password: str = "",
        ADMIN_ID: int = None,
    ):
        self.bot = telebot.TeleBot(TOKEN)
        self.messages = messages
        self.password = password
        self.ADMIN_ID = ADMIN_ID
        self.DB_PATH = DB_PATH
        self.db = DataBase(self.DB_PATH)
        self.category = Category("https://www.olx.ua")
        self.confirm = {}

    def __check_input(self, timeout=20, long_polling_timeout=20):
        self.bot.infinity_polling(
            timeout=timeout,
            long_polling_timeout=long_polling_timeout
        )

    def __get_keyboard(self, user_id: int, btn_names: Union[list, dict]):
        if type(btn_names) == list:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = []
            if user_id == self.ADMIN_ID:
                buttons.append(types.KeyboardButton("🟢ADMIN PANEL"))
            if btn_names:
                for btn_name in btn_names:
                    buttons.append(types.KeyboardButton(btn_name))
                keyboard.add(*buttons)
                return keyboard
            elif buttons:
                keyboard.add(*buttons)
                return keyboard
            else:
                return types.ReplyKeyboardRemove()

        elif type(btn_names) == dict:
            markup = types.InlineKeyboardMarkup()
            for btn_name, (url, callback_data) in btn_names.items():
                btn = types.InlineKeyboardButton(
                    btn_name, url=url, callback_data=callback_data
                )
                markup.add(btn)
            return markup

    def __register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def __start(message):
            self.bot.send_message(
                message.from_user.id,
                self.messages["welcome"]
            )
            if self.db.check_user(message.from_user.id):
                self.bot.send_message(
                    message.from_user.id, self.messages["verific_true"]
                )
                __start_parse(message)
            else:
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["password_enter"],
                    reply_markup=self.__get_keyboard(
                        message.from_user.id,
                        list()
                    )
                )
                self.bot.register_next_step_handler(
                    message, __user_verification
                )

        @self.bot.message_handler(func=lambda message: message.text == "🟢ADMIN PANEL")
        def __admin_panel(message):
            if message.from_user.id == self.ADMIN_ID:
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["choose"],
                    reply_markup=self.__get_keyboard(
                        message.from_user.id,
                        {
                            "🟢Users List": (None, "list_users"),
                            "🔴Delete Users": (None, "delete_users"),
                            "🔴Update Categories": (None, "update_categories"),
                        }
                    )
                )
            else:
                self.bot.send_message(
                    message.from_user.id, self.messages["command_wo_permission"])

        @self.bot.message_handler(func=lambda message: message.text == "🟢Категория")
        def __select_category_for_user(message):
            self.bot.send_message(
                message.from_user.id,
                self.messages["cat_select"],
                reply_markup=self.__get_keyboard(
                    message.from_user.id,
                    self.db.get_category_names()
                )
            )
            self.bot.register_next_step_handler(
                message, __confirm_select_category_for_user
            )

        @self.bot.message_handler(func=lambda message: message.text == "🟢Запрос")
        def __select_query_for_user(message):
            self.bot.send_message(
                message.from_user.id,
                self.messages["query_select"],
                reply_markup=self.__get_keyboard(
                    message.from_user.id, list()
                )
            )
            self.bot.register_next_step_handler(
                message,
                __confirm_select_query_for_user
            )

        @self.bot.message_handler(func=lambda message: message.text == "🟢URL")
        def __select_url_for_user(message):
            self.bot.send_message(
                message.from_user.id,
                self.messages["url_choose_filter_and_enter"],
                parse_mode='HTML',
                reply_markup=self.__get_keyboard(
                    message.from_user.id, list()
                )
            )
            self.bot.register_next_step_handler(
                message,
                __confirm_select_url_for_user
            )

        @self.bot.message_handler(func=lambda message: message.text in ("🟢ТОП", "🟢Без ТОП"))
        def __turn_top(message):
            self.db.turn_top_status(message.from_user.id)
            self.bot.send_message(
                message.from_user.id,
                f"{self.messages['top_selected']}{message.text}"
            )
            __start_parse(message)

        @self.bot.message_handler(func=lambda message: message.text == "🔴Следить")
        def __track(message):
            url, category_name, query, top_status = self.db.get_query_info(
                message.from_user.id
            )
            if url:
                msg_string = f"{self.messages['url_selected']}{url}\n"
            else:
                msg_string = f"{self.messages['cat_selected']}{category_name}\n{self.messages['query_selected']}{query}\n"
            self.bot.send_message(
                message.from_user.id,
                f"{msg_string}{self.messages['top_selected']}{'с ТОП' if top_status else 'без ТОП'}"
            )
            self.confirm[message.from_user.id] = ''.join(
                random.choices(string.digits, k=4)
            )
            self.bot.send_message(
                message.from_user.id,
                self.messages["password_enter_confirm"] +
                self.confirm[message.from_user.id],
                reply_markup=self.__get_keyboard(message.from_user.id, list())
            )
            self.bot.register_next_step_handler(
                message, __confirm_track
            )

        @self.bot.message_handler(func=lambda message: message.text == "🔴СТОП!")
        def __stop_tracking(message):
            self.db.set_tracking_users(message.from_user.id, False)
            self.bot.send_message(
                message.from_user.id,
                self.messages["please_wait"]
            )

        @self.bot.callback_query_handler(func=lambda call: call.data == "list_users")
        def __list_users(call):
            if call.from_user.id == self.ADMIN_ID:
                users_list = self.db.get_users_list()
                if users_list:
                    user_lines = []
                    for user_id, username, first_name, last_name, category_name, query, url, top_status, tracking in users_list:
                        user_lines.append(
                            f"ID: {user_id}, Nickname: @{username}\nFirst Name: {first_name}, Last Name: {last_name}\nQuery: {url if url else category_name+query}\n{'TOP' if top_status else 'w/o TOP'}, Status: {'Work' if tracking else 'STOP'}"
                        )
                    msg = "\n\n\n".join(user_lines)
                    self.bot.send_message(call.from_user.id, msg)
                else:
                    self.bot.send_message(
                        call.from_user.id,
                        self.messages["db_users_nofound"]
                    )
            else:
                self.bot.send_message(
                    call.from_user.id,
                    self.messages["command_wo_permission"]
                )
            self.bot.answer_callback_query(call.id)

        @self.bot.callback_query_handler(func=lambda call: call.data == "delete_users")
        def __delete_users(call):
            if call.from_user.id == self.ADMIN_ID:
                self.confirm[call.from_user.id] = ''.join(
                    random.choices(string.digits, k=4)
                )
                self.bot.send_message(
                    self.ADMIN_ID,
                    self.messages["password_enter_confirm"] +
                    self.confirm[call.from_user.id],
                    reply_markup=self.__get_keyboard(call.from_user.id, list())
                )
                self.bot.register_next_step_handler(
                    call.message, __confirm_delete_users
                )
            else:
                self.bot.send_message(
                    call.from_user.id,
                    self.messages["command_wo_permission"]
                )
            self.bot.answer_callback_query(call.id)

        @self.bot.callback_query_handler(func=lambda call: call.data == "update_categories")
        def __update_categories(call):
            if call.from_user.id == self.ADMIN_ID:
                self.data_categories = self.category.parse()
                self.bot.send_message(
                    self.ADMIN_ID,
                    self.messages["cat_write_all_or_not"],
                    reply_markup=self.__get_keyboard(
                        call.from_user.id,
                        {
                            "Да": (None, "all_category_entry"),
                            "Нет": (None, "select_category")
                        }
                    )
                )
            else:
                self.bot.send_message(
                    call.from_user.id,
                    self.messages["command_wo_permission"]
                )
            self.bot.answer_callback_query(call.id)

        @self.bot.callback_query_handler(func=lambda call: call.data == "all_category_entry")
        def __all_category_entry(call):
            __approve_category_entry(call.message)

        @self.bot.callback_query_handler(func=lambda call: call.data == "select_category")
        def __select_category(call):
            name_categories = []
            for name, _, _ in self.data_categories:
                name_categories.append(name)
            self.bot.send_message(
                self.ADMIN_ID,
                self.messages["cat_enter_available_list"]
            )
            self.bot.send_message(
                self.ADMIN_ID,
                "\n".join(name_categories),
                reply_markup=self.__get_keyboard(
                    call.from_user.id, list()
                )
            )
            self.bot.register_next_step_handler(
                call.message, __category_filtering
            )

        def __approve_category_entry(message):
            self.confirm[message.from_user.id] = ''.join(
                random.choices(string.digits, k=4))
            self.bot.send_message(
                self.ADMIN_ID,
                self.messages["password_enter_confirm"] +
                self.confirm[message.from_user.id],
                reply_markup=self.__get_keyboard(
                    message.from_user.id, list()
                )
            )
            self.bot.register_next_step_handler(
                message, __confirm_update_categories
            )

        def __category_filtering(message):
            new_data_categories = []
            name_categories = message.text.split("\n")
            for category_data in self.data_categories:
                if category_data[0] in name_categories:
                    new_data_categories.append(category_data)
            if new_data_categories:
                self.data_categories = new_data_categories
                __approve_category_entry(message)
            else:
                self.bot.send_message(
                    self.ADMIN_ID,
                    self.messages["cat_no_available_list"]
                )

        def __confirm_delete_users(message):
            if message.text == self.confirm.pop(message.from_user.id):
                try:
                    self.db.delete_all_users()
                    self.bot.send_message(
                        self.ADMIN_ID,
                        self.messages["db_users_removed"]
                    )
                except Exception as e:
                    self.bot.send_message(
                        self.ADMIN_ID, f"{self.messages['error']}{e}"
                    )
            else:
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["password_incorrect"]
                )

        def __confirm_update_categories(message):
            if message.text == self.confirm.pop(message.from_user.id):
                try:
                    self.db.delete_all_categories()
                    self.db.add_category_records(self.data_categories)
                    self.bot.send_message(
                        self.ADMIN_ID,
                        self.messages["cat_updated"]
                    )
                except Exception as e:
                    self.bot.send_message(
                        self.ADMIN_ID, f"{self.messages['error']}{e}"
                    )
            else:
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["password_incorrect"]
                )

        def __confirm_select_category_for_user(message):
            self.db.set_query_users(
                message.from_user.id, category_name=message.text
            )
            self.bot.send_message(
                message.from_user.id,
                self.messages["cat_selected"] + message.text
            )
            __start_parse(message)

        def __confirm_select_query_for_user(message):
            self.db.set_query_users(
                message.from_user.id, query=message.text
            )
            self.bot.send_message(
                message.from_user.id,
                self.messages["query_selected"] + message.text
            )
            __start_parse(message)

        def __confirm_select_url_for_user(message):
            self.db.set_query_users(
                message.from_user.id, url=message.text
            )
            self.bot.send_message(
                message.from_user.id,
                self.messages["url_selected"] + message.text
            )
            __start_parse(message)

        def __user_verification(message):
            if (message.text != None) and (message.text == self.password):
                self.db.sign_up_user(
                    message.from_user.id,
                    message.from_user.username,
                    message.from_user.first_name if message.from_user.first_name else "",
                    message.from_user.last_name if message.from_user.last_name else ""
                )
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["verific_done"]
                )
                __start_parse(message)
            else:
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["password_incorrect_repeat"]
                )
                self.bot.register_next_step_handler(
                    message, __user_verification
                )

        def __start_parse(message):
            url, category_name, query, top_status = self.db.get_query_info(
                message.from_user.id
            )
            top_btn = "🟢Без ТОП" if top_status else "🟢ТОП"
            self.bot.send_message(
                message.from_user.id,
                self.messages["choose_for_tracking"],
                reply_markup=self.__get_keyboard(
                    message.from_user.id,
                    ["🟢Категория", "🟢Запрос", "🟢URL", top_btn, "🔴Следить",]
                )
            )

        def __confirm_track(message):
            if message.text == self.confirm.pop(message.from_user.id):
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["please_wait"],
                    reply_markup=self.__get_keyboard(
                        message.from_user.id, ["🔴СТОП!"]
                    )
                )
                self.db.set_tracking_users(message.from_user.id, True)
                pause_post = float(f'1.{message.from_user.id}')
                pause_parse = 30
                url, category_name, query, top_status = self.db.get_query_info(
                    message.from_user.id
                )
                name_table = url if url else f"{category_name}+{query}"
                while self.db.check_tracking_users(message.from_user.id):
                    if not self.db.check_user(message.from_user.id):
                        __start(message)
                    cooldown = time() + pause_parse
                    response = Parse(
                        DB_PATH=self.DB_PATH,
                        category_name=category_name,
                        query=query,
                        url=url,
                        count_page=0
                    ).parse()
                    if response != None:
                        self.bot.send_message(
                            message.from_user.id,
                            self.messages["request_nofound_try_change"]
                        )
                        break

                    new_posts = self.db.check_new_posts(
                        message.from_user.id,
                        name_table,
                        top_status
                    )
                    if new_posts:
                        for new_post in new_posts:
                            post_id, link, promo, title, price, post_type, location, date = new_post
                            date = datetime.fromisoformat(
                                date).strftime("%d.%m.%Y %H:%M")
                            formatted_message = f'<a href="{link}">{title}</a>\n<b>Цена:</b> {price}\n<b>Локация:</b> {location}\n<b>Дата:</b> {date}\n{"<b>💸ТОП</b>" if promo else ""}'
                            self.bot.send_message(
                                message.from_user.id,
                                formatted_message,
                                parse_mode='HTML',
                                reply_markup=self.__get_keyboard(
                                    message.from_user.id, ["🔴СТОП!"]
                                )
                            )
                            sleep(pause_post)
                    now = time()
                    if cooldown > now:
                        sleep(cooldown - now)

            else:
                self.bot.send_message(
                    message.from_user.id,
                    self.messages["password_incorrect"]
                )
            __start_parse(message)

    def run(self):
        self.__register_handlers()
        self.__check_input(timeout=100, long_polling_timeout=50)
