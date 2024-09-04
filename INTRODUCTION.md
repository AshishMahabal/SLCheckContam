# Introduction

This app allows you to compare a list of bacteria species against a curated list
with various properties, such as temperature tolerance and oxygen levels. You can:

- Upload your own bacteria dataset in CSV format.
- Adjust weights for different bacteria properties to customize filtering.
- Set score and read thresholds to filter results.
- View filtered bacteria lists and statistics dynamically.

## Input CSV Format

Your CSV file should have the following format:

| #Datasets                      | loc1 | loc2 | loc3 | ... |
|--------------------------------|------|------|------|-----|
| Acidobacteria bacterium Mor1   | 200  | 1240 | 0    | ... |
| Acidipila rosea                | 300  | 4240 | 0    | ... |

- **`#Datasets` Column**: First column must be named `#Datasets` with bacteria names.
- **Location Columns**: Subsequent columns represent locations with measurement counts.

Use the sidebar to navigate between options and configure your settings.
