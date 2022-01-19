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
    category_text = category
    if category in event_categories:
        for i in event_info:
            if i != '':
                st.write(i)
        category_text = event_categories[category]
        st.markdown('Kategorie: __' + event_categories[category] + '__')
    limit = st.select_slider(
        'Max počet závodníků', options=constants.RUNNERS_LIMIT
    )
    runners = st.multiselect(
        "Výběr závodníků k porovnání s vítězem", options=category_runners
    )
    st.markdown("__Zobrazení grafu__")
    show_relative = st.checkbox("Relativní porovnání dle ztráty", value=False, help="Výchozí zobrazení dle času od startu")

    filtered = loader.filter_runner_id(runners)
    if filtered:
        limit = 'none'
    st.write(loader.load_split_graphs(entity, show_relative, limit, filtered))
    st.markdown('__Celkové časy a umístění__')
    st.dataframe(loader.crop_and_style(entity, limit, filtered, False))
    st.markdown('__Časy a umístění podle mezičasů__')
    st.dataframe(loader.crop_and_style(entity, limit, filtered, True))
    export_as_pdf = st.button("Exportovat", help="Vygeneruje se pdf, které je poté nutné stáhnout kliknutím na odkaz")
    if export_as_pdf:
        pdf = pdf_creator.pdf_with_graph(entity, limit, 'Kategorie: ' + category_text, filtered)
        html = create_download_link(pdf.output(dest="S").encode("latin-1"), "analysis_" + event_id + "_" + category_text)
        st.markdown(html, unsafe_allow_html=True)


def splits_handle_error(error: str, mask: str):
    if error == 'not found':
        st.error("Žádné výsledky pro filtr { " + mask + " } nenalezeny")
        st.markdown("_Možná jsou podmínky příliš přísné_")
    elif 'unsupported' in error:
        st.error("Nepodporováno: " + error + "")
    else:
        show_error(error)
        if 'kategorie' in error:
            st.markdown("_Možná je v názvu kategorie překlep_")
            if event_categories:
                st.write("Platné kategorie:")
                vals = [*event_categories.values()]
                half = len(vals) // 2
                col1, col2 = st.columns(2)
                with col1:
                    st.table(pandas.DataFrame(vals[:half]).assign(hack='').set_index('hack'))
                with col2:
                    st.table(pandas.DataFrame(vals[half:]).assign(hack='').set_index('hack'))


def splits_layout():
    """Creates sidebar layout for split analysis"""
    st.sidebar.header("Zadejte ID závodu a kategorii...")
    event = st.sidebar.text_input("ID závodu:", help="Po zadání ID se zobrazí kategorie")
    category = st.sidebar.text_input("Jméno kategorie:")
    st.sidebar.header("...nebo vyberte sezónu")
    event_year = st.sidebar.selectbox(
        "Sezóna:", options=constants.YEARS
    )
    show_advanced = st.sidebar.checkbox("Pokročilé filtry", value=False)
    mask = ''
    levels = []
    all_sports = False
    all_events = False
    if show_advanced:
        st.sidebar.markdown("---")
        mask = st.sidebar.text_input("Vyhledání dle jména:")
        levels = st.sidebar.multiselect(
            "Úroveň závodu:", options=constants.EVENT_LEVELS
        )
        all_sports = st.sidebar.checkbox("Zobrazit všechny sporty", value=False, help="Výchozí nastavení je pouze OB")
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


def show_error(error: str):
    st.error("Chyba: [ " + error + " ] je neplatné")


def main():
    st.set_page_config(page_title='ORIS data analyser', layout='wide', initial_sidebar_state='auto')
    st.title('ORIS data analyser')

    st.sidebar.title("Vyberte režim analýzy")
    mode = st.sidebar.selectbox(
        "Režim analýzy", options=['Analýza výsledků', 'Analýza závodníka']
    )
    st.sidebar.markdown("""---""")
    if mode == 'Analýza výsledků':
        category, event, event_year, mask, levels, all_sports, all_events = splits_layout()

        if event != '' and category != '':
            ctg = loader.get_category_id_from_name(category, event)
            if 'event' in ctg:
                show_error(category)
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
                    st.info('Vyberte kategorii')
                else:
                    st.info('Vyberte ID závodu')
                st.table(entity)
    else:
        st.sidebar.header("Vyberte rok a zadejte registrační číslo")
        years = st.sidebar.selectbox(
            "Sezóna", options=constants.YEARS
        )
        reg_no = st.sidebar.text_input("Registrační číslo:", help="Formát ABC1234, kde ABC je zkratka klubu")
        if reg_no == '':
            st.info("Zadejte registrační číslo")
            st.markdown("_Pozn.: Načítání stránky bude trvat delší dobu (záleží na počtu závodů, v průměru 1s na závod)_")
        else:
            entity = loader.load_runner(reg_no, years)
            if type(entity) is str:
                if 'error' in entity:
                    st.error("Chyba: žádné závody pro závodníka [ " + reg_no + " ] v sezóně [ " + years + " ]")
                else:
                    show_error(entity)
            else:
                load_page_runner(entity)

    st.markdown("---")
    st.markdown("_Autor: Ondřej Měšťan (semetrální práce z předmětu BI-PYT na ČVUT FIT)_")
    st.markdown(f'_Kód je veřejný na mém <a href="https://github.com/mestaond/analyser">GitHubu</a>_', unsafe_allow_html=True)
    st.markdown(f'_Chyby a připomínky pište na mail: <a href="mailto:mestanondrej@seznam.cz">mestanondrej@seznam.cz</a>_', unsafe_allow_html=True)
