import streamlit as st
import pandas as pd
import io
from checkContaminants import location_contamination

st.title("Contamination Analysis")

# Sidebar inputs
st.sidebar.header("Input Parameters")

uploaded_file = st.sidebar.file_uploader("Upload Locations Data File", type=["csv", "json", "tsv"])
outfile = st.sidebar.selectbox("Output Format", ["terminal", "txt", "json", "csv", "tsv"])
noheader = st.sidebar.checkbox("CSV/TSV file does not have a header")

sort_order = st.sidebar.text_input("Sort Order (S: Score, L: Locations, A: Alphabetic, I: Input order)", "SLA")
local_threshold = st.sidebar.number_input("Local threshold for location reads", value=2000)
score_threshold = st.sidebar.number_input("Score threshold for positive contaminants", value=1.0, step=0.1)
datfile = st.sidebar.text_input("Curated species file", "curated_species.csv")
config_file = st.sidebar.text_input("Score weight config file", "score_weights.txt")

v_option = st.sidebar.checkbox("Show summary table (Species, Scores, Number of Locations)")
vv_option = st.sidebar.checkbox("Show detailed summary table (including Location Names)")
pdf_option = st.sidebar.checkbox("Create PDF of contamination report")
logchart_option = st.sidebar.checkbox("Use log scale for read bars in 3rd chart")

if uploaded_file is not None:
    # Read the file
    file_contents = uploaded_file.read()
    file_type = uploaded_file.name.split('.')[-1]
    
    # Create a BytesIO object
    file_buffer = io.BytesIO(file_contents)
    
    # Initialize location_contamination object
    loc = location_contamination(curated=datfile, config=config_file, local=local_threshold)
    
    # Prepare arguments for get_score method
    kwargs = {
        "file": file_buffer,
        "t": score_threshold,
        "v": v_option,
        "vv": vv_option,
        "pdf": pdf_option,
        "outfile": "terminal",  # We'll capture the output and display it in Streamlit
        "sort_species": sort_order.lower(),
        "csv_header": not noheader,
        "local_threshold": local_threshold,
        "logchart": logchart_option,
        "curated": datfile,
        "config": config_file,
        "local": local_threshold
    }
    
    # Capture the output
    output = io.StringIO()
    import sys
    sys.stdout = output
    
    # Run the analysis
    loc.get_score(**kwargs)
    
    # Reset stdout
    sys.stdout = sys.__stdout__
    
    # Display the output in the main area
    st.text(output.getvalue())
    
    # If PDF was generated, provide a download link
    if pdf_option:
        st.write("PDF report generated. Please check your local directory.")

else:
    st.write("Please upload a file to begin the analysis.")
