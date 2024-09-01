import streamlit as st
import pandas as pd
from checkContaminants import location_contamination

# Set up the Streamlit app
st.title("Bacterial Contamination Analysis")

# Sidebar configuration
st.sidebar.header("Configuration")

# File Upload
uploaded_file = st.sidebar.file_uploader("Upload Locations Data File (CSV)", type=["csv"])

# Configuration Setup
local_threshold = st.sidebar.number_input("Local Threshold", value=2000, step=100)
score_threshold = st.sidebar.number_input("Score Threshold for Positive Contaminants", min_value=0.0, value=1.0, step=0.1)

# Curated Species File
use_default_dat = st.sidebar.checkbox("Use default Curated Species with Scores file", value=True)
if use_default_dat:
    dat_file = "curated_species.csv"
else:
    uploaded_dat_file = st.sidebar.file_uploader("Upload Curated Species with Scores file (CSV)", type=["csv"])
    dat_file = uploaded_dat_file if uploaded_dat_file is not None else None

# Run Analysis Button
if st.sidebar.button("Run Analysis"):
    if uploaded_file is not None and (use_default_dat or dat_file is not None):
        try:
            # Initialize location_contamination object
            loc_cont = location_contamination(
                config="score_weights.txt",
                curated=dat_file,
                local_threshold=local_threshold
            )

            # Run the analysis
            result, num_pos, info = loc_cont.get_score(
                file=uploaded_file,
                csv_header=True,
                t=score_threshold
            )

            if isinstance(result, str):  # Check if result is an error message
                st.error(result)
            else:
                st.success("Analysis completed successfully.")

                # Display results
                st.header("Analysis Results")
                st.dataframe(result)

                # Display additional information
                st.write(f"Number of positive contaminants: {num_pos}")
                st.header("Analysis Information")
                st.write(info)

                # Generate and display charts
                st.header("Top 10 Species by Number of Locations")
                fig1 = loc_cont.bar_locs_for_top10_species(result)
                st.pyplot(fig1)

                st.header("Survey Reads at Top 10 Locations")
                fig2 = loc_cont.survey_reads_at_top10_locs(result, uploaded_file, False, False)
                st.pyplot(fig2)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.error("Please upload a valid input file and ensure a Curated Species file is selected or uploaded.")
else:
    st.write("Please configure the analysis parameters in the sidebar and click 'Run Analysis' to start.")
