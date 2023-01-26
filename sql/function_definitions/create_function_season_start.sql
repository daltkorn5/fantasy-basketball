CREATE OR REPLACE FUNCTION get_season_start()
RETURNS DATE
LANGUAGE plpgsql
AS
$$
DECLARE
    season_start DATE;
BEGIN
    SELECT week_start INTO season_start FROM match_ups where week_no = 1;
    RETURN season_start;
END;
$$;