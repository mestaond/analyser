# -*- coding: utf-8 -*-
import pandas as pd
from app.src import constants
import urllib.request
import urllib.parse
import json
import streamlit as st


@st.cache
def load_splits(class_id: str):
    """Sends get request method getSplits and parses data from json to DataFrame\n
    :returns DataFrame or error string"""
    values = {'format': 'json',
              'method': 'getSplits',
              'classid': class_id}
    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    request = urllib.request.Request(constants.URL, data)
    with urllib.request.urlopen(request) as url:
        data = json.loads(url.read().decode())
        if data['Status'] != 'OK' or not data['Data']:
            return 'ID kategorie ' + class_id
        splits = data['Data']['Splits']

    df = pd.DataFrame.from_dict(splits, orient='index')
    df.reset_index(level=0, inplace=True)
    df = df.drop(['index', 'StartTime', 'FinishTime', 'PersID'], axis=1)

    f1 = df.filter(regex="Res.*|Reg.*")
    f1 = f1[['ResPlace', 'ResName', 'ResClub', 'RegNo', 'ResTime', 'ResLoss']]
    f2 = df.drop(df.filter(regex="Res.*|Reg.*").columns, axis=1)
    result = pd.concat([f1, f2], axis=1)

    return result


@st.cache
def load_categories(event_id: str):
    """Sends get request method getEvent and parses data from json to DataFrame\n
    Saves event_info in global variables sapp.event_info and sapp.event_categories\n
    :returns DataFrame or error string"""
    with urllib.request.urlopen(constants.URL_CATEGORIES + event_id) as url:
        data = json.loads(url.read().decode())
        if data['Status'] != 'OK':
            return 'ID závodu ' + event_id, [], {}
        if not data['Data']['Discipline']['ID'] in constants.SUPPORTED_DISCIPLINES_ID:
            return 'unsupported discipline: ' + data['Data']['Discipline']['NameCZ'], [], {}
        classes = data['Data']['Classes']

    event_info = []
    cols = ['Name', 'Date', 'Place', 'Map']
    legend = ['Jméno', 'Datum', 'Místo', 'Mapa']
    for i in range(0, len(cols)):
        if cols[i] == 'Date':
            x = data['Data'][cols[i]].split('-')
            event_info.append(legend[i] + ': ' + x[2] + '.' + x[1] + '.' + x[0])
        else:
            event_info.append(legend[i] + ': ' + data['Data'][cols[i]])
    event_info.append('Disciplína: ' + data['Data']['Discipline']['NameCZ'])
    df = pd.DataFrame.from_dict(classes, orient='index')
    df = df[df['Distance'] != '0.00']
    categories = df[['ID', 'Name']].copy()
    df.set_index('ID', inplace=True)
    event_categories = categories.set_index('ID').to_dict('index')
    event_categories = {k: v['Name'] for k, v in event_categories.items()}
    return df[['Name', 'Distance', 'Climbing', 'Controls']], event_info, event_categories


def reformat_date(x: str) -> str:
    """Transforms string text in date value"""
    p = x.split('-')
    return p[2] + '.' + p[1] + '.' + p[0]


def load_events(values: dict):
    """Sends get request method getEventList and parses data from json to DataFrame\n
    Request is encoded in utf-8, because ``values`` may contain Czech alphabet symbols\n
    Drops cancelled events\n
    :returns DataFrame or error string"""
    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    request = urllib.request.Request(constants.URL, data)
    with urllib.request.urlopen(request) as url:
        data = json.loads(url.read().decode())
        if data['Status'] != 'OK':
            return 'event listing error'
        events = data['Data']

    df = pd.DataFrame.from_dict(events, orient='index')
    if df.empty:
        return 'not found'
    df = df[df['Cancelled'] == '0']
    if df.empty:
        return 'not found'
    df['Discipline'] = df['Discipline'].apply(lambda x: x['ShortName'])
    df = df[df.Discipline.isin(constants.SUPPORTED_DISCIPLINES)]
    df['Level'] = df['Level'].apply(lambda x: x['ShortName'])
    df['Sport'] = df['Sport'].apply(lambda x: x['NameCZ'])
    df['DateStr'] = df['Date']
    df['Date'] = df['Date'].apply(lambda x: reformat_date(x))
    df['Org'] = df['Org1'].apply(lambda x: x['Abbr'])
    df.reset_index(level=0, inplace=True)
    return df[['ID', 'Date', 'Name', 'Org', 'Region', 'Sport', 'DateStr', 'Discipline', 'Level']]
