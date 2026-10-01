
import bisect
from collections import defaultdict


class AllocationUnit:
    def __init__(self, offset: int, size: int):
        self.offset: int = offset
        self.size: int = size
        self.in_use: bool = False
    
    @property
    def next_block_offset(self) -> int:
        return self.offset + self.size

class ResourcePool:
    def __init__(self, capacity: int):
        self.capacity = capacity
        initial_block = AllocationUnit(0, capacity)

        # O(1) lookups of exact start or end lookups
        self.start_map: dict[int, AllocationUnit] = { 0: initial_block }
        self.end_map: dict[int, AllocationUnit] = { capacity: initial_block }

        # O(log N) allocation: A sorted list of tuples (size, offset)
        # Keeps free blocks ordered by size to allow binary search (bisect).
        self.free_blocks: list[tuple[int, int]] = [(capacity, 0)]

    def allocate(self, size: int) -> int | None:
        if size <= 0:
            return None

        #1. O(log N) Search
        #   Search for (size, -1) to find teh forst block that is greater than
        #   or equal to the requested size, picking the one with the lowest
        #   offset.
        idx = bisect.bisect_left(self.free_blocks, (size, -1))
        if idx == len(self.free_blocks):
            return None # Resource exhaustion

        #2. Extract the block.
        found_size, offset = self.free_blocks.pop(idx)

        # Remove the original large free block from the tracking maps
        original_block = self.start_map.pop(offset)
        next_offset = original_block.next_block_offset
        self.end_map.pop(next_offset)

        #3. Create and register the newly allocated block
        allocated_block = AllocationUnit(offset, size)
        allocated_block.in_use = True
        self.start_map[offset] = allocated_block

        alloc_next = allocated_block.next_block_offset
        self.end_map[alloc_next] = allocated_block

        #4. Handle Fragmentation (the remainig block if any).
        remainder_size = original_block.size - size
        if remainder_size > 0:
            remainder_offset = offset + size
            remainder_block = AllocationUnit(remainder_offset, remainder_size)

            # Add the remainder back to the tracking maps.
            self.start_map[remainder_offset] = remainder_block
            self.end_map[remainder_block.next_block_offset] = remainder_block

            # Reinsert the remainter back into the sorted free blocks.
            bisect.insort(
                self.free_blocks,
                (remainder_block.size, remainder_block.offset)
            )

        return offset
        

    def free(self, start_index: int):
        if start_index < 0:
            raise ValueError(f"Block offset: {start_index} is invalid.")

        # O(1) search for block.
        target_block = self.start_map[start_index]
        if not target_block:
            raise ValueError(f"Bloack offset {start_index} is invalid.")

        if not target_block.in_use:
            raise ValueError(f"Block offset at {start_index} is not valid")

        target_block.in_use = False
        end_index = target_block.next_block_offset

        new_start = start_index
        new_size = target_block.size

        # Check for merge left.
        left_neighbor = self.end_map.get(start_index)
        if left_neighbor and not left_neighbor.in_use:
           new_start = left_neighbor.offset
           new_size += left_neighbor.size

           # Remove left neighbor from tracking structures.
           del self.start_map[start_index]
           del self.end_map[start_index]
           self.free_blocks.remove((left_neighbor.size, left_neighbor.offset))

        # Check for merge right.
        right_neighbor = self.start_map.get(end_index)
        if right_neighbor and not right_neighbor.in_use:
            new_size += right_neighbor.size

            #Remove the right neighbor for structures.
            del self.start_map[end_index]
            del self.end_map[end_index]
            self.free_blocks.remove((right_neighbor.size, right_neighbor.offset))

        # Finalize the merged block
        # If no merge happened this just updates the original block's status.
        merged_block = AllocationUnit(new_start, new_size)
        merged_block.in_use = False

        self.start_map[new_start] = merged_block
        self.end_map[merged_block.next_block_offset] = merged_block

        # Insert back into the free list.
        bisect.insort(
            self.free_blocks,
            (merged_block.size, merged_block.offset)
        )
    


if __name__ == "__main__":
    pool = ResourcePool(1024)
    p1 = pool.allocate(100) # Offset 0
    print(f" P1: {p1}")
    p2 = pool.allocate(50)  # Offset 100
    print(f" P2: {p2}")
    p3 = pool.allocate(200) # Offset 150
    print(f" P3: {p3}")

    
    pool.free(p1)
    pool.free(p3)
    pool.free(p2) # This will trigger a massive 3-way merge
    print(f"Final free blocks: {pool.free_blocks}") # Should return [(1024, 0)]

