package atlas

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestAggregateCacheInvalidationAndBounds(t *testing.T) {
	c := newAggregateCache()
	now := time.Now()
	c.now = func() time.Time { return now }
	calls := 0
	read := func() (laneAggregate, error) {
		calls++
		year := 1750
		return laneAggregate{Total: 42, FirstYear: &year, Density: []Period{{Count: 42}}}, nil
	}
	load := func(rev, sql string, args []any) laneAggregate {
		t.Helper()
		v, e := c.load(context.Background(), rev, sql, args, read)
		if e != nil {
			t.Fatal(e)
		}
		return v
	}
	v := load("1", "scope", []any{1})
	*v.FirstYear = 0
	v.Density[0].Count = 0
	v = load("1", "scope", []any{1})
	if calls != 1 || *v.FirstYear != 1750 || v.Density[0].Count != 42 {
		t.Fatal("cache alias or missed reuse")
	}
	load("2", "scope", []any{1})
	load("2", "scope", []any{2})
	load("2", "other", []any{2})
	if calls != 4 {
		t.Fatal("revision, SQL or filter did not invalidate")
	}
	now = now.Add(time.Minute)
	load("2", "other", []any{2})
	if calls != 5 {
		t.Fatal("TTL ignored")
	}
	for i := 0; i < 150; i++ {
		load(fmt.Sprint(i), "scope", nil)
	}
	if len(c.entries) > 128 || c.bytes > 4<<20 {
		t.Fatal("unbounded cache")
	}
	if len(c.pending) != 0 {
		t.Fatal("unfinished loads")
	}
	fail := func() (laneAggregate, error) { return laneAggregate{}, errors.New("read failed") }
	if _, err := c.load(context.Background(), "bad", "", nil, fail); err == nil {
		t.Fatal("error swallowed")
	}
	load("bad", "", nil)
}

func TestAggregateCacheSingleFlightAndCancellation(t *testing.T) {
	c := newAggregateCache()
	start, finish := make(chan struct{}), make(chan struct{})
	var calls atomic.Int32
	read := func() (laneAggregate, error) {
		if calls.Add(1) == 1 {
			close(start)
		}
		<-finish
		return laneAggregate{Total: 7}, nil
	}
	var wg sync.WaitGroup
	wg.Add(1)
	go func() { defer wg.Done(); _, _ = c.load(context.Background(), "1", "scope", nil, read) }()
	<-start
	cancelled, cancel := context.WithCancel(context.Background())
	cancel()
	if _, err := c.load(cancelled, "1", "scope", nil, read); !errors.Is(err, context.Canceled) {
		t.Fatal(err)
	}
	for i := 0; i < 12; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			v, e := c.load(context.Background(), "1", "scope", nil, read)
			if e != nil || v.Total != 7 {
				t.Errorf("load: %v %v", v, e)
			}
		}()
	}
	close(finish)
	wg.Wait()
	if calls.Load() != 1 {
		t.Fatalf("duplicate concurrent reads: %d", calls.Load())
	}
}
