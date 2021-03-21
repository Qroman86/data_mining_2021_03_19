import time
import json
from pathlib import Path
import requests

class Parse5ka:


    def __init__(self, start_url: str, result_path: Path):
        self.start_url = start_url
        self.result_path = result_path

    def _get_response(self, url, *args, **kwargs) -> requests.Response:
        while True:
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(1)

    def run(self):
        for category_data in self._parse(self.start_url):
            self._save(category_data)

    def _parse_products(self, url, category):
        params = {
            "categories": category.get("parent_group_code")
        }
        first_page = True
        response = self._get_response(url, params=params)
        products = []
        while url:
            if first_page == False:
                response = self._get_response(url)
            product_data = response.json()
            products.extend(product_data.get("results", []))
            url = product_data.get("next")
            first_page = False
        return products

    def _parse(self, url):
        response = self._get_response(url)
        data = response.json()

        for category in data:

            product_url = "https://5ka.ru/api/v2/special_offers/"
            products_data = self._parse_products(product_url, category)
            category_data = {}
            category_data["name"] = category.get("parent_group_name")
            category_data["code"] = category.get("parent_group_code")
            category_data["products"] = products_data

            yield category_data

    def _save(self, data):
        file_path = self.result_path.joinpath(f'{data["code"]}.json')
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')



if __name__ == "__main__":
    file_path = Path(__file__).parent.joinpath("categories")
    if not file_path.exists():
        file_path.mkdir()

    parser = Parse5ka("https://5ka.ru/api/v2/categories/", file_path)
    parser.run()