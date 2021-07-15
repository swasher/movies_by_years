"""
Этот скрипт парсит страницы пользовательские кинопоиска, напрмер https://www.kinopoisk.ru/mykp/movies/list/type/3575/
Вебстраницы нужно сохранять "полностью", иначе хром сохранит по 25 фильмов вместо 200.
Страницы нужно поместить в папку (переменная htmldir), скрипт отпрарсит все файлы и сохранит csv

Далее данные этого csv нужно итегригрировать в данные от kinorium
"""

from parsel import Selector
import codecs
from glob import glob
import pandas as pd

from pathlib import Path

htmldir = 'kinopoisk буду смотреть'
p = Path(htmldir)
files = list(p.glob('**/*.html'))


row_list = []
for f in files:
    text = codecs.open(f, "r", "utf-8").read()
    selector = Selector(text=text)
    ulli = selector.xpath('//ul[@id="itemList"]/li')

    for x in ulli:
        """
        Есть разные методы создания dataFrame. Но увеличивать Dataframe "row by row" является самым медленным.
        Поэтому создаем dict и заполняем Dataframe одной командой.
        https://stackoverflow.com/a/47979665/1334825 - SPEED PERFORMANCE
        https://stackoverflow.com/a/62734983/1334825 - NEVER grow a DataFrame!
        https://stackoverflow.com/a/17496530/1334825 - best method
        """
        d = {'movie': x.xpath("div[@class='info']/a/text()").get(), 'date_added_kp': x.xpath("span/text()").get()[:10],
             'year': x.xpath("div[@class='info']/span/text()").re_first(r'\((\d{4})[\)\s]'),
             'orig_name': x.xpath("div[@class='info']/span/text()").re_first(r'.*\s*\(')[:-2],
             'number': x.xpath("div[@class='number']/text()").get()
             }
        print("{number:>4}  {year:<4}  {date_added:<10}  {movie:<34}  {orig_name:<30}".format(**d))
        row_list.append(d)

df = pd.DataFrame(row_list)
df.to_csv(path_or_buf='csv/kinopoisk_unseen.csv', sep='\t')
