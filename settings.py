""" Default settings """
import pathlib

default_box_options = {'rows': 9,
                       'columns': 9,
                       'separator': 2}

code_column = 'Код'
weight_column = 'Weight'
default_columns = (code_column, 'st0', 'st1', 'st2', 'st3', 'st4', weight_column)
color_unpacked = (200, 10, 10, 70)      # RGBA background color for unpacked sample cell
color_packed = (10, 200, 10, 70)        # RGBA background color for packed sample cell
color_free = (10, 10, 200, 100)          # RGBA background color for free cell
color_separator = (10, 10, 10, 100)      # RGBA background color for not available cell

move_step = (1, default_box_options['columns'])             # default steps for rows moving: SHIFT, ALT
insert_many = default_box_options['columns']                # default rows amount for multi-insertion

# export parameters

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
