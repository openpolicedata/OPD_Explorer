import re
from urllib.parse import urlparse

NA_DISPLAY_VALUE = "NOT APPLICABLE"
ALL = "ALL"

def get_default(vals, default_val, required=True):
    if default_val!=0:
        default_val_index = [k for k,x in enumerate(vals) if x==default_val]
        if len(default_val_index)>0:
            default_val_index = default_val_index[0]
        elif required:
            raise ValueError(f"Unable to find requested default {default_val} in {vals}")
        else:
            default_val_index = 0
    else:
        default_val_index = 0

    return default_val_index


def split_tables(table_types):
    isstr = isinstance(table_types, str)
    if isstr:
        table_types = [table_types]

    # Table types that may be split into multiple sub-tables
    table_type_general = table_types.copy()
    table_types_sub = [None for _ in range(len(table_types))]
    for k,x in enumerate(table_types):
        if (m:=re.match(r'(.+) - (.+)$', x, re.DOTALL)):
            table_type_general[k] = m.group(1)
            table_types_sub[k] = m.group(2)

    table_type_general_sort = list(set(table_type_general))
    table_type_general_sort.sort()

    if isstr:
        table_type_general = table_type_general[0]
        table_type_general_sort = table_type_general_sort[0]
        table_types_sub = table_types_sub[0]

    return table_type_general, table_type_general_sort, table_types_sub


def get_unique_urls(urls, dataset_ids):
    if isinstance(urls, str):
        urls = [urls]
    elif isinstance(urls, pd.Series):
        urls = urls.tolist()

    if isinstance(dataset_ids, str):
        dataset_ids = [dataset_ids]
    elif isinstance(dataset_ids, pd.Series):
        dataset_ids = dataset_ids.tolist()

    unique_urls = []
    for u,d in zip(urls, dataset_ids):
        if urls.count(u)==1 or d is None:
            o = urlparse(u)
            if sum([o.hostname in x for x in urls])<2:
                # hostname is unique
                unique_urls.append(o.hostname)
            else:
                unique_urls.append(u)
        else:
            unique_urls.append(f'{u}: {d}')

    return unique_urls