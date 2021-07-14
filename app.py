# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


# TODO найти фильмы-дубликаты
# TODO очень много значений показывает на графиках seen=unseen, похоже на глюк


from itertools import chain
import dash
import codecs
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from datetime import datetime
from util import generate_table

df = pd.read_csv('csv/normalized_data.csv')

# сортировка - в продакшене не нужна
# df = df.sort_values('Year')


# TEST PURPOSE - чтобы уменьшить размер таблицы для тестов
#df = df.iloc[range(0, 15)]


# Находим минимальный и максимальный года в Date - мы будем строить отчеты для каждого из этих годов
year_min = min(df['Date'])
year_max = max(df['Date'])


# Находим самый старый фильм и текущий год
oldest_movie = int(min(df['Year']))
current_year = datetime.now().year


def make_grouped(df, slice_by_year):
    """
    Берет "сырой" dataframe df и возвращает датафрейм для графика (см. ниже), обрезанный по году,
    типа, "какое было состояние просмотров в таком-то году"
    :param df:
    :param slice_by_year:
    :return:
    """
    sliced = df[df.Date <= slice_by_year]

    grouped = sliced.groupby('Year').agg(
        # Year=pd.NamedAgg(column='Year'),
        Total=pd.NamedAgg(column='Seen', aggfunc='count'),  # тотал считает seen+unseen - правильно!
        Seen=pd.NamedAgg(column='Seen', aggfunc='sum'),     # sum считает сумму - т.е. кол-во едениц - получется кол-во просмотренных - правильно!
    )

    grouped['Unseen'] = grouped['Total'] - grouped['Seen']

    # На данном этапе мы имеем примерно следующее:
    #       Total   Seen    Notseen
    # 1965  1       1       0
    # 1967  2       0       2

    # годы, как нарисовано чуть выше - это не значения, а "имена столбцов". Чтобы годы стали значениями - применяем reset_index, получаем следующее:
    #       Year    Total   Seen    Notseen
    # 0     1965    1       1       0
    # 1     1967    2       0       2
    grouped.reset_index(inplace=True)

    return grouped


def fig(df, year):
    grouped = make_grouped(df, year)
    bar = px.bar(grouped, x='Year', y=['Seen', 'Unseen'])
    bar.update_xaxes(title_text=str(year)+' YEAR')
    bar.update_xaxes(title_font_size=20)
    # TODO цифра 500 прибита гвоздями, нужно подумать, как ее вычислять. Это нужно для того, чтобы графики за все года
    # TODO имели одинаковый масштаб по высоте
    bar.update_layout(yaxis_range=[0, 500])
    # bar.update_layout(xaxis_range=[0, current_year-oldest_movie])
    bar.update_xaxes(range=[oldest_movie, current_year+1])
    return bar


# Подсчитать, сколько просмотрено/непросмотрено фильмов, выпущенных в определенном году
# df[df['Seen'] == 0]['Year'].value_counts()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


app.layout = html.Div(children=[
    html.Plaintext(children='min year: '+str(year_min)+', max year: '+str(year_max)),
    html.Plaintext(children='oldest movie: '+str(oldest_movie)+', current year: '+str(current_year)),

] + [dcc.Graph(id=str(year), figure=fig(df, year)) for year in range(year_min, year_max+1)]
)

# пример как создать layout
# app.layout = html.Div(
#     [dcc.Input(id=column, value=column) for column in columns]
#     + [html.Button("Save", id="save"), dcc.Store(id="cache", data=[]), table])


# dcc_graph_stack = []
#
# for y in range(1, 4):
#     g = dcc.Graph(
#         id='Test graph',
#         figure=fig
#     )
#     dcc_graph_stack.append(g)


if __name__ == '__main__':
    app.run_server(debug=True)