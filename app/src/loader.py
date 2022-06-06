import re
import pandas

from app.gui import streamlitapp as sapp
from app.src import runner_parser
from app.src import constants, splits_parser, graphs
from datetime import date
import streamlit as st


def load_splits(category: str, event_id: str, event_year: str, mask: str, levels: list, all_sports: bool, all_events: bool):
    """Calls appropriate DataFrame loader according to provided parameters\n
    :returns load_mode, DataFrame/error string"""
    if category != '':
        entity = splits_parser.load_splits(category)
        if type(entity) is pandas.DataFrame:
            sapp.category_runners = sorted((entity.loc[1:, 'RegNo'] + ': ' + entity.loc[1:, 'ResName']).to_list())
        return constants.MODE_SPLITS, entity
    elif event_id != '':
        sapp.event_id = event_id
        entity, info, categories = splits_parser.load_categories(event_id)
        sapp.event_info = info
        sapp.event_categories = categories
        return constants.MODE_CATEGORIES, entity
    else:
        return load_event_calendar(event_year, mask, levels, all_sports, all_events, True)


@st.cache
def load_event_calendar(event_year: str, mask: str, levels: list, all_sports: bool, all_events: bool, drop_date: bool):
    return get_event_calendar(event_year, mask, levels, all_sports, all_events, drop_date)


def get_event_calendar(event_year: str, mask: str, levels: list, all_sports: bool, all_events: bool, drop_date: bool):
    """Parses all given parameters to json and then calls request with these parameters\n
    :returns load_mode, DataFrame/error string"""
    if event_year == '':
        event_year = (str(date.today().year))
    values = splits_parser.load_events_parse_data(event_year, mask, levels, all_sports, all_events)
    data = splits_parser.load_events(values)
    if type(data) is pandas.DataFrame:
        if drop_date:
            data.drop('DateStr', axis=1, inplace=True)
        if not all_sports:
            data.drop('Sport', axis=1, inplace=True)
    return constants.MODE_EVENTS, data


def load_runner(reg_no: str, year: str):
    """Loads all events, where runner with ``reg_no`` in ``year`` competed
    returns DataFrame or string error message for invalid reg_no"""
    entity, info = runner_parser.load_results(reg_no, year)
    sapp.runner_info = info
    return entity


def get_category_id_from_name(category: str, event_id: str) -> str:
    """Converts category name in its ID, returns ID as string or 'err'"""
    if sapp.event_id == '' or sapp.event_id != event_id:
        ret = splits_parser.load_categories(event_id)
        if type(ret) == str:
            return ret
    key_list = list(sapp.event_categories.keys())
    val_list = list(sapp.event_categories.values())
    for i in range(len(val_list)):
        val_list[i] = val_list[i].upper()

    try:
        position = val_list.index(category.upper())
        return key_list[position]
    except ValueError:
        return 'err'


def load_split_graphs(data: pandas.DataFrame, show_relative: bool, limit: str, filtered: list):
    """Creates an absolute/relative graph with limited count of filtered"""
    if show_relative:
        return graphs.get_plotly_splits_relative(data, limit, filtered)
    return graphs.get_plotly_splits_absolute(data, limit, filtered)


def load_runner_graphs(data: pandas.DataFrame, level: int):
    """Creates a graph with results of events of event ``level``"""
    filtered = data[data['Level'].isin(constants.LEVEL_SHORTCUTS[level])]
    filtered = filtered[filtered['Place'] != 'DISK']
    if filtered.shape[0] > 0:
        return graphs.get_plotly_runner_event_level(filtered, level)
    return ''


def crop_and_style(splits: pandas.DataFrame, limit: str, filtered: list, splits_mode: bool):
    """Reshapes and styles DataFrame
    If some runners are ``filtered``, their rows are highlighted
    If ``limit`` is set, only first n rows are displayed"""
    data = crop_dataframe(splits, splits_mode)
    if limit != 'none':
        data = data.iloc[:int(limit), :]
    data = data.rename(columns=lambda x: re.sub('Res', '', x))
    data = data.style.apply(lambda r: row_styling(r, filtered), axis=1)
    return data


@st.cache
def crop_dataframe(splits: pandas.DataFrame, splits_mode: bool) -> pandas.DataFrame:
    """Drops unnecessary time and place columns, and renames some other"""
    data = splits.copy()
    data['ResPlace'] = data['ResPlace'] + ' ' + data['ResName']
    if splits_mode:
        data = data.drop(data.filter(regex="Total.*|ResName").columns, axis=1)
        data.rename(columns={'SplitTime999': 'ToFinishTime', 'SplitPlace999': 'ToFinishPlace'}, inplace=True)
    else:
        data = data.drop(data.filter(regex="Split.*|ResName").columns, axis=1)
        data.rename(columns={'TotalTime999': 'FinishTime', 'TotalPlace999': 'FinishPlace'}, inplace=True)
    data.set_index('ResPlace', inplace=True)
    data = data.replace('999', '---')
    return data


# inspired by StackOverflow
def row_styling(row, filtered):
    color = 'white'
    if row['RegNo'] in filtered:
        color = 'yellow'
    return ['background-color: %s' % color]*len(row.values)


def shrink_table(data: pandas.DataFrame):
    """Prepares table for pdf export: shortens column names and splits table in three parts:
    front legend, time columns and standings columns"""
    data = data.rename(columns=lambda x: re.sub('Total|Split', '', x))
    data = data.rename(columns=lambda x: re.sub('Res|To', '', x))
    data = data.drop('Club', axis=1)
    front = data.iloc[:, 0:3].copy()
    data = data.iloc[:, 3:]
    times = data[data.filter(regex="T.*").columns.to_list()]
    times = times.rename(columns=lambda x: re.sub('Time', '', x))
    times = times.rename(columns=lambda x: re.sub('Finish', 'F', x))
    positions = data[data.filter(regex="P.*").columns.to_list()]
    return front, times, positions


def filter_runner_id(to_filter: list) -> list:
    """Adjusts list of RegNo:Name elements to list of RegNo"""
    filtered = []
    for r in to_filter:
        filtered.append(r.split(':')[0])
    return filtered
