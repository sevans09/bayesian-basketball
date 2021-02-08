from lxml import html
import requests, re, math
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os
import glob
import matplotlib.pyplot as plt
plt.style.use('ggplot')

def parse_files_for_teams(fpath_3, fpath_w):
    with open(fpath_3, "r") as file_3, open(fpath_w, "r") as file_w:
        pcts = [s.strip("\n") for s in list(file_3.readlines())]
        wins = [s.strip("\n") for s in list(file_w.readlines())]
        for i in range(len(pcts)):
            p = pcts[i]
            idx = p.find(".")
            team = p[:idx-1]
            three = float(p[idx:])
            w = wins[i]
            idx = w.find(".")
            team = w[:idx-1]
            win = float(w[idx:])
            team_info[team] = {'3pt_pct': three, 'win_pct': win}
        
def get_three_rate():
    for key1 in team_info.keys():
        s = []
        for key2 in team_info.keys():
            if not key1 == key2:
                s.append(team_info[key1]['3pt_pct'] / (team_info[key1]['3pt_pct'] + team_info[key2]['3pt_pct']))
        team_info[key1]['marginal'] = np.mean(s)
        
def get_scores_and_pbp(team, page):
    result = requests.get(page)
    tree = html.fromstring(result.content)
    tree = html.tostring(tree)
    soup = BeautifulSoup(tree, 'lxml')
    table = soup.find_all('table')[0]
    df = pd.read_html(table.prettify())[0]
    score = df.iloc[len(df)-2, 3]
    a_score, b_score = score.split('-')
    a_score = int(a_score)
    b_score = int(b_score)
    df = df.iloc[:, [1, 5]]
    cols = df.columns
    end = df.index[df[cols[0]] == "3rd Q"].tolist()[0]
    df = df.iloc[:end, :]
    df = df[~df[cols[0]].isin(['1st Q', '2nd Q', '3rd Q', '4th Q'])]
    df = df.iloc[1:, ]
    t = soup.title.string
    visitor = t[:(t.find(" at "))].strip()
    home = t[(t.find(" at ")+4):(t.find("Play")-1)].strip()
    df.columns = [visitor, home]
    won = True if (team == home and b_score > a_score) or (team == visitor and a_score > b_score) else False
    return won, df

def get_merged_plays(df):
    merged_plays = []
    for index, row in df.iterrows():
        for col in df.columns:
            if not pd.isnull(row[col]):
                merged_plays.append((col, row[col]))
    return merged_plays

def get_threes(cols, plays):
    threes = {cols[0]: 0, cols[1]: 0}
    for idx, event in enumerate(plays):
        if re.match(r'^(?=.*?\bmakes 3-pt\b).*$', event[1]):
            threes[event[0]] += 1
    return threes

def get_key(boool):
    if boool:
        return "won"
    else:
        return "lost"

def get_three_tally_by_team():
    folder_path = './box_links'
    for filename in glob.glob(os.path.join(folder_path, '*box_links.txt')):
        with open(filename, 'r') as f:
            tally = {'won': [0, 0], 'lost': [0, 0]}
            pages = [s.strip() for s in list(f.readlines())]
            team = pages[0]
            print(team)
            pages = pages[1:]
            for idx, page in enumerate(pages):
                if page.find("2021") != -1:
                    continue
                str_idx = page.find("boxscores/") + 10
                page = page[:str_idx] + "pbp/" + page[str_idx:]
                try:
                    won, df = get_scores_and_pbp(team, page)
                    plays = get_merged_plays(df)
                    threes = get_threes(df.columns, plays)
                    try:
                        for t in df.columns:
                            if t != team:
                                opponent = t
                        if (threes[team] >= threes[opponent]):
                            tally[get_key(won)][0] += 1
                        else:
                            tally[get_key(won)][1] += 1
                    except:
                        print("uh oh", team, opponent, page)
                except:
                    print("aight bet")
                    print()
            team_info[team]['tally'] = tally

def bayes():
    for key in team_info.keys():
        try:
            likelihood = (team_info[key]['tally']['won'][0] / sum(team_info[key]['tally']['won']))
            prior = team_info[key]['win_pct']
            marginal = (likelihood * prior) + ((team_info[key]['tally']['lost'][0] / sum(team_info[key]['tally']['lost'])) * (1 - prior))
            posterior = (likelihood * prior) / marginal
            team_info[key]['marginal'] = marginal
            team_info[key]['posterior'] = posterior
        except:
            print(key)

def visualize_posterior_proba():
    y = []
    for key in team_info.keys():
        y.append(team_info[key]['posterior'])
    x = list(team_info.keys())
    y, x = zip(*sorted(zip(y, x)))
    print("Average Posterior Probability Across All Teams (2019-2020):", np.mean(y))
    fig = plt.figure()
    plt.bar(x, y, color='#3a7ca5')
    plt.ylim([0, 1])
    plt.xticks(rotation=90)
    plt.ylabel('Posterior Probability')
    plt.title('Probability of Winning Given More 3s Made in First Half')
    plt.show()
    plt.tight_layout()
    fig.savefig('./posterior_plot_all_teams.png', bbox_inches='tight')

team_info = dict()
parse_files_for_teams("teams_3pts.txt", "teams_win_pcts.txt")
get_three_rate()
get_three_tally_by_team()
bayes()
df = pd.DataFrame.from_dict(team_info, orient='index')
df.to_csv('team_info.csv')
visualize_posterior_proba()