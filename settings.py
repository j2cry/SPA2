""" Default settings """

default_box_options = {'rows': 9,
                       'columns': 9,
                       'separator': 2}

code_column = 'Код'
weight_column = 'Weight'
default_columns = (code_column, 'st0', 'st1', 'st2', 'st3', 'st4', weight_column)
color_unpacked = (200, 10, 10, 50)      # RGBA background color for unpacked sample cell
color_packed = (10, 200, 10, 50)        # RGBA background color for packed sample cell
color_na = (10, 10, 10, 50)             # RGBA background color for not available cell

move_step = (1, default_box_options['columns'])             # default steps for rows moving: SHIFT, ALT
insert_many = default_box_options['columns']                # default rows amount for multi-insertion
