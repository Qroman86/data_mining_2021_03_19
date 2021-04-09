import re
import scrapy

from ..loaders import HhLoader, HhAuthorLoader

class HhSpider(scrapy.Spider):
    name = 'hh'
    allowed_domains = ['hh.ru']
    start_urls = ['https://hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113']
    visited_urls = []

    _xpaths_selectors = {
        "pagination": "//div[@data-qa='pager-block']//a[@data-qa='pager-next']/@href",
        "vacancies": "//div[contains(@class,'vacancy-serp-item')]//a[@data-qa='vacancy-serp__vacancy-title']/@href",
        "author": "//div[contains(@class,'vacancy-company__details')]//a[@data-qa='vacancy-company-name']/@href",
        "direct_vacancies": "//div[contains(@class,'vacancy-list-item')]//a[@data-qa='vacancy-serp__vacancy-title']/@href"
    }

    _xpath_vacancy_selectors = {
        "name": "//div[contains(@class,'vacancy-title')]//h1[@data-qa='vacancy-title']/text()",
        "salary": "//div[contains(@class,'vacancy-title')]//p[contains(@class,'vacancy-salary')]/span/text()",
        "desc": "//div[contains(@class,'vacancy-description')]/descendant::*/text()",
        "key_skills": "//div[contains(@data-qa,'skills-element')]//span/text()",
        "author_link": "//div[contains(@class,'vacancy-company__details')]//a[@data-qa='vacancy-company-name']/@href"
    }

    _xpath_author_selectors = {
        "title": "//span[@data-qa='company-header-title-name']/text()",
        "link": "//a[@data-qa='sidebar-company-site']/@href",
        "work_spheres": "//div[contains(text(),'Сферы деятельности')]/following-sibling::p/text()",
        "desc": "//div[@data-qa='company-description-text']/descendant::*/text()"
    }

    def _get_follow_xpath(self, response, selector, callback, **kwargs):
        for link in response.xpath(selector):
            yield response.follow(link, callback=callback, cb_kwargs=kwargs)

    def parse(self, response, *args, **kwargs):
        if response.url in self.visited_urls:
            return
        self.visited_urls.append(response.url)
        yield from self._get_follow_xpath(
            response, self._xpaths_selectors["vacancies"], self.vacancy_parse
        )

        yield from self._get_follow_xpath(
             response, self._xpaths_selectors["pagination"], self.vacancies_parse
        )



    def vacancy_parse(self, response, **kwargs):
        if response.url in self.visited_urls:
            return
        self.visited_urls.append(response.url)

        loader = HhLoader(response=response)
        loader.add_value("url", response.url)
        for key, xpath in self._xpath_vacancy_selectors.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()

        yield from self._get_follow_xpath(
            response, self._xpaths_selectors["author"], self.author_parse
        )




    def author_parse(self, response, **kwargs):
        if response.url in self.visited_urls:
            return
        self.visited_urls.append(response.url)

        loader = HhAuthorLoader(response=response)
        loader.add_value("url", response.url)
        for key, xpath in self._xpath_author_selectors.items():
            loader.add_xpath(key, xpath)
        yield loader.load_item()

        print(response)
        yield from self._get_follow_xpath(
            response, self._xpaths_selectors["direct_vacancies"], self.vacancy_parse
        )

    def vacancies_parse(self, response, **kwargs):
        if response.url in self.visited_urls:
            return
        self.visited_urls.append(response.url)

        yield from self._get_follow_xpath(
            response, self._xpaths_selectors["vacancies"], self.vacancy_parse
        )

        yield from self._get_follow_xpath(
            response, self._xpaths_selectors["pagination"], self.vacancies_parse
        )

