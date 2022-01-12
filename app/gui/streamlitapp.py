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
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'


def load_page_splits(entity: pandas.DataFrame, category: str):
    """Creates page layout for a DataFrame ``entity`` with information about event and ``category`` at the top
    Layout consists of graph with control elements and two DataFrames, with total time and with split time"""
    category_text = ''
    if category in event_categories:
        for i in event_info:
            if i != '':
                st.write(i)
        category_text = 'Category: ' + event_categories[category]
        st.markdown('Category: __' + event_categories[category] + '__')
    limit = st.select_slider(
        'Competitors limit', options=constants.RUNNERS_LIMIT
    )
    runners = st.multiselect(
        "Select runners for comparing with winner", options=category_runners
    )
    show_relative = st.checkbox("Show relative compare", value=False)

    filtered = loader.filter_runner_id(runners)
    if filtered:
        limit = 'none'
    st.write(loader.load_split_graphs(entity, show_relative, limit, filtered))
    st.write('Total times and standings')
    st.dataframe(loader.crop_and_style(entity, limit, filtered, False))
    st.write('Split times and standings')
    st.dataframe(loader.crop_and_style(entity, limit, filtered, True))
    export_as_pdf = st.button("Export Analysis")
    if export_as_pdf:
        pdf = pdf_creator.pdf_with_graph(entity, limit, category_text, filtered)
        html = create_download_link(pdf.output(dest="S").encode("latin-1"), "analysis")
        st.markdown(html, unsafe_allow_html=True)


def splits_handle_error(error: str, mask: str):
    if error == 'not found':
        st.markdown("No results for mask {__" + mask + "__} found")
        st.markdown("_Maybe filter conditions are too strict_")
    elif 'unsupported' in error:
        st.markdown("Not possible: __" + error + "__")
    else:
        st.markdown("Entity error: {__" + error + "__} is invalid")
        if 'category' in error:
            st.markdown("_Maybe you misspelled category ID number or haven't filled event ID when using category name_")


def splits_layout():
    """Creates sidebar layout for split analysis"""
    st.sidebar.title("Insert category name...")
    category = st.sidebar.text_input("Category name:")
    st.sidebar.title("...and insert event ID...")
    event = st.sidebar.text_input("Event ID:")
    st.sidebar.title("...or select year")
    event_year = st.sidebar.selectbox(
        "Select year of event", options=constants.YEARS
    )
    show_advanced = st.sidebar.checkbox("Show advanced filtering", value=False)
    mask = ''
    levels = []
    all_sports = False
    all_events = False
    if show_advanced:
        mask = st.sidebar.text_input("Event name mask:")
        levels = st.sidebar.multiselect(
            "Select event level", options=constants.EVENT_LEVELS
        )
        all_sports = st.sidebar.checkbox("Show all sports (not just Foot-O)", value=False)
        all_events = st.sidebar.checkbox("Show unofficial events", value=False)
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
        "Select analyser mode", options=['Split Analyser', 'Runner Analyser']
    )
    st.sidebar.markdown("""---""")
    if mode == 'Split Analyser':
        category, event, event_year, mask, levels, all_sports, all_events = splits_layout()

        if event != '' and category != '':
            ctg = loader.get_category_id_from_name(category, event)
            if 'event' in ctg:
                st.markdown("Entity error: {__" + ctg + "__} is invalid")
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
                    st.markdown('_Select category name_')
                else:
                    st.markdown('_Select event ID_')
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
