import streamlit as st
import pandas as pd
import json

# Load Data
@st.cache_data
def load_data():
    # Load curated species list
    curated_df = pd.read_csv('data/curated_species.csv')

    # Load score weights
    with open('data/score_weights.txt', 'r') as f:
        score_weights = json.load(f)

    # Load input comparison CSV
    input_df = pd.read_csv('data/sample-infile.csv')

    return curated_df, score_weights, input_df

curated_df, score_weights, input_df = load_data()

# Sidebar - Display options
st.sidebar.title("Display Options")
show_curated = st.sidebar.checkbox('Show first few lines of Curated List')
show_weights = st.sidebar.checkbox('Show Score Weights')
show_input = st.sidebar.checkbox('Show first few lines of Input CSV')

# Sidebar - Threshold Settings
st.sidebar.title("Threshold Settings")
# Radio buttons for Score Threshold and Reads Threshold with horizontal options
score_threshold = st.sidebar.radio('Score Threshold', [0, 1, 2, 3, 4], index=0, horizontal=True)
reads_threshold = st.sidebar.radio('Reads Threshold', [1, 10, 100, 1000, 10000], index=0, horizontal=True)

# Display Dat
st.title("Bacteria Data Comparison App")

if show_curated:
    st.subheader("Curated Species List (First Few Lines)")
    st.dataframe(curated_df.head())

if show_weights:
    st.subheader("Score Weights")
    st.json(score_weights)

if show_input:
    st.subheader("Input Comparison CSV (First Few Lines)")
    st.dataframe(input_df.head())

# Calculate Stats
st.subheader("Statistics")
num_rows = len(input_df)
matching_rows = input_df[input_df['#Datasets'].isin(curated_df['Species'])].shape[0]

st.write(f"Number of rows in input CSV: {num_rows}")
st.write(f"Number of rows matching the curated list of names: {matching_rows}")

# Filtering Based on Thresholds
def filter_bacteria(input_df, curated_df, score_weights, score_threshold, reads_threshold):
    # Filter based on reads threshold
    filtered_df = input_df.copy()
    location_columns = [col for col in input_df.columns if col.startswith('loc')]

    # Determine if any location's reads exceed the threshold
    filtered_df['Location Counts Above Threshold'] = filtered_df[location_columns].apply(lambda x: x[x > reads_threshold].count(), axis=1)
    filtered_df['Location Details'] = filtered_df[location_columns].apply(lambda x: {loc: count for loc, count in x.items() if count > reads_threshold}, axis=1)

    # Keep rows where location count exceeds threshold
    filtered_df = filtered_df[filtered_df['Location Counts Above Threshold'] > 0]

    # Score calculation based on weights
    matching_species = filtered_df['#Datasets'].isin(curated_df['Species'])
    filtered_df = filtered_df[matching_species]
    filtered_df['Weight Score'] = filtered_df['#Datasets'].apply(lambda x: sum(curated_df[curated_df['Species'] == x][list(score_weights.keys())].values.flatten() * list(score_weights.values())))

    # Filter based on score threshold
    filtered_df = filtered_df[filtered_df['Weight Score'] >= score_threshold]

    return filtered_df[['#Datasets', 'Location Counts Above Threshold', 'Location Details']]

filtered_bacteria = filter_bacteria(input_df, curated_df, score_weights, score_threshold, reads_threshold)

st.subheader("Filtered Bacteria List")
st.dataframe(filtered_bacteria)


