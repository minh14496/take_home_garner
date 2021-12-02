import pandas as pd
import numpy as np
import sqlite3


def get_tables(db_file):
    """
    get_tables print out tables name from the SQLite database specified
    by the db_file

    Return:
    """

    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print(f"Table Name : {cursor.fetchall()}")
    conn.close()


def create_dataframe(table, db_file) -> pd.DataFrame:
    """
    create_dataframe create pandas dataframe using table name
    from the SQLite database specified by the db_file

    Returns: pd.DataFrame

    """

    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    df = pd.DataFrame()
    try:
        df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
        df.reset_index(drop=True, inplace=True)
    except:
        print('There is no table with that name')
    conn.close()
    return df


def find_codes(df, codes, filter=1) -> pd.DataFrame:
    """
    find_codes find all the rows that have input medical codes
    There are 3 filter:
    - 1: Keep all the rows that have the codes
    - 2: Keep all the rows that don't have the codes
    - 3: Keep all the rows from the original dataframe

    Returns: pd.DataFrame
    """

    df['new_col'] = np.zeros(len(df), dtype=int)
    for code in codes:
        df['new_col'] += [1 if x >= 1 else 0 for x in np.sum(df.values == code, 1)]
    if filter == 1:
        df_new = df[df['new_col'] >= 1].copy()
        df_new.reset_index(drop=True, inplace=True)
        df_new.drop(columns='new_col', inplace=True)
    elif filter == 2:
        df_new = df[df['new_col'] < 1].copy()
        df_new.reset_index(drop=True, inplace=True)
        df_new.drop(columns='new_col', inplace=True)
    elif filter == 3:
        df_new = df.copy()
    return df_new


def get_list_codes(start, end, step):
    """
    get_list_codes Input a range of number with step and return a
    list of code in which codes are strings

    Returns: list of codes
    """

    if end <= start:
        return f'Ending value must be bigger than starting value'
    if step <= 0:
        return f'Step must be larger than 0'
    code_list = []
    num = start
    if step < 1:
        round_to = int(np.log10(1/step))
        while num < end:
            code_list.append(str(round(num, round_to)))
            num += step
    else:
        while num <= end:
            code_list.append(str(num))
            num += step
    return code_list


def violation_rate(left, right, codes) -> pd.DataFrame:
    """
    violation_rate find not-recommended procedure for a diagnosis
    The right table can be any table as long as it has the same encounter_key
    col with the left table

    Returns: pd.DataFrame with violation rate column
    """
    
    df = left.merge(right, how='left', on='encounter_key')
    df_new = find_codes(df, codes, filter=3)
    df_new = df_new.groupby('encounter_key').sum().reset_index(drop=True)
    left['violate'] = df_new['new_col']
    df_violate = left.groupby('patient_id').sum().reset_index()
    final_df = df_violate.merge(left[['doctor_id', 'patient_id']], how='right', on='patient_id')
    final_df['number_of_patients'] = np.ones(len(final_df), dtype=int)
    final_df['violate'] = final_df['violate'].apply(lambda x: 1 if x >= 1 else 0)
    final_df = final_df.groupby('doctor_id').sum().reset_index()
    final_df['rate'] = final_df['violate']/final_df['number_of_patients']
    return final_df
