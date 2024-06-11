import streamlit as st
import pandas as pd
import re
from io import BytesIO
from aws.aws_funcs import *
from datetime import datetime

S3_BUCKET_NAME_PROJECTS = st.secrets['S3_BUCKET_NAME_PROJECTS']
AWS_ACCESS_KEY_PROJECTS = st.secrets['AWS_ACCESS_KEY_PROJECTS']
AWS_SECRET_KEY_PROJECTS = st.secrets['AWS_SECRET_KEY_PROJECTS']

names = ['Konsta', 'Dmitriy', 'Nikita']

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


def highlight_matching_cells(row):
    styles = [''] * len(row)
    row['Datum'] = pd.to_datetime(row['Datum'])
    if row['Ergebnis'] != '-:-' and row['Datum'] >= datetime.now():
        for name in names:
            if name in row.index:
                idx = row.index.get_loc(name)
                if row[name] == row['Ergebnis']:
                    styles[idx] = 'background-color: lightgreen'
                else:
                    styles[idx] = 'background-color: red'
    return styles


def options_for_group(df):
    df['Datum'] = pd.to_datetime(df['Datum'])
    df_filtered = df[df['Datum'] >= datetime.now()]
    return df_filtered['Begegnung']


def show_df(*args):
    for df in args:
        if 'Ergebnis' in df.columns:
            df_styled = df.style.apply(highlight_matching_cells, axis=1)
            st.dataframe(df_styled)
        else:
            st.write(df)


def show_group(group_name):
    df_1 = get_csv('groups/' + group_name + '.csv')
    df_2 = get_csv('groups/' + group_name + ' Ergebnis' + '.csv')

    if df_1 is not None and df_2 is not None:
        show_df(df_1, df_2)
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
    groups = ['Group A', 'Group B', 'Group C', 'Group D', 'Group E', 'Group F']

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


def results():
    d = {name: [0] for name in names}
    for let in 'ABCDEF':
        df = get_csv(f'groups/Group {let}.csv')
        df['Ergebnis'] = '0-0'
        for name in names:
            d[name][0] += df[df[name] == df['Ergebnis']].shape[0]
    st.dataframe(pd.DataFrame(d)) 


def main():  # sourcery skip: use-named-expression
    st.title('Wer wird gewonnen?')

    tab_bets, tab_results = st.tabs(['Groups', 'Results'])

    with tab_bets:
        bets()  

    with tab_results:
        results()



if __name__ == '__main__':
    main()
