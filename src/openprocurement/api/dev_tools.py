# -*- coding: utf-8 -*-
import os, sys


def get_fields_name(cls):
    fields_name = set(cls._fields._keys)
    fields_name.update(cls._serializables.keys())
    return fields_name


def get_roles_from_object(cls):
    fields_name = get_fields_name(cls)
    roles_keys = [role_name for role_name in cls._options.roles]
    roles = {}
    for role_name in roles_keys:
        rr = cls._options.roles[role_name]
        roles[role_name] = set([i for i in list(fields_name) if not rr(i, '')])
    return roles


def create_csv_roles(cls):
    import csv
    roles = get_roles_from_object(cls)
    fields_name = list(get_fields_name(cls))
    path_role_csv = ''
    for i in os.path.abspath(sys.modules[cls.__module__].__file__).split('/')[:-1]:
        path_role_csv += i+'/'
    with open('{0}{1}.csv'.format(path_role_csv, cls.__name__), 'wb') as csvfile:
        fields_name.insert(0, 'rolename')
        writer = csv.DictWriter(csvfile, fieldnames=fields_name)
        writer.writeheader()
        writer = csv.writer(csvfile)
        for role_name in roles:
            row = [role_name]
            for field_name in fields_name[1:]:
                if field_name in roles[role_name]:
                   row.append('1')
                else:
                    row.append('')
            writer.writerow(row)
