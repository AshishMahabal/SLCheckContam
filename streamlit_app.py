import streamlit as st
import pandas as pd
#from checkContaminants import check_sample_for_contaminants  # Adjust this import based on the actual function names
import checkContaminants
## About to replace code - new from ChatGPT 4o

# Set up the Streamlit app
st.title("Bacterial Contaminant Checker")
st.write("Upload a sample data file to check for harmful bacterial contaminants.")

# Sidebar for options
st.sidebar.header("Analysis Options")
# Example options; adjust based on package functionality
bacteria_list = st.sidebar.text_input("Specify Bacteria to Check (comma-separated)", value="Salmonella, E. coli")
threshold = st.sidebar.slider("Detection Threshold", 0.0, 1.0, 0.5, step=0.01)

# File uploader for sample data
uploaded_file = st.file_uploader("Upload Sample Data File (CSV, Excel, or TXT)", type=["csv", "xlsx", "txt"])

if uploaded_file is not None:
    # Read file content into a DataFrame or appropriate format
    if uploaded_file.name.endswith(".csv"):
        sample_data = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(".xlsx"):
        sample_data = pd.read_excel(uploaded_file)
    else:
        sample_data = pd.read_table(uploaded_file)

    # Option to display raw content
    st.write("### Uploaded Sample Data")
    st.dataframe(sample_data)

    # Run analysis when button is clicked
    if st.button("Run Contaminant Check"):
        # Call the check_sample_for_contaminants function with relevant parameters
        try:
            # Modify based on the actual parameters required by the function
            result = check_sample_for_contaminants(sample_data, bacteria_list.split(','), threshold)
            
            # Convert results to a DataFrame if it's not already one
            if isinstance(result, dict):
                result_df = pd.DataFrame([result])
            else:
                result_df = result

            # Display the results
            st.write("### Contaminant Check Results")
            st.dataframe(result_df)

            # Provide a download option for the results
            st.download_button(
                label="Download Results",
                data=result_df.to_csv(index=False).encode('utf-8'),
                file_name='bacterial_contaminant_check_results.csv',
                mime='text/csv'
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")

