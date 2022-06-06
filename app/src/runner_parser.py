import json
import urllib.request
import urllib.parse
import pandas
import pandas as pd
import streamlit as st
from app.src import constants, splits_parser, loader


def load_results(reg_no: str, year: str):
    """Loads table of (supported) events, where runner with ``reg_no`` competed in ``year``\n
    For each event, some details and standing is loaded\n
    :returns DataFrame/error string and ``runner_info`` list"""
    entries, runner_info, user_id = load_event_entries(reg_no, year)
    if type(entries) is str:
        return entries, []

    df = pd.DataFrame.from_dict(entries, orient='index')
    tmp, events = loader.load_event_calendar(year, '', [], False, True, True, False)
    df = df[['EventID', 'ClassID', 'ClassDesc']]
    df['idx'] = df['EventID']
    df.set_index('idx', inplace=True)
    events = events.set_index('ID')
    result = pd.concat([df, events], axis=1, join="inner")
    result = get_all_standings(result, events, user_id)
    return result, runner_info


#@st.cache
def load_event_entries(reg_no: str, year: str):
    """Calls request for data of (supported) events, where runner with ``reg_no`` competed in ``year``\n
    :returns string with json/error message, runner info and user_id as string"""
    with urllib.request.urlopen(constants.URL_USER_ID + reg_no) as url:
        data = json.loads(url.read().decode())
        if data['Status'] != 'OK' or not data['Data']:
            return 'registrační číslo ' + reg_no.upper(), [], ''
        runner_info = ["Jméno: __" + data['Data']['FirstName'] + " " + data['Data']['LastName'] + "__",
                       "Registrační číslo: __" + reg_no.upper() + "__", "Sezóna: __" + year + "__"]
        user_id = data['Data']['ID']

    values = {'format': 'json',
              'method': 'getUserEventEntries',
              'userid': user_id,
              'datefrom': year + '-01-01',
              'dateto': year + '-12-31'}
    data = urllib.parse.urlencode(values)
    data = data.encode('utf-8')
    request = urllib.request.Request(constants.URL, data)

    with urllib.request.urlopen(request) as url:
        data = json.loads(url.read().decode())
        if data['Status'] != 'OK' or not data['Data']:
            return 'error', [], ''
        entries = data['Data']
    return entries, runner_info, user_id


#@st.cache
def get_all_standings(entries: pandas.DataFrame, events: pandas.DataFrame, user_id: str):
    """Fills ``entries`` DataFrame with results of all events\n
    For two-day championships, only final day is loaded\n
    :returns filled and formatted DataFrame"""
    entries['Place'] = entries.apply(lambda row: get_place(row['EventID'], row['ClassID'], user_id), axis=1)
    entries.rename(columns={'ClassDesc': 'Class'}, inplace=True)
    entries = get_two_day_champ_data(entries, events, user_id)
    entries = entries[entries['Place'] != '']
    entries.sort_values(by=['DateStr', 'Name'], inplace=True)
    entries = entries[['Date', 'Name', 'Discipline', 'Level', 'Class', 'Place']]
    return entries


def get_two_day_champ_data(entries: pandas.DataFrame, events: pandas.DataFrame, user_id: str) -> pandas.DataFrame:
    """Loads results of two-day championships (only final, not qualification)"""
    champs_entries = entries[entries['Level'] == 'MČR']
    champs_entries = champs_entries[champs_entries['Place'] == '']
    entries = entries[entries['Place'] != '']
    champs_entries = champs_entries.apply(lambda row: get_finals_results(row, events, user_id), axis=1)
    champs_entries['idx'] = champs_entries['EventID']
    champs_entries.set_index('idx', inplace=True)
    result = pd.concat([entries, champs_entries])
    return result


def get_finals_results(row, events: pandas.DataFrame, user_id: str):
    """For qualification event finds appropriate final event and result"""
    final = events.loc[((events['Discipline'] == row['Discipline']) & (events['Name'].str.contains("finále")))]
    if not final.empty:
        event_id = final.index.to_list()[0]
        row['EventID'] = event_id
        row['Name'] = final.loc[event_id, 'Name']
        row['Date'] = final.loc[event_id, 'Date']
    else:
        event_id = row['EventID']
    ctg, tmp1, tmp2 = splits_parser.load_categories(event_id)
    ctg = ctg[ctg['Name'].str.contains(row['Class'])].reset_index(level=0)
    classes = ctg['ID'].to_list()
    for i in range(0, len(classes)):
        place = get_place(event_id, classes[i], user_id)
        if place != '':
            row['Place'] = place
            row['Class'] = ctg.loc[i, 'Name']
            break
    return row


def get_place(event_id: str, class_id: str, user_id: str) -> str:
    """Gets place for ``user`` on ``event`` in ``class``
    returns empty string (when not present), or DISK when disqualified or standing"""
    with urllib.request.urlopen(constants.URL_RESULTS + event_id + '&classid=' + class_id) as url:
        data = json.loads(url.read().decode())
        if data['Status'] != 'OK' or not data['Data']:
            return ''
        val_list = list(data['Data'].values())
        r = [x for x in val_list if x['UserID'] == user_id]
        if r:
            r = r[0]
            if r['Place'] == '':
                if r['Time'] == 'DISK':
                    return 'DISK'
                return ''
            return r['Place']
        return ''
