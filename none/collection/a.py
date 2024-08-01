# none/collection/a.py
# ====================
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

# NOTE: In this module iterators are defined instead of generators to better
#       match CPython implementation.

import sys
import typing as ty
import inspect
import builtins
import itertools

from collections.abc import AsyncIterator

from none.typeset import T, AsyncCallable, missing


async def all(iterable: ty.AsyncIterator[T]) -> bool:
    """Return ``True`` if **all** elements of the iterable are true (or if the
    iterable is empty).


    :param iterable: The asynchronous iterable to be checked.
    :type iterable: ~typing.AsyncIterator


    :returns: Whether all elements of the iterable are true or if the iterable
              is empty.
    :rtype: bool

    """
    async for x in iter(iterable):
        if not x:
            return False
    return True


async def any(iterable: ty.AsyncIterator[T]) -> bool:
    """Return ``True`` if at least one element of the iterable is true. If the
    iterable is empty, return ``False``.


    :param iterable: The asynchronous iterable to be checked.
    :type iterable: ~typing.AsyncIterator


    :returns: Whether at least one element of the iterable is true. If the
              iterable is empty, ``False`` is returned.
    :rtype: bool

    """
    async for x in iter(iterable):
        if x:
            return True
    return False


class dropwhile(AsyncIterator):
    """Make an asynchronous iterator that drops elements from the iterable as
    long as the predicate is true; afterwards, returns every element. Note, the
    iterator does not produce any output until the predicate first becomes
    false, so it may have a lengthy start-up time.


    :param predicate: An awaitable callable which is provided each value from
                      the iterable and which boolean return value will be used
                      to decide on whether the value should be dropped
    :type predicate: ~none.typeset.AsyncCallable

    """

    __slots__ = ("_drop", "_func", "_it")

    def __init__(self, predicate: AsyncCallable, iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.dropwhile`."""
        self._it = iter(iterable)
        self._drop = True
        self._func = predicate

    def __aiter__(self) -> "dropwhile":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        if self._drop:
            while True:
                x = await next(self._it)
                if await self._func(x):
                    continue

                self._drop = False
                return x
        else:
            return await next(self._it)


class enumerate(AsyncIterator):
    """Make an asynchronous iterator which returns a tuple containing a count
    (from start which defaults to 0) and the values obtained from iterating over
    iterable.


    :param iterable: A sequence, an iterator, or some other object which
                     supports asynchronous iteration.
    :type iterable: ~typing.AsyncIterator

    :param start: The value to start counting the iteration from.
    :type start: int

    """

    __slots__ = ("_idx", "_it")

    def __init__(self, iterable: ty.AsyncIterator[T], start: int = 0):
        """Constructor for :class:`none.collection.a.dropwhile`."""
        self._it = iter(iterable)
        self._idx = start

    def __aiter__(self) -> "enumerate":
        """Return the iterator."""
        return self

    async def __anext__(self) -> ty.Tuple[int, T]:
        """Return the next value of this iterator."""
        i = self._idx
        x = await next(self._it)

        self._idx += 1
        return i, x


class filter(AsyncIterator):
    """Construct an asynchronous iterator from those elements of iterable for
    which function returns true.


    :param function: A function which is provided each element of the iterable
                     and select element to be filtered out by returning
                     ``True``.
    :type function: ~none.typeset.AsyncCallable

    :param iterable: A sequence, an iterator, or some other object which
                      supports asynchronous iteration.
    :type iterable: ~typing.AsyncIterator

    """

    __slots__ = ("_func", "_it")

    def __init__(self, function: AsyncCallable, iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.filter`."""
        self._it = iter(iterable)

        self._func = function
        if function is None:

            async def _func(x):
                return bool(x)

            self._func = _func

    def __aiter__(self) -> "filter":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        while True:
            x = await next(self._it)
            if await self._func(x):
                return x


class filterfalse(AsyncIterator):
    """Construct an asynchronous iterator from those elements of iterable for
    which function returns false.


    :param function: A function which is provided each element of the iterable
                     and select element to be filtered out by returning
                     ``False``.
    :type function: ~none.typeset.AsyncCallable

    :param iterable: A sequence, an iterator, or some other object which
                     supports asynchronous iteration.
    :type iterable: ~typing.AsyncIterator

    """

    __slots__ = ("_func", "_it")

    def __init__(self, function: AsyncCallable, iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.filterfalse`."""
        self._it = iter(iterable)

        self._func = function
        if function is None:

            async def _func(x):
                return bool(x)

            self._func = _func

    def __aiter__(self) -> "filterfalse":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        while True:
            x = await next(self._it)
            if not await self._func(x):
                return x


class islice(AsyncIterator):
    """Make an asynchronous iterator that returns selected elements from the
    iterable. If ``start`` is non-zero, then elements from the iterable are
    skipped until ``start`` is reached. Afterward, elements are returned
    consecutively unless step is set higher than one which results in items
    being skipped. If stop is ``None``, then iteration continues until the
    iterator is exhausted, if at all; otherwise, it stops at the specified
    position.

    Unlike regular slicing, :class:`~none.collection.a.islice` does not support
    negative values for ``start``, ``stop``, or ``step``.


    :param iterable: A sequence, an iterator, or some other object which
                     supports asynchronous iteration.
    :type iterable: ~typing.AsyncIterator

    :param start: The initial position from which to start generating values
                  from the provided iterable.
    :type start: int

    :param stop: The final position at which to stop generating values from the
                 provided iterable.
    :type stop: int

    :param step: Interval a which values will be taken from the provided
                 iterable.
    :type step: int

    """

    __slots__ = ("_cursor", "_it", "_next", "_nextit", "_step", "_stop")

    @ty.overload
    def __init__(self, iterable: ty.AsyncIterator[T], stop: ty.Optional[int]):
        ...

    @ty.overload
    def __init__(
        self,
        iterable: ty.AsyncIterator[T],
        start: int,
        stop: int,
        step: ty.Optional[int],
    ):
        ...

    def __init__(self, iterable: ty.AsyncIterator[T], *args: ty.Optional[int]):
        """Constructor for :class:`none.collection.a.islice`."""
        s = slice(*args)
        if s.start is not None and s.start < 0:
            raise ValueError("start must be a positive integer.")
        if s.stop is not None and s.stop < 0:
            raise ValueError("stop must be a positive integer.")
        if s.step is not None and s.step < 1:
            raise ValueError("step must be a non-null positive integer.")

        self._next = s.start or 0
        self._stop = s.stop if s.stop is not None else sys.maxsize
        self._step = s.step or 1
        self._cursor = 0

        if self._next > self._stop:
            raise ValueError("start cannot be higher than stop.")

        self._it = iter(iterable)
        self._nextit = builtins.iter(range(self._next, self._stop, self._step))

    def __aiter__(self) -> "islice":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        try:
            self._next = builtins.next(self._nextit)
        except StopIteration:
            # Leave iterable to requested *stop* index.
            for _ in range(self._cursor + 1, self._stop):
                await next(self._it)
            raise StopAsyncIteration

        while self._cursor < self._next:
            await next(self._it)
            self._cursor += 1

        item = await next(self._it)
        self._cursor += 1
        return item


class IterCallable(AsyncIterator):
    """Make an asynchronous iterator from the values returned by the provided
    awaitable callable. The iteration stops when the value returned from the
    callable matches a provided sentinel value.


    :param function: The awaitable callable to iterate values from.
    :type function: ~none.typeset.AsyncCallable

    :param sentinel: An object which stops the iteration when it equals a value
                     from the callable.
    :type sentinel: ~typing.Any

    """

    __slots__ = ("_func", "_sentinel")

    def __init__(self, function: AsyncCallable, sentinel: ty.Any = missing):
        """Constructor for :class:`none.collection.a.IterCallable`."""
        self._func = function
        self._sentinel = sentinel

    def __aiter__(self) -> "IterCallable":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        x = await self._func()
        if x == self._sentinel:
            raise StopAsyncIteration
        return x


@ty.overload
def iter(iterable: ty.AsyncIterator[T]) -> ty.AsyncIterator:
    ...


@ty.overload
def iter(iterable: AsyncCallable, sentinel: ty.Any) -> ty.AsyncIterator:
    ...


def iter(
    iterable: ty.Union[ty.AsyncIterator[T], AsyncCallable], sentinel: ty.Any = missing
) -> ty.AsyncIterator:
    """Return an asynchronous iterator object. The first argument is interpreted
    very differently depending on the presence of the second argument. Without a
    second argument, object must be a collection object which supports the
    asynchronous iteration protocol (the :meth`object.__aiter__` method). If
    the protocol is not supported, :class:`TypeError` is raised.

    If the second argument, ``sentinel``, is given, then object must be an
    awaitable callable object. The iterator created in this case will call
    object with no arguments for each call to its
    :meth:`~none.collection.a.iter.__anext__` method; if the value returned is
    equal to ``sentinel``, :class:`StopAsyncIteration` will be raised,
    otherwise the value will be returned.


    :param iterable: An object which supports the asynchronous iteration
                     protocol or when ``sentinel`` is provided, an awaitable
                     callable to fetch values from.
    :type iterable: ~typing.Union[~typing.AsyncIterator, AsyncCallable]

    :param sentinel: When ``iterable`` is a callable, a value to stop the
                     iteration when encountered.
    :type sentinel: ~typing.Any


    :returns: The asynchronous iterator object bound to the provided iterable.


    :raises TypeError: When the provided iterable does not support the
                       asynchronous iteration protocol or when it is not a
                       callable.

    """
    if sentinel is missing:
        if isinstance(iterable, AsyncIterator):
            return iterable

        try:
            return iterable.__aiter__()
        except AttributeError:
            raise TypeError(f"{type(iterable)} object is not an async iterator.")
    else:
        if not callable(iterable):
            raise TypeError("iterable must be a callable.")
        return IterCallable(iterable, sentinel=sentinel)


class map(AsyncIterator):
    """Return an asynchronous iterator that applies ``function`` to every item
    of ``iterable``, yielding the results. If additional iterable arguments are
    passed, ``function`` must take that many arguments and is applied to the
    items from all iterables in parallel.

    With multiple iterables, the iterator stops when the shortest iterable is
    exhausted.


    :param function: An awaitable callable to apply on each values produced by
                     the given iterable(s).
    :type function: ~none.typeset.AsyncCallable

    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator


    :raises TypeError: When provided function is not a callable object.

    """

    __slots__ = ("_func", "_it")

    def __init__(self, function: AsyncCallable, *iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.iter`."""
        if not callable(function):
            raise TypeError("function is not a callable object.")

        self._func = function
        self._it = [iter(x) for x in iterable]

    def __aiter__(self) -> "map":
        """Return the iterator."""
        return self

    async def __anext__(self) -> ty.Any:
        """Return the next value of this iterator."""
        return await self._func(*[await next(x) for x in self._it])


async def next(
    iterable: ty.AsyncIterator[T], default: ty.Optional[ty.Any] = missing
) -> ty.Union[T, ty.Any]:
    """Retrieve the next item from the asynchronous iterator by awaiting its
    :meth:`object.__anext__` method. If ``default`` is given, it is returned if
    the iterator is exhausted, otherwise :class:`StopAsyncIteration` is raised.


    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator

    :param default: A value to be returned in case the iterator is exhausted.
    :type default: ~typing.Any


    :returns: The next value from the provided asynchronous iterator or the
              provided default in case it is exhausted.


    :raises StopAsyncIteration: When the iterator is exhausted and no default
                                value is provided.

    """
    anxt = iter(iterable).__anext__
    try:
        return await anxt()
    except StopAsyncIteration:
        if default is not missing:
            return default
        raise


class onexlast(AsyncIterator):
    """Make an asynchronous iterator that returns at least one element or all
    elements except the last one from the provided asynchronous iterable.


    :param iterable: Iterable to get the elements from.
    :type iterable: ~typing.AsyncIterator

    """

    __slots__ = ("_it", "_next")

    def __init__(self, iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.onexlast`."""
        self._it = iter(iterable)
        self._next = missing

    def __aiter__(self) -> "onexlast":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        if self._next is missing:
            self._next, self._it = await next(self._it), xlast(self._it)
            return self._next
        return await next(self._it)


class repeat(AsyncIterator):
    """Make an asynchronous iterator that returns object over and over again.
    Runs indefinitely unless the ``times`` argument is specified.


    :param obj: An abject to be repeated, the object can also be an awaitable
                or an awaitable callable which will be awaited to get the value
                to be repeated.
    :type obj: ~typing.Union[~none.typeset.AsyncCallable, ~typing.Awaitable, ~typing.Any]

    :param times: When not ``None`` the amount of times the provided object
                  should repeat.
    :type times: ~typing.Optional[int]

    """

    __slots__ = ("_provider", "_repeat")

    def __init__(
        self,
        obj: ty.Union[AsyncCallable, ty.Awaitable, ty.Any],
        times: ty.Optional[int] = None,
    ):
        """Constructor for :class:`none.collection.a.repeat`."""
        self._provider = obj

        self._repeat = itertools.repeat(True)
        if times is not None:
            self._repeat = builtins.iter(range(times))

    def __aiter__(self) -> "repeat":
        """Return the iterator."""
        return self

    async def __anext__(self) -> ty.Any:
        """Return the next value of this iterator."""
        try:
            builtins.next(self._repeat)
        except StopIteration:
            raise StopAsyncIteration

        if callable(self._provider):
            return await self._provider()
        elif inspect.isawaitable(self._provider):
            return await self._provider
        else:
            return self._provider


class starmap(AsyncIterator):
    """Make an asynchronous iterator that computes the function using arguments
    obtained from the iterable. Used instead of :class:`none.collection.a.map`
    when argument parameters are already grouped in tuples from a single
    asynchronous iterable.


    :param function: An awaitable callable to apply on each values produced by
                     the given iterable(s).
    :type function: ~none.typeset.AsyncCallable

    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator


    :raises TypeError: When provided function is not a callable object.

    """

    __slots__ = ("_func", "_it")

    def __init__(self, function: AsyncCallable, iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.starmap`."""
        if not callable(function):
            raise TypeError("function is not a callable object.")

        self._func = function
        self._it = iter(iterable)

    def __aiter__(self) -> "starmap":
        """Return the iterator."""
        return self

    async def __anext__(self) -> ty.Any:
        """Return the next value of this iterator."""
        return await self._func(*(await next(self._it)))


async def sum(iterable: ty.AsyncIterator[T], start: ty.Optional[T] = None) -> T:
    """Sums ``start`` and the items of an asynchronous iterable from left to
    right and returns the total.

    The iterable’s items are normally numbers but any object allowing the
    addition operation is accepted.


    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator

    :param start: The initial value to start the sum from.
    :type start: ~typing.Any


    :returns: The left to right sum of the elements from provided iterator.
    :rtype: ~typing.Any

    """
    it = iter(iterable)

    stack = start
    if start is None:
        stack = await next(it)

    async for x in it:
        stack += x
    return stack


class takewhile(AsyncIterator):
    """Make an iterator that takes elements from the iterable as long as the
    predicate is true; afterwards, returns every element. Note, the iterator
    does not produce any output until the predicate first becomes false, so it
    may have a lengthy start-up time.


    :param predicate: An awaitable callable which is provided each value from
                       the iterable and which boolean return value will be used
                       to decide on whether the value should be dropped
    :type predicate: ~none.typeset.AsyncCallable

    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator

    """

    __slots__ = ("_take", "_func", "_it")

    def __init__(self, predicate: AsyncCallable, iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.takewhile`."""
        self._it = iter(iterable)
        self._take = True
        self._func = predicate

    def __aiter__(self) -> "takewhile":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        if self._take:
            x = await next(self._it)
            if await self._func(x):
                return x
            else:
                self._take = False

        raise StopAsyncIteration


class xlast(AsyncIterator):
    """Make an asynchronous iterator that returns all elements from the
    asynchronous iterable except the last one.


    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator

    """

    __slots__ = ("_it", "_next")

    def __init__(self, iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.xlast`."""
        self._it = iter(iterable)
        self._next = missing

    def __aiter__(self) -> "xlast":
        """Return the iterator."""
        return self

    async def __anext__(self) -> T:
        """Return the next value of this iterator."""
        if self._next is missing:
            self._next = await next(self._it)
        current, self._next = self._next, await next(self._it)
        return current


class zip(AsyncIterator):
    """Make an asynchronous iterator that aggregates elements from each of the
    asynchronous iterables. The iterator stops when the shortest input iterable
    is exhausted. With a single iterable argument, it returns an iterator of
    1-tuples.


    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator

    """

    __slots__ = ("_it",)

    def __init__(self, *iterable: ty.AsyncIterator[T]):
        """Constructor for :class:`none.collection.a.zip`."""
        self._it = tuple(iter(x) for x in iterable)

    def __aiter__(self) -> "zip":
        """Return the iterator."""
        return self

    async def __anext__(self) -> ty.Tuple[T, ...]:
        """Return the next value of this iterator."""
        return tuple([await next(x) for x in self._it])


class zip_longest(AsyncIterator):
    """Make an asynchronous iterator that aggregates elements from each of the
    iterables. If the iterables are of uneven length, missing values are
    filled-in with ``fillvalue``. Iteration continues until the longest iterable
    is exhausted.


    :param iterable: An object which supports the asynchronous iteration
                     protocol.
    :type iterable: ~typing.AsyncIterator

    :param fillvalue: An object to replace missing values from exhausted
                      iterators. The object can also be an awaitable
                      or an awaitable callable which will be awaited to get the
                      replacement value.
    :type fillvalue: ~typing.Union[~none.typeset.AsyncCallable, ~typing.Awaitable, ~typing.Any]

    """

    __slots__ = ("_fill", "_it", "_running")

    def __init__(
        self,
        *iterable: ty.AsyncIterator[T],
        fillvalue: ty.Optional[ty.Union[AsyncCallable, ty.Awaitable, ty.Any]] = None,
    ):
        """Constructor for :class:`none.collection.a.zip_longest`."""
        self._it = [iter(x) for x in iterable]
        self._fill = fillvalue
        self._running = len(self._it)

    def __aiter__(self) -> "zip_longest":
        """Return the iterator."""
        return self

    async def __anext__(self):
        """Return the next value of this iterator."""
        if not self._running:
            raise StopAsyncIteration

        values = []
        for i, it in builtins.enumerate(self._it):
            try:
                x = await next(it)
            except StopAsyncIteration:
                self._running -= 1
                if not self._running:
                    raise

                self._it[i] = repeat(self._fill)
                x = await next(self._it[i])

            values.append(x)

        return tuple(values)
