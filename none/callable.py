# none/callable.py
# ================
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
"""Callable facilities."""
import sys
import time
import random
import typing as ty
import asyncio
import logging
import functools

from none.typeset import C, N, AsyncCallable


log = logging.getLogger(__name__)


class hook(object):
    """A *hook* is a function or a method which when it is called, will also
    execute all other functions or methods hanging to it.

    A hook is created by using the class as a decorator.

    ::

        >>> import none
        >>> @none.callable.hook
        ... def my_hook():
        ...     print("I'm a hook.")


    Other functions can hang to the hook defined above by using the
    :class:`none.callable.catch` decorator.

    ::

        >>> @none.callable.catch(my_hook)
        ... def my_catch():
        ...     print("I'm hanging.")


    Therefore, when ``my_hook()`` is called, it will also call ``my_hanger()``
    (and other hanging functions) afterwards.

    ::

        >>> my_hook()
        I'm a hook.
        I'm hanging.


    A hook can also decorate a method. A catch within the same class context
    (including a child class) can hang to the hook by using it's name.

    ::

        >>> class Hookable(object):
        ...     @none.callable.hook
        ...     def my_hook(self):
        ...          print("I'm a hook in a class.")
        ...     @none.callable.catch("my_hook")
        ...     def my_catch(self)
        ...         print("I'm catching in a class.")
        ...
        >>> h = Hookable()
        >>> h.my_hook()
        I'm a hook in a class.
        I'm catching in a class.


    :param fn: The function or method which must serve as a hook.
    :type fn: ~typing.Optional[~typing.Callable]

    """

    def __init__(self, fn: ty.Optional[ty.Callable]):
        """Constructor for :class:`none.callable.hook`."""
        self.fn = fn
        self.hanging = set()
        self._owner: ty.Optional[ty.Type] = None

        if fn is not None:
            functools.update_wrapper(self, fn)

    def __call__(self, *args, **kwargs):
        """Execute the hook function along with its hanging functions."""
        self.hangup()
        self.fn(*(self._args + args), **kwargs)
        for fn in self.hanging:
            fn(*args, **kwargs)

    def __get__(self, instance: ty.Any, owner: ty.Optional[ty.Type] = None) -> "hook":
        """Allow the hook to serve has a method in a class context.


        :param instance: An instance of the owning class.
        :type instance: ~typing.Any

        :param owner: The owner class when the method is accessed has a class
                      method.
        :type owner: ~typing.Optional[~typing.Type]


        :returns: The callable to be used by the owning class, in this instance,
                  the hook itself.
        :rtype: ~none.callable.hook

        """
        self._owner = instance or owner
        return self

    @property
    def _args(self):
        """Quick facility to provide the owning class as first argument within
        a class context.

        """
        if self._owner is not None:
            return (self._owner,)
        return ()

    def hangup(self):
        """When the decorator is used within a class context, look for catching
        methods and hang them to the hook.

        """
        if self._owner is None:
            # The hook has not been accessed from a class context.
            return

        for name in dir(self._owner):
            # NOTE: By using ``getattr``, we force all catchers in the class to
            # already setup their owning class via ``__get__``.
            member = getattr(self._owner, name, None)
            if isinstance(member, catch) and member.hook == getattr(
                self, "__name__", None
            ):
                member._owner = self._owner
                self.hanging.add(member)


class asynchook(hook):
    """An asynchronous *hook* is a coroutine which when it is scheduled, will
    also call all other coroutines hanging to it.

    A hook is created by using the class as a decorator.

    ::

        >>> import none
        >>> @none.callable.asynchook
        ... async def my_hook():
        ...     print("I'm an asynchronous hook.")


    Other coroutines can hang to the hook defined above by using the
    :class:`none.callable.asynccatch` decorator.

    ::

        >>> @none.callable.asynccatch(my_hook)
        ... async def my_catch():
        ...     print("I'm hanging asynchronously.")


    Therefore, when ``my_hook()`` is scheduled, it will also call ``my_catch()``
    (and other hanging functions) afterwards.

    ::

        >>> import asyncio
        >>> asyncio.get_event_loop().run_until_complete(my_hook())
        I'm an asynchronous hook.
        I'm hanging asynchronously.


    An asynchrounous hook can also decorate an asynchronous method. A catch
    within the same class context (including a child class) can hang to the hook
    by using it's name.

    ::

        >>> class AsyncHookable(object):
        ...     @none.callable.asynchook
        ...     async def my_hook(self):
        ...          print("I'm an asynchronous hook in a class.")
        ...     @none.callable.asynccatch("my_hook")
        ...     async def my_catch(self)
        ...         print("I'm catching asynchronously in a class.")
        ...
        >>> h = AsyncHookable()
        >>> asyncio.get_event_loop().run_until_complete(h.my_hook())
        I'm an asynchronous hook in a class.
        I'm catching asynchronously in a class.


    :param fn: The coroutine which can be hooked to.
    :type fn: ~typing.Optional[~typing.Callable]

    """

    async def __call__(self, *args, **kwargs):
        """Execute the hook along with its hanging coroutines."""
        self.hangup()
        await self.fn(*(self._args + args), **kwargs)
        await asyncio.gather(*(fn(*args, **kwargs) for fn in self.hanging))


class catch(hook):
    """The ``catch`` decorator allow a function to notify a hook that it needs
    to be executed when the hook is called. A *catch* is also a hook, therefore
    allowing a chain of reaction when the primary hook is called.

    In order to define a catching function, a hook must already be available.

    ::

        >>> import none
        >>> @none.callable.hook
        ... def my_hook():
        ...     print("I'm a hook.")


    Then any function can catch an existing hook.

    ::

        >>> @none.callable.catch(my_hook)
        ... def my_catch():
        ...     print("I'm hanging.")


    By calling the hook, all functions hanging to it will also be called.

    ::

        >>> my_hook()
        I'm a hook.
        I'm hanging.


    It is also possible to catch a hook within the same class context by
    using its name.

    ::

        >>> class Hookable(object):
        ...     @none.callable.hook
        ...     def my_hook(self):
        ...          print("I'm a hook in a class.")
        ...     @none.callable.catch("my_hook")
        ...     def my_catch(self)
        ...         print("I'm catching in a class.")
        ...
        >>> h = Hookable()
        >>> h.my_hook()
        I'm a hook in a class.
        I'm catching in a class.


    :param target: The hook or the name of the hook to catch.
    :type target: ~typing.Union[~none.callable.hook, str]

    """

    def __init__(self, target: ty.Union[hook, str]):
        """Constructor for :class:`none.callable.hook`."""
        super(catch, self).__init__(None)
        self.hook = target

    def __call__(self, *args, **kwargs):
        """Execute the hook function along with its hanging functions."""
        if self.fn is None:
            # Decorator mode, we need to setup the decorated function.
            self._register(args[0])
            return self
        else:
            # Run mode.
            return super(catch, self).__call__(*args, **kwargs)

    def _register(self, fn: ty.Callable):
        """Utility the register the decorated function with its hook.


        :param fn: The callable being decorated.
        :type fn: ~typing.Callable

        """
        self.fn = fn
        functools.update_wrapper(self, self.fn)
        if isinstance(self.hook, hook):
            self.hook.hanging.add(self)


class asynccatch(asynchook, catch):
    """The ``asynccatch`` decorator allow a coroutine to notify an asynchronous
    hook that it needs to be called when the hook is scheduled. A *catch* is
    also a hook, therefore allowing a chain of reaction when the primary hook is
    called.

    In order to define a catching coroutine, a hook must already be available.

    ::

        >>> import none
        >>> @none.callable.asynchook
        ... async def my_hook():
        ...     print("I'm an asynchronous hook.")


    Then any coroutine can catch an existing hook.

    ::

        >>> @none.callable.asynccatch(my_hook)
        ... async def my_catch():
        ...     print("I'm hanging asynchronously.")


    By scheduling the hook, all coroutines hanging to it will also be called.

    ::

        >>> import asyncio
        >>> asyncio.get_event_loop().run_until_complete(my_hook())
        I'm an asynchronous hook.
        I'm hanging asynchronously.


    It is also possible to catch an asynchronous hook within the same class
    context by using its name.

    ::

        >>> class AsyncHookable(object):
        ...     @none.callable.asynchook
        ...     async def my_hook(self):
        ...          print("I'm an asynchronous hook in a class.")
        ...     @none.callable.asynccatch("my_hook")
        ...     async def my_catch(self)
        ...         print("I'm catching asynchronously in a class.")
        ...
        >>> h = AsyncHookable()
        >>> asyncio.get_event_loop().run_until_complete(h.my_hook())
        I'm an asynchronous hook in a class.
        I'm catching asynchronously in a class.


    :param target: The hook or the name of the hook to catch.
    :type target: ~typing.Union[~none.callable.asynchook, str]

    """

    def __init__(self, target: ty.Union[hook, str]):
        """Constructor for :class:`none.callable.asynccatch`."""
        super(asynccatch, self).__init__(None)
        self.hook = target

    def __call__(self, *args, **kwargs):
        """Execute the hook function along with its hanging functions."""
        if self.fn is None:
            # Decorator mode, we need to setup the decorated coroutine.
            self._register(args[0])
            return self
        else:
            # Run mode, we have to execute our decorated coroutine.
            return asyncio.ensure_future(
                super(asynccatch, self).__call__(*args, **kwargs)
            )


class delay(object):
    """Delay the execution of the decorated function within specified bounds.
    When both ``low`` and  ``high`` are provided, a value within bounds of the
    two values is randomly chosen with. The ``mode``, is a value between ``low``
    and ``high`` to influence the delay distribution.


    :param low: The minimum amount of time in seconds for the function to be
                delayed.
    :type low: ~typing.Optional[~typing.Union[float, int]]

    :param high: The maximum amount of time in seconds for the function to be
                 delayed.
    :type high: ~typing.Union[float, int]

    :param mode: A weight value within bounds of ``low`` and ``high`` to
                 influence the distribution of the delay value.
    :type mode: ~typing.Optional[~typing.Union[float, int]]

    """

    @ty.overload
    def __init__(self, high: N):
        ...

    @ty.overload
    def __init__(self, low: N, high: N, mode: ty.Optional[N] = None):
        ...

    def __init__(self, *args):
        """Constructor for :class:`none.callable.delay`."""
        #: The minimum amount of time the function will be delayed.
        self.low: ty.Optional[N] = None
        #: The maximum amount of time the function will be delayed.
        self.high: N = None
        #: An optional weight to adjust the distribution value.
        self.mode: ty.Optional[N] = None

        if len(args) == 1 and callable(args[0]):
            # We were called without parenthesis.
            raise ValueError("cannot be used without arguments.")

        if len(args) == 1:
            # We're called only with the high delay value.
            self.high = args[0]
        elif len(args) == 2:
            # We're called with a range delay value.
            self.low, self.high = args
        elif len(args) == 3:
            self.low, self.high, self.mode = args
        else:
            raise ValueError("unexpected arguments.")

        if self.high is None:
            raise ValueError("`high` cannot be `None`.")
        if (self.low is not None and self.low < 0) or self.high < 0:
            raise ValueError("delay values must be non-negative.")
        if self.low is not None and self.low > self.high:
            raise ValueError("`low` cannot be higher than `high`.")

        # Mode cannot be outside low and high bounds.
        if (self.low is not None and self.mode is not None) and (
            self.low > self.mode or self.mode > self.high
        ):
            raise ValueError("`mode` is out of bounds.")

    def __call__(self, fn: C) -> C:
        """Wrap the decorated function to be delayed.


        :param fn: The function to be delayed.
        :type fn: ~typing.Callable


        :returns: The given callable, wrapped to be delayed as requested.
        :rtype: ~typing.Callable

        """

        @functools.wraps(fn)
        def _wrapper(*args, **kwargs):
            _secs = self.delay
            log.info(f"{fn.__name__}: delayed for {_secs:.02f} seconds.")
            time.sleep(_secs)
            log.info(f"{fn.__name__}: executing.")
            return fn(*args, **kwargs)

        return _wrapper

    @property
    def delay(self) -> N:
        """Return the amount of time by which the wrapped function must be
        delayed.


        :returns: The amount of time in seconds by which the function must be
                  delayed.
        :rtype: ~typing.Union[float, int]

        """
        if self.low is None:
            return self.high
        else:
            return random.triangular(self.low, self.high, self.mode)


class adelay(delay):
    """Delay the execution of the decorated awaitable function within specified
    bounds. When both ``low`` and  ``high`` are provided, a value within bounds
    of the two values is randomly chosen with. The ``mode``, is a value between
    ``low`` and ``high`` to influence the delay distribution.


    :param low: The minimum amount of time in seconds for the function to be
                delayed.
    :type low: ~typing.Optional[~typing.Union[float, int]]

    :param high: The maximum amount of time in seconds for the function to be
                 delayed.
    :type high: ~typing.Union[float, int]

    :param mode: A weight value within bounds of ``low`` and ``high`` to
                 influence the distribution of the delay value.
    :type mode: ~typing.Optional[~typing.Union[float, int]]

    """

    def __call__(self, fn: AsyncCallable) -> AsyncCallable:
        """Wrap the decorated awaitable function to be delayed.


        :param fn: The awaitable function to be delayed.
        :type fn: ~none.typeset.AsyncCallable


        :returns: The given awaitable callable, wrapped to be delayed as
                  requested.
        :rtype: ~none.typeset.AsyncCallable

        """

        @functools.wraps(fn)
        async def _wrapper(*args, **kwargs):
            _secs = self.delay
            log.info(f"{fn.__name__}: delayed for {_secs:.02f} seconds.")
            await asyncio.sleep(_secs)
            log.info(f"{fn.__name__}: executing.")
            return await fn(*args, **kwargs)

        return _wrapper


class retry(object):
    """Retry the provided function when the listed exception(s) is raised. If
    the allowed number of attempts is reached and the function still didn't
    succeed, the latest exception is raised on last resort.


    :param exception: The exception for which execution of the callable can be
                       tried again.
    :type exception: ~typing.Type[Exception]

    :param attempts: The amount of times execution of the function should be
                     tried. When set to ``None``, the function is tried
                     indefinitely.
    :type attempts: ~typing.Optional[int]

    """

    def __init__(
        self, *exception: ty.Type[Exception], attempts: ty.Optional[int] = None
    ):
        """Constructor for :class:`none.callable.retry`."""
        self.exception = exception
        if attempts is None:
            self._loop = range(sys.maxsize)
        elif attempts < 0:
            raise ValueError("attempts value must be non-negative.")
        else:
            self._loop = range(attempts)

    def __call__(self, fn: C) -> C:
        """Wrap the decorated function to be retried.


        :param fn: The function to be retried.
        :type fn: ~typing.Callable


        :returns: The given callable, wrapped to be retried as requested.
        :rtype: ~typing.Callable

        """

        @functools.wraps(fn)
        def _wrapper(*args, **kwargs):
            _exc = None
            for i in self._loop:
                log.info(f"{fn.__name__}: attempt {i}.")
                _exc = None
                try:
                    return fn(*args, **kwargs)
                except self.exception as e:
                    log.debug(f"{fn.__name__}: raised `{e!r}`.", exc_info=True)
                    log.info(f"{fn.__name__}: retry on `{e!r}`.")
                    _exc = e
            if _exc:
                log.error(f"{fn.__name__}: failed last with `{_exc!r}`.")
                raise _exc
            log.info(f"{fn.__name__}: completed.")

        return _wrapper


class aretry(retry):
    """Retry the provided awaitable function when the listed exception(s) is
    raised. If the allowed number of attempts is reached and the function still
    didn't succeed, the latest exception is raised on last resort.


    :param exception: The exception for which execution of the callable can be
                       tried again.
    :type exception: ~typing.Type[Exception]

    :param attempts: The amount of times execution of the function should be
                     tried. When set to ``None``, the function is tried
                     indefinitely.
    :type attempts: ~typing.Optional[int]

    """

    def __call__(self, fn: AsyncCallable) -> AsyncCallable:
        """Wrap the decorated awaitable function to be retried.


        :param fn: The awaitable function to be retried.
        :type fn: ~none.typeset.AsyncCallable


        :returns: The given callable, wrapped to be retried as requested.
        :rtype: ~none.typeset.AsyncCallable

        """

        @functools.wraps(fn)
        async def _wrapper(*args, **kwargs):
            _exc = None
            for i in self._loop:
                log.info(f"{fn.__name__}: attempt {i}.")
                _exc = None
                try:
                    return await fn(*args, **kwargs)
                except self.exception as e:
                    log.debug(f"{fn.__name__}: raised `{e!r}`.", exc_info=True)
                    log.info(f"{fn.__name__}: retry on `{e!r}`.")
                    _exc = e
            if _exc:
                log.error(f"{fn.__name__}: failed last with `{_exc!r}`.")
                raise _exc
            log.info(f"{fn.__name__}: completed.")

        return _wrapper
