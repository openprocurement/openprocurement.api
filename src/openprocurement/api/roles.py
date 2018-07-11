import os
from schematics.transforms import export_loop, whitelist
import csv, os


class RolesFromCsv(dict):

    def __init__(self, path, relative_to=__file__):
        super(RolesFromCsv, self).__init__(())
        self.base_dir = os.path.dirname(os.path.abspath(relative_to))
        with open(os.path.join(self.base_dir, path)) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self[row['rolename']] = whitelist(*[k for k in row if k != 'rolename' and row[k]])
