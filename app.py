# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from datetime import datetime


import codecs
doc_list = codecs.open('csv/backup_76444_movie_list.csv','rU','UTF-16')
doc_vote = codecs.open('csv/backup_76444_votes.csv','rU','UTF-16')

# Экспорт кинориума так устроен, что мы не можем получить в одном csv и проспотренные и непросмотренные.
# Поэтому мы используем две таблицы: LIST - это экспорт всех списков кинориума, нас интересует только один из них - "Буду смотреть"
# и VOTE - это таблица моих оценок фильмам, соотв. содержит все просмотренные фильмы.

# ListTile - список, в котором фильм, нас интересует только "Буду смотреть", "Date" - дата внесения в таблицу, т.е. просмотра или желания посмотреть
movie_list = pd.read_csv(doc_list, sep='\t')[["ListTitle", "Date", "Title", "Year"]]
# Type - ненужный столбец для совместимости по столбцам с movie_list
movie_vote = pd.read_csv(doc_vote, sep='\t')[["Date", "Title", "Year"]]

# оставляем строки только "буду смотреть"
movie_list = movie_list[movie_list["ListTitle"]=="Буду смотреть"]

# Объеденяем таблицы
df = pd.concat([movie_list, movie_vote], axis=0)[["ListTitle", "Date", "Title", "Year"]]

# Переименовываем заголовки ListTitle -> Seen
df.columns = ["Seen", "Date", "Title", "Year"]

# Устанавливаем значения поля Seen в true или false
df.loc[df.Seen == 'Буду смотреть', 'Seen'] = 0
df.loc[pd.isna(df['Seen']), 'Seen'] = 1

# в поле Date нам не нужна дата, нужен только год, так что заменяем дату на год
df['Date'] = df.apply(lambda x: datetime.strptime(x.Date, "%Y-%m-%d %H:%M:%S").year, axis=1)

# temp
df = df.sort_values('Year')

# удаляем записи, где год=0 (это багованые строки)
# df = df[df.Year != '0']
# or - check speed
df.drop(df.loc[df['Year']=='0'].index, inplace=True)

df = df.iloc[range(0, 15)]

grouped = df.groupby('Year').agg(
    # Year=pd.NamedAgg(column='Year'),
    Total=pd.NamedAgg(column='Seen', aggfunc='count'),  # тотал считает всего - правильно!
    Seen=pd.NamedAgg(column='Seen', aggfunc='sum'),     # sum считает сумму - т.е. кол-во едениц - получется кол-во просмотренных - правильно!
)

grouped['Notseen'] = grouped['Total'] - grouped['Seen']

# На данном этапе мы имеем примерно следующее:
#       Total   Seen    Notseen
# 1965  1       1       0
# 1967  2       0       2

# Переворачиваем, чтобы по оси X у нас были года
grouped = grouped.T
grouped = grouped.rename_axis('Year', axis="columns")

fig = px.bar(df, x='Year', y='Seen')

# Находим минимальный и максимальный года в Date - мы будем строить отчеты для каждого из этих годов
year_min = min(df['Date'])
year_max = max(df['Date'])

# Находим самый старый фильм и текущий год
oldest_movie = int(min(df['Year']))
current_year = datetime.now().year
print('CURRENT YEAR'+str(current_year))

# TODO найти дубликаты

# TODO что делать с двойными датами в years: для Шерлока, напр., 2010-2017 - ВЫЧИСЛЯТЬ СРЕДНЕЕ АРИФМЕТИЧЕСКОЕ

# TODO сделать новую таблицу, содержащую год-просмотрено-непросмотрено и далее функцию, которая генерит такие таблицы на каждый мой год

# my_years = pd.DataFrame({})

# Подсчитать, сколько просмотрено/непросмотрено фильмов, выпущенных в определенном году
# df[df['Seen'] == 0]['Year'].value_counts()


# for year in range(oldest_movie, current_year+1):
#     print(year)


def generate_table(dataframe, max_rows=40000):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])





external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    html.Plaintext(children='min year: '+str(year_min)+', max year: '+str(year_max)),
    html.Plaintext(children='oldest movie: '+str(oldest_movie)+', current year: '+str(current_year)),

    html.H5(children='DF table'),
    generate_table(df),
    html.H5(children='GROUPED table'),
    generate_table(grouped),

    dcc.Graph(
        id='Test graph',
        figure=fig
    )

    # html.H1(children='Movie vote'),
    # generate_table(movie_vote)

])

if __name__ == '__main__':
    app.run_server(debug=True)