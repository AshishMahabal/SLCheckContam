# Check Contamination

Welcome to **Check Contamination**. This Streamlit application allows users to
compare bacteria data against a curated list with specific properties. Users
can adjust contamination weights, set custom thresholds, and filter bacteria
data based on location counts and other properties.

## Key Features

- **Upload Your Own CSV**: Easily upload your own bacteria dataset in CSV
  format for comparison.
- **Adjust Contamination Weights**: Fine-tune weights for various bacteria
  properties to customize the filtering process.
- **Set Custom Thresholds**: Use radio buttons to set score and location count
  thresholds.
- **Dynamic Output Display**: Choose to recompute results automatically or
  manually based on user inputs.
- **Visualize Filtered Results**: View filtered bacteria lists and statistics
  based on your configurations.

## Input File Format

To use this app effectively, please ensure your input CSV file adheres to the
following format:

### Example Input CSV Format

| Species                    | loc1 | loc2 | loc3  | ...   |
|------------------------------|------|------|-------|-------|
| Acidobacteria bacterium Mor1 | 200  | 1240 | 0     | ...   |
| Acidipila rosea              | 300  | 4240 | 0     | ...   |
| Acidisarcina polymorpha      | 2200 | 1240 | 10000 | ...   |
| ...                          | ...  | ...  | ...   | ...   |

#### Input File Requirements

1. **`Species` Column**: The first column must contain the names of bacteria
   species.
2. **Location Columns**: Subsequent columns (e.g., `loc1`, `loc2`, `loc3`, etc.)
   should represent different locations. Each cell under these columns contains
   numeric values representing the number of measurements for the corresponding
   bacteria found at that location.

## What the App Does

1. **Data Comparison**: Compares the input bacteria species against a curated
   list (`curated_species.csv`) that includes various properties like
   temperature type, oxygen tolerance, and spore formation.

2. **Adjust Weights for Contamination Properties**:  
   Users can adjust weights for different properties (like psychrophilic,
   mesophilic, spore formation, etc.) which are used to calculate scores.
   A default weights file (`score_weights.txt`) is provided, and users can
   upload their own JSON file with custom weights or adjust the default weights.

3. **Set Thresholds for Filtering**:
   - **Score Threshold**: A threshold that determines which bacteria species are
     considered based on their properties.
   - **Reads Threshold**: A threshold for the number of measurements in a
     location column that a species must exceed to be included in the output.

4. **Dynamic Recalculation**:  
   Users can select whether to automatically recompute results when settings
   are changed or manually trigger the computation.

## Outputs Explained

### 1. **Statistics Table**

This table provides a summary of the comparison and filtering results:

- **Num**: The total number of bacteria in the uploaded list.
- **Matched**: The number of bacteria whose names match those in the curated
  list.
- **Above Threshold**: The number of bacteria that meet the selected thresholds
  for both score and location count.

### 2. **Filtered Bacteria List**

Displays a table with bacteria that pass both the score and reads thresholds.
This table contains:

- **Species**: Name of the bacteria species.
- **Score**: The weighted score of the bacteria based on their properties.
- **Num loc**: The number of locations where the reads (measurements) exceed the
  selected threshold.
- **Locations**: A dictionary showing the location names and their corresponding
  counts that exceed the threshold.

## How to Use the App

1. **Display Options**:  
   Use the checkbox to display the first few lines of the curated list.

2. **Upload Your Data**:  
   Choose to use the default input file or upload your CSV file in the required
   format.

3. **Adjust Contamination Weights**:  
   Optionally modify weights using the provided number input fields for each
   property. Restore default weights or upload a custom weights JSON file if
   needed.

4. **Set Thresholds**:  
   Use radio buttons to set the thresholds for score and reads.

5. **Recompute Options**:  
   Select "Recompute automatically" to update the results dynamically.
   If unchecked, use the "Compute" button to manually trigger the output
   generation.

## Example Output

The app provides visual representations of filtered bacteria lists and
statistical summaries based on your inputs and settings. This helps in
identifying bacteria species of interest based on location data and weighted
properties.

## Tips

- Ensure your input CSV file is correctly formatted for accurate comparison.
- Adjust weights thoughtfully to filter bacteria based on relevant properties.
- Experiment with different threshold values to explore different filtering
  results.

## Feedback and Support

If you have any questions, encounter any issues, or have suggestions for
improvement, feel free to reach out via the credits section on the app or open
an issue on the GitHub repository.

Enjoy using [**Check Contamination**](https://checkcontam.streamlit.app/)!
