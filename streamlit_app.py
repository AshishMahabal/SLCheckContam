import io
import json

import pandas as pd
import streamlit as st
from checkContamination import ContaminationChecker
from display_utils import display_markdown

# Sidebar - Menu Options
st.sidebar.title("Check Contamination")
# if st.sidebar.button("Introduction"):
#     display_markdown("INTRODUCTION.md")

# Sidebar - markdown links
col1, col2, col3 = st.sidebar.columns(3)
if "show_intro" not in st.session_state:
    st.session_state["show_intro"] = False
if "show_issues" not in st.session_state:
    st.session_state["show_issues"] = False
if "show_credits" not in st.session_state:
    st.session_state["show_credits"] = False
if "recompute_automatically" not in st.session_state:
    st.session_state[
        "recompute_automatically"
    ] = True  # Default to auto recompute being enabled

if col1.button("Intro"):
    st.session_state["show_intro"] = True  # Set flag for intro display
    st.session_state["recompute_automatically"] = False  # Turn off auto computation
    display_markdown("INTRODUCTION.md")
    st.session_state["show_intro"] = False  # Reset flag after display

if col2.button("Known Issues"):
    st.session_state["show_issues"] = True  # Set flag for issues display
    st.session_state["recompute_automatically"] = False  # Turn off auto computation
    display_markdown("ISSUES.md")
    st.session_state["show_issues"] = False  # Reset flag after display

if col3.button("Credits"):
    st.session_state["show_credits"] = True  # Set flag for credits display
    st.session_state["recompute_automatically"] = False  # Turn off auto computation
    display_markdown("CREDITS.md")
    st.session_state["show_credits"] = False  # Reset flag after display

# Display the introduction screen initially
if "introduction_shown" not in st.session_state:
    display_markdown("INTRODUCTION.md")
    st.session_state["introduction_shown"] = True

# Sidebar - Display options
st.sidebar.title("Display Options")
# Load Data
# Load curated species list
curated_file = st.sidebar.radio(
    "Choose curated species list:",
    ["Curated Species List", "Expanded Semi-Curated List"],
    format_func=lambda x: x,
)

# Map the selected option to the corresponding file path
file_path = (
    "data/curated_species.csv"
    if curated_file == "Curated Species List"
    else "data/semicurated.csv"
)

show_curated = st.sidebar.checkbox("Show first few lines of Curated List", value=False)


# @st.cache_data
def load_data():
    # Load curated species list
    curated_df = pd.read_csv(file_path)

    # Load score weights
    with open("data/score_weights.txt", "r") as f:
        default_score_weights = json.load(f)

    return curated_df, default_score_weights


curated_df, default_score_weights = load_data()

# Initialize Contamination Checker
contamination_checker = ContaminationChecker(curated_df, default_score_weights)


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
    # if recompute_button:
    #     st.session_state["show_intro"] = True  # Set flag for intro display
    #     st.session_state["recompute_automatically"] = False  # Turn off auto computation
    #     display_markdown("INTRODUCTION.md")
    #     st.session_state["show_intro"] = False  # Reset flag after display
    

def display_outputs():
    # Check if any markdown is being displayed
    # st.write("Intro: ", st.session_state.get("show_intro"))
    # st.write("Compute: ", st.session_state.get("recompute_automatically"))
    if (
        st.session_state.get("show_intro", False)
        or st.session_state.get("show_issues", False)
        or st.session_state.get("show_credits", False)
    ):
        return  # Exit early if any markdown is displayed

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
        reverse_table,
    ) = contamination_checker.filter_bacteria(
        input_df, st.session_state["score_weights"], score_threshold, reads_threshold
    )

    # Handle case where no results were returned
    if isinstance(filtered_bacteria, int) and filtered_bacteria == 0:
        st.warning("No bacteria species meet the specified thresholds.")
        return  # Exit the function early

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

    show_reverse_table = st.checkbox("Show Table by Properties", value=False)
    if show_reverse_table:
        st.subheader("Table by Properties")
        st.dataframe(reverse_table.head(100))

    show_venn = st.checkbox("Show Venn diagram of contributing properties", value=False)
    if show_venn:
        try:
            venn_fig = contamination_checker.generate_venn_diagram(filtered_bacteria)
            if venn_fig is None:
                st.info(
                    "No Venn diagram generated. This may be due to insufficient data or selected properties."
                )
        except ImportError as e:
            st.error(
                "Error: Required library for Venn diagram not installed. "
                f"Please check your requirements.txt file. Details: {str(e)}"
            )
            venn_fig = None
        except ValueError as e:
            st.error(f"Error: Invalid data for Venn diagram. Details: {str(e)}")
            venn_fig = None
        except Exception as e:
            st.error(f"Unexpected error generating Venn diagram: {str(e)}")
            venn_fig = None

        if venn_fig is not None:
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
