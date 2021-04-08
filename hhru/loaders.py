import re
from scrapy.loader import ItemLoader
from scrapy import Selector
from itemloaders.processors import TakeFirst, MapCompose


def get_salary_str(item) -> str:
    return ''.join(item)

class HhLoader(ItemLoader):
    default_item_class = dict
    salary_in = get_salary_str