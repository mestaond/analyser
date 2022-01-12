import datetime
import re
import pandas
import plotly.graph_objects as go
from datetime import time
from app.src import constants


def to_time(x: str) -> datetime:
    """Transforms string text in datetime value (with fixed date)"""
    if x.count(':') != 2:
        x = '00:' + x
    p = x.split(':')
    mins = int(p[1])
    if mins >= 60:
        p[0] = str(mins // 60)
        p[1] = str(mins % 60)
    return datetime.datetime.combine(datetime.date(2017, 1, 1), time(int(p[0]), int(p[1]), int(p[2])))


def to_date(x: str) -> datetime:
    """Transforms string text in date value"""
    p = x.split('-')
    return datetime.date(int(p[0]), int(p[1]), int(p[2]))


def to_relative(x: datetime, leader: datetime) -> datetime:
    """Calculates difference between ``x`` and current ``leader``"""
    diff = x - leader
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return datetime.datetime.combine(datetime.date(2017, 1, 1), time(hours, minutes, seconds))


def get_plotly_splits_prepare_data(splits: pandas.DataFrame, limit: str, filtered: list):
    """Prepares DataFrame for plotting:
    filters total time and name, renames columns, adds start column, drops disqualified runners\n
    :returns ``data``, table indexes and frame with just``name`` column"""
    data = splits.filter(regex="ResName|RegNo|TotalTime.*")
    if limit != 'none' and limit != 'crop':
        data = data.iloc[:int(limit), :]
    if filtered:
        filtered.append(data.loc[0, 'RegNo'])
        data = data[data.RegNo.isin(filtered)]
    if limit == 'crop':
        if len(data.index) > constants.GRAPH_LEGEND_SIZE:
            data = data.iloc[:constants.GRAPH_LEGEND_SIZE, :]
    data = data.drop('RegNo', axis=1)
    data = data.rename(columns=lambda x: re.sub('TotalTime', 'K', x))
    data = data.rename(columns=lambda x: re.sub('K999', 'F', x))
    data = data[data.F != 'DISK']
    runners = data.index.to_list()
    names = data['ResName'].copy()
    data.rename(columns={'ResName': 'S'}, inplace=True)
    data['S'] = '00:00'
    cols = data.columns.to_list()
    for a in cols:
        data[a] = data[a].apply(to_time)
    return data, runners, names


def get_plotly_fill_graph(data: pandas.DataFrame, runners: list, names: pandas.DataFrame) -> go.Figure:
    """Fills graph object with given ``data``, lines are named by ``names``, returns graph object Figure"""
    fig = go.Figure()

    for r in runners:
        fig.add_trace(
            go.Scatter(
                y=data.loc[r].values,
                x=data.columns,
                name=names.loc[r],
                mode='lines'
            ))
    return fig


def get_plotly_splits_absolute(splits: pandas.DataFrame, limit: str, filtered: list) -> go.Figure:
    """Plots absolute time graph for ``splits`` table with ``limit`` runners"""
    data, runners, names = get_plotly_splits_prepare_data(splits, limit, filtered)

    fig = get_plotly_fill_graph(data, runners, names)

    fig.update_layout(
        title="Analýza - celkový čas od startu",
        width=constants.GRAPH_WIDTH,
        height=constants.GRAPH_HEIGHT,
        xaxis_title="Kontrola",
        yaxis_title="Čas (hh:mm:ss)",
        yaxis_type='date',
        yaxis_tickformat='%H:%M:%S',
        hovermode='x',
        showlegend=True
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def get_plotly_splits_relative(splits: pandas.DataFrame, limit: str, filtered: list) -> go.Figure:
    """Plots relative loss-to-leader graph for ``splits`` table with ``limit`` runners"""
    data, runners, names = get_plotly_splits_prepare_data(splits, limit, filtered)
    minimum = data.min()
    cols = data.columns.to_list()
    for a in cols:
        data[a] = data[a].apply(lambda x: to_relative(x, minimum.loc[a]))

    fig = get_plotly_fill_graph(data, runners, names)

    fig.update_layout(
        title="Analýza - ztráta na průběžně prvního",
        width=constants.GRAPH_WIDTH,
        height=constants.GRAPH_HEIGHT,
        xaxis_title="Kontrola",
        yaxis_title="Ztráta (+hh:mm:ss)",
        yaxis_tickformat='%H:%M:%S',
        hovermode='x',
        showlegend=True
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def get_plotly_runner_event_level(events: pandas.DataFrame, level: int) -> go.Figure:
    data = events.copy()
    data = data[data['Place'] != 'DISK']
    data['Date'] = data['Date'].apply(lambda x: to_date(x))
    data['Place'] = data['Place'].apply(lambda x: int(x.split('.')[0]))
    disciplines = [data[data['Discipline'] == 'SP'], data[data['Discipline'] == 'KT'], data[data['Discipline'] == 'KL']]

    fig = go.Figure()

    for r in range(0, 3):
        fig.add_trace(
            go.Scatter(
                y=disciplines[r]['Place'],
                x=disciplines[r]['Date'],
                name=constants.GRAPH_RUNNER_DISCIPLINES[r],
                mode='markers',
                hovertext=disciplines[r]['Name'] + '<br>' + disciplines[r]['Class']
            ))
    fig.update_layout(
        title="Výsledky dle disciplíny na úrovni " + constants.GRAPH_LEVEL_TEXT[level],
        width=constants.GRAPH_WIDTH,
        height=constants.GRAPH_HEIGHT,
        xaxis_title="Datum",
        xaxis_tickformat='%d.%m.%Y',
        yaxis_title="Umístění",
        showlegend=True
    )
    return fig
