import openpolicedata as opd
import utils

def get_opd_explorer_dataset_url(state=None, source=None, table_type=None, url_type=None):
    '''Return URL that will go to default page and/or filters of OPD Explorer (https://openpolicedata.streamlit.app)
    If set, inputs state, source, and/or table_type will be appended to the URL to go to a filtered view of the OPD Explorer dataset finder page.
    If no parameters inputs, returned URL will be to the OPD Explorer dataset finder page

    Parameters
        ----------
        state : str
            Name of state. Set to None for a URL for all states, by default None
        source : str
            Name of source. This is generally the name of the municipality (i.e. Chicago, not Chicago Police Department)
            Set to None for a URL for all sources in the selected state(s) , by default None
        table_type : str
            Name of table type (such as USE OF FORCE or STOPS). Valid values can be found in the table type dropdown with no other filters set here: 
            https://openpolicedata.streamlit.app/?page=2_Find_Datasets. 
            Set to None for a URL for all table types for the selected state(s) and source(s), by default None
        url_type : str
            If set to 'local', the URL will be for running Streamlit locally: http://localhost:8501/, by default None

        Returns
        -------
        str | None
            URL if requested filter will find datasets and None if not

    '''

    url = 'https://openpolicedata.streamlit.app' if url_type!='local' else 'http://localhost:8501'

    url += '/Find_Datasets/?'

    df = opd.datasets.query()
    if state:
        df = df[df['State']==state]
        url+='&'+'state'+'='+state

    if source:
        df = df[df['SourceName']==source]
        url+='&'+'source'+'='+source

    if table_type:
        df['TableTypeGeneral'],_,_ = utils.split_tables(df['TableType'].tolist())
        df = df[df['TableTypeGeneral']==table_type]
        url+='&'+'table'+'='+table_type

    return url if len(df)>0 else None

