#!/usr/bin/env python3
"""
civil 総則のセットごとの所要時間分析スクリプト

ルール:
- 1セット = 講義（3コマ）+ 復習(Anki) + 短答問題
- セット: 1-3, 4-6, 7-9, 10-12, 13-15, 16-18, 19-21, 22-24, 25-27, 28-30, 31-33, 34-36, 37-39, 40-42
- 空白のNotesは前後から判断（基本的に直前のセット）
- 講義→復習→短答の順番は不変
- 範囲指定Anki（例: "40-41 Anki"）は最大コマ番号が含まれるセットに割り当て
"""

import pandas as pd
import re
import sys
from datetime import datetime

def parse_duration(duration_str):
    """Duration文字列を時間（小数）に変換"""
    if pd.isna(duration_str) or duration_str == "":
        return 0.0

    hours = 0.0
    minutes = 0.0

    # "X hr(s) Y min" 形式
    hr_match = re.search(r'(\d+)\s*hrs?', duration_str)
    if hr_match:
        hours = float(hr_match.group(1))

    min_match = re.search(r'(\d+)\s*min', duration_str)
    if min_match:
        minutes = float(min_match.group(1))

    return hours + minutes / 60.0

def format_hours_to_hhmm(hours):
    """時間（小数）をhh:mm形式に変換"""
    hours_int = int(hours)
    minutes_int = int((hours - hours_int) * 60)
    return f"{hours_int}:{minutes_int:02d}"

def extract_lecture_numbers(notes):
    """Notesからコマ番号を抽出（複数の場合もあり）"""
    if pd.isna(notes) or notes == "":
        return []

    notes_str = str(notes)
    numbers = []

    # "40-41" のような範囲指定
    range_match = re.search(r'(\d+)-(\d+)', notes_str)
    if range_match:
        start = int(range_match.group(1))
        end = int(range_match.group(2))
        numbers.extend(range(start, end + 1))
        return numbers

    # "35,36" のようなカンマ区切り
    if ',' in notes_str:
        parts = notes_str.split(',')
        for part in parts:
            match = re.search(r'(\d+)', part)
            if match:
                numbers.append(int(match.group(1)))
        if numbers:
            return numbers

    # 単一の数字（例: "24", "42途中", "41民法総則終了..."）
    match = re.match(r'^(\d+)', notes_str.strip())
    if match:
        numbers.append(int(match.group(1)))

    return numbers

def get_activity_type(notes):
    """活動タイプを判定: 講義, Anki, 短答, その他"""
    if pd.isna(notes) or notes == "":
        return "空白"

    notes_str = str(notes).lower()

    if "anki" in notes_str or "復習" in notes_str:
        return "Anki"
    elif "短答" in notes_str or "過去問" in notes_str:
        return "短答"
    elif re.match(r'^\d+', notes_str.strip()):
        return "講義"
    else:
        return "その他"

def get_set_from_lecture_num(lecture_num):
    """コマ番号からセット番号を取得"""
    if lecture_num is None or lecture_num < 1:
        return None
    return ((lecture_num - 1) // 3) + 1

def main():
    # コマンドライン引数からCSVパスを取得
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        print("使い方: python src/civil_sousoku_analysis.py <CSVファイルパス>")
        print("例: python src/civil_sousoku_analysis.py 'Time Tracking 2026-01-02.csv'")
        sys.exit(1)

    print(f"CSVファイル: {csv_path}\n")

    # CSVを読み込み
    df = pd.read_csv(csv_path)

    # civil 総則のみ抽出
    df_civil = df[df['Category'] == 'civil 総則'].copy()

    # Duration を時間に変換
    df_civil['Hours'] = df_civil['Duration'].apply(parse_duration)

    # 日付を解析してソート（古い順）
    df_civil['DateTime'] = pd.to_datetime(df_civil['Start'])
    df_civil = df_civil.sort_values('DateTime').reset_index(drop=True)

    # 各行にセット番号を割り当て
    current_set = 1  # 現在追跡中のセット（最初はセット1とする）
    set_assignments = []

    for idx, row in df_civil.iterrows():
        notes = row['Notes']
        activity = get_activity_type(notes)
        lecture_nums = extract_lecture_numbers(notes)

        assigned_set = None

        if activity == "講義":
            # 講義の場合、コマ番号から直接セットを決定
            if lecture_nums:
                lecture_num = max(lecture_nums)  # 複数ある場合は最大値
                assigned_set = get_set_from_lecture_num(lecture_num)
                current_set = assigned_set

        elif activity == "Anki":
            # Ankiの場合、Notesに含まれる最大コマ番号のセットに割り当て
            if lecture_nums:
                max_lecture = max(lecture_nums)
                assigned_set = get_set_from_lecture_num(max_lecture)
            else:
                # コマ番号がない場合は現在のセットに割り当て
                assigned_set = current_set

        elif activity == "短答":
            # 短答は直前のセットに割り当て
            assigned_set = current_set

        elif activity == "空白" or activity == "その他":
            # 空白やその他は直前のセットに割り当て
            assigned_set = current_set

        set_assignments.append(assigned_set)

    df_civil['Set'] = set_assignments

    # 未割り当てデータの確認
    df_unassigned = df_civil[pd.isna(df_civil['Set'])].copy()
    total_rows = len(df_civil)
    assigned_rows = len(df_civil[pd.notna(df_civil['Set'])])
    unassigned_rows = len(df_unassigned)

    print("=== データ統計 ===\n")
    print(f"総データ数: {total_rows}")
    print(f"セット割り当て済み: {assigned_rows}")
    print(f"セット未割り当て: {unassigned_rows}")
    print()

    if unassigned_rows > 0:
        print("=== セット未割り当てデータの詳細 ===\n")
        print(df_unassigned[['DateTime', 'Notes', 'Hours']].to_string())
        print(f"\n未割り当てデータの合計時間: {format_hours_to_hhmm(df_unassigned['Hours'].sum())}")
        print("\n")

    # セットごとに集計
    print("=== セットごとの時間集計 ===\n")

    set_summary = {}
    sets = sorted([s for s in df_civil['Set'].unique() if pd.notna(s)])

    for set_num in sets:
        df_set = df_civil[df_civil['Set'] == set_num].copy()

        # コマ範囲
        start_lecture = int((set_num - 1) * 3 + 1)
        end_lecture = int(set_num * 3)

        # 講義時間
        df_set['ActivityType'] = df_set['Notes'].apply(get_activity_type)
        lecture_hours = df_set[df_set['ActivityType'] == '講義']['Hours'].sum()

        # Anki時間
        anki_hours = df_set[df_set['ActivityType'] == 'Anki']['Hours'].sum()

        # 短答時間
        tanto_hours = df_set[df_set['ActivityType'] == '短答']['Hours'].sum()

        # その他・空白
        other_hours = df_set[df_set['ActivityType'].isin(['その他', '空白'])]['Hours'].sum()

        # 合計
        total_hours = lecture_hours + anki_hours + tanto_hours + other_hours

        set_summary[set_num] = {
            'range': f"{start_lecture}-{end_lecture}",
            'lecture': lecture_hours,
            'anki': anki_hours,
            'tanto': tanto_hours,
            'other': other_hours,
            'total': total_hours
        }

        print(f"セット{int(set_num)} (コマ {start_lecture}-{end_lecture}):")
        print(f"  講義:         {format_hours_to_hhmm(lecture_hours)}")
        print(f"  復習(Anki):   {format_hours_to_hhmm(anki_hours)}")
        print(f"  短答問題:     {format_hours_to_hhmm(tanto_hours)}")
        if other_hours > 0:
            print(f"  その他:       {format_hours_to_hhmm(other_hours)}")
        print(f"  合計:         {format_hours_to_hhmm(total_hours)}")
        print()

    # サマリーテーブル
    print("\n=== サマリーテーブル ===\n")
    print("セット  | コマ範囲 | 講義  | Anki  | 短答  | その他 | 合計")
    print("-" * 70)
    for set_num in sets:
        s = set_summary[set_num]
        lecture_str = format_hours_to_hhmm(s['lecture'])
        anki_str = format_hours_to_hhmm(s['anki'])
        tanto_str = format_hours_to_hhmm(s['tanto'])
        other_str = format_hours_to_hhmm(s['other'])
        total_str = format_hours_to_hhmm(s['total'])
        print(f"  {int(set_num):2d}    | {s['range']:7s} | {lecture_str:5s} | {anki_str:5s} | {tanto_str:5s} | {other_str:6s} | {total_str:5s}")

    print()

if __name__ == "__main__":
    main()
