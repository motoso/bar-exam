# Bar Exam Study Tracker

This script visualizes and summarizes study time for bar exam preparation from a time tracking CSV file.

## Features

- Generates a stacked bar chart showing weekly study hours, categorized by subject.
- Calculates and prints the total study time for a specific week and the cumulative total up to that week.
- Customizable through command-line arguments.

## Usage

```zsh
rye run python main.py [CSV_FILE] [--end-date YYYY-MM-DD]
```

### Arguments

- `CSV_FILE` (optional): The path to your time tracking CSV file. If not provided, it defaults to `Time Tracking 2025-06-29.csv`.
- `--end-date` (optional): The end date of the week you want to analyze, in `YYYY-MM-DD` format. This date should typically be a Saturday. If not provided, it defaults to the current date.

### Date and Time Calculations

- **Weekly Summary:** The script calculates study time for a full 7-day week, from Sunday to Saturday.
  - **Example:** If you set `--end-date 2025-06-28`, the summary will cover the period from `2025-06-22 00:00:00` to `2025-06-28 23:59:59`.

- **Graph Display:** The bar chart displays weekly study data. Each bar represents a full week, labeled with its start date (Sunday).
  - **Example:** For the week of June 22nd to June 28th, the corresponding bar on the graph will be labeled `2025-06-22`.
  - The graph includes all data up to and including the week specified by the `--end-date`.
