import asyncio
import importlib
import time

import pytest

pool_module = importlib.import_module("µvmpool")
DuplicateKeyError = pool_module.DuplicateKeyError
VM = pool_module.VM
MicroVMPool = pool_module.MicroVMPool
WarmMicroVMPool = pool_module.WarmMicroVMPool


async def _fast_sleep(_seconds):
    return None


# ---------------------------------------------------------------------------
# VM
# ---------------------------------------------------------------------------

class TestVM:
    def test_new_vm_has_expected_defaults(self):
        vm = VM("vm-1")

        assert vm.id == "vm-1"
        assert vm.tenant_id is None
        assert vm.status == "idle"
        assert vm.warm_time == 0.0
        assert isinstance(vm.creation_time, float)

    def test_each_vm_gets_its_own_creation_time(self, monkeypatch):
        times = iter([1.0, 2.0])
        monkeypatch.setattr(time, "time", lambda: next(times))

        first = VM("a")
        second = VM("b")

        assert first.creation_time == 1.0
        assert second.creation_time == 2.0


# ---------------------------------------------------------------------------
# DuplicateKeyError
# ---------------------------------------------------------------------------

class TestDuplicateKeyError:
    def test_is_a_value_error_subclass(self):
        assert issubclass(DuplicateKeyError, ValueError)

    def test_can_be_raised_and_caught_with_message(self):
        with pytest.raises(DuplicateKeyError, match="boom"):
            raise DuplicateKeyError("boom")


# ---------------------------------------------------------------------------
# MicroVMPool (abstract base)
# ---------------------------------------------------------------------------

class TestMicroVMPoolABC:
    def test_cannot_be_instantiated_directly(self):
        with pytest.raises(TypeError):
            MicroVMPool()

    def test_subclass_missing_methods_cannot_be_instantiated(self):
        class Incomplete(MicroVMPool):
            async def get_vm(self, tenant_id):
                return None

        with pytest.raises(TypeError):
            Incomplete()

    def test_subclass_implementing_all_methods_can_be_instantiated(self):
        class Complete(MicroVMPool):
            async def get_vm(self, tenant_id):
                return None

            async def put_vm(self, tenant_id, vm):
                return None

            async def teardown(self, vm):
                return None

        assert isinstance(Complete(), MicroVMPool)


# ---------------------------------------------------------------------------
# WarmMicroVMPool - construction
# ---------------------------------------------------------------------------

class TestWarmMicroVMPoolInit:
    def test_stores_capacity_and_default_threshold(self):
        pool = WarmMicroVMPool([], capacity=10)

        assert pool.pool_capacity == 10
        assert pool.pool_min_threshold == WarmMicroVMPool.MIN_POOL_THRESHOLD

    def test_all_allocated_vms_start_idle(self):
        vms = [VM(str(index)) for index in range(4)]

        pool = WarmMicroVMPool(vms, capacity=2)

        assert list(pool.idle_vms) == vms
        assert all(vm.status == "idle" for vm in vms)

    def test_starts_with_empty_lru_and_tenant_pools(self):
        pool = WarmMicroVMPool([VM("0")], capacity=1)

        assert len(pool.global_lru) == 0
        assert len(pool.tenant_pools) == 0


# ---------------------------------------------------------------------------
# WarmMicroVMPool.get_vm
# ---------------------------------------------------------------------------

class TestWarmMicroVMPoolGetVm:
    def test_returns_none_when_no_idle_or_warm_vms_exist(self):
        pool = WarmMicroVMPool([], capacity=1)

        assert asyncio.run(pool.get_vm(tenant_id=1)) is None

    def test_pulls_from_idle_vms_when_tenant_has_no_warm_vm(self):
        vms = [VM(str(index)) for index in range(2)]
        pool = WarmMicroVMPool(vms, capacity=2)

        vm = asyncio.run(pool.get_vm(tenant_id=42))

        assert vm is vms[0]
        assert vm.tenant_id == 42
        assert vm.status == "in_use"
        assert vm not in pool.idle_vms

    def test_prefers_tenants_own_warm_vm_over_idle_pool(self):
        vms = [VM(str(index)) for index in range(2)]
        pool = WarmMicroVMPool(vms, capacity=2)

        async def scenario():
            warm_vm = vms[0]
            warm_vm.tenant_id = 7
            await pool.put_vm(7, warm_vm)
            return await pool.get_vm(tenant_id=7)

        vm = asyncio.run(scenario())

        assert vm is vms[0]
        assert vm.status == "in_use"
        assert vm.id not in pool.global_lru
        assert len(pool.tenant_pools[7]) == 0

    def test_returns_most_recently_warmed_vm_for_tenant_lifo(self):
        vms = [VM(str(index)) for index in range(3)]
        pool = WarmMicroVMPool(vms, capacity=3)

        async def scenario():
            for vm in vms[:2]:
                vm.tenant_id = 1
                await pool.put_vm(1, vm)
            return await pool.get_vm(tenant_id=1)

        vm = asyncio.run(scenario())

        assert vm is vms[1]


# ---------------------------------------------------------------------------
# WarmMicroVMPool.put_vm
# ---------------------------------------------------------------------------

class TestWarmMicroVMPoolPutVm:
    def test_rejects_none_vm(self):
        pool = WarmMicroVMPool([], capacity=1)

        with pytest.raises(ValueError):
            asyncio.run(pool.put_vm(1, None))

    def test_rejects_vm_that_is_tearing_down(self):
        pool = WarmMicroVMPool([], capacity=1)
        vm = VM("0")
        vm.status = "tearing_down"

        with pytest.raises(ValueError):
            asyncio.run(pool.put_vm(1, vm))

    def test_marks_vm_warm_and_indexes_it(self, monkeypatch):
        monkeypatch.setattr(time, "time", lambda: 99.0)
        pool = WarmMicroVMPool([], capacity=2)
        vm = VM("0")
        vm.tenant_id = 5

        asyncio.run(pool.put_vm(5, vm))

        assert vm.status == "warm"
        assert vm.warm_time == 99.0
        assert pool.global_lru["0"] is vm
        assert pool.tenant_pools[5]["0"] is vm

    def test_evicts_oldest_global_entry_once_over_capacity(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", _fast_sleep)
        vms = [VM(str(index)) for index in range(3)]
        for index, vm in enumerate(vms):
            vm.tenant_id = index
        pool = WarmMicroVMPool([], capacity=2)

        async def scenario():
            for vm in vms:
                await pool.put_vm(vm.tenant_id, vm)
            await asyncio.gather(*pool._background_tasks)

        asyncio.run(scenario())

        assert len(pool.global_lru) == 2
        assert vms[0].id not in pool.global_lru
        assert vms[0].id not in pool.tenant_pools[vms[0].tenant_id]

    def test_eviction_schedules_teardown_as_background_task(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", _fast_sleep)
        vms = [VM(str(index)) for index in range(3)]
        for index, vm in enumerate(vms):
            vm.tenant_id = index
        pool = WarmMicroVMPool([], capacity=2)

        async def scenario():
            for vm in vms:
                await pool.put_vm(vm.tenant_id, vm)
            await asyncio.gather(*pool._background_tasks)

        asyncio.run(scenario())

        assert vms[0].status == "idle"
        assert vms[0] in pool.idle_vms


# ---------------------------------------------------------------------------
# WarmMicroVMPool.teardown
# ---------------------------------------------------------------------------

class TestWarmMicroVMPoolTeardown:
    def test_marks_vm_idle_and_returns_it_to_the_idle_pool(self, monkeypatch):
        monkeypatch.setattr(asyncio, "sleep", _fast_sleep)
        pool = WarmMicroVMPool([], capacity=1)
        vm = VM("0")
        vm.status = "warm"
        vm.warm_time = 123.0

        asyncio.run(pool.teardown(vm))

        assert vm.status == "idle"
        assert vm.warm_time == 0.0
        assert vm in pool.idle_vms

    def test_sleeps_for_five_seconds(self, monkeypatch):
        recorded = {}

        async def fake_sleep(seconds):
            recorded["seconds"] = seconds

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        pool = WarmMicroVMPool([], capacity=1)
        vm = VM("0")

        asyncio.run(pool.teardown(vm))

        assert recorded["seconds"] == 5
