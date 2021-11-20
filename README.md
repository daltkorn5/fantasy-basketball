# Fantasy Basketball
This repo contains some stuff to help me pick players for my fantasy basketball team.
It gets data from the Yahoo Fantasy Sports API and from scraping Basketball Reference,
and stores those data in a PostgreSQL database.

## Setup
### 1. Set up environment
To be able to use the make commands and just generally run
everything in this repo more easily, add a `BBALL_HOME` environment
variable to your `.bash_profile` that points to the root of this repo.
In other words, add `export BBALL_HOME=/full/path/to/fantasy-basketball`
### 2. Initialize the Database
To initialize the database for the first time, you can run the following:
```shell
make init-db
```
This will create the seven tables you need, **and only needs to be run once**.

## Drafting Players
This section will contain info about how to use the code in here
to help you draft

## Season Setup
At the beginning of the season, after the draft, you can run
```shell
make init-season
```
This will get all the data from Yahoo and Basketball Reference
that you need in order to help you have a better-informed draft.
It loads the Yahoo Fantasy teams, rosters, match-ups, players, 
NBA teams, and schedule into the database