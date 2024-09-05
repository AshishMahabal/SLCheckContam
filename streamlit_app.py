import io
import json

import pandas as pd
import streamlit as st
from checkContamination import ContaminationChecker
from display_utils import display_markdown
from matplotlib_venn import venn3


# Load Data
@st.cache_data
def load_data():
    # Load curated species list
    curated_df = pd.read_csv("data/curated_species.csv")

    # Load score weights
    with open("data/score_weights.txt", "r") as f:
        default_score_weights = json.load(f)

    return curated_df, default_score_weights


curated_df, default_score_weights = load_data()

# Initialize Contamination Checker
contamination_checker = ContaminationChecker(curated_df, default_score_weights)

# Sidebar - Menu Options
st.sidebar.title("Check Contamination")
# if st.sidebar.button("Introduction"):
#     display_markdown("INTRODUCTION.md")

# Sidebar - Credits Link
col1, col2 = st.sidebar.columns(2)
if col1.button("Introduction"):
    st.session_state["show_input_preview"] = False  # Turn off display of input CSV
    st.session_state["show_curated_preview"] = False  # Turn off display of curated CSV
    st.session_state["Recompute automatically"] = False  # Turn off auto computation
    display_markdown("INTRODUCTION.md")
if col2.button("Credits"):
    display_markdown("CREDITS.md")
    st.session_state["show_input_preview"] = False  # Turn off display of input CSV
    st.session_state["show_curated_preview"] = False  # Turn off display of curated CSV
    st.session_state["Recompute automatically"] = False  # Turn off auto computation

# Display the introduction screen initially
if "introduction_shown" not in st.session_state:
    display_markdown("INTRODUCTION.md")
    st.session_state["introduction_shown"] = True

# Sidebar - Display options
st.sidebar.title("Display Options")
show_curated = st.sidebar.checkbox("Show first few lines of Curated List", value=False)

# Input File Selection
st.sidebar.title("Input File")
use_default_file = st.sidebar.checkbox(
    "Use default input file: sample-infile.csv", value=True
)

if use_default_file:
    input_df = pd.read_csv("data/sample-infile.csv")
else:
    uploaded_file = st.sidebar.file_uploader(
        "Upload a CSV file for comparison", type="csv"
    )
    if uploaded_file is not None:
        input_df = pd.read_csv(uploaded_file)
    else:
        st.warning("Please upload a CSV file for comparison.")
        input_df = None  # Set input_df to None if no file is uploaded
        # Turn off autodisplay of first 5 lines of input CSV and auto computation
        st.session_state["show_input_preview"] = False
        st.session_state["Recompute automatically"] = False

# Continue displaying the rest of the sidebar menu regardless of file upload status

# Sidebar - Contam Weights settings
st.sidebar.title("Contam Weights")

# Initialize weights and UI state in session state
if "score_weights" not in st.session_state:
    st.session_state["score_weights"] = default_score_weights.copy()
if "weights_expanded" not in st.session_state:
    st.session_state["weights_expanded"] = False

weights_expander = st.sidebar.expander(
    "Adjust Contam Weights", expanded=st.session_state["weights_expanded"]
)

with weights_expander:
    st.write("Adjust the weights for each property.")

    # Create form elements for each weight
    weight_inputs = {}
    for key in st.session_state["score_weights"].keys():
        weight_inputs[key] = st.number_input(
            f"Weight for {key}",
            min_value=0,
            max_value=2,
            value=st.session_state["score_weights"][key],
        )

    # Update the weights from the input fields
    for key in st.session_state["score_weights"].keys():
        st.session_state["score_weights"][key] = weight_inputs[key]

    # Restore default weights button
    if st.button("Restore Default Weights"):
        # Reset to default weights
        st.session_state["score_weights"] = default_score_weights.copy()
        # Keep the section expanded and retrigger outputs display
        st.session_state["weights_expanded"] = True
        st.session_state["recompute_trigger"] = True

    # Option to upload custom weights file
    st.write("Upload a custom weights file (JSON format).")
    custom_weights_file = st.file_uploader(
        "Upload a JSON file for weights", type="json"
    )
    if custom_weights_file is not None:
        st.session_state["score_weights"] = json.load(custom_weights_file)
        st.session_state["weights_expanded"] = True
        st.session_state["recompute_trigger"] = True

# Sidebar - Threshold Settings
st.sidebar.title("Threshold Settings")

# Radio buttons for Score Threshold and Reads Threshold with horizontal options
score_threshold = st.sidebar.radio(
    "Score Threshold", [1, 2, 3, 4, 5], index=0, horizontal=True
)
reads_threshold = st.sidebar.radio(
    "Reads Threshold", [1, 10, 100, 1000, 10000], index=0, horizontal=True
)

# Sidebar - Recompute Option
st.sidebar.title("Recompute Options")
recompute_automatically = st.sidebar.checkbox(
    "Recompute automatically", value=True if input_df is not None else False
)

if not recompute_automatically:
    recompute_button = st.sidebar.button("Compute")


def display_outputs():
    # Display Data
    st.title("Check Contamination")

    if show_curated:
        st.subheader("Curated Species List (First Few Lines)")
        st.dataframe(curated_df.head())

    if input_df is not None:
        st.subheader("Input Comparison CSV (First Few Lines)")
        st.dataframe(input_df.head())

    # Run computations
    (
        matching_rows,
        filtered_bacteria,
        thresh_rows,
    ) = contamination_checker.filter_bacteria(
        input_df, st.session_state["score_weights"], score_threshold, reads_threshold
    )

    # Display Stats Table
    st.subheader("Statistics")
    st.write(f"**Threshold: Score {score_threshold}, Count {reads_threshold}**")
    stats_df = pd.DataFrame(
        {
            "Num": [len(input_df)],
            "Matched": [matching_rows],
            "Above Threshold": [thresh_rows],
        }
    )
    st.table(stats_df)

    st.subheader("Filtered Bacteria List")
    st.dataframe(filtered_bacteria.head(100))

    show_venn = st.checkbox("Show Venn diagram of contributing properties", value=False)
    if show_venn:
        venn_fig = contamination_checker.generate_venn_diagram(filtered_bacteria)
        st.pyplot(venn_fig)

        # Save the Venn diagram as PNG for download
        img_buffer = io.BytesIO()
        venn_fig.savefig(img_buffer, format="png")
        img_buffer.seek(0)
        st.download_button(
            label="Download Venn Diagram",
            data=img_buffer,
            file_name="venn_diagram.png",
            mime="image/png",
        )

    col1, col2, col3 = st.columns(3)
    show_unmatched = col1.checkbox("Show top unmatched rows", value=False)
    n = col2.number_input(
        "Number of rows to display", min_value=1, max_value=20, value=10
    )
    if show_unmatched:
        st.subheader("Top Unmatched Rows")
        col3.dataframe(
            contamination_checker.non_matching_rows_df.iloc[:n, 0].to_frame()
        )


# Display outputs based on automatic or manual compute option
if recompute_automatically or st.session_state.get("recompute_trigger", False):
    display_outputs()
    st.session_state["recompute_trigger"] = False
elif "recompute_button" in locals() and recompute_button:
    display_outputs()
