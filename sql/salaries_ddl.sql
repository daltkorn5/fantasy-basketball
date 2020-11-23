create table salaries(
    player_name varchar not null,
    team varchar,
    salary bigint not null
);

create index salaries_player_name_index on salaries (player_name);