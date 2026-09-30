from abc import ABC, abstractmethod
import asyncio
from collections import OrderedDict, defaultdict, deque
import time
import random

class DuplicateKeyError(ValueError):
    """This exception is raised when inserting a key that already exists"""

class VM:
    def __init__(self, id: str):
        self.id: str = id
        self.tenant_id: int | None = None
        self.status: str = "idle"
        self.creation_time: float = time.time()
        self.warm_time: float = 0.0


class MicroVMPool(ABC):
    @abstractmethod
    async def get_vm(self, tenant_id: int) -> VM | None:
        pass

    @abstractmethod
    async def put_vm(self, tenant_id: int, vm: VM):
        pass

    @abstractmethod
    async def teardown(self, vm:VM):
        pass

class WarmMicroVMPool(MicroVMPool):

    MIN_POOL_THRESHOLD: int = 5

    def __init__(self, alloc_vms:list[VM], capacity: int):
        self.vms: list[VM] = alloc_vms
        self.pool_capacity: int = capacity
        self.pool_min_threshold: int = self.MIN_POOL_THRESHOLD

        # O(1) eviction pool maps vm.id to VM.
        self.global_lru: OrderedDict[str, VM] = OrderedDict()

        # O(1) tenant specific lookup: tenant_id -> OrderedDict
        self.tenant_pools: defaultdict[int, OrderedDict[str, VM]] = defaultdict(OrderedDict)

        # O(1) Idle resource tracker.
        self.idle_vms: deque[VM] = deque(alloc_vms)
        self._background_tasks: set[asyncio.Task] = set()
   
    async def get_vm(self, tenant_id: int) -> VM | None:
        tenant_pool = self.tenant_pools[tenant_id]
        if tenant_pool:
            # 1. O(1) LIFO retrieval: Pop the most recently used VM from the tenant pool.
            vm_id, vm = tenant_pool.popitem(last=True)

            # 2. O(1) Synchronization: Remove it from the global LRU cache
            #    so it cannot be evicted while actively in use by the tenant.
            del self.global_lru[vm_id]

            vm.status = "in_use"
            return vm

        # Lazy Priming: If no warm VMs exist for this tenant, pull a cold one.
        if self.idle_vms:
            vm = self.idle_vms.popleft()
            vm.tenant_id = tenant_id
            vm.status = "in_use"
            return vm


        # The entire shystem has exhausted all allocated VMs.
        return None

    async def put_vm(self, tenant_id: int, vm: VM) -> None:
        if not vm:
            raise ValueError(f"VM is invalid or None")
        
        # Guard clause: Prevent re-insertion of a VM currently being destroyed.
        if vm.status == "tearing_down":
            # In a real system, you might log a warning here or raise an exception
            # depending on how the control plane handles dropped instances.
            raise ValueError("VM: {vm.id} is still being torn down.")
        
        vm.status = "warm"
        vm.warm_time = time.time()

        # O(1) insertion into the both tracking structures
        self.tenant_pools[vm.tenant_id][vm.id] = vm
        self.global_lru[vm.id] = vm

        if len(self.global_lru) > self.pool_capacity:
            # O(1) eviction from: popitem(last=False removes
            # the first inserted item from the OrderedDict.
            _, victim_vm = self.global_lru.popitem(last=False)

            # O(1) remove the victim from its specific tenant pool.
            del self.tenant_pools[victim_vm.tenant_id][victim_vm.id]

            # 1. Schedule the teardown task for the fcitim vm concurrently.
            task = asyncio.create_task(self.teardown(victim_vm))

            # 2, Add the task to the set of background tasks.
            self._background_tasks.add(task)

            # 3. Add a callback to remove the task from the set once it is done.
            task.add_done_callback(self._background_tasks.discard)

    async def teardown(self, vm: VM):
        vm.status = "tearing_down"
        await asyncio.sleep(5)
        vm.status = "idle"
        vm.warm_time = 0.0

        # Return to the idela pool.
        self.idle_vms.append(vm)

async def main():

    micro_vm_pool = WarmMicroVMPool([VM(str(vm)) for vm in range(1000)], 100)

    for i in range(10000):
        tenant_id = random.randrange(1000)
        vm = await micro_vm_pool.get_vm(tenant_id)
        if vm:
            # Print the VM structure for visual inspection.
            print(f"VM: {vars(vm)}")
            await micro_vm_pool.put_vm(tenant_id, vm)

if __name__ == "__main__":
    asyncio.run(main())
