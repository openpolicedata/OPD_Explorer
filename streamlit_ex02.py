import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import copy
module_path = os.path.abspath(os.path.join('../../cjc/openpolicedata'))
sys.path.append(module_path)
import openpolicedata as opd

if 't_data' not in st.session_state:
    st.session_state['t_data'] = None

t_data = st.session_state['t_data']

#@st.cache 
@st.cache_data
def get_df():
        df = opd.datasets.query(table_type='TRAFFIC WARNINGS', state="Virginia")
        return df

df=get_df()
st.write("This is Virginia traffic warning data:")
st.write(df.head())

st.write(pd.unique(df['SourceName']))

csv_text = df.to_csv(index=False)
st.download_button('Download CSV', data = csv_text, file_name="traffic_data.csv", mime='text/csv')

source_year=st.selectbox('Year',pd.unique(df['Year']),help='Select the year to display')
#st.write('You selected: ', source_year, ' to load')
active_src=df[df['Year']==source_year].iloc[0]
#st.write(active_src)

#@st.cache(allow_output_mutation=True) 
@st.cache_data
def get_traffic_data(source_name, year, table_type, agency):
	src = opd.Source(source_name=source_name)
	t_data = src.load_from_url(year=year, table_type=table_type, agency=agency)
	return t_data

if st.button('Load and Plot Data'):
	t_data=get_traffic_data(source_name=active_src['SourceName'], year=source_year, table_type=active_src['TableType'], agency=active_src['Agency'])
	
	
	#t_data = src.load_from_url(year=source_year, table_type=active_src['TableType'].iloc[0], agency=active_src['Agency'].iloc[0])
	
 	#t_data = src.load_from_url(year=source_year, table_type=active_src['TableType'], agency=active_src['Agency'])
	
	#st.write(t_data.table.head())

	fig, ax = plt.subplots()
	mask = (t_data.table['X_Cord'] > 10) & (t_data.table['Y_Cord'] > 10) & (t_data.table['Y_Cord'] < 9.5e6)
	ax.scatter(t_data.table['X_Cord'][mask],t_data.table['Y_Cord'][mask])
	ax.set_title(f"{active_src['SourceName']} TRAFFIC WARNINGS data in {source_year}")
	ax.set_xlabel('Longitude')	
	ax.set_ylabel('Latitude')
	st.session_state['t_data'] = t_data
  	
	st.pyplot(fig)    
else:
	if t_data is not None:
		fig, ax = plt.subplots()
		mask = (t_data.table['X_Cord'] > 10) & (t_data.table['Y_Cord'] > 10) & (t_data.table['Y_Cord'] < 9.5e6)
		ax.scatter(t_data.table['X_Cord'][mask],t_data.table['Y_Cord'][mask])
		ax.set_title(f"{active_src['SourceName']} TRAFFIC WARNINGS data in {source_year}")
		ax.set_xlabel('Longitude')	
		ax.set_ylabel('Latitude')
		
		st.pyplot(fig)
    #st.write('Goodbye')
