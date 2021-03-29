from pathlib import Path
import time
import datetime
import requests
from urllib.parse import urljoin
import bs4
import pymongo
from pytz import timezone


class MagnitParse:
    def __init__(self, start_url, mongo_url):
        self.start_url = start_url
        client = pymongo.MongoClient(mongo_url)
        self.db = client["gb_parse_magnit"]

    def get_response(self, url, *args, **kwargs):
        for _ in range(15):
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(1)
        raise ValueError("URL DIE")

    def get_soup(self, url, *args, **kwargs) -> bs4.BeautifulSoup:
        soup = bs4.BeautifulSoup(self.get_response(url, *args, **kwargs).text, "lxml")
        return soup



    #    "date_from": "DATETIME",
    #    "date_to": "DATETIME",
    __months = ("января", "февраля", "марта", "апреля",
                "мая", "июня", "июля", "августа",
                "сентября", "октября", "ноября", "декабря")


    def convert_to_datetime(self, input_str: str, is_from_date: bool):
        if input_str is None:
            return None

        hour_val = 0
        min_val = 0
        sec_val = 0
        if is_from_date == False:
            hour_val = 23
            min_val = 59
            sec_val = 59

        for month_index in range(0, len(self.__months)):
            if self.__months[month_index] in input_str:
                num_list = [int(num) for num in filter(
                    lambda num: num.isnumeric(), input_str.split())]
                if len(num_list) != 1:
                    return None
                return datetime.datetime(2021, month_index+1, num_list[0], hour_val, min_val, sec_val, tzinfo = timezone('Europe/Moscow'))
        return None




    @property
    def template(self):
        data_template = {
            "url": lambda a: urljoin(self.start_url, a.attrs.get("href", "/")),
            "product_name": lambda a: a.find("div", attrs={"class": "card-sale__title"}).text,
            "image_url": lambda a: urljoin(
                self.start_url, a.find("picture").find("img").attrs.get("data-src", "/")
            ),
            "promo_name": lambda a: a.find("div", attrs={"class":"card-sale__header"}).text,
            "old_price": lambda a: float(".".join(
                (a.find("div", attrs={"class": "label__price_old"}).
                 find("span", attrs={"class": "label__price-integer"}).text,
                a.find("div", attrs={"class": "label__price_old"}).
                 find("span", attrs={"class": "label__price-decimal"}).text)
                )
            ),
            "new_price": lambda a: float(".".join(
                (a.find("div", attrs={"class": "label__price_new"}).
                 find("span", attrs={"class": "label__price-integer"}).text,
                 a.find("div", attrs={"class": "label__price_new"}).
                 find("span", attrs={"class": "label__price-decimal"}).text)
                )
            ),
            "date_from": lambda a: self.convert_to_datetime(a.find("div", attrs={"class": "card-sale__date"}).findNext("p").text, True),
            "date_to": lambda a: self.convert_to_datetime(a.find("div", attrs={"class": "card-sale__date"}).findNext("p").findNext("p").text, False)
        }
        return data_template

    def run(self):
        for product in self._parse(self.get_soup(self.start_url)):
            self.save(product)

    def _parse(self, soup):
        products_a = soup.find_all("a", attrs={"class": "card-sale"})
        for prod_tag in products_a:
            product_data = {}
            for key, func in self.template.items():
                try:
                    product_data[key] = func(prod_tag)
                except AttributeError:
                    pass
            yield product_data

    def save(self, data):
        collection = self.db["magnit"]
        collection.insert_one(data)


if __name__ == "__main__":
    url = "https://magnit.ru/promo/"
    mongo_url = "mongodb://localhost:27017"
    parser = MagnitParse(url, mongo_url)
    parser.run()