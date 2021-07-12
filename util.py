# -*- coding: utf-8 -*-
import dash_html_components as html


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


def int_or_mean(x):
    """
    В таблице попадаются года типа 2010-2016 - типа если сериал шел несколько лет
    TODO тут говнокод, нужно проверку сделать на входящие значения
    :param x: 2010-2016 или 2015
    :return:
    """
    if x.isnumeric():
        return x
    else:
        return str(
            int(
                (int(x[:4]) + int(x[5:]))/2
            )
        )
