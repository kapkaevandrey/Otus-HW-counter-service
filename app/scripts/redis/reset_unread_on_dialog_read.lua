-- KEYS:
-- 1 = processed_event_key   (processed:{event_id})
-- 2 = unread_key            (unread:{user_id})
--
-- ARGV:
-- 1 = peer_id               (hash field in unread key)
-- 2 = processed_ttl_sec
--
-- Returns:
-- nil  - event already processed
-- 0    - unread counter reset for peer

local processed_event_key = KEYS[1]
local unread_key = KEYS[2]
local peer_id = ARGV[1]
local processed_ttl_sec = tonumber(ARGV[2])

if redis.call("SET", processed_event_key, "1", "NX", "EX", processed_ttl_sec) then
  redis.call("HSET", unread_key, peer_id, 0)
  return 0
end

return nil
