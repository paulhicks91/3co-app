SELECT lurk_key
FROM `hot-chee-to.match_stats.lurk_queue`
WHERE (ts >= TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL -20 MINUTE) AND expiration_ts IS NULL)
   OR expiration_ts >= CURRENT_TIMESTAMP()
ORDER BY ts
LIMIT 1