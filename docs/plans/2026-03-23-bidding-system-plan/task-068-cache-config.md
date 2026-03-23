# Task 068: Cache Strategy Configuration (缓存策略配置)

## Task Header

| Field | Value |
|-------|-------|
| Task ID | 068 |
| Name | Cache Strategy Configuration |
| Type | config |
| Dependencies | Task 067 (Database Optimization) - cache layer complements DB |
| Created | 2026-03-23 |
| Estimated Effort | 6-10 hours |

## Description

Implement a comprehensive Redis caching strategy for the bidding system to reduce database load and improve response times for frequently accessed data. This includes caching active auction listings, bid counts, user bid history, and implementing proper cache invalidation strategies to ensure data consistency during concurrent bidding operations.

## Files to Create/Modify

### Create
- `src/cache/redis-client.ts` - Redis connection and client configuration
- `src/cache/cache-keys.ts` - Centralized cache key definitions
- `src/cache/strategies/auction-cache.ts` - Auction-specific caching logic
- `src/cache/strategies/bid-cache.ts` - Bid-specific caching logic
- `src/cache/invalidation.ts` - Cache invalidation rules and triggers
- `src/middleware/cache-middleware.ts` - Express/Route cache middleware
- `config/cache.ts` - Cache configuration and TTL settings

### Modify
- `src/services/AuctionService.ts` - Integrate cache layer
- `src/services/BidService.ts` - Add cache reads/writes
- `src/services/LeaderboardService.ts` - Cache ranking data
- `docker-compose.yml` - Add Redis service configuration
- `.env.example` - Add Redis connection variables

## Implementation Steps

### Step 1: Redis Client Setup

```typescript
// src/cache/redis-client.ts
import Redis from 'ioredis';

export const redisClient = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  db: parseInt(process.env.REDIS_DB || '0'),
  maxRetriesPerRequest: 3,
  enableReadyCheck: true,
  lazyConnect: true,
});

// Connection pooling
export const redisPub = new Redis({ host: process.env.REDIS_HOST });
export const redisSub = new Redis({ host: process.env.REDIS_HOST });
```

### Step 2: Cache Key Strategy

```typescript
// src/cache/cache-keys.ts
export const CacheKeys = {
  // Auction keys
  activeAuctions: (page: number, limit: number) => `auctions:active:${page}:${limit}`,
  auctionDetail: (id: string) => `auction:${id}:detail`,
  auctionBids: (id: string) => `auction:${id}:bids`,
  auctionBidCount: (id: string) => `auction:${id}:bid_count`,
  auctionTopBid: (id: string) => `auction:${id}:top_bid`,

  // User keys
  userBids: (userId: string, page: number) => `user:${userId}:bids:${page}`,
  userWatchlist: (userId: string) => `user:${userId}:watchlist`,

  // Leaderboard keys
  bidLeaderboard: (auctionId: string) => `leaderboard:${auctionId}`,
  dailyStats: (date: string) => `stats:daily:${date}`,

  // TTL constants
  TTL_SHORT: 60,      // 1 minute
  TTL_MEDIUM: 300,    // 5 minutes
  TTL_LONG: 3600,     // 1 hour
  TTL_EXTENDED: 86400 // 24 hours
};
```

### Step 3: Auction Caching Strategy

```typescript
// src/cache/strategies/auction-cache.ts
import { redisClient } from '../redis-client';
import { CacheKeys } from '../cache-keys';

export class AuctionCache {
  // Cache active auctions list
  async cacheActiveAuctions(auctions: Auction[], page: number, limit: number): Promise<void> {
    const key = CacheKeys.activeAuctions(page, limit);
    await redisClient.setex(key, CacheKeys.TTL_SHORT, JSON.stringify(auctions));
  }

  // Get cached active auctions
  async getActiveAuctions(page: number, limit: number): Promise<Auction[] | null> {
    const key = CacheKeys.activeAuctions(page, limit);
    const cached = await redisClient.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  // Cache auction detail with longer TTL
  async cacheAuctionDetail(auction: Auction): Promise<void> {
    const key = CacheKeys.auctionDetail(auction.id);
    await redisClient.setex(key, CacheKeys.TTL_MEDIUM, JSON.stringify(auction));
  }

  // Cache bid count for auction (useful for display)
  async cacheBidCount(auctionId: string, count: number): Promise<void> {
    const key = CacheKeys.auctionBidCount(auctionId);
    await redisClient.setex(key, CacheKeys.TTL_SHORT, count.toString());
  }

  // Increment bid count atomically
  async incrementBidCount(auctionId: string): Promise<void> {
    const key = CacheKeys.auctionBidCount(auctionId);
    await redisClient.incr(key);
    await redisClient.expire(key, CacheKeys.TTL_SHORT);
  }
}
```

### Step 4: Bid Caching Strategy

```typescript
// src/cache/strategies/bid-cache.ts
import { redisClient } from '../redis-client';
import { CacheKeys } from '../cache-keys';

export class BidCache {
  // Cache top bids using Redis sorted set
  async cacheTopBids(auctionId: string, bids: Bid[]): Promise<void> {
    const key = CacheKeys.auctionTopBid(auctionId);
    const pipeline = redisClient.pipeline();

    bids.forEach(bid => {
      pipeline.zadd(key, bid.amount, JSON.stringify(bid));
    });

    pipeline.expire(key, CacheKeys.TTL_SHORT);
    await pipeline.exec();
  }

  // Get top bids from cache
  async getTopBids(auctionId: string, limit: number = 10): Promise<Bid[]> {
    const key = CacheKeys.auctionTopBid(auctionId);
    const results = await redisClient.zrevrange(key, 0, limit - 1);
    return results.map(r => JSON.parse(r));
  }

  // Cache user bid history
  async cacheUserBids(userId: string, page: number, bids: Bid[]): Promise<void> {
    const key = CacheKeys.userBids(userId, page);
    await redisClient.setex(key, CacheKeys.TTL_MEDIUM, JSON.stringify(bids));
  }
}
```

### Step 5: Cache Invalidation Rules

```typescript
// src/cache/invalidation.ts
export class CacheInvalidator {
  // Invalidate auction-related caches when bid is placed
  async onNewBid(auctionId: string, userId: string): Promise<void> {
    const pipeline = redisClient.pipeline();

    // Invalidate auction detail (bid count changed)
    pipeline.del(CacheKeys.auctionDetail(auctionId));
    pipeline.del(CacheKeys.auctionBidCount(auctionId));

    // Invalidate top bids (new bid may affect ranking)
    pipeline.del(CacheKeys.auctionTopBid(auctionId));

    // Invalidate active auctions list (bid count display)
    pipeline.keys('auctions:active:*').then(keys => {
      keys.forEach(key => pipeline.del(key));
    });

    // Invalidate user bid caches
    pipeline.keys(`user:${userId}:bids:*`).then(keys => {
      keys.forEach(key => pipeline.del(key));
    });

    await pipeline.exec();
  }

  // Invalidate when auction ends
  async onAuctionEnd(auctionId: string): Promise<void> {
    const pipeline = redisClient.pipeline();

    pipeline.del(CacheKeys.auctionDetail(auctionId));
    pipeline.del(CacheKeys.auctionBids(auctionId));
    pipeline.del(CacheKeys.auctionBidCount(auctionId));
    pipeline.del(CacheKeys.auctionTopBid(auctionId));
    pipeline.keys('auctions:active:*').then(keys => {
      keys.forEach(key => pipeline.del(key));
    });

    await pipeline.exec();
  }
}
```

### Step 6: Configuration Settings

```typescript
// config/cache.ts
export const cacheConfig = {
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    retryStrategy: (times: number) => {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
  },

  ttl: {
    activeAuctions: 60,      // 1 minute
    auctionDetail: 300,      // 5 minutes
    bidCount: 30,            // 30 seconds
    topBids: 60,             // 1 minute
    userBids: 300,           // 5 minutes
    leaderboard: 300,        // 5 minutes
  },

  // Circuit breaker settings
  circuitBreaker: {
    failureThreshold: 5,
    resetTimeout: 30000,
    enabled: true,
  },
};
```

### Step 7: Middleware Integration

```typescript
// src/middleware/cache-middleware.ts
import { redisClient } from '../cache/redis-client';

export function cacheMiddleware(ttl: number = 300) {
  return async (req, res, next) => {
    const key = `cache:${req.originalUrl}`;

    try {
      const cached = await redisClient.get(key);
      if (cached) {
        return res.json(JSON.parse(cached));
      }

      // Override res.json to cache response
      const originalJson = res.json.bind(res);
      res.json = (data) => {
        redisClient.setex(key, ttl, JSON.stringify(data));
        return originalJson(data);
      };

      next();
    } catch (error) {
      // On cache error, proceed without caching
      next();
    }
  };
}
```

## Verification Steps

### Functional Tests
- [ ] Verify cache hit rate > 80% for auction list endpoint
- [ ] Verify cache invalidation on new bid submission
- [ ] Verify stale data is not served after auction updates
- [ ] Test circuit breaker behavior during Redis failure

### Performance Tests
```bash
# Test cache hit performance
wrk -t12 -c400 -d30s "http://localhost:3000/api/auctions/active"

# Expected: < 10ms response time for cached responses
# Expected: < 50ms response time for cache misses
```

### Redis Monitoring
- [ ] Check memory usage: `INFO memory`
- [ ] Monitor eviction rate: `INFO stats`
- [ ] Verify key expiration rates
- [ ] Set up alerts for Redis memory > 80%

### Cache Consistency Tests
- [ ] Concurrent bid test: verify no stale bid counts
- [ ] Auction end test: verify immediate cache clearance
- [ ] Race condition test: bid submission during cache refresh

### Integration Verification
```typescript
// Test script
describe('Cache Integration', () => {
  it('should cache auction list', async () => {
    // First request - cache miss
    const r1 = await getActiveAuctions();
    expect(r1.fromCache).toBe(false);

    // Second request - cache hit
    const r2 = await getActiveAuctions();
    expect(r2.fromCache).toBe(true);
  });

  it('should invalidate on new bid', async () => {
    await placeBid(auctionId, amount);
    const cached = await redisClient.get(`auction:${auctionId}:bid_count`);
    expect(cached).toBeNull();
  });
});
```

## Rollback Plan

1. Disable caching via feature flag
2. Set all cache TTL to 0 (immediate expiration)
3. Clear all bidding-related cache keys
4. Restart services without cache middleware

## Git Commit Message

```
config(cache): implement Redis caching strategy for bidding system

- Add Redis client with connection pooling and retry logic
- Create cache key naming convention for auctions and bids
- Implement auction list caching with 1-minute TTL
- Add bid count cache with atomic increment support
- Create cache invalidation triggers for bid operations
- Add circuit breaker for Redis failure handling
- Configure cache TTL values based on data volatility
- Add cache middleware for route-level caching
- Include Redis service in docker-compose configuration

Task: 068
```

## Notes

- Cache TTL should be shorter for volatile data (bid counts: 30s)
- Use Redis sorted sets for leaderboard/ranking data
- Implement cache warming for popular auctions
- Coordinate invalidation strategy with Task 069 (E2E tests)
- Consider Redis Cluster for production high availability
