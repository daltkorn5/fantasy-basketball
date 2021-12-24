"""Spotrac is the definitive source of NBA player salaries so that's where we'll get them from"""
from typing import List, Dict, Any

from bs4 import BeautifulSoup

import requests

from src.utils.utils import sanitize_player_name

import logging


logging.getLogger("chardet.charsetprober").setLevel(logging.INFO)


class SpotracScraperTool:
    SPOTRAC_URL = "https://www.spotrac.com"

    @staticmethod
    def _format_year_for_url(year: int) -> str:
        """Helper function to format the year for the Spotrac URL

        This assumes that the provided year is the year that the NBA season
        ends in. For example, if provided 2022, the formatted year will be:
            2021-22

        :param year: The year in which the NBA season ends
        :return: The year formatted for the spotrac URL
        """
        prev_year = year - 1
        return f"{prev_year}-{str(year)[2:]}"

    def _get_parseable_html(self, url: str) -> BeautifulSoup:
        """Get the HTML for Spotrac's salary list

        For reasons I don't totally understand, in order to get all the results
        you need to make a post request to Spotrac. A get request or a urlopen
        call only gets the first 100 results

        :param url: The URL for the page with all the NBA salaries
        :return:
        """
        response = requests.post(f"{self.SPOTRAC_URL}/{url}", data={"ajax": True, "mobile": False})
        assert response.status_code == 200

        return BeautifulSoup(response.content, features="lxml")

    @staticmethod
    def _convert_salary(salary: str) -> int:
        """Helper function to convert the salary string into an integer

        :param salary: The string representation of the salary
        :return: The salary as an integer
        """
        return int(salary.strip().replace("$", "").replace(",", ""))

    def scrape_salaries(self, year: int) -> List[Dict[str, Any]]:
        """Scrape the NBA salaries for the given year from Spotrac

        :param year: The year in which the NBA season ends
        :return: A list of dicts containing the salary info of each player. Looks like:
            [
                {
                    "player_name": "Michael Jordan",
                    "salary": 1000000000
                },
                {
                    "player_name": "Derrick Rose",
                    "salary": 12345678
                }
            ]
        """
        year_for_url = self._format_year_for_url(year)
        url = f"/nba/rankings/{year_for_url}/base/"

        html = self._get_parseable_html(url)
        table_body: BeautifulSoup = html.find('tbody')
        table_rows = table_body.find_all('tr')

        salaries = []
        for row in table_rows:
            player_name = row.find("h3").text
            salary_str = row.find("span", {"class": "info"}).text
            salary = self._convert_salary(salary_str)
            salaries.append({
                "player_name": sanitize_player_name(player_name),
                "salary": salary
            })

        return salaries
