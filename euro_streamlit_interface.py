import streamlit as st
import pandas as pd
import re
from io import BytesIO
from aws.aws_funcs import *
from datetime import datetime

try:
    S3_BUCKET_NAME_PROJECTS = st.secrets['S3_BUCKET_NAME_PROJECTS']
    AWS_ACCESS_KEY_PROJECTS = st.secrets['AWS_ACCESS_KEY_PROJECTS']
    AWS_SECRET_KEY_PROJECTS = st.secrets['AWS_SECRET_KEY_PROJECTS']
except Exception:
    print(Exception)

names = ['Konsta', 'Alexey', 'Dmitriy', 'Nikita']

def get_csv(name):
    try:
        if file := get_from_s3(f'{name}'):
            return pd.read_csv(file['Body'])
    except Exception:
            st.error('Object File is not Found. Please, try later!')


def upload_csv(df, csv_name):
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    upload_to_s3_obj(csv_buffer, f'groups/{csv_name}.csv')


def check_credentials(name, password):
    return 1 if password == st.secrets[name.upper()] else 0


def user_credentials(teams_str):
    name = st.selectbox('Choose your name', options=names, index=None)
    password = st.text_area('Enter your password: ', value='')
    if name and password:
        if check_credentials(name, password):
            teams_str = teams_str.lower().replace(' ', '').replace('-', '_')
            return name
        else:
            st.error('Please, check your password')
            return 0


def write_to_file(name, group, game, score):
    df_1 = get_csv(f'groups/{group}.csv')
    df_1.loc[df_1['Begegnung'] == game, name] = '-'.join(score)
    upload_csv(df_1, group)


def write_to_results(name, group, game, score):
    file_key = 'groups/results.txt'
    existing_content = read_s3_file(S3_BUCKET_NAME_PROJECTS, file_key)
    to_write = f'\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t' + f'{name}_{group}_{game}:{"_".join(score)}'.lower().replace('-', '_').replace(' ', '')
    updated_content = existing_content + to_write
    write_to_s3(S3_BUCKET_NAME_PROJECTS, file_key, updated_content)


def options_for_group(df):
    df['Datum'] = pd.to_datetime(df['Datum'])
    df_filtered = df[df['Datum'] >= datetime.now()]
    return df_filtered['Begegnung']

def highlight_matching_cells(row):
    styles = [''] * len(row)
    row['Datum'] = pd.to_datetime(row['Datum'])
    if row['Ergebnis'] != '-:-' and row['Datum'] <= datetime.now():
        for name in names:
            if name in row.index:
                idx = row.index.get_loc(name)
                which_color = yes_or_no(row, name)
                if which_color == 3:
                    styles[idx] = 'background-color: green'
                elif which_color == 1:
                    styles[idx] = 'background-color: lightgreen' 
                else:
                    styles[idx] = 'background-color: lightcoral'
    return styles


def show_df(*args):
    for df in args:
        if 'Ergebnis' in df.columns:
            df_styled = df.style.apply(highlight_matching_cells, axis=1)
            st.dataframe(df_styled)
        else:
            st.write(df)

def unite_dfs(df_full, df_ergebnis):
    df_merged = pd.merge(df_full, df_ergebnis, on='Begegnung', how='left')
    df_merged.rename(columns={'Ergebnis_y': 'Ergebnis'}, inplace=True)
    df_merged.drop('Ergebnis_x', axis=1, inplace=True)
    if 'Alexey' not in df_merged.columns:
        df_merged['Alexey'] = None
    df_merged = df_merged[['Datum', 'Begegnung', 'Ergebnis', 'Konsta', 'Alexey', 'Dmitriy', 'Nikita','Stadion']]
    return df_merged

def create_df_with_ergebnis(group_name):
    df_1 = get_csv('groups/' + group_name + '.csv')
    df_1_ergebnis = get_csv('groups/' + group_name + '_nur_ergebnis' + '.csv')
    df_1 = unite_dfs(df_1, df_1_ergebnis)
    return df_1
    

def show_group(group_name):
    df_1 = create_df_with_ergebnis(group_name)
    if 'Group' in group_name:
        df_2 = get_csv('groups/' + group_name + ' Ergebnis' + '.csv')
    else:
        df_2 = None


    if df_1 is not None and df_2 is not None:
        show_df(df_1, df_2)
    elif df_1 is not None and df_2 is None:
        show_df(df_1)
    else:
        st.error('Object File is not Found. Please, try later!')
        return 0

    return df_1


def select_result_for_game(teams_str):
    teams = [elem.strip() for elem in teams_str.split(' - ')]

    team_1_col, team_2_col = st.columns(2)
    
    with team_1_col:
        team_1 = st.number_input(teams[0], min_value=0, max_value=10, step=1)
    
    with team_2_col:
        team_2 = st.number_input(teams[1], min_value=0, max_value=10, step=1)

    return str(team_1), str(team_2)


def bets():
    groups = ['1-8', '1-4', '1-2', 'Final', 'Group A', 'Group B', 'Group C', 'Group D', 'Group E', 'Group F']

    chosen_group = st.selectbox(label='Choose the group: ', options=groups)

    if chosen_group:
        df_group = show_group(chosen_group)
        choose_game_options = options_for_group(df_group)

        chosen_game = st.selectbox('Choose the game', options=choose_game_options, index=None)

        if chosen_game:
            score = select_result_for_game(chosen_game)

            if score:
                name = user_credentials(chosen_game)
                button_to_submit = st.button('Submit Prediction')
                if name and button_to_submit:
                    write_to_file(name, chosen_group, chosen_game, score)
                    write_to_results(name, chosen_group, chosen_game, score)
                    st.success('Your result is saved!')



def yes_or_no(row, name):
    # st.write(row[name])
    if row['Ergebnis'] != '-:-' and type(row[name]) == str:
        er_1, er_2 = map(int, row['Ergebnis'].split(':')) 
        pr_1, pr_2 = map(int, row[name].split('-'))
        if er_1 == pr_1 and er_2 == pr_2:
            return 3
        elif er_1 > er_2 and pr_1 > pr_2:
            return 1
        elif er_1 < er_2 and pr_1 < pr_2:
            return 1
    return 0
    



def results_groups():
    st.markdown('Groups Results')
    d = {name: [0] for name in names}
    for let in 'ABCDEF':
        df = create_df_with_ergebnis(f'Group {let}')
        
        for name in names:
            df[f'{name}_points'] = df.apply(lambda row: yes_or_no(row, name), axis=1)
            d[name][0] += df[f'{name}_points'].sum()
    
    return pd.DataFrame(d)

def results_final():
    st.markdown('Play-Off Results')
    d = {name: [0] for name in names}
    stages = ['1-8', '1-4', '1-2', 'Final']
    for stage in stages:
        df = create_df_with_ergebnis(stage)
        
        for name in names:
            df[f'{name}_points'] = df.apply(lambda row: yes_or_no(row, name), axis=1)
            d[name][0] += df[f'{name}_points'].sum()
    
    return pd.DataFrame(d)



def main():  # sourcery skip: use-named-expression
    st.title('Wer wird gewonnen?')

    tab_bets, tab_results = st.tabs(['Matches', 'Results'])

    with tab_bets:
        bets()  

    with tab_results:
        st.write(results_final())
        st.write(results_groups())



if __name__ == '__main__':
    main()