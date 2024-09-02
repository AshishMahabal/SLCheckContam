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

    return curated_df, score_weights

curated_df, score_weights = load_data()

# Function to read comparison CSV file
def load_comparison_file(uploaded_file):
    return pd.read_csv(uploaded_file)

# Sidebar - Display options
st.sidebar.title("Display Options")
show_curated = st.sidebar.checkbox('Show first few lines of Curated List')
show_weights = st.sidebar.checkbox('Show Score Weights')

# Input File Selection
st.sidebar.title("Input File")
use_default_file = st.sidebar.checkbox('Use default input file: sample-infile.csv', value=True)

if use_default_file:
    input_df = pd.read_csv('data/sample-infile.csv')
else:
    uploaded_file = st.sidebar.file_uploader("Upload a CSV file for comparison", type="csv")
    if uploaded_file is not None:
        input_df = load_comparison_file(uploaded_file)
    else:
        st.warning("Please upload a CSV file for comparison.")
        st.stop()

# Sidebar - Threshold Settings
st.sidebar.title("Threshold Settings")

# Radio buttons for Score Threshold and Reads Threshold with horizontal options
score_threshold = st.sidebar.radio('Score Threshold', [0, 1, 2, 3, 4], index=0, horizontal=True)
reads_threshold = st.sidebar.radio('Reads Threshold', [1, 10, 100, 1000, 10000], index=0, horizontal=True)

# Display Data
st.title("Bacteria Data Comparison App")

if show_curated:
    st.subheader("Curated Species List (First Few Lines)")
    st.dataframe(curated_df.head())

if show_weights:
    st.subheader("Score Weights")
    st.json(score_weights)

st.subheader("Input Comparison CSV (First Few Lines)")
st.dataframe(input_df.head())

# Calculate Stats
num_rows = len(input_df)
matching_rows_df = input_df[input_df['#Datasets'].isin(curated_df['Species'])]
matching_rows = matching_rows_df.shape[0]

def calculate_threshold_stats(matching_rows_df, reads_threshold):
    location_columns = [col for col in matching_rows_df.columns if col.startswith('loc')]
    thresh_rows = matching_rows_df[location_columns].apply(lambda x: any(x > reads_threshold), axis=1).sum()
    return thresh_rows

thresh_rows = calculate_threshold_stats(matching_rows_df, reads_threshold)

# Display Stats Table
st.subheader("Statistics")
st.write(f"**Threshold: Score {score_threshold}, Count {reads_threshold}**")
stats_df = pd.DataFrame({
    'Num': [num_rows],
    'Matched': [matching_rows],
    'Thresh': [thresh_rows]
})
st.table(stats_df)

# Filtering Based on Thresholds
def filter_bacteria(matching_rows_df, curated_df, score_weights, score_threshold, reads_threshold):
    # Filter based on reads threshold
    filtered_df = matching_rows_df.copy()
    location_columns = [col for col in matching_rows_df.columns if col.startswith('loc')]

    # Determine if any location's reads exceed the threshold
    filtered_df['Num loc'] = filtered_df[location_columns].apply(lambda x: x[x > reads_threshold].count(), axis=1)
    filtered_df['Locations'] = filtered_df[location_columns].apply(lambda x: {loc: count for loc, count in x.items() if count > reads_threshold}, axis=1)

    # Keep rows where location count exceeds threshold
    filtered_df = filtered_df[filtered_df['Num loc'] > 0]

    # Score calculation based on weights
    filtered_df['Weight Score'] = filtered_df['#Datasets'].apply(lambda x: sum(curated_df[curated_df['Species'] == x][list(score_weights.keys())].values.flatten() * list(score_weights.values())))

    # Filter based on score threshold
    filtered_df = filtered_df[filtered_df['Weight Score'] >= score_threshold]

    return filtered_df[['#Datasets', 'Num loc', 'Locations']].rename(columns={'#Datasets': 'Species'})

filtered_bacteria = filter_bacteria(matching_rows_df, curated_df, score_weights, score_threshold, reads_threshold)

st.subheader("Filtered Bacteria List")
st.dataframe(filtered_bacteria)
