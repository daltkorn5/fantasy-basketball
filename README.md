# Fantasy Basketball
This repo contains some stuff to help me pick players for my fantasy basketball team.
It gets data from the Yahoo Fantasy Sports API and from scraping Basketball Reference,
and stores those data in a PostgreSQL database.

## Setup
### 1. Initialize the Database
To initialize the database for the first time, you can run the following:
```shell
make init-db
```
This will create the seven tables you need, **and only needs to be run once**.