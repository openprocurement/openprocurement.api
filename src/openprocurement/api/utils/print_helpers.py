# -*- coding: utf-8 -*-
def delimited_printer(printing_function, delimiter):

    def print_preformatter(*args):
        message = delimiter.join(args)
        printing_function(message)

    return print_preformatter
