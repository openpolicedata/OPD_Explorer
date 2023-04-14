import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import copy
module_path = os.path.abspath(os.path.join('../../cjc/openpolicedata'))
sys.path.append(module_path)
import openpolicedata as opd


# 
if 't_data' not in st.session_state:
    st.session_state['t_data'] = None

t_data = st.session_state['t_data']

#@st.cache 
@st.cache_data
def get_data_catalog():
        df = opd.datasets.query()
        return df

#@st.cache(allow_output_mutation=True) 
@st.cache_data
def get_traffic_data(source_name, year, table_type, agency):
	src = opd.Source(source_name=source_name)
 
	t_data = src.load_from_url(year=year, table_type=table_type, agency=agency)
	return t_data


data_catalog=get_data_catalog()

st.header('List of datasets to download')
expander_container = st.container()

with st.sidebar:
	multiselect_states=st.multiselect('States',pd.unique(data_catalog['State']),help='Select the states you want to download data for')
	if len(multiselect_states)==0:
		# make a copy of data_catalog	
		selected_rows = copy.deepcopy(data_catalog)
	else:
		selected_rows = data_catalog[data_catalog['State'].isin(multiselect_states)]

	multiselect_sources=st.multiselect('Available sources',pd.unique(pd.unique(selected_rows['SourceName'])),help='Select the sources')

	if len(multiselect_sources)==0:
		# make a copy of data_catalog pandas dataframe
		selected_rows = copy.deepcopy(selected_rows)
	else:
		# todo filter selected_rows by State and SourceName	
		selected_rows = selected_rows[selected_rows['SourceName'].isin(multiselect_sources)]

	multiselect_table_types=st.multiselect('Available table types',pd.unique(pd.unique(selected_rows['TableType'])),help='Select the table type')

	if len(multiselect_table_types)==0:
		# make a copy of data_catalog pandas dataframe
		selected_rows = copy.deepcopy(selected_rows)
	else:
		# todo filter selected_rows by State and SourceName	
		selected_rows = selected_rows[selected_rows['TableType'].isin(multiselect_table_types)]

	multiselect_years=st.multiselect('Available years',pd.unique(pd.unique(selected_rows['Year'])),help='Select the year')

	if len(multiselect_years)==0:
		# make a copy of data_catalog pandas dataframe
		selected_rows = copy.deepcopy(selected_rows)
	else:
		# todo filter selected_rows by State and SourceName	
		selected_rows = selected_rows[selected_rows['Year'].isin(multiselect_years)]

	csv_text = selected_rows.to_csv(index=False)
	st.download_button('Download CSV', data = csv_text, file_name="selected_rows.csv", mime='text/csv')


with expander_container:
	st.dataframe(data=selected_rows)

# st.write(pd.unique(df['SourceName']))

# csv_text = df.to_csv(index=False)
# st.download_button('Download CSV', data = csv_text, file_name="traffic_data.csv", mime='text/csv')

# #st.write('You selected: ', source_year, ' to load')
# 	# below IndexError: single positional indexer is out-of-bounds
# df_active_years=df[df['Year'].isin(source_years)]
# if len(source_years)==0:
# 	pass
# else:
# 	active_src = df[df['Year'].isin(source_years)].iloc[0]
# 	if st.button('Load and Plot Data'):
# 		t_data=get_traffic_data(source_name=active_src['SourceName'], year=source_years, table_type=active_src['TableType'], agency=active_src['Agency'])
		
		
# 		#t_data = src.load_from_url(year=source_year, table_type=active_src['TableType'].iloc[0], agency=active_src['Agency'].iloc[0])
		
# 		#t_data = src.load_from_url(year=source_year, table_type=active_src['TableType'], agency=active_src['Agency'])
		
# 		#st.write(t_data.table.head())

# 		fig, ax = plt.subplots()
# 		mask = (t_data.table['X_Cord'] > 10) & (t_data.table['Y_Cord'] > 10) & (t_data.table['Y_Cord'] < 9.5e6)
# 		ax.scatter(t_data.table['X_Cord'][mask],t_data.table['Y_Cord'][mask])
# 		ax.set_title(f"{active_src['SourceName']} TRAFFIC WARNINGS data in {source_years}")
# 		ax.set_xlabel('Longitude')	
# 		ax.set_ylabel('Latitude')
# 		st.session_state['t_data'] = t_data
		
# 		st.pyplot(fig)    
# 	else:
# 		if t_data is not None:
# 			fig, ax = plt.subplots()
# 			mask = (t_data.table['X_Cord'] > 10) & (t_data.table['Y_Cord'] > 10) & (t_data.table['Y_Cord'] < 9.5e6)
# 			ax.scatter(t_data.table['X_Cord'][mask],t_data.table['Y_Cord'][mask])
# 			ax.set_title(f"{active_src['SourceName']} TRAFFIC WARNINGS data in {source_years}")
# 			ax.set_xlabel('Longitude')	
# 			ax.set_ylabel('Latitude')
			
# 			st.pyplot(fig)
# 		#st.write('Goodbye')
