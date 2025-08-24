import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict
from cube_alchemy import Hypercube

# --- Load data (AdventureWorks dummy) ---
def _clean_currency(x):
	if isinstance(x, str):
		return float(x.replace('$', '').replace(',', ''))
	return x

@st.cache_data(show_spinner=False)
def load_tables():
	import importlib.util
	from pathlib import Path

	app_dir = Path(__file__).parent
	tables_py = app_dir / 'data' / 'AdventureWorksDummy' / 'tables.py'

	tables = {}
	if tables_py.exists():
		spec = importlib.util.spec_from_file_location('aw_tables', tables_py)
		mod = importlib.util.module_from_spec(spec)
		assert spec and spec.loader
		spec.loader.exec_module(mod)  # type: ignore[attr-defined]
		raw_tables = getattr(mod, 'tables')
		for name in ['Product', 'Region', 'Reseller', 'Sales', 'Salesperson']:
			df = raw_tables[name].copy()
			for col in ['Unit Price', 'Cost']:
				if col in df.columns:
					df[col] = df[col].apply(_clean_currency)
			tables[name] = df
		return tables

	# Fallback: read CSVs in case direct import fails
	data_dir = app_dir / 'data' / 'AdventureWorksDummy' / 'csv_files'
	for csv in ['Product.csv', 'Region.csv', 'Reseller.csv', 'Sales.csv', 'Salesperson.csv']:
		path = data_dir / csv
		if path.exists():
			df = pd.read_csv(path, sep='\t')
			for col in ['Unit Price', 'Cost']:
				if col in df.columns:
					df[col] = df[col].apply(_clean_currency)
			tables[csv.replace('.csv','')] = df
	return tables

# --- Build or reuse Hypercube ---
def get_cube():
	if 'cube' not in st.session_state:
		st.session_state.cube = Hypercube(load_tables())
		_define_metrics_and_queries(st.session_state.cube)
	return st.session_state.cube

def _define_metrics_and_queries(cube: Hypercube):
	# Base metrics
	cube.define_metric(name='Revenue', expression='[Unit Price] * [Quantity]', aggregation='sum')
	cube.define_metric(name='Cost',    expression='[Cost]',                 aggregation='sum')
	cube.define_metric(name='avg Unit Price', expression='[Unit Price]',    aggregation='mean')
	cube.define_metric(name='number of Orders', expression='[SalesOrderNumber]', aggregation=lambda x: x.nunique())

	# Computed metrics (post-aggregation)
	cube.define_computed_metric(name='Margin', expression='[Revenue] - [Cost]', fillna=0)
	cube.define_computed_metric(name='Margin %', expression='100 * ([Revenue] - [Cost]) / [Revenue]')

	# Queries
	cube.define_query(
		name='Sales by Region',
		metrics=['Revenue'],
		computed_metrics=['Margin %'],
		dimensions=['Region', 'Category'],
		drop_null_dimensions=True,
		sort=[('Revenue', 'desc')]
	)

	cube.define_query(
		name='avg Unit Price by Category & Business Type',
		metrics=['avg Unit Price'],
		dimensions=['Category', 'Business Type'],
		drop_null_dimensions=True
	)

	cube.define_query(
		name='High-Margin Products (>35%)',
		metrics=['number of Orders'],
		computed_metrics=['Margin'],
		dimensions=['Product'],
		having='[Margin %] >= 35',
		drop_null_dimensions=True,
		sort=[('Margin', 'desc')]
	)

# --- UI helpers ---
def apply_filters(cube: Hypercube, criteria: Dict[str, List[str]]):
	"""Apply the exact criteria from the UI. If empty, fully reset filters."""
	cube.reset_filters('all')
	if criteria:
		cube.filter(criteria)

def bar_chart(df: pd.DataFrame, dims: List[str], measure: str, title: str):
	if df is None or df.empty:
		st.info('No data to plot.')
		return
	if len(dims) == 2:
		piv = df.pivot_table(index=dims[0], columns=dims[1], values=measure, fill_value=0)
		st.bar_chart(piv, height=360, stack=False)
	elif len(dims) == 1:
		s = df.set_index(dims[0])[measure]
		st.bar_chart(s, height=360)
	else:
		st.dataframe(df[[measure]])


# --- App ---
st.set_page_config(page_title='Cube Alchemy • AdventureWorks', layout='wide')
st.sidebar.title('AdventureWorks Explorer')
#st.caption('Minimal Streamlit app powered by cube_alchemy Hypercube')

cube = get_cube()
def _ensure_schema_fig(cube: Hypercube):
	if 'schema_fig' not in st.session_state:
		try:
			cube.visualize_graph(full_column_names=False)
			st.session_state['schema_fig'] = plt.gcf()
		except Exception as e:
			st.session_state['schema_fig'] = None
			st.warning(f'Unable to render schema graph: {e}')
_ensure_schema_fig(cube)

## Sidebar filters (choose dimensions, then values; options from Unfiltered state)
st.sidebar.header('Filters')
all_dims = cube.get_dimensions()
selected_dims = st.sidebar.multiselect('Filter dimensions', options=all_dims, key='filter_dims')

criteria: Dict[str, List[str]] = {}
for dim in selected_dims:
	try:
		vals = cube.dimensions([dim], context_state_name='Unfiltered')[dim]
		options = vals.dropna().sort_values().unique().tolist()
	except Exception:
		options = []
	picked = st.sidebar.multiselect(dim, options=options, key=f'flt_{dim}')
	if picked:
		criteria[dim] = picked

# Apply filters on every change to mirror the exact UI state
apply_filters(cube, criteria)

# Top navigation tabs
tab_schema, tab_defs, tab_visuals = st.tabs(["Schema", "Definitions", "Visuals"])

with tab_schema:
	st.subheader('Tables and relationships')
	if st.session_state.get('schema_fig') is not None:
		st.pyplot(st.session_state['schema_fig'])
	else:
		st.info('Schema graph not available.')

with tab_defs:
	st.subheader('Definitions')
	col1, col2 = st.columns(2)
	with col1:
		st.markdown('Filters (current state)')
		st.json(cube.get_filters())
		st.markdown('Metrics')
		st.json(cube.get_metrics())
	with col2:
		st.markdown('Computed Metrics')
		st.json(cube.get_computed_metrics())
		st.markdown('Queries')
		st.json(cube.get_queries())

with tab_visuals:
	# Query selection
	queries = list(cube.queries.keys())
	q = st.selectbox('Query', options=queries, index=0)
	q_def = cube.get_query(q)

	# Results
	res = cube.query(q)

	# Charts for each metric in the selected query
	st.subheader('Charts')
	dims = q_def['dimensions']
	for m in q_def['metrics'] + q_def['computed_metrics']:
		st.markdown(f'**{m}**')
		bar_chart(res, dims, m, q)

	st.subheader('Result table')
	st.dataframe(res, use_container_width=True)


