import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import argparse
import datetime

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

# Ensure all weeks from 2025-02-02 onwards are present
all_weeks = pd.date_range(start='2025-02-02', end=weekly.index.max(), freq='7D')
weekly = weekly.reindex(all_weeks, fill_value=0)
weekly.index.name = 'week_start'

end_date = pd.to_datetime(args.end_date)
start_of_week = end_date - pd.Timedelta(days=6)

# Include all data up to the specified end_date in the graph
weekly_graph = weekly[weekly.index <= end_date.normalize()]

# Plot stacked bar chart
plt.style.use('fivethirtyeight')
fig, ax = plt.subplots(figsize=(14, 6))
ind = np.arange(len(weekly_graph))
bottom = np.zeros(len(weekly_graph))
for cat in weekly_graph.columns:
    ax.bar(ind, weekly_graph[cat].values, width=0.8, bottom=bottom, label=cat)
    bottom += weekly_graph[cat].values

ax.set_xticks(ind)
ax.set_xticklabels([d.strftime('%Y-%m-%d') for d in weekly_graph.index], rotation=45, ha='right', fontsize='small')
ax.set_xlabel('Week Start', fontsize='small')
ax.set_ylabel('Hours Studied', fontsize='small')
ax.set_title('Weekly Study Time for Bar Exam Preparation', fontsize='small')
ax.legend(title='Category', fontsize='small')
plt.tight_layout()
plt.show()

# Task 2: calculate study times
start_week = start_of_week
end_week = end_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
current_week_total = df2[(df2['Start'] >= start_week) & (df2['Start'] <= end_week)]['duration_hours'].sum()
cumulative_total = df2[df2['Start'] <= end_week]['duration_hours'].sum()

print(f"今週の勉強時間（{start_of_week.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}）: {current_week_total:.1f} 時間")
print(f"累積勉強時間（〜{end_date.strftime('%Y-%m-%d')}）: {cumulative_total:.1f} 時間")