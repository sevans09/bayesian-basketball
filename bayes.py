from lxml import html
import requests, re, math

# Site to begin scraping
page = "https://www.baseball-reference.com/teams/PIT/2020-schedule-scores.shtml"

# Scrape start page into tree
result = requests.get(page)
tree = html.fromstring(result.content)

# Isolate schedule table
schedule = tree.xpath('//table[@id="team_schedule"]')

# Loop through every row
rows = schedule[0].xpath('./tbody/tr')
for row in rows:
    # Get the boxscore column that contains the game url
    boxscore_td = row.xpath('./td[@data-stat="boxscore"]')
    if len(boxscore_td) == 0:
        continue
    
    # Get the game path
    game_href = boxscore_td[0].xpath('./a/@href')[0]
    
    # Get the root url of the page variable
    regex = r'.*\.com'
    page_root = re.findall(regex, page)[0]
    
    # Formulate the final game base_url
    game_url = '{}{}'.format(page_root, game_href)
    
    # regex to find makes ___ shot
    ^(?=.*?\bmakes\b)(?=.*?\bshot\b).*$
    # regex to find turnover
    ^.*\b(Turnover)\b.*$
    # regex to get timeout
    \^.*\b(timeout)\b.*$

    print(game_url)
    