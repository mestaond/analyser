import datetime
import tempfile
import fpdf
import pandas
from fpdf import FPDF
from app.gui import streamlitapp as sapp
from app.src import loader
from app.src import constants


def cut_graph_limit(limit: str, filtered: list) -> str:
    """Gets limit value and cuts it to 22 (graph legend size) or crop (max 22 filtered runners)"""
    if filtered:
        limit = 'crop'
    elif limit == 'none':
        limit = '22'
    elif int(limit) > constants.GRAPH_LEGEND_SIZE:
        limit = '22'
    return limit


def get_relative_data(data: pandas.DataFrame, show_relative: bool) -> (pandas.DataFrame, str):
    """Reduces dataframe to splits_only or total_time_only and with it return appropriate header"""
    if show_relative:
        return loader.crop_dataframe(data, True), 'Split times and standings'
    return loader.crop_dataframe(data, False), 'Total times and standings'


def add_table(pdf: fpdf.FPDF, data: pandas.DataFrame, show_relative: bool, to_color: list):
    """Creates a table with times and standings on a new page (or more for many runners), displays all of them
    Table will contain absolute times if show_relative=False or split times if show_relative=True
    When course has more than 15+finish controls, then cell will be narrower to fit on one page"""
    pdf.add_page(orientation='L')
    df, label = get_relative_data(data, show_relative)
    pdf.set_font('DejaVu', 'B', 10)
    pdf.write(5, label)
    pdf.ln(7)
    front, times, positions = loader.shrink_table(df)
    coef = 1
    cell_cnt = len(times.columns.to_list())
    if cell_cnt > 16:
        coef = 16 / cell_cnt
    pdf.set_font('DejaVu', 'B', constants.FONT_SIZE)
    pdf.cell(constants.INDEX_CELL_WIDTH, constants.HEADER_CELL_HEIGHT, '', 1, 0, 'C')
    for x in front.columns.to_list():
        pdf.cell(constants.FRONT_CELL_WIDTH, constants.HEADER_CELL_HEIGHT, x, 1, 0, 'C')
    for x in times.columns.to_list():
        pdf.cell(constants.CELL_WIDTH * coef, constants.HEADER_CELL_HEIGHT, x, 1, 0, 'C')
    pdf.ln(constants.HEADER_CELL_HEIGHT)
    for i in range(0, len(df)):
        pdf.set_font('DejaVu', 'CB', constants.FONT_SIZE)
        name = df.index.to_list()[i]
        if str(front.loc[name, 'RegNo']) in to_color:
            is_colored = True
        else:
            is_colored = False
        pdf.cell(constants.INDEX_CELL_WIDTH, constants.CELL_HEIGHT, '%s' % name, 1, 0, 'C', is_colored)
        pdf.set_font('DejaVu', '', constants.FONT_SIZE)
        for x in front.columns.to_list():
            pdf.cell(constants.FRONT_CELL_WIDTH, constants.CELL_HEIGHT, '%s' % (str(front.loc[name, x])), 1, 0, 'C', is_colored)
        pdf.set_font('DejaVu', '', constants.FONT_SIZE * coef)
        for x in times.columns.to_list():
            pdf.cell(constants.CELL_WIDTH * coef, constants.CELL_HEIGHT / 2, '%s' % (str(times.loc[name, x])), 1, 0, 'C', is_colored)
        pdf.ln(constants.CELL_HEIGHT / 2)
        pdf.cell(constants.LINE_OFFSET)
        for x in positions.columns.to_list():
            text = str(positions.loc[name, x])
            pdf.cell(constants.CELL_WIDTH * coef, constants.CELL_HEIGHT / 2, '%s' % text, 1, 0, 'C', is_colored)
        pdf.ln(constants.CELL_HEIGHT / 2)
    return pdf


def get_rows_to_color(filtered: list, limit: str, all_runners: list):
    """Returns array of RegNo of runners, that should be highlighted"""
    if limit == 'crop':
        return filtered
    if limit == 'none':
        return []
    lim = int(limit)
    if lim > len(all_runners):
        return all_runners
    return all_runners[:lim]


def pdf_with_graph(data: pandas.DataFrame, limit: str, category_text: str, filtered: list) -> fpdf.FPDF:
    """Creates a pdf file for given dataframe:
    First page contains some information, then there are two similar sections, each with graph and table
    One section displays total time, the other relative split time"""
    pdf = FPDF()
    pdf.add_page(orientation='P')
#     pdf.image('./app/fonts/Orienteering_symbol.png', 60, 20, 100)
#     pdf.ln(120)
    pdf.add_font('DejaVu', '', './app/fonts/DejaVuSansMono.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', './app/fonts/DejaVuSansMono-Bold.ttf', uni=True)
    pdf.add_font('DejaVu', 'CB', './app/fonts/DejaVuSansCondensed-Bold.ttf', uni=True)
    pdf.set_fill_color(255, 255, 128)
    pdf.set_font('DejaVu', '', 20)
    pdf.write(10, "Split analysis")
    pdf.ln(10)
    pdf.ln(10)
    pdf.set_font('DejaVu', '', 14)

    if category_text != '':
        for x in sapp.event_info:
            pdf.write(5, x)
            pdf.ln(5)
            pdf.ln(5)
        pdf.write(5, category_text)
        pdf.ln(5)
        pdf.ln(5)
    timestamp = datetime.datetime.now()
    timestamp_str = timestamp.strftime("%d-%b-%Y %H:%M:%S")
    pdf.write(5, 'Exported at: ' + timestamp_str)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        pdf.add_page(orientation='L')
        limit = cut_graph_limit(limit, filtered)
        graph = loader.load_split_graphs(data, False, limit, filtered)
        graph.write_image(tmpfile.name, format="png")
        pdf.image(tmpfile.name, 10, 10, constants.GRAPH_SCALE)

    all_runners = data['RegNo'].to_list()
    to_color = get_rows_to_color(filtered, limit, all_runners)
    pdf = add_table(pdf, data, False, to_color)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        pdf.add_page(orientation='L')
        graph = loader.load_split_graphs(data, True, limit, filtered)
        graph.write_image(tmpfile.name, format="png")
        pdf.image(tmpfile.name, 10, 10, constants.GRAPH_SCALE)

    pdf = add_table(pdf, data, True, to_color)
    return pdf
