import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3
import pandas as pd
import streamlit as st


class ContaminationChecker:
    """Class to perform contamination checks and filtering on bacteria data."""

    def __init__(self, curated_df, score_weights):
        self.curated_df = curated_df
        self.default_score_weights = score_weights

    def flatten_set_of_lists(set_of_lists):
        flattened_list = [item for sublist in set_of_lists for item in sublist]
        return set(flattened_list)

    def get_unique_properties(filtered_bacteria):
        # Get unique properties from the 'Contributing Properties' column
        all_properties = ContaminationChecker.flatten_set_of_lists(
            filtered_bacteria["Contributing Properties"].dropna()
        )

        # Check if the set is empty and print debug information if it is
        if not all_properties:
            print("Debug: all_properties set is empty")
            print("Sample of 'Contributing Properties' column:")
            print(filtered_bacteria["Contributing Properties"].head())

        # Get all properties
        return list(all_properties)

    def generate_venn_diagram(self, filtered_bacteria):
        """Generate a Venn diagram of contributing properties."""

        properties = ContaminationChecker.get_unique_properties(filtered_bacteria)
        num_properties = len(properties)

        if num_properties == 0:
            st.write("No contributing properties found.")
            return None
        elif num_properties == 1:
            count = sum(
                properties[0] in item
                for item in filtered_bacteria["Contributing Properties"]
                if isinstance(item, list)
            )
            st.write(
                f"Only one property found: {properties[0]}. {count} bacteria belong to this property."
            )
            return None
        elif num_properties == 2:
            subsets = [
                set(
                    filtered_bacteria[
                        filtered_bacteria["Contributing Properties"].apply(
                            lambda x: prop in x
                        )
                    ].index
                )
                for prop in properties
            ]
            plt.figure(figsize=(4, 4))
            venn = venn2(subsets=subsets, set_labels=properties)
        else:
            # Create three side-by-side dropdowns
            col1, col2, col3 = st.columns(3)
            prop1 = col1.selectbox("Property 1", properties, index=0)
            prop2 = col2.selectbox("Property 2", properties, index=1)
            prop3 = col3.selectbox(
                "Property 3",
                ["None"] + properties,
                index=3 if num_properties > 2 else 0,
            )

            if len(set([prop1, prop2, prop3])) < 3 or prop3 == "None":
                if prop1 == prop2 or (
                    prop3 != "None" and (prop1 == prop3 or prop2 == prop3)
                ):
                    st.warning("Please select distinct properties.")
                    return None

                subsets = [
                    set(
                        filtered_bacteria[
                            filtered_bacteria["Contributing Properties"].apply(
                                lambda x: prop in x
                            )
                        ].index
                    )
                    for prop in [prop1, prop2]
                ]
                plt.figure(figsize=(4, 4))
                venn = venn2(subsets=subsets, set_labels=[prop1, prop2])
            else:
                subsets = [
                    set(
                        filtered_bacteria[
                            filtered_bacteria["Contributing Properties"].apply(
                                lambda x: prop in x
                            )
                        ].index
                    )
                    for prop in [prop1, prop2, prop3]
                ]
                plt.figure(figsize=(4, 4))
                venn = venn3(subsets=subsets, set_labels=[prop1, prop2, prop3])

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

        # Check if the filtered DataFrame is empty
        if filtered_df.empty:
            # Handle the case where no rows meet the threshold
            print("Warning: No bacteria species meet the location count threshold.")
            # For Streamlit, it's better to return early with empty results
            return 0, 0, 0, 0

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

        # Create reverse table: properties and their corresponding bacteria
        properties = ContaminationChecker.get_unique_properties(filtered_bacteria)

        property_species_data = []
        for prop in properties:
            matching_species = filtered_bacteria[
                filtered_bacteria["Contributing Properties"].apply(lambda x: prop in x)
            ][self.species_column_name].tolist()
            property_species_data.append(
                {"Property": prop, "Matching Species": matching_species}
            )

        reverse_table = pd.DataFrame(property_species_data)
        return matching_rows, filtered_bacteria, thresh_rows, reverse_table
