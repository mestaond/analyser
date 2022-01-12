import base64
import pandas
import streamlit as st

from app.gui import pdf_creator
from app.src import loader
from app.src import constants

event_id = ''
event_info = []
event_categories = dict()
category_runners = []
runner_info = []


# inspired by Streamlit forum
def create_download_link(val, filename):
    """Simple function, that creates link for downloading file
    Not my work, borrowed from StackOverflow"""
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Stáhnout</a>'


def load_page_splits(entity: pandas.DataFrame, category: str):
    """Creates page layout for a DataFrame ``entity`` with information about event and ``category`` at the top
    Layout consists of graph with control elements and two DataFrames, with total time and with split time"""
    category_text = ''
    if category in event_categories:
        for i in event_info:
            if i != '':
                st.write(i)
        category_text = 'Kategorie: ' + event_categories[category]
        st.markdown('Kategorie: __' + event_categories[category] + '__')
    limit = st.select_slider(
        'Max počet závodníků', options=constants.RUNNERS_LIMIT
    )
    runners = st.multiselect(
        "Výběr závodníků k porovnání s vítězem", options=category_runners
    )
    show_relative = st.checkbox("Relativní porovnání", value=False)

    filtered = loader.filter_runner_id(runners)
    if filtered:
        limit = 'none'
    st.write(loader.load_split_graphs(entity, show_relative, limit, filtered))
    st.write('Celkové časy a umístění')
    st.dataframe(loader.crop_and_style(entity, limit, filtered, False))
    st.write('Časy a umístění podle mezičasů')
    st.dataframe(loader.crop_and_style(entity, limit, filtered, True))
    export_as_pdf = st.button("Exportovat")
    if export_as_pdf:
        pdf = pdf_creator.pdf_with_graph(entity, limit, category_text, filtered)
        html = create_download_link(pdf.output(dest="S").encode("latin-1"), "analysis")
        st.markdown(html, unsafe_allow_html=True)


def splits_handle_error(error: str, mask: str):
    if error == 'not found':
        st.markdown("Žádné výsledky pro filtr {__" + mask + "__} nenalezeny")
        st.markdown("_Možná jsou podmínky příliš přísné_")
    elif 'unsupported' in error:
        st.markdown("Nepodporováno: __" + error + "__")
    else:
        st.markdown("Chyba: {__" + error + "__} je neplatné")
        if 'kategorie' in error:
            st.markdown("_Možná je v názvu kategorie překlep_")


def splits_layout():
    """Creates sidebar layout for split analysis"""
    st.sidebar.title("Zadejte jméno kategorie...")
    category = st.sidebar.text_input("Jméno kategorie:")
    st.sidebar.title("...a zadejte ID závodu...")
    event = st.sidebar.text_input("ID závodu:")
    st.sidebar.title("...nebo vyberte sezónu")
    event_year = st.sidebar.selectbox(
        "Vyberte sezónu", options=constants.YEARS
    )
    show_advanced = st.sidebar.checkbox("Pokročilé filtry", value=False)
    mask = ''
    levels = []
    all_sports = False
    all_events = False
    if show_advanced:
        mask = st.sidebar.text_input("Jméno závodu obsahuje:")
        levels = st.sidebar.multiselect(
            "Úroveň závodu", options=constants.EVENT_LEVELS
        )
        all_sports = st.sidebar.checkbox("Zobrazit všechny sporty (ne jen pěší OB)", value=False)
        all_events = st.sidebar.checkbox("Zobrazit neoficiální akce", value=False)
    return category, event, event_year, mask, levels, all_sports, all_events


def load_page_runner(entity: pandas.DataFrame):
    """Creates page layout for ``entity`` with event results and then creates graphs for 3 event levels"""
    for i in runner_info:
        st.markdown(i)
    st.table(entity)
    for x in range(0, 3):
        graph = loader.load_runner_graphs(entity, x)
        if type(graph) != str:
            st.write(graph)


def main():
    st.set_page_config(page_title='ORIS data analyser', layout='wide', initial_sidebar_state='auto')
    st.title('ORIS data analyser')

    st.sidebar.title("Select analyser mode")
    mode = st.sidebar.selectbox(
        "Režim analýzy", options=['Analýza výsledků', 'Analýza závodníka']
    )
    st.sidebar.markdown("""---""")
    if mode == 'Analýza výsledků':
        category, event, event_year, mask, levels, all_sports, all_events = splits_layout()

        if event != '' and category != '':
            ctg = loader.get_category_id_from_name(category, event)
            if 'event' in ctg:
                st.markdown("Chyba: {__" + error + "__} je neplatné")
            if ctg != 'err':
                category = ctg
        load_mode, entity = loader.load_splits(category, event, event_year, mask, levels, all_sports, all_events)
        if type(entity) is str:
            splits_handle_error(entity, mask)
        else:
            if load_mode == constants.MODE_SPLITS:
                load_page_splits(entity, category)
            else:
                if load_mode == constants.MODE_CATEGORIES:
                    for i in event_info:
                        if i != '':
                            st.write(i)
                    st.markdown('_Vyberte kategorii_')
                else:
                    st.markdown('_Vyberte ID závodu_')
                st.table(entity)
    else:
        st.sidebar.title("Insert runner registration number")
        reg_no = st.sidebar.text_input("RegNo (format XXX1111, where XXX is club shortcut):")
        years = st.sidebar.selectbox(
            "Select year to analyze", options=constants.YEARS
        )
        if reg_no == '':
            st.markdown("_Insert registration number_")
            st.markdown("_Note: Due to multi-request calling may data loading take little longer (depends on number of events, in average 1s per event)_")
        else:
            entity = loader.load_runner(reg_no, years)
            if type(entity) is str:
                st.markdown("Entity error: {__" + entity + "__} is invalid")
            else:
                load_page_runner(entity)
