
class ContaminationChecker:
    """Class to perform contamination checks and filtering on bacteria data."""

    def __init__(self, curated_df, score_weights):
        self.curated_df = curated_df
        self.default_score_weights = score_weights

    def filter_bacteria(
        self,
        input_df,
        score_weights,
        score_threshold,
        reads_threshold,
    ):
        """Filter bacteria based on thresholds and weights."""
        # Determine if bacteria species exist in the curated list
        species_column = "#Datasets"
        matching_rows_df = input_df[
            input_df[species_column].isin(self.curated_df["Species"])
        ]
        matching_rows = matching_rows_df.shape[0]

        # Determine location columns (all except the first column)
        location_columns = input_df.columns[1:]

        # Apply reads threshold
        filtered_df = matching_rows_df.copy()
        filtered_df["Num loc"] = filtered_df[location_columns].apply(
            lambda x: x[x > reads_threshold].count(), axis=1
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
        filtered_df["Weight Score"] = filtered_df[species_column].apply(
            lambda x: sum(
                self.curated_df[self.curated_df["Species"] == x][
                    list(score_weights.keys())
                ].values.flatten()
                * list(score_weights.values())
            )
        )
        filtered_df = filtered_df[filtered_df["Weight Score"] >= score_threshold]

        thresh_rows = filtered_df.shape[0]

        # Rename columns and prepare final output
        filtered_bacteria = filtered_df[["#Datasets", "Num loc", "Locations"]].rename(
            columns={"#Datasets": "Species"}
        )

        return matching_rows, filtered_bacteria, thresh_rows
