#!/Users/daltkorn5/compsci/anaconda3/bin/python
"""
Script to scrape the stats and salaries of NBA players from Basketball Reference and load them into a postgres database
"""
from bs4 import BeautifulSoup
from urllib.request import urlopen
import src.query_tool as query_tool


def fix_percentages(record):
    """
    If a player has no FG or FT attempts Basketball Reference has their FG% and FT% as '',
    but we need a number for loading the data into postgres
    :param record: The record scraped from Basketball Reference
    :return: The modified record
    """
    for key in ('FT', 'FG'):
        if record[key] == '':
            record[key] = 0
    return record


def scrape_stats(year):
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_totals.html"
    html = urlopen(url)
    soup = BeautifulSoup(html, features="lxml")

    desired_fields = (
        "player",  # player name
        "pos",  # position
        "team_id",  # team
        "g",  # games played
        "gs",  # games started
        "mp",  # minutes played
        "fg",  # field goals made
        "fga",  # field goal attempts
        "ft",  # free throws made
        "fta",  # free throw attempts
        "fg3",  # three-pointers
        "pts",  # points
        "trb",  # total rebounds
        "ast",  # assists
        "stl",  # steals
        "blk",  # blocks
        "tov",  # turnovers
    )

    headers = [th.getText().strip('%') for th in soup.find_all('tr', limit=2)[0].find_all('th', attrs={'data-stat': desired_fields})]
    rows = soup.find_all('tr', {'class': 'full_table'})
    player_stats = [[td.getText() for td in row.find_all('td', attrs={'data-stat': desired_fields})]
                    for row in rows]

    return [fix_percentages(dict(zip(headers, player))) for player in player_stats]


def convert_salary(record):
    """Function to convert the salary from a string to an int
    
    :param record: A record scraped from the Basketball Reference salary page
    :return: The record with the updated salary
    """
    record[2] = int(record[2].strip('$').replace(',', ''))
    return record


def scrape_salaries():
    url = "https://www.basketball-reference.com/contracts/players.html"
    html = urlopen(url)
    soup = BeautifulSoup(html, features="lxml")

    desired_fields = ('y1', 'player', 'team_id')

    headers = [th.getText() for th in soup.find_all('tr', limit=2)[1].find_all('th', attrs={'data-stat': desired_fields})]
    # third header is the salary for 'y1' but since we're ignoring the rest of the years we can just call it salary
    headers[2] = "salary"
    rows = soup.find_all('tr')[2:]
    salaries = [[td.getText() for td in row.find_all('td', attrs={'data-stat': desired_fields})]
                for row in rows]

    return [dict(zip(headers, convert_salary(salary))) for salary in salaries if len(salary) > 0]


def load_stats(stats):
    query = """
    insert into players(
        player_name, 
        position, 
        team, 
        games_played, 
        games_started, 
        minutes_played,
        field_goals,
        field_goal_attempts,
        free_throws,
        free_throw_attempts,
        three_pointers,
        points,
        rebounds,
        assists,
        steals,
        blocks,
        turnovers
    ) values (
        %(Player)s,
        %(Pos)s,
        %(Tm)s,
        %(G)s,
        %(GS)s,
        %(MP)s,
        %(FG)s,
        %(FGA)s,
        %(FT)s,
        %(FTA)s,
        %(3P)s,
        %(PTS)s,
        %(TRB)s,
        %(AST)s,
        %(STL)s,
        %(BLK)s,
        %(TOV)s
    );
    """
    query_tool.insert(query, stats)


def load_salaries(salaries):
    query = """
    insert into salaries(
        player_name,
        team,
        salary
    ) values (
        %(Player)s,
        %(Tm)s,
        %(salary)s
    );
    """
    query_tool.insert(query, salaries)


def main():
    stats = scrape_stats("2020")
    load_stats(stats)

    salaries = scrape_salaries()
    load_salaries(salaries)


if __name__ == '__main__':
    main()
