# quick poke at the bucket math, delete me
from notify.ratelimit import TokenBucketLimiter
l = TokenBucketLimiter(rate=1.0, burst=3)
print([l.allow("x") for _ in range(5)])
