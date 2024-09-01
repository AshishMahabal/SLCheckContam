import streamlit as st
import pandas as pd
from checkContaminants import run_analysis, location_contamination  # Import the refactored functions and classes

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

# Run Analysis Button
if st.sidebar.button("Run Analysis"):
    # Check if the input file is uploaded
    if uploaded_input_file is not None:
        # Read the uploaded file based on its type
        if uploaded_input_file.name.endswith('.csv'):
            data = pd.read_csv(uploaded_input_file, header=None if no_header else 'infer')
        elif uploaded_input_file.name.endswith('.json'):
            data = pd.read_json(uploaded_input_file)
        elif uploaded_input_file.name.endswith('.tsv'):
            data = pd.read_csv(uploaded_input_file, delimiter='\t', header=None if no_header else 'infer')
        else:
            st.error("Unsupported file type. Please upload a .csv, .json, or .tsv file.")
            st.stop()

        # Display the input data for verification
        st.write("### Input Data Preview")
        st.dataframe(data.head())

        # Run the refactored analysis function
        try:
            loc, result = run_analysis(
                infile=uploaded_input_file.name,
                outfile=output_file_name,
                noheader=no_header,
                s=sort_by,
                local=local_threshold,
                t=score_threshold,
                datfile=dat_file,
                config=config_file,
                v=summary_v,
                vv=detailed_vv,
                pdf=create_pdf,
                logchart=log_chart
            )

            st.success("Analysis completed successfully.")

            # Display or download results as needed
            st.write("### Analysis Results")
            # Example of displaying results (assuming the result is in a usable format)
            st.dataframe(result)

            # Optionally call other functions based on user input
            if summary_v or detailed_vv:
                # Example: Generate bar chart for the top 10 species
                fig, ax = plt.subplots()
                loc.bar_locs_for_top10_species(ax, result)
                st.pyplot(fig)

            if log_chart:
                # Example: Generate a log-scaled chart
                fig, ax = plt.subplots()
                loc.survey_reads_at_top10_locs(ax, result, filename=uploaded_input_file.name, noheader=no_header, logchart=log_chart)
                st.pyplot(fig)

            # PDF generation, if implemented
            if create_pdf:
                st.write("PDF generation is not implemented yet but would go here.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please upload a valid input file.")
