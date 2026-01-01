

def get_widget(items, label, required=True):
    result = [x for x in items if x.label==label]
    assert not required or len(result)!=0, f'No results found for label {label}'
    assert len(result)<2, f'Multiple results found for label {label}'

    return result[0] if len(result)>0 else None


def get_state_filter(app):
    return get_widget(app.sidebar.selectbox, 'States')

def get_source_filter(app):
    return get_widget(app.sidebar.selectbox, 'Sources')

def get_table_filter(app):
    return get_widget(app.sidebar.selectbox, 'Table Types')

def get_year_filter(app):
    return get_widget(app.sidebar.selectbox, 'Years')