# tests/collection/test_a.py
# ==========================
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
import typing as ty
import builtins
import itertools

from collections.abc import Iterator, AsyncIterator

import pytest

from hypothesis import given, assume, strategies as st

import none


#: Maximum range stop value not to have infinite loop tests.
MAX_RANGE = (2 ** 13) - 1


@pytest.fixture
def arange() -> ty.Type[ty.AsyncIterator[int]]:
    """Generate an asynchronous range iterator."""

    class AsyncRange(AsyncIterator):
        __slots__ = ("_it",)

        def __init__(self, *args: ty.Optional[int]):
            s = builtins.slice(*args)
            start, stop, step = (
                s.start or 0,
                s.stop or builtins.min(s.stop, MAX_RANGE),
                s.step or 1,
            )
            self._it = builtins.iter(builtins.range(start, stop, step))

        def __aiter__(self) -> "AsyncRange":
            return self

        async def __anext__(self) -> int:
            try:
                return builtins.next(self._it)
            except StopIteration:
                raise StopAsyncIteration

    return AsyncRange


@pytest.fixture
def astarrange() -> ty.Type[ty.AsyncIterator[ty.Tuple[int, ...]]]:
    """Generate an asynchronous star range iterator."""

    class AsyncStarRange(AsyncIterator):
        __slots__ = ("_it",)

        def __init__(self, *args: ty.Optional[int], elements: int = 1):
            s = builtins.slice(*args)
            start, stop, step = (
                s.start or 0,
                s.stop or builtins.min(s.stop, MAX_RANGE),
                s.step or 1,
            )
            self._it = builtins.tuple(
                builtins.iter(builtins.range(start, stop, step))
                for _ in builtins.range(elements)
            )

        def __aiter__(self) -> "AsyncStarRange":
            return self

        async def __anext__(self) -> ty.Tuple[int, ...]:
            try:
                return builtins.tuple([builtins.next(x) for x in self._it])
            except StopIteration:
                raise StopAsyncIteration

    return AsyncStarRange


@pytest.fixture
def starrange() -> ty.Type[ty.Iterator[ty.Tuple[int, ...]]]:
    """Generate a synchronous star range iterator."""

    class StarRange(Iterator):
        __slots__ = ("_it",)

        def __init__(self, *args: ty.Optional[int], elements: int = 1):
            s = slice(*args)
            start, stop, step = (
                s.start or 0,
                s.stop or min(s.stop, MAX_RANGE),
                s.step or 1,
            )
            self._it = tuple(iter(range(start, stop, step)) for _ in range(elements))

        def __iter__(self) -> "StarRange":
            return self

        def __next__(self) -> ty.Tuple[int, ...]:
            return tuple([next(x) for x in self._it])

    return StarRange


@pytest.fixture
def noopiter() -> ty.Type[ty.AsyncIterator]:
    """Generate an asynchronous iterator which just raises
    ``StopAsyncIterator``.

    """

    class NoopIter(AsyncIterator):
        __slots__ = ()

        def __aiter__(self) -> "NoopIter":
            return self

        async def __anext__(self):
            raise StopAsyncIteration

    return NoopIter


@pytest.fixture
def repeatfalse() -> ty.Type[ty.AsyncIterator[bool]]:
    """Generate an asynchronous iterator which repeats ``False`` for a specified
    amount of times.

    """

    class RepeatFalse(AsyncIterator):
        __slots__ = ("_it",)

        def __init__(self, times: int):
            self._it = iter(range(min(times, MAX_RANGE)))

        def __aiter__(self) -> "RepeatFalse":
            return self

        async def __anext__(self) -> bool:
            try:
                next(self._it)
            except StopIteration:
                raise StopAsyncIteration
            return False

    return RepeatFalse


@pytest.fixture
def repeattrue() -> ty.Type[ty.AsyncIterator[bool]]:
    """Generate an asynchronous iterator which repeats ``True`` for a specified
    amount of times.

    """

    class RepeatTrue(AsyncIterator):
        __slots__ = ("_it",)

        def __init__(self, times: int):
            self._it = iter(range(min(times, MAX_RANGE)))

        def __aiter__(self) -> "RepeatTrue":
            return self

        async def __anext__(self) -> bool:
            try:
                next(self._it)
            except StopIteration:
                raise StopAsyncIteration
            return True

    return RepeatTrue


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_all_should_return_true(
    repeattrue: ty.Type[ty.AsyncIterator[bool]], stop: int
):
    """An iterable with only true values should return ``True``."""
    assert await none.collection.a.all(repeattrue(stop)) is True


@pytest.mark.asyncio
@given(stop=st.integers(1, MAX_RANGE))
async def test_all_should_return_false(
    repeatfalse: ty.Type[ty.AsyncIterator[bool]], stop: int
):
    """An iterable with only false values should return ``False``."""
    assert await none.collection.a.all(repeatfalse(stop)) is False


@pytest.mark.asyncio
@given(stop=st.integers(1, MAX_RANGE))
async def test_all_mixed_should_return_false(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """An iterable mixed with false and true values should return ``False``."""
    assert await none.collection.a.all(arange(stop)) is False


# Empty list will return ``False`` so start from ``1``.
@pytest.mark.asyncio
@given(stop=st.integers(1, MAX_RANGE))
async def test_any_should_return_true(
    repeattrue: ty.Type[ty.AsyncIterator[bool]], stop: int
):
    """An iterable with only true values should return ``True``."""
    assert await none.collection.a.any(repeattrue(stop)) is True


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_any_should_return_false(
    repeatfalse: ty.Type[ty.AsyncIterator[bool]], stop: int
):
    """An iterable with only false values should return ``False``."""
    assert await none.collection.a.any(repeatfalse(stop)) is False


@pytest.mark.asyncio
@given(stop=st.integers(2, MAX_RANGE))
async def test_any_mixed_should_return_true(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """An iterable mixed with false and true values should return ``True``."""
    assert await none.collection.a.any(arange(stop)) is True


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_dropwhile_matches_itertools_dropwhile(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async dropwhile implementation follows the standard
    implementation.

    """

    async def _lowerhalf(x):
        return x < int(stop / 2)

    target = list(itertools.dropwhile(lambda x: x < int(stop / 2), range(stop)))
    result = [x async for x in none.collection.a.dropwhile(_lowerhalf, arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_enumerate_expected_result(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Look for expected results which should returned by
    :class:`none.collection.a.enumerate`.

    """
    async for i, x in none.collection.a.enumerate(arange(stop)):
        assert i == x


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_enumerate_matches_builtin_enumerate(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async enumerate implementation follows the standard
    implementation.

    """
    target = list(enumerate(range(stop)))
    result = [x async for x in none.collection.a.enumerate(arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_filter_matches_builtin_filter(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async filter implementation follows the standard
    implementation.

    """

    async def _pair(x):
        return (x % 2) == 0

    target = list(filter(lambda x: (x % 2) == 0, range(stop)))
    result = [x async for x in none.collection.a.filter(_pair, arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_filterfalse_matches_itertools_filterfalse(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async filterfalse implementation follows the standard
    implementation.

    """

    async def _pair(x):
        return (x % 2) == 0

    target = list(itertools.filterfalse(lambda x: (x % 2) == 0, range(stop)))
    result = [x async for x in none.collection.a.filterfalse(_pair, arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(
    start=st.integers(0, MAX_RANGE),
    stop=st.integers(0, MAX_RANGE),
    step=st.integers(0, MAX_RANGE),
)
async def test_islice_matches_itertools_islice(
    arange: ty.Type[ty.AsyncIterator[int]], start: int, stop: int, step: int
):
    """Ensure that our async islice implementation follows the standard
    implementation.

    """
    assume(step != 0)
    assume(start < stop)

    target = list(itertools.islice(range(stop), start, stop, step))
    result = [
        x async for x in none.collection.a.islice(arange(stop), start, stop, step)
    ]

    assert result == target


@pytest.mark.parametrize("start,stop,step", [(1, 1, 0), (1, -1, 1), (-1, 1, 1)])
def test_islice_should_raise_valueerror_on_negative_indicies(
    noopiter: ty.Type[ty.AsyncIterator], start: int, stop: int, step: int
):
    """Giving negative indices to :class:`none.collection.a.islice` should raise
    a ``ValueError`` exception.

    """
    with pytest.raises(ValueError):
        none.collection.a.islice(noopiter(), start, stop, step)


@given(start=st.integers(0, MAX_RANGE), stop=st.integers(0, MAX_RANGE))
def test_islice_start_higher_than_stop_should_raise_valueerror_on_negative_indicies(
    noopiter: ty.Type[ty.AsyncIterator], start: int, stop: int
):
    """Providing a ``start`` value higher than ``stop`` should raise a
    ``ValueError``.

    """
    assume(start > stop)

    with pytest.raises(ValueError):
        none.collection.a.islice(noopiter(), start, stop)


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_iter_with_callable_matches_builtin_iter(stop: int):
    """Ensure that our async iter implementation follows the standard
    implementation when using a callable function/awaitable.

    """
    sentinel = object()

    class _agen(object):
        def __init__(self, high: int, marker: ty.Any = sentinel):
            self._low = int(high / 2)
            self._cursor = 0
            self._marker = marker

        async def __call__(self) -> ty.Union[int, ty.Any]:
            if self._cursor < self._low or self._cursor > self._low:
                self._cursor += 1
            else:
                return self._marker
            return self._cursor

    class _gen(object):
        def __init__(self, high: int, marker: ty.Any = sentinel):
            self._low = int(high / 2)
            self._cursor = 0
            self._marker = marker

        def __call__(self) -> ty.Union[int, ty.Any]:
            if self._cursor < self._low or self._cursor > self._low:
                self._cursor += 1
            else:
                return self._marker
            return self._cursor

    target = [x for x in iter(_gen(stop), sentinel)]
    result = [x async for x in none.collection.a.iter(_agen(stop), sentinel)]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_map_expected_result(arange: ty.Type[ty.AsyncIterator[int]], stop: int):
    """Look for expected results which should returned by
    :class:`none.collection.a.map`.

    """

    async def _add1(x: int) -> int:
        return x + 1

    async for i, x in none.collection.a.enumerate(
        none.collection.a.map(_add1, arange(stop)), start=1
    ):
        assert x == i


def test_map_non_callable_should_raise_typeerror(noopiter: ty.Type[ty.AsyncIterator]):
    """Providing a non-callable object should raise a ``TypeError``."""
    with pytest.raises(TypeError):
        none.collection.a.map(None, noopiter())


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_map_matches_builtin_map(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async map implementation follows the standard
    implementation.

    """

    async def _add1(x: int) -> int:
        return x + 1

    target = list(map(lambda x: x + 1, range(stop)))
    result = [x async for x in none.collection.a.map(_add1, arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_map_two_iterables_expected_result(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Look for expected results which should returned by
    :class:`none.collection.a.map` with two iterables given.

    """

    async def _add(a: int, b: int) -> int:
        return a + b

    async for i, x in none.collection.a.enumerate(
        none.collection.a.map(_add, arange(stop), arange(stop))
    ):
        assert x == (i + i)


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_map_matches_builtin_map_with_two_iterables(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async map implementation follows the standard
    implementation with two iterables.

    """

    async def _add(a: int, b: int) -> int:
        return a + b

    target = list(map(lambda a, b: a + b, range(stop), range(stop)))
    result = [x async for x in none.collection.a.map(_add, arange(stop), arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_map_next_should_provide_expected_value(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Look for expected results which should returned by
    :class:`none.collection.a.enumerate`.

    """

    async def _noop(x):
        return x

    it = none.collection.a.map(_noop, arange(stop))
    for i in range(stop):
        assert await none.collection.a.next(it) == i


@pytest.mark.asyncio
async def test_map_exhausted_should_raise_stopasynciteration(
    noopiter: ty.Type[ty.AsyncIterator],
):
    """Reaching iterator exhaustion should raise a ``StopAsyncIteration``
    exception.

    """

    async def _noop(x):
        return x

    with pytest.raises(StopAsyncIteration):
        await none.collection.a.next(none.collection.a.map(_noop, noopiter()))


@pytest.mark.asyncio
async def test_next_exhausted_should_raise_stopasynciteration(
    noopiter: ty.Type[ty.AsyncIterator],
):
    """Reaching iterator exhaustion should raise a ``StopAsyncIteration``
    exception.

    """
    with pytest.raises(StopAsyncIteration):
        await none.collection.a.next(noopiter())


@pytest.mark.asyncio
@pytest.mark.parametrize("default", [object(), None])
async def test_next_exhausted_should_return_default(
    noopiter: ty.Type[ty.AsyncIterator], default
):
    """Reaching iterator exhaustion should return the default value when
    provided.

    """
    assert await none.collection.a.next(noopiter(), default=default) is default


@pytest.mark.asyncio
async def test_next_non_iterator_should_raise_typeerror():
    """Providing a non-iterable object should raise a ``TypeError``."""
    with pytest.raises(TypeError):
        await none.collection.a.next(1)


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_onexlast_list_expected(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """At least one item from a given iterable should be returned except the
    last element.

    """
    if stop > 1:
        target = list(range(stop))[:-1]
    else:
        target = list(range(stop))
    result = [x async for x in none.collection.a.onexlast(arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_repeat_awaitable_callable(stop: int):
    """Ensure that :class:`none.collection.a.repeat` can repeat the value
    returned by an awaitable callable.

    """

    async def _true():
        return True

    result = [x async for x in none.collection.a.repeat(_true, times=stop)]

    assert len(result) == stop
    assert all(result)


@pytest.mark.asyncio
@given(stop=st.integers(1, MAX_RANGE))
async def test_starmap_expected_result(
    astarrange: ty.Type[ty.AsyncIterator[ty.Tuple[int, ...]]], stop: int
):
    """Look for expected results which should returned by
    :class:`none.collection.a.starmap`.

    """

    async def _add1(x: int) -> int:
        return x + 1

    async for i, x in none.collection.a.enumerate(
        none.collection.a.starmap(_add1, astarrange(stop)), start=1
    ):
        assert x == i


def test_starmap_non_callable_should_raise_typeerror(
    noopiter: ty.Type[ty.AsyncIterator],
):
    """Providing a non-callable object should raise a ``TypeError``."""
    with pytest.raises(TypeError):
        none.collection.a.starmap(None, noopiter())


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_starmap_matches_builtin_starmap(
    astarrange: ty.Type[ty.AsyncIterator[ty.Tuple[int, ...]]],
    starrange: ty.Type[ty.Iterator[ty.Tuple[int, ...]]],
    stop: int,
):
    """Ensure that our async starmap implementation follows the standard
    implementation.

    """

    async def _add1(x: int) -> int:
        return x + 1

    target = list(itertools.starmap(lambda x: x + 1, starrange(stop)))
    result = [x async for x in none.collection.a.starmap(_add1, astarrange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_startmap_two_elements_iterable_expected_result(
    astarrange: ty.Type[ty.AsyncIterator[ty.Tuple[int, ...]]], stop: int
):
    """Look for expected results which should returned by
    :class:`none.collection.a.start` with a two elements iterable given.

    """

    async def _add(a: int, b: int) -> int:
        return a + b

    async for i, x in none.collection.a.enumerate(
        none.collection.a.starmap(_add, astarrange(stop, elements=2))
    ):
        assert x == (i + i)


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_starmap_matches_itertools_starmap_with_two_elements_iterable(
    astarrange: ty.Type[ty.AsyncIterator[ty.Tuple[int, ...]]],
    starrange: ty.Type[ty.Iterator[ty.Tuple[int, ...]]],
    stop: int,
):
    """Ensure that our async starmap implementation follows the standard
    implementation with two elements.

    """

    async def _add(a: int, b: int) -> int:
        return a + b

    target = list(itertools.starmap(lambda a, b: a + b, starrange(stop, elements=2)))
    result = [
        x async for x in none.collection.a.starmap(_add, astarrange(stop, elements=2))
    ]

    assert result == target


@pytest.mark.asyncio
async def test_starmap_exhausted_should_raise_stopasynciteration(
    noopiter: ty.Type[ty.AsyncIterator],
):
    """Reaching iterator exhaustion should raise a ``StopAsyncIteration``
    exception.

    """

    async def _noop(x):
        return x

    with pytest.raises(StopAsyncIteration):
        await none.collection.a.next(none.collection.a.starmap(_noop, noopiter()))


@pytest.mark.asyncio
@given(stop=st.integers(1, MAX_RANGE))
async def test_sum_matches_builtin_sum(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async sum implementation follows the standard
    implementation.

    """
    target = sum(range(stop))
    result = await none.collection.a.sum(arange(stop))

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_takewhile_matches_itertools_takewhile(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async takewhile implementation follows the standard
    implementation.

    """

    async def _lowerhalf(x):
        return x < int(stop / 2)

    target = list(itertools.takewhile(lambda x: x < int(stop / 2), range(stop)))
    result = [x async for x in none.collection.a.takewhile(_lowerhalf, arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_xlast_list_expected(arange: ty.Type[ty.AsyncIterator[int]], stop: int):
    """All items from a given iterable should be returned except the last
    element.

    """
    target = list(range(stop))[:-1]
    result = [x async for x in none.collection.a.xlast(arange(stop))]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_zip_matches_builtin_zip(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async zip implementation follows the standard
    implementation.

    """
    target = list(zip(range(int(stop / 2)), range(int(stop))))
    result = [
        x async for x in none.collection.a.zip(arange(int(stop / 2)), arange(stop))
    ]

    assert result == target


@pytest.mark.asyncio
@given(stop=st.integers(0, MAX_RANGE))
async def test_zip_longest_matches_itertools_zip_longest(
    arange: ty.Type[ty.AsyncIterator[int]], stop: int
):
    """Ensure that our async zip_longest implementation follows the standard
    implementation.

    """
    fillvalue = object()

    target = list(
        itertools.zip_longest(
            range(int(stop / 2)), range(int(stop)), fillvalue=fillvalue
        )
    )
    result = [
        x
        async for x in none.collection.a.zip_longest(
            arange(int(stop / 2)), arange(stop), fillvalue=fillvalue
        )
    ]

    assert result == target
