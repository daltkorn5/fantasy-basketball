from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.request import urlopen
import time
import requests
import datetime

from src.utils.utils import sanitize_player_name


class BasketballReferenceWebScraper:
    BASKETBALL_REFERENCE_URL = "https://www.basketball-reference.com"

    def _get_parseable_html(self, url: str) -> BeautifulSoup:
        """Helper function to get parseable HTML for the provided web page

        :param url: The basketball reference page from which you want to scrape data
        :return: A BeautifulSoup object for parsing the HTML for the page you specified
        """
        full_url = f"{self.BASKETBALL_REFERENCE_URL}/{url}"
        html = requests.get(
            full_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        ).content.decode("utf-8")
        return BeautifulSoup(html, features="lxml")

    def _scrape_schedule_for_month(self, month: str, year: int) -> List[Dict[str, Any]]:
        """Scrapes the NBA schedule for the given month and year

        :param month: The month whose schedule you want
        :param year: The year whose schedule you want
        :return: A list of dicts with the NBA schedule for the given month and year. Looks like:
            [
                {
                    "game_date": datetime.date(2022, 1, 1),
                    "home_team": "Milwaukee Bucks",
                    "visiting_team": "New Orleans Pelicans"
                },
                {
                    "game_date": datetime.date(2022, 1, 1),
                    "home_team": "Detroit Pistons",
                    "visiting_team": "San Antonio Spurs"
                },
                ...
            ]
        """
        html = self._get_parseable_html(f"leagues/NBA_{year}_games-{month}.html")
        table_body: BeautifulSoup = html.find('tbody')
        table_rows = table_body.find_all('tr')

        schedule = []
        for row in table_rows:
            date_str = row.find('th', attrs={"data-stat": "date_game"}).text
            game_date = datetime.datetime.strptime(date_str, "%a, %b %d, %Y").date()

            visiting_team = row.find('td', attrs={"data-stat": "visitor_team_name"}).text
            home_team = row.find('td', attrs={"data-stat": "home_team_name"}).text

            schedule.append({
                "game_date": game_date,
                "home_team": home_team,
                "visiting_team": visiting_team
            })

        return schedule

    def scrape_schedule(self, year: int) -> List[Dict[str, Any]]:
        """Scrapes the whole NBA schedule for the given year

        :param year: The year whose schedule you want to scrape
        :return: A list of dicts with the NBA schedule for the given month and year. Looks like:
            [
                {
                    "game_date": datetime.date(2022, 1, 1),
                    "home_team": "Milwaukee Bucks",
                    "visiting_team": "New Orleans Pelicans"
                },
                {
                    "game_date": datetime.date(2022, 1, 1),
                    "home_team": "Detroit Pistons",
                    "visiting_team": "San Antonio Spurs"
                },
                ...
            ]
        """
        print(f"Getting NBA schedule for {year}")
        months = ("october", "november", "december", "january", "february", "march", "april")
        schedule = []
        for month in months:
            schedule.extend(self._scrape_schedule_for_month(month, year))
            time.sleep(10)

        return schedule

    @staticmethod
    def _convert_minutes_played(minutes_played: str) -> float:
        """Convert minutes played from a string to a float

        :param minutes_played: Minutes played as a string. In the form MM:SS
        :return: Minutes played as a float
        """
        minutes, seconds = minutes_played.split(":")
        return round(int(minutes) + (int(seconds) / 60), 2)

    def scrape_game_log(self, game_date: datetime.date, home_team: str, away_team: str) -> List[Dict[str, Any]]:
        """Scrape the box score for a single NBA game

        :param game_date: The date the game was played
        :param home_team: The three letter code for the home team
        :param away_team: The three letter code for the away team
        :return: The box score of the desired game
        """
        game_date_str = game_date.strftime("%Y%m%d")
        html = self._get_parseable_html(f"boxscores/{game_date_str}0{home_team}.html")
        tables: BeautifulSoup = html.find_all("table", {"class": "stats_table"})

        # Basketball reference has many "stats_table" tables on its box score page,
        # but these are the two that we want
        home_team_box_score_table = f"box-{home_team}-game-basic"
        away_team_box_score_table = f"box-{away_team}-game-basic"

        desired_tables = [
            table for table in tables if table.get("id") in (home_team_box_score_table, away_team_box_score_table)
        ]

        desired_fields = (
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

        game_log = []
        for table in desired_tables:
            table_header: BeautifulSoup = table.find("thead")
            header_row = table_header.find_all("tr", limit=2)[1]
            headers = [th.text.lower() for th in header_row.find_all("th", attrs={"data-stat": desired_fields})]

            table_body: BeautifulSoup = table.find("tbody")
            rows = table_body.find_all("tr", class_=lambda x: x != "thead")
            for row in rows:
                player_name = row.find("th", attrs={"data-stat": "player"}).text

                # This means the player didn't play
                if row.find("td", attrs={"data-stat": "reason"}):
                    continue

                stats = [td.text for td in row.find_all("td", attrs={"data-stat": desired_fields})]
                stats_dict = dict(zip(headers, stats))
                # We'll get minutes played separately since we need to convert it into a float
                minutes_played = row.find("td", attrs={"data-stat": "mp"}).text

                stats_dict.update({
                    "player_name": sanitize_player_name(player_name),
                    "mp": self._convert_minutes_played(minutes_played),
                    "game_date": game_date
                })
                game_log.append(stats_dict)

        return game_log


if __name__ == "__main__":
    scraper = BasketballReferenceWebScraper()
    scraper.scrape_schedule(2023)
