# Selectbox options
YEARS = ['2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013']
EVENT_LEVELS = ['1: MČR', '8: ČP + ŽA', '3: ŽB', '11: OM', '4: OŽ', '5: E', '14: OF', '6: OST ( + zobrazit neoficiální závody)']
RUNNERS_LIMIT = ['none', '3', '4', '5', '6', '7', '8', '9', '10', '12', '14', '16', '18', '20', '25', '30']

# Filters
SUPPORTED_DISCIPLINES_ID = ['1', '2', '3', '9']
SUPPORTED_DISCIPLINES = ['KL', 'KT', 'SP', 'NOB']
LEVEL_SHORTCUTS = [['ČP', 'MČR'], ['ŽB'], ['OŽ', 'OM', 'E', 'OF']]

# URL adresses
URL_CATEGORIES = 'https://oris.orientacnisporty.cz/API/?format=json&method=getEvent&id='
URL_USER_ID = 'https://oris.orientacnisporty.cz/API/?format=json&method=getUser&rgnum='
URL_RESULTS = 'https://oris.orientacnisporty.cz/API/?format=json&method=getEventResults&eventid='
URL = 'https://oris.orientacnisporty.cz/API/?'

# Splits loading - modes return values
MODE_SPLITS = 0
MODE_CATEGORIES = 1
MODE_EVENTS = 2

# Graph options
GRAPH_HEIGHT = 600
GRAPH_WIDTH = 1000
GRAPH_LEGEND_SIZE = 22
GRAPH_RUNNER_DISCIPLINES = ['Sprint', 'Krátká', 'Klasika']
GRAPH_LEVEL_TEXT = ['<b>MČR & Český Pohár & Žebříček A</b>', '<b>Žebříček B</b>', '<b>Oblastní závody & Etapové</b>']

# Pdf export settings
CELL_HEIGHT = 7.65
HEADER_CELL_HEIGHT = CELL_HEIGHT * 0.6
CELL_WIDTH = 12
INDEX_CELL_WIDTH = 35
FRONT_CELL_WIDTH = 16
FONT_SIZE = 6.8
LINE_OFFSET = INDEX_CELL_WIDTH + 3 * FRONT_CELL_WIDTH
GRAPH_SCALE = 280
