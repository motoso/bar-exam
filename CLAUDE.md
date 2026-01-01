# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Japanese bar exam study tracker that visualizes and summarizes study time from CSV time tracking data. It generates stacked bar charts showing weekly study hours by subject category and outputs summary statistics in Japanese.

## Development Environment

- **Language**: Python 3.8+
- **Package Manager**: Rye (see `pyproject.toml`)
- **Dependencies**: pandas, matplotlib
- **Virtual Environment**: `.venv/` (managed by Rye)

## Common Commands

```bash
# Run the main script with default CSV file
rye run python src/main.py

# Run with custom CSV file
rye run python src/main.py "Time Tracking 2025-07-07.csv"

# Run with custom end date (typically a Saturday)
rye run python src/main.py --end-date 2025-07-06

# Run with both custom CSV and end date
rye run python src/main.py "Time Tracking 2025-07-07.csv" --end-date 2025-07-06

# Install/sync dependencies
rye sync
```

## Code Architecture

### Entry Point
- `src/main.py`: Single-file application containing all logic

### Data Flow
1. **Input**: CSV file with columns: `Start`, `End`, `Duration`, `Category`, `Notes`
2. **Parsing**: Duration strings (e.g., "1 hr 49 min") are parsed into decimal hours
3. **Categorization**: Categories are reassigned based on keyword matching in the description:
   - Constitution categories: Essay Master (論文マスター), Basic, MCQs (短答)
   - Civil Law categories: General Provisions (総則)
4. **Weekly Aggregation**: Study time is grouped by week (Sunday-Saturday) and category
5. **Output**:
   - Matplotlib stacked bar chart showing weekly study hours
   - Japanese console output with current week and cumulative totals

### Key Implementation Details

- **Week Calculation**: Weeks start on Sunday. The `week_start` is calculated as the preceding Sunday from each study session's start date.
- **Date Range**: The graph includes all weeks from 2025-02-02 onwards up to the specified `--end-date`.
- **Summary Period**: When using `--end-date`, the weekly summary covers 7 days ending on that date (the week from Sunday to the specified date).
- **Graph Labels**: X-axis labels show week start dates (Sundays) in `YYYY-MM-DD` format.
- **Output Language**: Console output is in Japanese (今週の勉強時間, 累積勉強時間).

### Category Assignment Logic

The `assign_category()` function maps CSV category strings to display categories:
- Looks for keywords in lowercase description
- Checks for Japanese terms (論文マスター, 短答, 総則) to distinguish subcategories
- Returns `None` for unmatched categories (filtered out in analysis)

## CSV Data Format

Expected columns:
- `Start`: Date and time (YYYY-MM-DD HH:MM)
- `End`: Date and time (YYYY-MM-DD HH:MM)
- `Duration`: Human-readable format (e.g., "1 hr 49 min", "24 min")
- `Category`: Study category (used for keyword matching)
- `Notes`: Study notes/description
