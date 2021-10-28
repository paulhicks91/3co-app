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
)

SELECT
    map,
    ARRAY_AGG(STRUCT(
    totalBerryDeposits,
    nickname,
    matchTimestamp) ORDER BY totalBerryDeposits DESC, matchTimestamp, nickname LIMIT 20) AS player_stats
FROM stat_agg
GROUP BY 1
ORDER BY map
;