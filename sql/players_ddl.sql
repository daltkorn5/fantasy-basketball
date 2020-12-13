create table players(
    player_name varchar not null,
    position varchar not null,
    team varchar,
    games_played int,
    games_started int,
    minutes_played int,
    field_goals int,
    field_goal_attempts int,
    free_throws int,
    free_throw_attempts int,
    three_pointers int,
    points int,
    rebounds int,
    assists int,
    steals int,
    blocks int,
    turnovers int,
    is_available bool not null default true
);

create index players_player_name_index on players (player_name);
create index players_is_available_index on players (is_available);
create index players_position_index on players (position);