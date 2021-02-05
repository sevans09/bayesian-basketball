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

    print(game_url)
    
events = [('chicago', 'timeout'), ('philadelphia', 'Turnover'), ('chicago', 'makes a dunk')]

for event in events:
    print("event is", event[1])
    if re.match(r"^.*\b(timeout)\b.*$", event[1]):
        print("found a timeout")
    elif re.match(r'^.*\b(Turnover)\b.*$', event[1]):
        print("found a turnover")
    elif re.match(r'^(?=.*?\bmakes\b).*$', event[1]):
        print("found a  shot")

# read csv into tuples