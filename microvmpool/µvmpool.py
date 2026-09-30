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
        self.tenant_id = None
        self.status: str = "idle"
        self.creation_time: float = time.time()
        self.warm_time: float = 0.0


class MicroVMPool(ABC):
    @abstractmethod
    async def get_vm(self) -> VM:
        pass

    @abstractmethod
    async def put_vm(self, vm: VM):
        pass

    @abstractmethod
    async def teardown(self, vm:VM):
        pass

class Tenant:
    def __init__(self, tenant_id: int, micro_vm_pool: MicroVMPool):
        self.id = tenant_id
        self.micro_vm_pool = micro_vm_pool

class TenantPool:
    def __init__(self):
        self.tenants: defaultdict[Tenant] = defaultdict(Tenant)

    async def add_tenant(self, tenant: Tenant) -> None:
        if tenant.id in self.tenants:
            raise DuplicateKeyError("f Tenant with tenant id:{tenant.id!r} already exists")

        self.tenants[tenant.id] = tenant

    async def get_vm(self, tenant_id: int) -> VM:
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            # Tenant is not part of the tenant dictionary.
            raise KeyError("Tenant: {tenant_id} does not exist.")

        return await tenant.micro_vm_pool.get_vm()

    async def put_vm(self, tenant_id: int, vm: VM) -> None:
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            # Tenant is not part of the tenant dictionary.
            raise KeyError("Tenant: {tenant_id} does not exist.")
        vm.tenant_id = tenant_id
        await tenant.micro_vm_pool.put_vm(vm)

    async def teardown(self, vm: VM):
        tenant = self.tenants.get(vm.tenant_id)
        if not tenant:
            # The VM is not in a valid tenant.
            raise KeyError("Tenant: {tenant_id} associated with VM: {vm.id} does not exist.")

        await tenant.micro_vm_pool.teardown(vm)

class WarmMicroVMPool(MicroVMPool):

    MIN_POOL_THRESHOLD: int = 5

    def __init__(self, alloc_vms:list[VM],capacity: int):
        self.vms: list[VM] = alloc_vms
        self.pool_capacity: int = capacity
        self.pool_min_threshold: int = self.MIN_POOL_THRESHOLD

        # O(1) eviction pool maps vm.id to VM.
        self.warm_pool: OrderedDict[str, VM] = OrderedDict()

        # O(1) Idle resource tracker.
        self.idle_vms: deque[VM] = deque(alloc_vms)
    
        self._background_tasks: set[asyncio.Task] = set()

        # Initialize the warm pool with the first 'pool_capacity' VMs.
        while len(self.warm_pool) < self.pool_capacity and self.idle_vms:
            vm = self.idle_vms.popleft()
            vm.status = "warm"
            vm.warm_time = time.time()
            self.warm_pool[vm.id] = vm

        
    async def get_vm(self) -> VM | None:
        if not self.warm_pool:
            return None

        # O(1) retrieval of: popitem(last=True) acts as a LIFO queue to get the hotttest VM
        # or popitem(last=False) for FIFO.
        vm_id, vm = self.warm_pool.popitem(last=True)
        vm.status = "in_use"

        #O(1) replenishment when done.
        if len(self.warm_pool) < self.pool_min_threshold:
            replenish_vm = self.idle_vms.popleft()
            replenish_vm.status = "warm"
            replenish_vm.warm_time = time.time()
            self.warm_pool[replenish_vm.id] = replenish_vm

        return vm

    async def put_vm(self, vm: VM) -> None:
        vm.status = "warm"
        vm.warm_time = time.time()

        # O(1) insertion into the Ordered dictionary.
        self.warm_pool[vm.id] = vm

        if len(self.warm_pool) > self.pool_capacity:
            # O(1) eviction from: popitem(last=False removes
            # the first inserted item from the OrderedDict.
            _, victim_vm = self.warm_pool.popitem(last=False)

            # 1. Schedule the teardown task for the fcitim vm concurrently.
            task = asyncio.create_task(self.teardown(victim_vm))

            # 2, Add the task to the set of background tasks.
            self._background_tasks.add(task)

            # 3. Add a callback to remove the task from the set once it is done.
            task.add_done_callback(self._background_tasks.discard)

    async def teardown(self, vm: VM):
        await asyncio.sleep(5)
        vm.status = "idle"
        vm.warm_time = 0.0

        # Return to the idela pool.
        self.idle_vms.append(vm)

async def main():
    tenant_pool = TenantPool()
    for tenant_id in range(1000):
        warm_pool = WarmMicroVMPool([VM(str(vm)) for vm in range(1000)], 10)
        print(f"Warm pool has {len(warm_pool.idle_vms)} idle vms.")
        await tenant_pool.add_tenant(Tenant(tenant_id, warm_pool))

    print(f"Tenant pool has {len(tenant_pool.tenants)} tenants.")

    for i in range(5):
        vm = await tenant_pool.get_vm(random.randint(0, 999))
        # Print the VM structure for visual inspection.
        print(f"VM: {vars(vm)}")
        await warm_pool.put_vm(vm)

if __name__ == "__main__":
    asyncio.run(main())
