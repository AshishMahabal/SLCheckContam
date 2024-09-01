import streamlit as st
import pandas as pd
from checkContaminants import location_contamination, run_analysis  # Import the refactored functions and classes

# Set up the Streamlit app
st.title("Bacterial Contamination Analysis")
st.sidebar.header("Basic Usage")

# File Upload and Text Input for Input and Output Files
uploaded_input_file = st.sidebar.file_uploader("Upload Locations Data File (.csv, .json, or .tsv)", type=["csv", "json", "tsv"])
output_file_name = st.sidebar.text_input("Output File Name", value="terminal")

# Checkbox for noheader option
no_header = st.sidebar.checkbox("No Header (if the input CSV/TSV file does not have a header)")

# Configuration Setup Section
st.sidebar.header("Configuration Setup")
sort_by = st.sidebar.text_input("Sort By (e.g., SLA, SA, SL, LS, I for input order)", value="SLA")
local_threshold = st.sidebar.number_input("Local Threshold for Location Reads", min_value=0, value=2000)
score_threshold = st.sidebar.number_input("Score Threshold for Positive Contaminants", min_value=0.0, value=1.0, step=0.1)
dat_file = st.sidebar.text_input("Curated Species with Scores", value="curated_species.csv (provided)")
config_file = st.sidebar.text_input("Score Weight Configuration File", value="score_weights.txt")

# Output Preferences Section
st.sidebar.header("Output Preferences")
summary_v = st.sidebar.checkbox("Summary Table: Species, Scores, Number of Locations")
detailed_vv = st.sidebar.checkbox("Detailed Table: Species, Scores, Number of Locations, Location Names")
create_pdf = st.sidebar.checkbox("Create PDF of Contamination Report")
log_chart = st.sidebar.checkbox("Log Scale for Third Chart (if bars have vast size differences)")

# Add a checkbox for Venn diagram
create_venn = st.sidebar.checkbox("Create Venn Diagram", value=False)

# Run Analysis Button
if st.sidebar.button("Run Analysis"):
    # Check if the input file is uploaded
    if uploaded_input_file is not None:
        try:
            # Initialize location_contamination object
            loc_cont = location_contamination(
                config=config_file,
                curated=dat_file,
                local_threshold=local_threshold
            )

            # Run the analysis
            result, num_pos, info = loc_cont.get_score(
                file=uploaded_input_file,
                csv_header=not no_header,
                t=score_threshold,
                v=summary_v,
                vv=detailed_vv,
                pdf=create_pdf,
                logchart=log_chart
            )

            if isinstance(result, str):  # Check if result is an error message
                st.error(result)
            else:
                st.success("Analysis completed successfully.")

                # Display results
                st.write("### Analysis Results")
                st.dataframe(result)

                # Display additional information
                st.write(f"Number of positive contaminants: {num_pos}")
                st.write("### Analysis Information")
                st.write(info)

                # Generate and display charts
                st.write("### Top 10 Species by Number of Locations")
                fig1 = loc_cont.bar_locs_for_top10_species(result)
                st.pyplot(fig1)

                st.write("### Survey Reads at Top 10 Locations")
                fig2 = loc_cont.survey_reads_at_top10_locs(result, uploaded_input_file, no_header, log_chart)
                st.pyplot(fig2)

                # PDF generation
                if create_pdf:
                    st.write("PDF generation is not implemented yet but would go here.")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.error("Please upload a valid input file.")
