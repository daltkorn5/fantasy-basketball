from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.request import urlopen
import datetime


class BasketballReferenceWebScraper:
    BASKETBALL_REFERENCE_URL = "https://www.basketball-reference.com"

    def _get_parseable_html(self, url: str) -> BeautifulSoup:
        """Helper function to get parseable HTML for the provided web page

        :param url: The basketball reference page from which you want to scrape data
        :return: A BeautifulSoup object for parsing the HTML for the page you specified
        """
        full_url = f"{self.BASKETBALL_REFERENCE_URL}/{url}"
        html = urlopen(full_url)
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
        months = ("october", "november", "december", "january", "february", "march", "april")
        schedule = []
        for month in months:
            schedule.extend(self._scrape_schedule_for_month(month, year))

        return schedule


if __name__ == "__main__":
    scraper = BasketballReferenceWebScraper()
    scraper.scrape_schedule(2022)
