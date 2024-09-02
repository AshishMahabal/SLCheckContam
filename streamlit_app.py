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
        default_score_weights = json.load(f)

    return curated_df, default_score_weights

curated_df, default_score_weights = load_data()

# Function to read comparison CSV file
def load_comparison_file(uploaded_file):
    return pd.read_csv(uploaded_file)

# Function to read custom weights file
def load_weights_file(uploaded_file):
    return json.load(uploaded_file)

# Sidebar - Display options
st.sidebar.title("Display Options")
show_curated = st.sidebar.checkbox('Show first few lines of Curated List')

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

# Sidebar - Contam Weights settings
st.sidebar.title("Contam Weights")

# Initialize weights with defaults
if 'score_weights' not in st.session_state:
    st.session_state['score_weights'] = default_score_weights.copy()

weights_expander = st.sidebar.expander("Adjust Contam Weights", expanded=False)

with weights_expander:
    st.write("Adjust the weights for each property.")

    # Create form elements for each weight
    weight_inputs = {}
    for key in st.session_state['score_weights'].keys():
        weight_inputs[key] = st.number_input(f"Weight for {key}", min_value=0, max_value=1, value=st.session_state['score_weights'][key])

    # Update the weights from the input fields
    for key in st.session_state['score_weights'].keys():
        st.session_state['score_weights'][key] = weight_inputs[key]

    # Restore default weights button
    if st.button("Restore Default Weights"):
        # Reset to default weights
        st.session_state['score_weights'] = default_score_weights.copy()
        # Trigger a rerun to reset input fields
        st.rerun()

    # Option to upload custom weights file
    st.write("Upload a custom weights file (JSON format).")
    custom_weights_file = st.file_uploader("Upload a JSON file for weights", type="json")
    if custom_weights_file is not None:
        st.session_state['score_weights'] = load_weights_file(custom_weights_file)
        st.rerun()

# Sidebar - Threshold Settings
st.sidebar.title("Threshold Settings")

# Radio buttons for Score Threshold and Reads Threshold with horizontal options
score_threshold = st.sidebar.radio('Score Threshold', [0, 1, 2, 3, 4], index=0, horizontal=True)
reads_threshold = st.sidebar.radio('Reads Threshold', [1, 10, 100, 1000, 10000], index=0, horizontal=True)

# Sidebar - Recompute Option
st.sidebar.title("Recompute Options")
recompute_automatically = st.sidebar.checkbox("Recompute automatically", value=True)

if not recompute_automatically:
    recompute_button = st.sidebar.button("Compute")

def display_outputs():
    # Display Data
    st.title("Bacteria Data Comparison App")

    if show_curated:
        st.subheader("Curated Species List (First Few Lines)")
        st.dataframe(curated_df.head())

    st.subheader("Input Comparison CSV (First Few Lines)")
    st.dataframe(input_df.head())

    # Calculate Stats
    num_rows = len(input_df)
    species_column = '#Datasets'
    matching_rows_df = input_df[input_df[species_column].isin(curated_df['Species'])]
    matching_rows = matching_rows_df.shape[0]

    # Determine location columns (all except the first column)
    location_columns = input_df.columns[1:]

    def calculate_threshold_stats(filtered_df):
        # Count the number of rows that pass both location and weight thresholds
        thresh_rows = filtered_df.shape[0]
        return thresh_rows

    # Filtering Based on Thresholds
    def filter_bacteria(matching_rows_df, curated_df, score_weights, score_threshold, reads_threshold):
        # Filter based on reads threshold
        filtered_df = matching_rows_df.copy()

        # Determine if any location's reads exceed the threshold
        filtered_df['Num loc'] = filtered_df[location_columns].apply(lambda x: x[x > reads_threshold].count(), axis=1)
        filtered_df['Locations'] = filtered_df[location_columns].apply(lambda x: {loc: count for loc, count in x.items() if count > reads_threshold}, axis=1)

        # Keep rows where location count exceeds threshold
        filtered_df = filtered_df[filtered_df['Num loc'] > 0]

        # Score calculation based on weights
        filtered_df['Weight Score'] = filtered_df[species_column].apply(
            lambda x: sum(
                curated_df[curated_df['Species'] == x][list(score_weights.keys())].values.flatten() * list(score_weights.values())
            )
        )

        # Filter based on score threshold
        filtered_df = filtered_df[filtered_df['Weight Score'] >= score_threshold]

        return filtered_df[['#Datasets', 'Num loc', 'Locations']].rename(columns={'#Datasets': 'Species'})

    filtered_bacteria = filter_bacteria(matching_rows_df, curated_df, st.session_state['score_weights'], score_threshold, reads_threshold)
    thresh_rows = calculate_threshold_stats(filtered_bacteria)

    # Display Stats Table
    st.subheader("Statistics")
    st.write(f"**Threshold: Score {score_threshold}, Count {reads_threshold}**")
    stats_df = pd.DataFrame({
        'Num': [num_rows],
        'Matched': [matching_rows],
        'Thresh': [thresh_rows]
    })
    st.table(stats_df)

    st.subheader("Filtered Bacteria List")
    st.dataframe(filtered_bacteria)

# Display outputs based on automatic or manual compute option
if recompute_automatically:
    display_outputs()
elif 'recompute_button' in locals() and recompute_button:
    display_outputs()
