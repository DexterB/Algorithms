import asyncio
import importlib

pool_module = importlib.import_module("µvmpool")
VM = pool_module.VM
WarmMicroVMPool = pool_module.WarmMicroVMPool


def test_constructor_warms_only_the_pool_capacity():
    vms = [VM(str(index)) for index in range(4)]

    pool = WarmMicroVMPool(vms, capacity=2)

    assert [vm.status for vm in vms] == ["warm", "warm", "idle", "idle"]
    assert len(pool.warm_pool) == 2


def test_get_vm_marks_vm_in_use_and_replenishes_to_minimum_threshold():
    vms = [VM(str(index)) for index in range(8)]
    pool = WarmMicroVMPool(vms, capacity=5)

    vm = asyncio.run(pool.get_vm())

    assert vm.status == "in_use"
    assert len(pool.warm_pool) == pool.pool_min_threshold
    assert sum(item.status == "warm" for item in vms) == pool.pool_min_threshold
    assert sum(item.status == "idle" for item in vms) == 2


def test_put_vm_returns_vm_to_the_warm_pool():
    pool = WarmMicroVMPool([VM(str(index)) for index in range(3)], capacity=2)
    vm = asyncio.run(pool.get_vm())

    asyncio.run(pool.put_vm(vm))

    assert vm.status == "warm"
    assert vm in pool.warm_pool
    assert len(pool.warm_pool) == 2


def test_put_vm_evicts_the_oldest_warm_vm_when_pool_is_at_capacity():
    vms = [VM(str(index)) for index in range(3)]
    pool = WarmMicroVMPool(vms, capacity=2)
    oldest, newest, replacement = vms
    oldest.warm_time = 1.0
    newest.warm_time = 2.0
    replacement.warm_time = 3.0
    pool.warm_pool = [oldest, newest]

    asyncio.run(pool.put_vm(replacement))

    assert oldest.status == "idle"
    assert replacement.status == "warm"
    assert len(pool.warm_pool) == 2
    assert oldest not in pool.warm_pool
    assert replacement in pool.warm_pool


def test_get_vm_returns_none_when_no_warm_vm_is_available():
    pool = WarmMicroVMPool([], capacity=1)

    assert asyncio.run(pool.get_vm()) is None