CREATE OR REPLACE FUNCTION get_season_end()
RETURNS DATE
LANGUAGE plpgsql
AS
$$
DECLARE
    season_end DATE;
BEGIN
    SELECT week_end INTO season_end FROM match_ups where week_no = (select max(week_no) from match_ups);
    RETURN season_end;
END;
$$;