import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import argparse
import datetime

STUDY_START = pd.Timestamp('2025-02-02')
YEAR2_START = pd.Timestamp('2026-02-01')

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate study report from time tracking data.')
parser.add_argument('csv_file', nargs='?', default='Time Tracking 2025-06-29.csv',
                    help='Path to the time tracking CSV file.')
parser.add_argument('--end-date', default=datetime.date.today().strftime('%Y-%m-%d'),
                    help='The end date of the week to include in the summary (YYYY-MM-DD), typically a Saturday.')
args = parser.parse_args()

# Load data
df = pd.read_csv(args.csv_file, parse_dates=['Start'])

# Parse duration into hours
def parse_duration(s):
    hours = sum(float(m) for m in re.findall(r'(\d+(?:\.\d+)?)\s*hr', s))
    minutes = sum(float(m) for m in re.findall(r'(\d+(?:\.\d+)?)\s*min', s))
    seconds = sum(float(m) for m in re.findall(r'(\d+(?:\.\d+)?)\s*sec', s))
    return hours + minutes / 60 + seconds / 3600

df['duration_hours'] = df['Duration'].apply(parse_duration)

# Define new categories based on keywords
def assign_category(description):
    description_lower = description.lower()
    if 'constitution' in description_lower and '論文マスター' in description:
        return 'Constitution - Essay Master'
    if 'constitution' in description_lower and 'basic' in description_lower:
        return 'Constitution - Basic'
    if 'constitution' in description_lower and '短答' in description_lower:
        return 'Constitution - MCQs'
    if 'civil' in description_lower and '総則' in description:
        return 'Civil Law - General Provisions'
    if 'civil' in description_lower and '物権' in description:
        return 'Civil Law - Property Rights'
    return None

df['Category'] = df['Category'].apply(assign_category)
df2 = df.dropna(subset=['Category']).copy()

# Compute week_start as the preceding Sunday
df2['week_start'] = df2['Start'] - pd.to_timedelta((df2['Start'].dt.weekday + 1) % 7, unit='d')
df2['week_start'] = df2['week_start'].dt.normalize()

# Weekly aggregation
weekly = df2.groupby(['week_start', 'Category'])['duration_hours'].sum().unstack(fill_value=0)

end_date = pd.to_datetime(args.end_date)
start_of_week = end_date - pd.Timedelta(days=6)

# Ensure all weeks from 2025-02-02 onwards are present.
# Only include a week if it's complete (Sunday–Saturday), so only go up to the last Saturday.
end_week_start = end_date - pd.Timedelta(days=int((end_date.weekday() + 1) % 7))
end_week_start = end_week_start.normalize()
# weekday() == 5 means Saturday; if end_date is not Saturday, the current week is incomplete — exclude it
if end_date.weekday() != 5:
    end_week_start -= pd.Timedelta(days=7)
all_weeks = pd.date_range(start='2025-02-02', end=end_week_start, freq='7D')
weekly = weekly.reindex(all_weeks, fill_value=0)
weekly.index.name = 'week_start'

# Include all data up to the specified end_date in the graph
weekly_graph = weekly[weekly.index <= end_date.normalize()]

# Split data into Year 1 and Year 2
year1 = weekly_graph[(weekly_graph.index >= STUDY_START) & (weekly_graph.index < YEAR2_START)]
year2 = weekly_graph[weekly_graph.index >= YEAR2_START]

# Assign relative week numbers (0-based)
year1_weeks = np.arange(len(year1))
year2_weeks = np.arange(len(year2))

# --- Single figure: Year 2, Year 1, Cumulative (3 rows) ---
plt.style.use('fivethirtyeight')

# Fixed color map using fivethirtyeight's color cycle for consistency across both years
all_categories = weekly_graph.columns.tolist()
style_colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
category_colors = {cat: style_colors[i % len(style_colors)] for i, cat in enumerate(all_categories)}
fig, (ax_y2, ax_y1, ax_cum) = plt.subplots(3, 1, figsize=(14, 14))

def plot_stacked_bar(ax, data, weeks, title):
    if len(data) == 0:
        ax.set_title(title, fontsize='small')
        ax.annotate('No data', xy=(0.5, 0.5), xycoords='axes fraction',
                     ha='center', va='center', fontsize=14, color='gray')
        return
    bottom = np.zeros(len(data))
    for cat in all_categories:
        if cat in data.columns:
            values = data[cat].values
        else:
            values = np.zeros(len(data))
        ax.bar(weeks, values, width=0.8, bottom=bottom,
               label=cat, color=category_colors[cat])
        bottom += values
    ax.set_title(title, fontsize='small')
    ax.set_ylabel('Hours Studied', fontsize='small')
    tick_positions = [w for w in weeks if w % 5 == 0]
    tick_labels = [f'W{w+1}' for w in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize='small')
    ax.set_xlabel('Week', fontsize='small')

plot_stacked_bar(ax_y2, year2, year2_weeks, 'Year 2 (2026-02-01 ~)')
plot_stacked_bar(ax_y1, year1, year1_weeks, 'Year 1 (2025-02-02 ~ 2026-01-25)')

# Align x-axis range
max_weeks = max(len(year1), len(year2), 1)
ax_y1.set_xlim(-0.5, max_weeks - 0.5)
ax_y2.set_xlim(-0.5, max_weeks - 0.5)

# Align y-axis scale between Year 1 and Year 2
shared_ymax = max(ax_y1.get_ylim()[1], ax_y2.get_ylim()[1])
ax_y1.set_ylim(0, shared_ymax)
ax_y2.set_ylim(0, shared_ymax)

# Single shared legend for bar charts
handles, labels = ax_y1.get_legend_handles_labels()
if not handles:
    handles, labels = ax_y2.get_legend_handles_labels()
fig.legend(handles, labels, title='Category', loc='upper right',
           fontsize='small', title_fontsize='small')

# Cumulative line chart
year1_cumulative = year1.sum(axis=1).cumsum()
year2_cumulative = year2.sum(axis=1).cumsum()

if len(year1_cumulative) > 0:
    ax_cum.plot(year1_weeks, year1_cumulative.values, marker='o', markersize=3,
                label='Year 1', color='steelblue')
if len(year2_cumulative) > 0:
    ax_cum.plot(year2_weeks, year2_cumulative.values, marker='s', markersize=3,
                label='Year 2', color='coral')

ax_cum.set_xlabel('Weeks since start', fontsize='small')
ax_cum.set_ylabel('Cumulative Hours', fontsize='small')
ax_cum.set_title('Cumulative Study Time — Year Comparison', fontsize='small')
ax_cum.legend(fontsize='small')
ax_cum.grid(True, alpha=0.3)

fig.suptitle('Weekly Study Time — Year Comparison', fontsize='medium')
fig.tight_layout(rect=[0, 0, 1, 0.96])
plt.show()

# Task 2: calculate study times
start_week = start_of_week
end_week = end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
current_week_total = df2[(df2['Start'] >= start_week) & (df2['Start'] <= end_week)]['duration_hours'].sum()
cumulative_total = df2[df2['Start'] <= end_week]['duration_hours'].sum()

print(f"今週の勉強時間（{start_of_week.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}）: {current_week_total:.1f} 時間")
print(f"累積勉強時間（〜{end_date.strftime('%Y-%m-%d')}）: {cumulative_total:.1f} 時間")