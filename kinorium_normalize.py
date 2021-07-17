# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


# TODO фильмы-дубликаты - почему их так много в исходном CSV???

import codecs

import numpy as np
import pandas as pd
from datetime import datetime
from util import int_or_mean


csv_list = codecs.open('kinorium_data/backup_76444_movie_list.csv', 'rU', 'UTF-16')
csv_vote = codecs.open('kinorium_data/backup_76444_votes.csv', 'rU', 'UTF-16')

# Экспорт кинориума так устроен, что мы не можем получить в одном csv и проспотренные и непросмотренные.
# Поэтому мы используем две таблицы: LIST - это экспорт всех списков кинориума, нас интересует только один из них - "Буду смотреть"
# и VOTE - это таблица моих оценок фильмам, соотв. содержит все просмотренные фильмы.


# Vote - таблица с оценками, т.е. это "просмотрено"
movie_vote = pd.read_csv(csv_vote, sep='\t')[["Date", "Title", "Year"]]
movie_vote.rename({'Date': 'Date_added'}, inplace=True, axis=1)
movie_vote['Date_added'] = movie_vote.apply(lambda x: datetime.strptime(x.Date_added, "%Y-%m-%d %H:%M:%S").year, axis=1)
movie_vote["Year"] = pd.to_numeric(movie_vote["Year"], errors="coerce")
# Сериалы имеют год типа 2010-2015. После предыдущей команды, когда не удалось год сконвертировать в int,
# Year получает значение nan. Дропаем эти строки.
movie_vote.dropna(subset=["Year"], inplace=True)
movie_vote = movie_vote.astype({"Year": int})
movie_vote['Seen'] = 1

# ListTile - список, в котором фильм, нас интересует только "Буду смотреть", "Date" - дата внесения в таблицу, т.е. когда фильм добавился в "буду смотреть"
movie_list = pd.read_csv(csv_list, sep='\t')[["ListTitle", "Date", "Title", "Year"]]

# оставляем строки только те, где ListTitle = "буду смотреть" и дропаем этот столбец
movie_list = movie_list[movie_list["ListTitle"]=="Буду смотреть"]
movie_list.drop(columns='ListTitle', inplace=True)

# На данный момент на кинориуме присутствует баг, и все фильмы из списка "Буду смотреть" выводятся дважды. Пока
# исправляем тут, потом уберем эти строчки, как исправят баг. Маляву написал.
movie_list['temp_column'] = movie_list['Title'] + movie_list['Year']
movie_list.drop_duplicates(subset='temp_column', inplace=True)
movie_list.drop(columns='temp_column', inplace=True)
# в поле Date нам не нужна дата, нужен только год, так что заменяем дату на год
movie_list['Date'] = movie_list.apply(lambda x: datetime.strptime(x.Date, "%Y-%m-%d %H:%M:%S").year, axis=1)
movie_list.rename({'Date': 'date_added_kinor'})

# инжектим данные кинопоиска в movie_list (т.е. в таблицу непросмотренных фильмов)
csv_kp = codecs.open('csv/kinopoisk_unseen.csv', 'rU', 'UTF-8')
dfkp = pd.read_csv(csv_kp, sep='\t')[["movie", "date_added_kp", "year", "orig_name"]]
# в поле Date нам не нужна дата, нужен только год, так что заменяем дату на год
dfkp['date_added_kp'] = dfkp.apply(lambda x: datetime.strptime(x.date_added_kp, "%d.%m.%Y").year, axis=1)


def deduplicate_titles(dfkp):
    # Может возникнуть проблема, что у нас есть два фильма с одинаковым названием и одинакового года. Тогда у нас будет
    # не уникальный ключ (год+русское название), и получем эксепшн при объеденении таблиц. Такие случаи редкие, но есть:
    # Остаться в живых - 2006 - Fritt vilt
    # Остаться в живых - 2006 - Stay Alive
    # Поэтому мы к дубликату (2006-Остаться в живых) добавляем англ. название (2006-Остаться в живых-Stay Alive)
    # TODO написал и понял проблему - если фильм русский, то у него аглийское название пустое
    # TODO надо, наверное, не выебываться с добавлением английского названия и прост цифру добавлять.

    # DEBUG df[df.index.duplicated()] - показывает, что дублируется

    if len(dfkp[dfkp.index.duplicated()]):
        dfkp['dedup'] = dfkp.groupby('ind').cumcount().astype(str).str.replace('0', '')
        dfkp['dedup'] = np.where(dfkp['dedup'] == '', dfkp['year'].astype(str) + '-' + dfkp['movie'],
        dfkp['year'].astype(str) + '-' + dfkp['movie'] + '-' + dfkp['orig_name'])
        dfkp.reset_index(drop=True, inplace=True)
        dfkp.rename(columns={"dedup": "ind"}, inplace=True)
        dfkp.set_index('ind', inplace=True)
        return dfkp
    else:
        return dfkp


# Стратегия такая - в обоих датасетах создаем индекс - YEAR+TITLE. И потом по этому индексу объеденяем таблицы.
movie_list['ind'] = movie_list.Year + '-' + movie_list.Title
movie_list.set_index('ind', inplace=True)

dfkp['ind'] = dfkp.year.map(str) + '-' + dfkp.movie
dfkp.set_index('ind', inplace=True)
dfkp = deduplicate_titles(dfkp)

# Объеденяем кинопоиск и кинориум по ключу "ind" - это год+название
df_unseen = pd.merge(dfkp, movie_list, on='ind', how="outer")

"""
На этом этапе слитая таблица df_combined выглядит так. Одинаковые фильмы слились в одну строку. Но есть фильмы, которые 
только в таблице кинопоиска, или только в таблице кинориуме. Соотв. в таких записях мы видим Nan 
-----------------кинопоиск---------------------  |  ----- кинориум ---------
movie       date_added_kp   year        orig_name   Date        Title   Year
Стелс		2020.00000		2005.00000	Stealth		2020.00000	Стелс	2005
Стена		2019.00000		2017.00000	The Wall	2020.00000	Стена	2017
Потаскушка	2018.00000		1984.00000	La garce	nan			nan		nan
Полночь FM	2019.00000		2010.00000	Simyaui FM	nan			nan		nan
nan			nan			    nan			nan			2021.00000	Попадос	2020
nan			nan			    nan			nan			2021.00000	Черный  2020
nan			nan			    nan			nan			2021.00000	Сек...	2012
"""

# Объеденяем столбцы с названиями и годами
df_unseen["Date_added_"] = df_unseen.apply(lambda row: row["date_added_kp"] if pd.notna(row["date_added_kp"]) else row["Date"], axis=1)
df_unseen["Title_"] = df_unseen.apply(lambda row: row["Title"] if pd.notna(row["Title"]) else row["movie"], axis=1)
df_unseen["Year_"] = df_unseen.apply(lambda row: row["Year"] if pd.notna(row["Year"]) else row["year"], axis=1)

df_unseen["Year_"] = pd.to_numeric(df_unseen["Year_"], errors="coerce")

# Сериалы имеют год типа 2010-2015. После предыдущей команды, когда не удалось год сконвертировать в int,
# Year_ получает значение nan. Дропаем эти строки.
df_unseen.dropna(subset=["Year_"], inplace=True)
#  Заодно дропаем "пустые строки" с нулями (это багованые строки - написал маляву в кинориум, ответили что это типа
# "удаленные из базы фильмы, которые у меня были в списках", имхо чушь
df_unseen.drop(labels=np.nan, inplace=True)

# И превращаем год в int, чтобы не было нулей (2021.0000).
df_unseen = df_unseen.astype({"Year_": int})
df_unseen = df_unseen.astype({"Date_added_": int})

# дропаем ненужные  столбцы, и на этом месте у нас полностью готовая таблицы "непросмотренных" фильмов
df_unseen.drop(['movie', 'date_added_kp', 'year', 'orig_name', 'Date', 'Title', 'Year'], axis=1, inplace=True)
df_unseen.rename(columns={'Date_added_': 'Date_added', 'Title_': 'Title', 'Year_': 'Year'}, inplace=True)
df_unseen['Seen'] = 0


# Объеденяем таблицы Буду смотреть и Просмотрено
df = pd.concat([df_unseen, movie_vote], axis=0)[["Date_added", "Title", "Year", "Seen"]]


# экспорт
df.sort_values('Title').to_csv(path_or_buf='csv/normalized_data.csv')

print('OK.')
