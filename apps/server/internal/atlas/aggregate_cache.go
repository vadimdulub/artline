package atlas

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"sync"
	"time"
)

type laneAggregate struct {
	Total               int
	FirstYear, LastYear *int
	Density             []Period
}
type aggregateEntry struct {
	body    []byte
	expires time.Time
}
type aggregateCache struct {
	mu      sync.Mutex
	entries map[[32]byte]aggregateEntry
	pending map[[32]byte]chan struct{}
	bytes   int
	now     func() time.Time
}

func newAggregateCache() *aggregateCache {
	return &aggregateCache{entries: map[[32]byte]aggregateEntry{}, pending: map[[32]byte]chan struct{}{}, now: time.Now}
}

// The SQL and its bound scope values include every filter, but no cursor/page
// size. The revision comes from the SAME repeatable-read snapshot as the page.
func aggregateKey(revision, sql string, args []any) [32]byte {
	b, _ := json.Marshal([]any{revision, sql, args})
	return sha256.Sum256(b)
}

func (c *aggregateCache) load(ctx context.Context, revision, sql string, args []any, read func() (laneAggregate, error)) (laneAggregate, error) {
	if c == nil || revision == "" {
		return read()
	}
	key := aggregateKey(revision, sql, args)
	for {
		c.mu.Lock()
		if e, ok := c.entries[key]; ok {
			if c.now().Before(e.expires) {
				c.mu.Unlock()
				var v laneAggregate
				err := json.Unmarshal(e.body, &v)
				return v, err
			}
			delete(c.entries, key)
			c.bytes -= len(e.body)
		}
		if pending := c.pending[key]; pending != nil {
			c.mu.Unlock()
			select {
			case <-pending:
				continue
			case <-ctx.Done():
				return laneAggregate{}, ctx.Err()
			}
		}
		if len(c.pending) >= 128 {
			c.mu.Unlock()
			return read()
		}
		c.pending[key] = make(chan struct{})
		c.mu.Unlock()
		value, err := read()
		body, encodeErr := json.Marshal(value)
		c.mu.Lock()
		if err == nil && encodeErr == nil && ctx.Err() == nil && len(body) <= 128<<10 {
			for len(c.entries) >= 128 || c.bytes+len(body) > 4<<20 {
				var oldest [32]byte
				var expiry time.Time
				for k, e := range c.entries {
					if expiry.IsZero() || e.expires.Before(expiry) {
						oldest, expiry = k, e.expires
					}
				}
				c.bytes -= len(c.entries[oldest].body)
				delete(c.entries, oldest)
			}
			c.entries[key] = aggregateEntry{body: body, expires: c.now().Add(time.Minute)}
			c.bytes += len(body)
		}
		close(c.pending[key])
		delete(c.pending, key)
		c.mu.Unlock()
		return value, err
	}
}
