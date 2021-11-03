WITH times AS (
    SELECT
        id,
        map,
        game_id,
        duration,
        matchTimestamp,
        role,
        playerId,
        totalBerryDeposits
    FROM `hot-chee-to.match_stats.game_berry_stats`
    WHERE match_type IN ('Ranked', 'Quick Play')
    AND win_condition = 'Economic'
    AND on_winning_team = 'Winner'
    GROUP BY 1,2,3,4,5,6,7,8
), match_agg AS (
    SELECT
        id,
        map,
        game_id,
        duration,
        matchTimestamp,
        ARRAY_AGG(STRUCT(role, totalBerryDeposits, nickname) ORDER BY role, totalBerryDeposits DESC) AS player
    FROM times
    LEFT JOIN `hot-chee-to.match_stats.profile_names` AS pnames USING (playerId)
    GROUP BY 1,2,3,4,5
)

SELECT
    map,
    ARRAY_AGG(STRUCT(duration, id, game_id, matchTimestamp, player) ORDER BY duration, matchTimestamp LIMIT 20) match_stats
FROM match_agg
GROUP BY 1
ORDER BY 1
;