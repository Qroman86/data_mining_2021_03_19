import re
from scrapy.loader import ItemLoader
from scrapy import Selector
from itemloaders.processors import TakeFirst, MapCompose


def join_text(item) -> str:
    return ' '.join(item)

def preparefull_link(url) -> str:
    return f"https://hh.ru{url[0]}"

class HhLoader(ItemLoader):
    default_item_class = dict
    salary_in = join_text
    desc_in = join_text
    author_link_in = preparefull_link

class HhAuthorLoader(ItemLoader):
    default_item_class = dict
    desc_in = join_text