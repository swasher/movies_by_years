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

# ListTile - список, в котором фильм, нас интересует только "Буду смотреть", "Date" - дата внесения в таблицу, т.е. просмотра или желания посмотреть
movie_list = pd.read_csv(csv_list, sep='\t')[["ListTitle", "Date", "Title", "Year"]]
# Type - ненужный столбец для совместимости по столбцам с movie_list
movie_vote = pd.read_csv(csv_vote, sep='\t')[["Date", "Title", "Year"]]

# оставляем строки только "буду смотреть"
movie_list = movie_list[movie_list["ListTitle"]=="Буду смотреть"]

# На данный момент на кинориуме присутствует баг, и все фильмы из списка "Буду смотреть" выводятся дважды. Пока исправляем тут,
# потом уберем эти строчки, как исправят баг. Маляву написал.
# Может быть такая ситуация, что разные фильмы имеют одинаковые названия. Поэтому мы будем искать дубликаты "год+название"
movie_list['temp_column'] = movie_list['Title'] + movie_list['Year']
movie_list.drop_duplicates(subset='temp_column', inplace=True)
movie_list.drop(columns='temp_column', inplace=True)

# ====================================================
# инжектим данные кинопоиска в movie_list (т.е. в таблицу непросмотренных фильмов)
csv_kp = codecs.open('csv/kinopoisk_unseen.csv', 'rU', 'UTF-8')
dfkp = pd.read_csv(csv_kp, sep='\t')[["movie", "date_added", "year", "orig_name"]]
# в поле Date нам не нужна дата, нужен только год, так что заменяем дату на год
dfkp['date_added'] = dfkp.apply(lambda x: datetime.strptime(x.date_added, "%d.%m.%Y").year, axis=1)


def deduplicate_titles(df):
    # Может возникнуть проблема, что у нас есть два фильма с одинаковым названием и одинакового года. Тогда у нас будет не уникальный ключ,
    # и получаем эксепшн при объеденении таблиц. Такие случаи редкие, но есть
    # Остаться в живых - 2006 - Fritt vilt
    # Остаться в живых - 2006 - Stay Alive

    # df[df.index.duplicated()] - показывает, что дублируется

    if len(df[df.index.duplicated()]):
        pass
    else:
        return df


# Стратегия такая - в обоих датасетах создаем индекс - YEAR+TITLE. И потом по этому индексу объеденяем таблицы.
dfkp['ind'] = dfkp.year.map(str) + '-' + dfkp.movie
dfkp.set_index('ind', inplace=True)

# dfkp = deduplicate_titles(dfkp)
dfkp['dedup'] = dfkp.groupby('ind').cumcount().astype(str).str.replace('0', '')
dfkp['dedup1'] = np.where(dfkp['dedup']=='', dfkp['year'].astype(str)+'-'+dfkp['movie'], dfkp['year'].astype(str)+'-'+dfkp['movie']+'-'+dfkp['orig_name'])
##### Теперь нужно dedup1 сделать индексом

movie_list['ind'] = movie_list['Year'] + '-' + movie_list['Title']
movie_list.set_index('ind', inplace=True)

# dftmp = pd.merge(dfkp, movie_list, on='ind')
dftmp = pd.concat([dfkp, movie_list], axis=1, ignore_index=True)

# Объеденяем таблицы
df = pd.concat([movie_list, movie_vote], axis=0)[["ListTitle", "Date", "Title", "Year"]]

# Переименовываем заголовки ListTitle -> Seen
df.columns = ["Seen", "Date", "Title", "Year"]

# Устанавливаем значения поля Seen в 0 или 1 (0 - непросмотрено)
df.loc[df.Seen == 'Буду смотреть', 'Seen'] = 0
df.loc[pd.isna(df['Seen']), 'Seen'] = 1

# в поле Date нам не нужна дата, нужен только год, так что заменяем дату на год
df['Date'] = df.apply(lambda x: datetime.strptime(x.Date, "%Y-%m-%d %H:%M:%S").year, axis=1)

# двойные даты в years: для Шерлока, напр., 2010-2017 - ВЫЧИСЛЯЕМ СРЕДНЕЕ АРИФМЕТИЧЕСКОЕ
df['Year'] = df['Year'].apply(lambda x: int_or_mean(x))

# удаляем записи, где год=0 (это багованые строки) - написал маляву в кинориум
# df = df[df.Year != '0']
# or - check speed
df.drop(df.loc[df['Year']=='0'].index, inplace=True)



# экспорт
df.sort_values('Title').to_csv(path_or_buf='csv/normalized_data.csv')

print('OK.')
