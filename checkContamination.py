import matplotlib.pyplot as plt
from matplotlib_venn import venn3
import streamlit as st


class ContaminationChecker:
    """Class to perform contamination checks and filtering on bacteria data."""

    def __init__(self, curated_df, score_weights):
        self.curated_df = curated_df
        self.default_score_weights = score_weights

    def generate_venn_diagram(self, filtered_bacteria):
        """Generate a Venn diagram of contributing properties."""

        # Get unique properties from the 'Contributing Properties' column
        def flatten_set_of_lists(set_of_lists):
            flattened_list = [item for sublist in set_of_lists for item in sublist]
            return set(flattened_list)

        all_properties = flatten_set_of_lists(
            filtered_bacteria["Contributing Properties"].dropna()
        )

        # Check if the set is empty and print debug information if it is
        if not all_properties:
            print("Debug: all_properties set is empty")
            print("Sample of 'Contributing Properties' column:")
            print(filtered_bacteria["Contributing Properties"].head())

        # Select the first three properties for the Venn diagram
        properties = list(all_properties)[:10]

        # Count bacteria for each property
        property_counts = [
            sum(
                prop in item
                for item in filtered_bacteria["Contributing Properties"]
                if isinstance(item, list)
            )
            for prop in properties
        ]

        # Create Venn diagram
        plt.figure(figsize=(4, 4))
        subsets = [
            set(
                filtered_bacteria[
                    filtered_bacteria["Contributing Properties"].apply(
                        lambda x: prop in x
                    )
                ].index
            )
            for prop in properties[:3]
        ]
        venn = venn3(subsets=subsets, set_labels=properties[:3])

        # Set title
        plt.title("Contributing Properties of Filtered Bacteria")

        return plt.gcf()  # Return the current figure

    def filter_bacteria(
        self,
        input_df,
        score_weights,
        score_threshold,
        reads_threshold,
    ):
        """Filter bacteria based on thresholds and weights."""
        # Determine if bacteria species exist in the curated list
        species_column = input_df.columns[0]  # Assuming the species column is first
        self.species_column_name = species_column  # Save the column name
        matching_rows_df = input_df[
            input_df[species_column].isin(self.curated_df["Species"])
        ]
        matching_rows = matching_rows_df.shape[0]

        # Identify rows not in curated set
        non_matching_rows_df = input_df[
            ~input_df[species_column].isin(self.curated_df["Species"])
        ]
        non_matching_rows = non_matching_rows_df.shape[0]

        # Store non-matching rows for later use
        self.non_matching_rows_df = non_matching_rows_df
        self.non_matching_rows = non_matching_rows

        # Determine location columns (all except the first column)
        location_columns = input_df.columns[1:]

        # Apply reads threshold
        filtered_df = matching_rows_df.copy()
        filtered_df["Num loc"] = filtered_df[location_columns].apply(
            lambda x: x[x >= reads_threshold].count(), axis=1
        )
        filtered_df["Locations"] = filtered_df[location_columns].apply(
            lambda x: {
                loc: count for loc, count in x.items() if count > reads_threshold
            },
            axis=1,
        )

        # Keep rows where location count exceeds threshold
        filtered_df = filtered_df[filtered_df["Num loc"] > 0]

        # Apply score threshold based on weights
        def calculate_score_and_properties(species):
            species_data = self.curated_df[self.curated_df["Species"] == species]
            if species_data.empty:
                return 0, []

            properties = list(score_weights.keys())
            values = species_data[properties].values.flatten()
            weights = list(score_weights.values())

            weighted_values = values * weights
            total_score = sum(weighted_values)

            contributing_properties = [
                prop for prop, val in zip(properties, weighted_values) if val > 0
            ]

            return total_score, contributing_properties

        filtered_df["Weight Score"], filtered_df["Contributing Properties"] = zip(
            *filtered_df[species_column].apply(calculate_score_and_properties)
        )
        filtered_df = filtered_df[filtered_df["Weight Score"] >= score_threshold]

        thresh_rows = filtered_df.shape[0]

        # Rename columns and prepare final output
        filtered_bacteria = filtered_df[
            [
                self.species_column_name,
                "Weight Score",
                "Contributing Properties",
                "Num loc",
                "Locations",
            ]
        ]
        filtered_bacteria = filtered_bacteria.rename(columns={"Weight Score": "Score"})
        return matching_rows, filtered_bacteria, thresh_rows
