import requests
from bs4 import BeautifulSoup
from classes.db import DataBase
from fake_useragent import UserAgent
from urllib.parse import quote, urlencode
from datetime import datetime
from time import time, sleep


class Parse:
    cooldown = time()

    def __init__(
        self,
        DB_PATH: str,
        category_name: str = "Без категорії",
        query: str = "",
        url: str = "",
        count_page: int = 100
    ):
        self.domain = "https://www.olx.ua"
        self.db = DataBase(DB_PATH)
        self.category_name = category_name
        self.category = self.db.get_category_link(self.category_name)
        self.query = query
        self.url = url
        self.table_name_for_save_data = url
        self.params = {'search[order]': 'created_at:desc'}
        self.count_page = count_page
        self.data = {}

    def __set_up(self, close: bool = False):
        if close:
            self.session.close()
        else:
            while True:
                user = UserAgent().random
                if not any(word in user for word in ['Mobile', 'Android']):
                    break
            self.session = requests.Session()
            self.session.headers.update({'user-agent': user})

    def __encode_url(self):
        if not self.url:
            request = f"q-{self.query.replace(' ', '-')}/" if self.query else ""
            base_url = f"{self.category}{request}"
            encoded_base_url = quote(base_url, safe=':/?=&')
            encoded_params = f"?{urlencode(self.params)}" if self.params else ""
            encoded_url = f"{encoded_base_url}{encoded_params}"
            self.url = encoded_url

    def __get_url(self):
        self.__check_cooldown()
        page = self.session.get(self.url)
        self.__set_cooldown(5)
        self.soup = BeautifulSoup(page.text, 'lxml')

    def __set_cooldown(self, seconds: int = 0):
        Parse.cooldown = time() + seconds

    def __check_cooldown(self):
        now = time()
        if Parse.cooldown > now:
            sleep(Parse.cooldown - now)

    def __paginator(self):
        while True:
            if self.soup.find(
                attrs={'data-testid': 'total-count'}
            ).text == "Ми знайшли  0 оголошень":
                self.__set_up(close=True)
                return "Ми знайшли 0 оголошень"
            self.__parse_page()
            if not self.soup.find_all(attrs={'data-testid': 'pagination-forward'}) or self.count_page <= 0:
                break
            self.url = self.domain + self.soup.find(
                attrs={'data-testid': 'pagination-forward'}
            ).get('href')
            self.__get_url()
            self.count_page -= 1
        self.__set_up(close=True)
        self.__save_data()

    def __parse_page(self):
        container_for_posts = self.soup.find(
            attrs={'data-testid': 'listing-grid'})
        posts = container_for_posts.find_all(attrs={'data-testid': 'l-card'})
        for post in posts:
            id = post.get('id')
            self.data[id] = {}
            self.data[id]['link'] = self.domain + post.find('a').get("href")
            self.data[id]['promo'] = bool(post.find_all(
                attrs={'data-testid': 'adCard-featured'}
            ))
            self.data[id]['name'] = post.find('h6').text
            self.data[id]['price'] = post.find('p').text
            self.__detect_post_type(id, post)

    def __detect_post_type(self, id, post):
        if post.find_all(attrs={'class': 'jobs-ad-card'}):
            self.data[id]['type'] = 'job-post'
        else:
            self.data[id]['type'] = 'post'
            self.data[id]['location'] = post.find(
                attrs={'data-testid': 'location-date'}
            ).text.split(" - ")[0]
            self.data[id]['date'] = self.__parse_date(post.find(
                attrs={'data-testid': 'location-date'}
            ).text.split(" - ")[-1])

    def __parse_date(self, date_str):
        if 'Сьогодні' in date_str:
            return datetime.now().isoformat()
        months = {
            'січня': 1, 'лютого': 2, 'березня': 3, 'квітня': 4,
            'травня': 5, 'червня': 6, 'липня': 7, 'серпня': 8,
            'вересня': 9, 'жовтня': 10, 'листопада': 11, 'грудня': 12
        }
        parts = date_str.split()
        day = int(parts[0])
        month = months[parts[1]]
        year = int(parts[2])
        return datetime(year, month, day).isoformat()

    def __save_data(self):
        table_name = self.table_name_for_save_data if self.table_name_for_save_data else f"{self.category_name}+{self.query}"
        self.db.save_parse_data(
            table_name,
            self.data,
            14
        )

    def parse(self):
        self.__set_up()
        self.__encode_url()
        self.__get_url()
        return self.__paginator()
