import pathlib

from additional import ItemSelection

""" Default settings """
save_path = pathlib.Path().home().joinpath('Рабочий стол')

default_box_options = {'rows': 9,
                       'columns': 9,
                       'separator': 2}

code_column = 'Код'
weight_column = 'Weight'
position_columns = ['st0', 'st1', 'st2', 'st3', 'st4']
default_columns = (code_column, *position_columns, weight_column)
color_unpacked = (200, 10, 10, 70)      # RGBA background color for unpacked sample cell
color_packed = (10, 200, 10, 70)        # RGBA background color for packed sample cell
color_free = (10, 10, 200, 100)          # RGBA background color for free cell
color_separator = (10, 10, 10, 100)      # RGBA background color for not available cell

move_step = (1, default_box_options['columns'])             # default steps for rows moving: SHIFT, ALT
insert_many = default_box_options['columns']                # default rows amount for multi-insertion

# export parameters
column_width = 16
# export Excel styles
export_style_border = {
    'border': 1,
}

export_style_common = {
    'align': 'center',
    'valign': 'vcenter',
}

export_style_headers = {
    **export_style_common,
    'font': 'Arial',
    'bold': True,
}

export_style_cells = {
    **export_style_common,
    'font': 'Courier New',
    'text_wrap': True,
}

use_model = 'model-ru'

acceptable_words = {
    'ноль':         '0',
    'один':         '1',
    'два':          '2',
    'три':          '3',
    'четыре':       '4',
    'пять':         '5',
    'шесть':        '6',
    'восемь':       '8',
    'семь':         '7',
    'девять':       '9',

    'двадцать ':    '2',
    'тридцать ':    '3',
    'сорок ':       '4',
    'десят ':       '',
    'дцать':        '',
    'и ':           '',
    'утка':         'Не надо недооценивать силу утки!',
}

acceptable_commands = {
    'назад':    ItemSelection.PREVIOUS,
    'дальше':   ItemSelection.NEXT,
    'конец': -1,
}
