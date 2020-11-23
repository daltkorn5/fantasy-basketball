create table players(
    player_name varchar not null,
    position varchar not null,
    team varchar,
    games_played int,
    games_started int,
    field_goal_percentage real,
    free_throw_percentage real,
    three_pointers real,
    points real,
    rebounds real,
    assists real,
    steals real,
    blocks real,
    turnovers real,
    is_available bool not null default true
);

create index players_player_name_index on players (player_name);
create index players_is_available_index on players (is_available);
create index players_position_index on players (position);