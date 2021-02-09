from lxml import html
import requests, re, math
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import os
import glob
import matplotlib.pyplot as plt
plt.style.use('ggplot')

# build dictionary of win percentage and 3PT percentage for each team
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
        
# identify if given team (Team X) is visitor or home
# figure out if Team X won the game (return bool)
# return 2 column df listing game play by play given the URL
# to the box score on https://sports-reference.com
# NOTE: only look at first half play by play, discard the rest
def get_scores_and_pbp(team, page):
    # get page content
    tree = requests.get(page).content
    soup = BeautifulSoup(tree, 'lxml')
    table = soup.find_all('table')[0]
    df = pd.read_html(table.prettify())[0]

    # get game score
    score = df.iloc[len(df)-2, 3]
    a_score, b_score = [int(x) for x in score.split('-')]

    # clean dataframe columns and discard second half play by play
    df = df.iloc[:, [1, 5]]
    cols = df.columns
    end = df.index[df[cols[0]] == "3rd Q"].tolist()[0]
    df = df.iloc[1:end, :]
    df = df[~df[cols[0]].isin(['1st Q', '2nd Q', '3rd Q', '4th Q'])]

    # extract visitor and home team from title string of webpage
    t = soup.title.string
    visitor = t[:(t.find(" at "))].strip()
    home = t[(t.find(" at ")+4):(t.find("Play")-1)].strip()
    df.columns = [visitor, home]
    print("Score:", {visitor: a_score, home: b_score})
    
    # determine if Team X won
    won = True if (team == home and b_score > a_score) or (team == visitor and a_score > b_score) else False

    # return won boolean and play by play dataframe through first half
    return won, df

# zig zag through the dataframe to get a 1-dimensional list of plays
# in the form of tuples (Team, Play)
def get_merged_plays(df):
    merged_plays = []
    for index, row in df.iterrows():
        for col in df.columns:
            if not pd.isnull(row[col]):
                merged_plays.append((col, row[col]))
    return merged_plays

# use regex expression to tally up made 3s per team
# return dictionary containing final tally in the first half 
def get_threes(cols, plays):
    threes = {cols[0]: 0, cols[1]: 0}
    for idx, event in enumerate(plays):
        if re.match(r'^(?=.*?\bmakes 3-pt\b).*$', event[1]):
            threes[event[0]] += 1
    return threes

# helper func
def get_key(boool):
    if boool:
        return "won"
    else:
        return "lost"

# get all files within box_links directory and scrape all game
# play by play data for 2019-2020 season
# tally up number of advantageous first half three point performances
# and record results separately depending on if Team X won or not
def get_three_tally_by_team():
    folder_path = './box_links'
    # traverse all files in directory
    for filename in glob.glob(os.path.join(folder_path, '*box_links.txt')):
        with open(filename, 'r') as f:
            tally = {'won': [0, 0], 'lost': [0, 0]}
            pages = [s.strip() for s in list(f.readlines())]
            team = pages[0]
            print("--- " + team + " ---", end="\n\n")
            pages = pages[1:]
            for idx, page in enumerate(pages):
                if page.find("2021") != -1:
                    continue
                # edit URLs to get play by play data
                str_idx = page.find("boxscores/") + 10
                page = page[:str_idx] + "pbp/" + page[str_idx:]
                # use try-except statements in case there are wack pages
                try:
                    won, df = get_scores_and_pbp(team, page)
                    plays = get_merged_plays(df)
                    threes = get_threes(df.columns, plays)
                    print("3PT:", threes, end="\n\n")
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

            print(tally, end="\n\n")
            team_info[team]['tally'] = tally

# compute bayes theorem for all teams using dictionary of all 2019-2020 season
# data (includes the playoffs)
# P(A) = prior = probability of winning (estimated via win percentage)
# P(B|A) = likelihood = probability of making more 3s in the first half 
# given Team X wins
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

# visualize posterior probability as bar chart for all teams
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

### MAIN SCRIPT ###

# STEP 1: scrape / accumulate the data
team_info = dict()
parse_files_for_teams("teams_3pts.txt", "teams_win_pcts.txt")
get_three_tally_by_team()

# STEP 2: compute posterior probability for all teams
bayes()

# (EXTRA) save data to CSV
df = pd.DataFrame.from_dict(team_info, orient='index')
df.to_csv('team_info.csv')

# (EXTRA) visualize posterior probability for all teams
visualize_posterior_proba()