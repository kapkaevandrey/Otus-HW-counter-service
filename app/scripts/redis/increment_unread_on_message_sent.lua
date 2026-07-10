-- KEYS:
-- 1 = processed_event_key   (processed:{event_id})
-- 2 = unread_key            (unread:{recipient_id})
--
-- ARGV:
-- 1 = sender_id             (hash field in unread key)
-- 2 = processed_ttl_sec
--
-- Returns:
-- nil  - event already processed
-- int  - new unread count for sender after increment

local processed_event_key = KEYS[1]
local unread_key = KEYS[2]
local sender_id = ARGV[1]
local processed_ttl_sec = tonumber(ARGV[2])

if redis.call("SET", processed_event_key, "1", "NX", "EX", processed_ttl_sec) then
  return redis.call("HINCRBY", unread_key, sender_id, 1)
end

return nil
