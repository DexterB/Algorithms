import pytest

from resalloc import ResourcePool


class TestInitialState:
    def test_single_free_block_spans_capacity(self):
        pool = ResourcePool(1024)
        assert pool.free_blocks == [(1024, 0)]
        assert set(pool.start_map) == {0}
        assert set(pool.end_map) == {1024}


class TestAllocate:
    def test_returns_offset_zero_for_first_allocation(self):
        pool = ResourcePool(1024)
        assert pool.allocate(100) == 0

    def test_leaves_remainder_as_free_block(self):
        pool = ResourcePool(1024)
        pool.allocate(100)
        assert pool.free_blocks == [(924, 100)]
        assert pool.start_map[100].size == 924
        assert pool.end_map[1024].offset == 100

    def test_sequential_allocations_are_contiguous(self):
        pool = ResourcePool(1024)
        p1 = pool.allocate(100)
        p2 = pool.allocate(50)
        p3 = pool.allocate(200)
        assert (p1, p2, p3) == (0, 100, 150)

    def test_exact_size_allocation_consumes_whole_block_without_remainder(self):
        pool = ResourcePool(1024)
        offset = pool.allocate(1024)
        assert offset == 0
        assert pool.free_blocks == []

    def test_allocated_block_is_marked_in_use(self):
        pool = ResourcePool(1024)
        offset = pool.allocate(100)
        assert pool.start_map[offset].in_use is True

    def test_returns_none_when_request_exceeds_capacity(self):
        pool = ResourcePool(1024)
        assert pool.allocate(2000) is None
        # pool state must be untouched by the failed allocation
        assert pool.free_blocks == [(1024, 0)]

    def test_returns_none_when_no_single_block_is_large_enough(self):
        pool = ResourcePool(1024)
        pool.allocate(600)
        # Remaining free block is 424 bytes; a 500 byte request cannot fit
        # even though total free space (424) is less than requested anyway.
        assert pool.allocate(500) is None

    @pytest.mark.parametrize("size", [0, -1, -100])
    def test_returns_none_for_non_positive_size(self, size):
        pool = ResourcePool(1024)
        assert pool.allocate(size) is None
        assert pool.free_blocks == [(1024, 0)]

    def test_picks_best_fit_smallest_sufficient_block(self):
        pool = ResourcePool(1000)
        # Carve out three free blocks of distinct sizes (50, 100, 200),
        # separated by small blocks that stay allocated so the free
        # blocks can't coalesce with one another.
        a = pool.allocate(50)    # offset 0, freed below
        pool.allocate(10)        # offset 50, separator, stays allocated
        b = pool.allocate(100)   # offset 60, freed below
        pool.allocate(10)        # offset 160, separator, stays allocated
        c = pool.allocate(200)   # offset 170, freed below
        pool.allocate(630)       # offset 370, consumes the rest

        pool.free(a)
        pool.free(b)
        pool.free(c)
        assert sorted(pool.free_blocks) == [(50, 0), (100, 60), (200, 170)]

        # A request for 80 should best-fit into the 100-byte block (offset 60),
        # not the oversized 200-byte block, and the 50-byte block is too small.
        offset = pool.allocate(80)
        assert offset == 60

    def test_resource_exhaustion_after_pool_is_full(self):
        pool = ResourcePool(256)
        assert pool.allocate(256) == 0
        assert pool.allocate(1) is None


class TestFree:
    def test_free_returns_block_to_free_list(self):
        pool = ResourcePool(1024)
        offset = pool.allocate(100)
        pool.free(offset)
        assert pool.start_map[offset].in_use is False

    def test_free_merges_with_left_neighbor(self):
        pool = ResourcePool(1024)
        p1 = pool.allocate(100)  # [0, 100)
        p2 = pool.allocate(50)   # [100, 150)
        pool.allocate(874)       # [150, 1024), stays allocated so it can't merge in
        pool.free(p1)
        pool.free(p2)
        # p1 and p2 should merge into a single [0, 150) free block.
        assert pool.free_blocks == [(150, 0)]

    def test_free_merges_with_right_neighbor(self):
        pool = ResourcePool(1024)
        p1 = pool.allocate(100)  # [0, 100)
        p2 = pool.allocate(50)   # [100, 150)
        pool.allocate(874)       # [150, 1024), stays allocated so it can't merge in
        pool.free(p2)
        pool.free(p1)
        # Freeing in the opposite order should still merge p1 with the
        # already-free p2 (right neighbor merge).
        assert pool.free_blocks == [(150, 0)]

    def test_free_triggers_three_way_merge(self):
        pool = ResourcePool(1024)
        p1 = pool.allocate(100)  # [0, 100)
        p2 = pool.allocate(50)   # [100, 150)
        p3 = pool.allocate(200)  # [150, 350)

        pool.free(p1)
        pool.free(p3)
        pool.free(p2)  # merges left (p1) and right (p3) in one call

        assert pool.free_blocks == [(1024, 0)]
        assert pool.start_map[0].size == 1024
        assert pool.end_map[1024].offset == 0

    def test_freed_space_can_be_reallocated(self):
        pool = ResourcePool(1024)
        offset = pool.allocate(1024)
        pool.free(offset)
        assert pool.allocate(1024) == 0

    def test_free_negative_offset_raises_value_error(self):
        pool = ResourcePool(1024)
        with pytest.raises(ValueError):
            pool.free(-1)

    def test_free_unknown_offset_raises(self):
        pool = ResourcePool(1024)
        with pytest.raises(KeyError):
            pool.free(999)

    def test_double_free_raises_value_error(self):
        pool = ResourcePool(1024)
        offset = pool.allocate(100)
        pool.free(offset)
        with pytest.raises(ValueError):
            pool.free(offset)

    def test_free_middle_of_block_raises_key_error(self):
        pool = ResourcePool(1024)
        pool.allocate(100)
        with pytest.raises(KeyError):
            pool.free(50)


class TestFullLifecycle:
    def test_allocate_and_free_everything_restores_single_block(self):
        pool = ResourcePool(2048)
        offsets = []
        for size in (128, 256, 64, 512, 1088):
            offsets.append(pool.allocate(size))

        assert pool.allocate(1) is None  # pool is fully allocated

        for offset in offsets:
            pool.free(offset)

        assert pool.free_blocks == [(2048, 0)]
        assert pool.allocate(2048) == 0
