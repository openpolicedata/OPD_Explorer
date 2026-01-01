import pytest
import openpolicedata as opd

import utils

@pytest.mark.parametrize("table",
                         [opd.defs.TableType.COMPLAINTS_SUBJECTS_OFFICERS, 
                          opd.defs.TableType.COMPLAINTS_BODY_WORN_CAMERA,
                          opd.defs.TableType.COMPLAINTS_SUBJECTS,
                          opd.defs.TableType.SHOOTINGS_SUBJECTS,
                          opd.defs.TableType.USE_OF_FORCE_SUBJECTS_OFFICERS])
def test_split_tables_split(table):
    table = str(table)

    table_type_general, table_type_general_sort, table_types_sub = utils.split_tables(table)

    loc = table.find(' - ')
    assert table_type_general==table[:loc]
    assert table_type_general_sort==table_type_general
    assert table_types_sub==table[loc+3:]


@pytest.mark.parametrize("table",
                         [opd.defs.TableType.COMPLAINTS, 
                          opd.defs.TableType.CALLS_FOR_SERVICE,
                          opd.defs.TableType.SHOOTINGS])
def test_split_tables_nosplit(table):
    table = str(table)

    table_type_general, table_type_general_sort, table_types_sub = utils.split_tables(table)

    assert table_type_general==table
    assert table_type_general_sort==table_type_general
    assert table_types_sub==None


def test_split_tables_list():
    tables = [str(opd.defs.TableType.SHOOTINGS_INCIDENTS), str(opd.defs.TableType.ARRESTS)]

    table_type_general, table_type_general_sort, table_types_sub = utils.split_tables(tables)

    loc = tables[0].find(' - ')

    assert table_type_general==[tables[0][:loc], tables[1]]
    assert table_type_general_sort==[tables[1], tables[0][:loc]]
    assert table_types_sub==[tables[0][loc+3:], None]


def test_get_default_0():
    assert utils.get_default([], 0)==0


def test_get_default_not_found_not_required():
    assert utils.get_default([], 'test', required=False)==None


def test_get_default_not_found_required():
    with pytest.raises(ValueError):
        utils.get_default([], 'test')


def test_get_default_found():
    assert utils.get_default(['wrong', 'test'], 'test', required=False)==1

def test_get_unique_urls_same_url():
    urls = ['www.test.com','www.test.com']
    ids = ['1','2']

    u = utils.get_unique_urls(urls, ids)

    assert u == [f'{x}: {y}' for x,y in zip(urls,ids)]

def test_get_unique_urls_same_website():
    urls = ['https://www.test.com/1','www.test.com/2']
    ids = ['1','2']

    u = utils.get_unique_urls(urls, ids)

    assert u == urls


def test_get_unique_urls_different_websites():
    urls = ['https://www.test.com/1','www.nottest.com/2']
    ids = ['1','2']

    u = utils.get_unique_urls(urls, ids)

    assert u == ['test.com', 'nottest.com']