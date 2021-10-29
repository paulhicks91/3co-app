WITH stat_agg AS (
    SELECT
        map,
        totalBerryDeposits,
        nickname,
        MIN(matchTimestamp) AS matchTimestamp
    FROM `hot-chee-to.match_stats.game_berry_stats`
    WHERE playerId IS NOT NULL
    AND role='Queen'
    AND match_type IN ('Quick Play', 'Ranked')
    AND totalBerryDeposits > 0
    AND bot_player != 'Bot'
    GROUP BY 1,2,3
), new_agg AS (
    SELECT
        map,
        totalBerryDeposits,
        nickname,
        matchTimestamp
    FROM stat_agg
    RIGHT JOIN (
        SELECT
            map,
            MAX(totalBerryDeposits) AS totalBerryDeposits,
            nickname
        FROM stat_agg
        GROUP BY 1,3
    ) USING (map, totalBerryDeposits, nickname)
    WHERE matchTimestamp IS NOT NULL
)

SELECT
    map,
    ARRAY_AGG(STRUCT(
    totalBerryDeposits,
    nickname,
    matchTimestamp) ORDER BY totalBerryDeposits DESC, matchTimestamp, nickname LIMIT 20) AS player_stats
FROM new_agg
GROUP BY 1
ORDER BY map
;