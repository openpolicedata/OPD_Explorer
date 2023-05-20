import math
import pandas as pd
import openpolicedata as opd


def get_years(src, table_type):
   try:
      return src.get_years(table_type)
   except:
      # Unable to get years. This data will have to be read in its entirety
      return None
   

def get_agencies(src, table_type, year):
#    try:
      return src.get_agencies(table_type, year)
#    except:
#       # Unable to get agencies. 
#       return None


def get_record_count(src, table_type, year=None, agency=None):
   try:
      return src.get_count(year=year, table_type=table_type, agency=agency)
   except:
      # Failed to get count
      return None
   

def load_data_in_batches_to_allow_timebar_update(src, table_type, year, agency=None, batch_size=10000):
    # 10000 is an arbitrary batch size. Best size depends on how often progress bar should refresh

    count = get_record_count(src, table_type, year, agency)
    if count is None:
       # Number of iterations required to load batches is unknown. 
       pass
    else:
       num_iter_for_progress_bar = math.ceil(count / batch_size)

    df_list = []
    for tbl in src.load_from_url_gen(year=year, table_type=table_type, agency=agency, nbatch=batch_size):
      # Add the DataFrame to the list (I think this is the best way to concatenate many DataFrames...)
      df_list.append(tbl.table)

      if count is None:
         # Update some sort of progress bar for unknown number of iterations
         pass
      else:
         # Update progress bar for len(tbl.table) new records
         pass
      
    return pd.concat(df_list)

if __name__ == "__main__":
   source_name = "Virginia"
   table_type = "STOPS"
   # Optional agency for multi-agency datasets (or None)
   agency="Fairfax County Police Department"

   all_datasets = opd.datasets.query()
   all_table_types = all_datasets["TableType"].unique()

   # Create a dictionary of table descriptions, we can probably improve these descriptions
   table_descriptions = {}
   for t in all_table_types:
      try:
         table_descriptions[t] = opd.defs.TableType(t).description
      except:
         pass

   src = opd.Source(source_name)

   # Get years for display for multi-year data
   # Maybe for multi-year cases, we could use the same year box as normal and have a button for the user
   # to manually request the years. When the use initially selects the dataset, it the years box could say something
   # like "Click button to fetch years". If they click the button, the years will be retrieved. This way, the user
   # won't see a delay (if they aren't actually interested in the dataset) unless they manually request the years.
   # NOTE: There are some datasets that have both single years and multi-year data. I would recommend treating these like
   # multi-year data and requiring a button push
   years = get_years(src, table_type)

   datasets = src.datasets[src.datasets["TableType"]==table_type]
   if years is None:  # The above call will only fail if years is MULTI
      # Unable to get years. Need to load in the whole table at once
      year = opd.defs.MULTI  # Use this instead of "MULTI" so we can change later if we want to
      year_in_source_table = opd.defs.MULTI
   elif years == [opd.defs.NA]:
      # How to handle None cases. Just read in the whole table.
      year = years[0]
      year_in_source_table = years[0]
   else:
      # Arbitrarily setting year to first year instead of user input
      year = years[0]
      if (datasets["Year"] == year).any():
         year_in_source_table = year
      else:
         year_in_source_table = opd.defs.MULTI
   
   ds = datasets[datasets["Year"]==year_in_source_table]

   # readme location for display
   # NOTE: If this is empty, this will not necessarily mean the readme does not exist.
   # It may be at the source_url. Currently, I have not been setting the readme equal to the source_url
   # if the data dictionary is directly in the source_url. Maybe I should put the same URL in both places?
   readme = ds["readme"]
   # Source URL for display
   # Will be implemented soon...
   # source_url = ds["source_url"]

   # Get agencies for display for multi-agency data
   # Alternatively, we could just have them always get all the agencies. This is probably the best option
   # so we don't have to think about how to handle another input
   agencies = get_agencies(src, table_type, year_in_source_table)

   # Get record count for display
   count = get_record_count(src, table_type, year, agency=agency)

   # Get a small amount of data for preview
   t = src.load_from_url(year=year, table_type=table_type, agency=agency, pbar=False, nrows = 10)
   preview = t.table
   # Display preview

   df = load_data_in_batches_to_allow_timebar_update(src, table_type, year, agency=agency)
