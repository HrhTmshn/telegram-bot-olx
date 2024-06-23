import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class Category:
    def __init__(
        self,
        domain: str = "https://www.olx.ua"
    ):
        self.domain = domain

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

    def __get_url(self):
        page = self.session.get(self.domain)
        self.soup = BeautifulSoup(page.text, 'lxml')

    def __parse_page(self):
        self.data = [
            ("Без категорії", "https://www.olx.ua/uk/list/", "")
        ]
        categories = self.soup.find(
            attrs={'data-testid': 'home-categories-menu-row'}
        ).find_all("a")

        for category in categories:
            name = category.find("p").text
            link = category.get("href")
            picture = category.find("img").get('src')
            self.data.append((name, self.domain + link, picture))

        return self.data

    def parse(self):
        self.__set_up()
        self.__get_url()
        return self.__parse_page()
