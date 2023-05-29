import streamlit as st
import math
import matplotlib.pyplot as plt
import pandas as pd
import copy
import openpolicedata as opd
import io


#create a global flag to say if should download or not  (default to false)  

if 'show_download' not in st.session_state:    
    print("Reset download flag")
    st.session_state['show_download'] = False
else:
    print("SKIP reset download flag")

if 'selected_rows' not in st.session_state:  
    st.session_state['selected_rows'] = None
    print(f"'selected_rows' NOT IN in st.session_state. st.session_state['selected_rows'] = {st.session_state['selected_rows']}")
else:
    selected_rows=st.session_state['selected_rows']
    print(f"'selected_rows' IN st.session_state. st.session_state['selected_rows'] = {st.session_state['selected_rows']}")
    
@st.cache_data
def get_data_catalog():
    df = opd.datasets.query()
    df = df[~df['Year'].isin(['MULTI', 'NONE'])]
    df['Year'] = df['Year'].astype(str)
    df = df.sort_values(by=["State","SourceName","TableType"])
    return df


data_catalog = get_data_catalog()
st.title('Open Police Data')


st.header('Filtered dataset')
expander_container = st.container()



with st.sidebar:
    st.header('Dataset Filters')
    selectbox_states = st.selectbox('States', pd.unique(
        data_catalog['State']), help='Select the states you want to download data for')
    print(f"selectbox_states = {selectbox_states}")
    if len(selectbox_states) == 0:
        selected_rows = copy.deepcopy(data_catalog)
        print(f"selectbox_states == 0, selected_rows = {selected_rows}")
    else:
        selected_rows = data_catalog[data_catalog['State'].isin([selectbox_states])]
        print(f"selectbox_states != 0, selected_rows = {selected_rows}")

    selectbox_sources = st.selectbox('Available sources', pd.unique(
        selected_rows['SourceName']), help='Select the sources')

    if len(selectbox_sources) == 0:
        selected_rows = copy.deepcopy(selected_rows)
        print(f"selectbox_sources == 0, selected_rows = {selected_rows}")
    else:        
        selected_rows = selected_rows[selected_rows['SourceName'].isin(
            [selectbox_sources])]
        print(f"selectbox_sources != 0, selected_rows = {selected_rows}")

    selectbox_table_types = st.selectbox('Available table types', pd.unique(
        selected_rows['TableType']), help='Select the table type')

    if len(selectbox_table_types) == 0:       
        selected_rows = copy.deepcopy(selected_rows)
        print(f"selectbox_table_types == 0, selected_rows = {selected_rows}")
    else:
        selected_rows = selected_rows[selected_rows['TableType'].isin(
            [selectbox_table_types])]
        print(f"selectbox_table_types != 0, selected_rows = {selected_rows}")

    selectbox_years = st.selectbox('Available years', pd.unique(
       selected_rows['Year']), help='Select the year')

    if len(selectbox_years) == 0:
        selected_rows = copy.deepcopy(selected_rows)
        print(f"selectbox_years == 0, selected_rows = {selected_rows}")
    else:
        selected_rows = selected_rows[selected_rows['Year'].isin([selectbox_years])]
        print(f"selectbox_years != 0, selected_rows = {selected_rows}")
        
    st.session_state['selected_rows']=selected_rows
print(f"selected_rows = {selected_rows}")



collect_help = "This collects the data from the data source such as a URL and will make it ready for download. This may take some time."

if st.session_state['show_download'] == True:
    if st.download_button('Download CSV', data=st.session_state['csv_text_output'] , file_name="selected_rows.csv", mime='text/csv'):
        st.session_state['show_download'] = False
        print('Download complete!!!!!')
        st.session_state['csv_text_output'] = None
        st.experimental_rerun()
 
else:
    if st.button('Collect data', help=collect_help):
        print(f'***source_name={selected_rows.iloc[0]["SourceName"]}, state={selected_rows.iloc[0]["State"]}')
        src = opd.Source(source_name=selected_rows.iloc[0]["SourceName"], state=selected_rows.iloc[0]["State"])        
        types = src.get_tables_types()
        print(f"types = {types}")
        years = src.get_years(table_type=types[0])
        print(f"years = {years}")
        print(f'***year={selected_rows.iloc[0]["Year"]}, table_type={selected_rows.iloc[0]["TableType"]}')
        print("Downloading data from URL")
        record_count = None
        year = int(selected_rows.iloc[0]["Year"])
        table_type = selected_rows.iloc[0]["TableType"]
        if not selected_rows.iloc[0]["DataType"] in ["CSV","Excel"]:
            with st.spinner("Retrieving record count..."):
                record_count = src.get_count(year=year, table_type=table_type)

        wait_text = "Retrieving Data..."
        if record_count is None:
            with st.spinner(wait_text):
                data_from_url = src.load_from_url(year=year, table_type=table_type).table
        else:
            df_list = []
            batch_size = 1000
            nbatches = math.ceil(record_count / batch_size)
            pbar = st.progress(0, text=wait_text)
            iter = 0
            for tbl in src.load_from_url_gen(year=year, table_type=table_type, nbatch=batch_size):
                iter+=1
                df_list.append(tbl.table)
                pbar.progress(iter / nbatches, text=wait_text)

            data_from_url = pd.concat(df_list)
        print(f"Data downloaded from URL. Total of {len(data_from_url)} rows")
        csv_text = data_from_url.to_csv(index=False)
        csv_text_output = csv_text.encode('utf-8', 'surrogateescape')
        st.session_state['csv_text_output'] = csv_text_output
        #st.dataframe(data=selected_rows)
        st.session_state['show_download'] = True
        print(f"csv_text_output len is {len(csv_text_output)}  type(csv_text_output) = {type(csv_text_output)}")
        print(f"st.session_state['selected_rows'] = {st.session_state['selected_rows']}")
        st.session_state['selected_rows']=selected_rows
        st.experimental_rerun()
    
    
show_all_datasets = False # st.checkbox('Show all datasets available')
if show_all_datasets == True:
    st.dataframe(data=data_catalog)
    
with expander_container:
    st.dataframe(data=selected_rows)

print(f"Done with rendering dataframe")