# tests/test_callable.py
# ======================
#
# Copying
# -------
#
# Copyright (c) 2020 none authors and contributors.
#
# This file is part of the *none* project.
#
# None is a free software project. You can redistribute it and/or
# modify it following the terms of the MIT License.
#
# This software project is distributed *as is*, WITHOUT WARRANTY OF ANY
# KIND; including but not limited to the WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE and NONINFRINGEMENT.
#
# You should have received a copy of the MIT License along with
# *none*. If not, see <http://opensource.org/licenses/MIT>.
#
"""Test cases for :mod:`none.callable`."""
import pytest

import none


class TestCatchHook(object):
    """Test cases for :class:`none.callable.catch` and
    :class:`none.callable.hook`.

    """

    def test_hook___init___function_isinstance_hook(self):
        """Ensure the a hooked function becomes a :class:`none.callable.hook`
        instance.

        """

        @none.callable.hook
        def my_hook():
            pass

        assert isinstance(my_hook, none.callable.hook)

    def test_hook___init___method_isinstance_hook(self):
        """Ensure the a hooked method becomes a :class:`none.callable.hook`
        instance.

        """

        class Hookable(object):
            @none.callable.hook
            def my_hook(self):
                pass

        assert isinstance(Hookable.my_hook, none.callable.hook)

    def test_hook___call___run_other_functions(self):
        """Test that by calling the hooked function, all hanging functions are
        also executed.

        """
        stack = set()

        @none.callable.hook
        def my_hook():
            stack.add(0)

        @none.callable.catch(my_hook)
        def my_catch1():
            stack.add(1)

        @none.callable.catch(my_hook)
        def my_catch2():
            stack.add(2)

        my_hook()
        assert stack == {0, 1, 2}

    def test_hook___call___run_other_methods(self):
        """Test that by calling the hooked method, all hanging methods are also
         executed.

        """
        stack = set()

        class Hookable(object):
            @none.callable.hook
            def my_hook(self):
                stack.add(0)

            @none.callable.catch("my_hook")
            def my_catch1(self):
                stack.add(1)

            @none.callable.catch("my_hook")
            def my_catch2(self):
                stack.add(2)

        h = Hookable()
        h.my_hook()
        assert stack == {0, 1, 2}

    def test_hook___call___run_other_methods_with_inheritance(self):
        """Test that by calling the hooked method, all hanging methods are also
         executed even when inheritance is involved.

        """
        stack = set()

        class Hookable(object):
            @none.callable.hook
            def my_hook(self):
                stack.add(0)

        class Catching(Hookable):
            @none.callable.catch("my_hook")
            def my_catch1(self):
                stack.add(1)

            @none.callable.catch("my_hook")
            def my_catch2(self):
                stack.add(2)

        c = Catching()
        c.my_hook()
        assert stack == {0, 1, 2}

    def test_hook___call___run_only_inherited_methods(self):
        """Make sure that only hanging methods within the class context are
        executed.

        """
        stack = set()

        class Hookable(object):
            @none.callable.hook
            def my_hook(self):
                stack.add(0)

        class Catching(Hookable):
            @none.callable.catch("my_hook")
            def my_catch1(self):
                stack.add(1)

            @none.callable.catch("my_hook")
            def my_catch2(self):
                stack.add(2)

        class _NOOP(Hookable):
            @none.callable.catch("my_hook")
            def my_noop_catch(self):
                stack.add("--noop--")

        c = Catching()
        c.my_hook()
        assert stack == {0, 1, 2}

    def test_hook_hangers_register_same_hanger_only_once(self):
        """Ensure that adding the same catch function twice is only
        registered once.

        """

        @none.callable.hook
        def my_hook():
            pass

        # First registration via decorator.
        @none.callable.catch(my_hook)
        def my_catch():
            pass

        # Force direct registration.
        my_hook.hanging.add(my_catch)

        assert len(my_hook.hanging) == 1

    def test_catch___init___function_isinstance_catch_and_hook(self):
        """Ensure the a catching function becomes an instance of
         :class:`none.callable.catch` and :class:`none.callable.hook`.

        """

        @none.callable.hook
        def my_hook():
            pass

        @none.callable.catch(my_hook)
        def my_catch():
            pass

        assert isinstance(my_catch, none.callable.catch)
        assert isinstance(my_catch, none.callable.hook)

    def test_catch___init___method_isinstance_catch_and_hook(self):
        """Ensure the a catching method becomes an instance of
         :class:`none.callable.catch` and :class:`none.callable.hook`.

        """

        class Hookable(object):
            @none.callable.hook
            def my_hook(self):
                pass

            @none.callable.catch("my_hook")
            def my_catch(self):
                pass

        assert isinstance(Hookable.my_catch, none.callable.catch)
        assert isinstance(Hookable.my_catch, none.callable.hook)

    def test_catch___call___update_hook_from_function(self):
        """Ensure that catching a hook from a function updates its list of
        hanging functions.

        """

        @none.callable.hook
        def my_hook():
            pass

        @none.callable.catch(my_hook)
        def my_catch():
            pass

        assert my_catch in my_hook.hanging

    def test_catch___call___function_can_also_be_a_hook(self):
        """Ensure that by catching another catch function, all functions in the
        chain are ran.

        """
        stack = set()

        @none.callable.hook
        def my_hook():
            stack.add(0)

        @none.callable.catch(my_hook)
        def my_catch1():
            stack.add(1)

        @none.callable.catch(my_catch1)
        def my_catch2():
            stack.add(2)

        my_hook()
        assert stack == {0, 1, 2}

    def test_hook___call___method_can_also_be_a_hook(self):
        """Ensure that by catching another catch method, all methods in the
        chain are ran.

        """
        stack = set()

        class Hookable(object):
            @none.callable.hook
            def my_hook(self):
                stack.add(0)

            @none.callable.catch("my_hook")
            def my_catch1(self):
                stack.add(1)

            @none.callable.catch("my_catch1")
            def my_catch2(self):
                stack.add(2)

        h = Hookable()
        h.my_hook()
        assert stack == {0, 1, 2}

    def test_hook___call___method_with_inheritance_can_also_be_a_hook(self):
        """Ensure that by catching another catch method, all methods in the
        chain are ran even when inheritance is involved.

        """
        stack = set()

        class Hookable(object):
            @none.callable.hook
            def my_hook(self):
                stack.add(0)

            @none.callable.catch("my_hook")
            def my_catch1(self):
                stack.add(1)

        class Catcher(Hookable):
            @none.callable.catch("my_catch1")
            def my_catch2(self):
                stack.add(2)

        c = Catcher()
        c.my_hook()
        assert stack == {0, 1, 2}


class TestAsyncCatchHook(object):
    """Test cases for :class:`none.callable.asynccatch` and
    :class:`none.callable.asynchook`.

    """

    def test_asynchook___init___coroutine_isinstance_asynchook_and_hook(self):
        """Ensure the a hooked coroutine becomes an
        :class:`none.callable.asynchook` and :class:`none.callable.hook`
        instance.

        """

        @none.callable.asynchook
        async def my_hook():
            pass

        assert isinstance(my_hook, none.callable.asynchook)
        assert isinstance(my_hook, none.callable.hook)

    def test_asynchook___init___method_isinstance_asynchook_and_hook(self):
        """Ensure the a hooked method becomes an :class:`none.callable.asynchook`
        and :class:`none.callable.hook` instance.

        """

        class AsyncHookable(object):
            @none.callable.asynchook
            async def my_hook(self):
                pass

        assert isinstance(AsyncHookable.my_hook, none.callable.asynchook)
        assert isinstance(AsyncHookable.my_hook, none.callable.hook)

    @pytest.mark.asyncio
    async def test_asynchook___call___run_other_coroutines(self):
        """Test that by calling the hooked coroutine, all hanging coroutines are
        also called.

        """
        stack = set()

        @none.callable.asynchook
        async def my_hook():
            stack.add(0)

        @none.callable.asynccatch(my_hook)
        async def my_catch1():
            stack.add(1)

        @none.callable.asynccatch(my_hook)
        async def my_catch2():
            stack.add(2)

        await my_hook()
        assert stack == {0, 1, 2}

    @pytest.mark.asyncio
    async def test_asynchook___call___run_other_methods(self):
        """Test that by calling the hooked method, all hanging methods are also
         executed.

        """
        stack = set()

        class AsyncHookable(object):
            @none.callable.asynchook
            async def my_hook(self):
                stack.add(0)

            @none.callable.asynccatch("my_hook")
            async def my_catch1(self):
                stack.add(1)

            @none.callable.asynccatch("my_hook")
            async def my_catch2(self):
                stack.add(2)

        h = AsyncHookable()
        await h.my_hook()
        assert stack == {0, 1, 2}

    @pytest.mark.asyncio
    async def test_asynchook___call___run_other_methods_with_inheritance(self):
        """Test that by calling the hooked method, all hanging methods are also
         executed even when inheritance is involved.

        """
        stack = set()

        class AsyncHookable(object):
            @none.callable.asynchook
            async def my_hook(self):
                stack.add(0)

        class AsyncCatching(AsyncHookable):
            @none.callable.asynccatch("my_hook")
            async def my_catch1(self):
                stack.add(1)

            @none.callable.asynccatch("my_hook")
            async def my_catch2(self):
                stack.add(2)

        c = AsyncCatching()
        await c.my_hook()
        assert stack == {0, 1, 2}

    @pytest.mark.asyncio
    async def test_asynchook___call___run_only_inherited_methods(self):
        """Make sure that only hanging methods within the class context are
        executed.

        """
        stack = set()

        class AsyncHookable(object):
            @none.callable.asynchook
            async def my_hook(self):
                stack.add(0)

        class AsyncCatching(AsyncHookable):
            @none.callable.asynccatch("my_hook")
            async def my_catch1(self):
                stack.add(1)

            @none.callable.asynccatch("my_hook")
            async def my_catch2(self):
                stack.add(2)

        class _NOOP(AsyncHookable):
            @none.callable.asynccatch("my_hook")
            def my_noop_catch(self):
                stack.add("--noop--")

        c = AsyncCatching()
        await c.my_hook()
        assert stack == {0, 1, 2}

    def test_asynchook_hangers_register_same_hanger_only_once(self):
        """Ensure that adding the same catch coroutine twice is only
        registered once.

        """

        @none.callable.asynchook
        async def my_hook():
            pass

        # First registration via decorator.
        @none.callable.asynccatch(my_hook)
        async def my_catch():
            pass

        # Force direct registration.
        my_hook.hanging.add(my_catch)

        assert len(my_hook.hanging) == 1

    def test_asynccatch___init___coroutine_isinstance_catch_hook_asynccatch_and_asynchook(
        self,
    ):
        """Ensure the a catching coroutine becomes an instance of
         :class:`none.callable.asynccatch`, :class:`none.callable.asynchook` but
         also :class:`none.callable.catch` and :class:`none.callable.hook`.

        """

        @none.callable.asynchook
        def my_hook():
            pass

        @none.callable.asynccatch(my_hook)
        def my_catch():
            pass

        assert isinstance(my_catch, none.callable.asynccatch)
        assert isinstance(my_catch, none.callable.catch)
        assert isinstance(my_catch, none.callable.asynchook)
        assert isinstance(my_catch, none.callable.hook)

    def test_asynccatch___init___method_isinstance_catch_hook_asynccatch_and_asynchook(
        self,
    ):
        """Ensure the a catching method becomes an instance of
         :class:`none.callable.asynccatch`, :class:`none.callable.asynchook` but
         also :class:`none.callable.catch` and :class:`none.callable.hook`.

        """

        class AsyncHookable(object):
            @none.callable.asynchook
            async def my_hook(self):
                pass

            @none.callable.asynccatch("my_hook")
            async def my_catch(self):
                pass

        assert isinstance(AsyncHookable.my_catch, none.callable.asynccatch)
        assert isinstance(AsyncHookable.my_catch, none.callable.catch)
        assert isinstance(AsyncHookable.my_catch, none.callable.asynchook)
        assert isinstance(AsyncHookable.my_catch, none.callable.hook)

    def test_asynccatch___call___update_hook_from_coroutine(self):
        """Ensure that catching a hook from a function updates its list of
        hanging coroutines.

        """

        @none.callable.asynchook
        async def my_hook():
            pass

        @none.callable.asynccatch(my_hook)
        async def my_catch():
            pass

        assert my_catch in my_hook.hanging

    @pytest.mark.asyncio
    async def test_asynccatch___call___function_can_also_be_a_hook(self):
        """Ensure that by catching another catch coroutine, all coroutines in
        the chain are ran.

        """
        stack = set()

        @none.callable.asynchook
        async def my_hook():
            stack.add(0)

        @none.callable.asynccatch(my_hook)
        async def my_catch1():
            stack.add(1)

        @none.callable.asynccatch(my_catch1)
        async def my_catch2():
            stack.add(2)

        await my_hook()
        assert stack == {0, 1, 2}

    @pytest.mark.asyncio
    async def test_asynccatch___call___method_can_also_be_a_hook(self):
        """Ensure that by catching another catch method, all methods in the
        chain are ran.

        """
        stack = set()

        class AsyncHookable(object):
            @none.callable.asynchook
            async def my_hook(self):
                stack.add(0)

            @none.callable.asynccatch("my_hook")
            async def my_catch1(self):
                stack.add(1)

            @none.callable.asynccatch("my_catch1")
            async def my_catch2(self):
                stack.add(2)

        h = AsyncHookable()
        await h.my_hook()
        assert stack == {0, 1, 2}

    @pytest.mark.asyncio
    async def test_asynccatch___call___method_with_inheritance_can_also_be_a_hook(self):
        """Ensure that by catching another catch method, all methods in the
        chain are ran even when inheritance is involved.

        """
        stack = set()

        class AsyncHookable(object):
            @none.callable.asynchook
            async def my_hook(self):
                stack.add(0)

            @none.callable.asynccatch("my_hook")
            async def my_catch1(self):
                stack.add(1)

        class AsyncCatcher(AsyncHookable):
            @none.callable.asynccatch("my_catch1")
            async def my_catch2(self):
                stack.add(2)

        c = AsyncCatcher()
        await c.my_hook()
        assert stack == {0, 1, 2}
