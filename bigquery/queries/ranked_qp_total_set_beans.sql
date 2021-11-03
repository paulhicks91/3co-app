WITH match_agg AS (
    SELECT
       id,
       matchTimestamp,
       playerId,
       pnames.nickname,
       SUM(totalBerryDeposits) AS totalBerryDeposits,
       SUM(1) AS totalMaps
    FROM `hot-chee-to.match_stats.game_berry_stats`
    LEFT JOIN `hot-chee-to.match_stats.profile_names` AS pnames USING (playerId)
    WHERE match_type IN ('Ranked', 'Quick Play')
    AND bot_player = 'Player'
    GROUP BY 1, 2, 3, 4
    ORDER BY 5 DESC, 2, 4
), map_beans AS (
    SELECT
        ARRAY_AGG(totalBerryDeposits ORDER BY totalBerryDeposits DESC LIMIT 1)[OFFSET(0)] AS totalBerryDeposits,
        playerId,
        nickname,
        ARRAY_AGG(matchTimestamp ORDER BY totalBerryDeposits DESC, matchTimestamp LIMIT 1)[OFFSET(0)] AS matchTimestamp,
        totalMaps
    FROM match_agg
    GROUP BY 2,3,5
)


SELECT
    totalMaps,
    ARRAY_AGG(STRUCT(totalBerryDeposits, nickname, matchTimestamp) ORDER BY totalBerryDeposits DESC, matchTimestamp, nickname LIMIT 20) AS player_stats
FROM map_beans
WHERE totalMaps >= 3
GROUP BY 1
ORDER BY 1
;