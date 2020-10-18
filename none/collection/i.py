# none/collection/i.py
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
import typing as ty

from collections.abc import Iterator

from none.typeset import T, missing


class xlast(Iterator):
    """Make an iterator that returns all elements from the provided iterable
    except the last one.


    :param iterable: Iterable to get the elements from.
    :type iterable: ~collections.abc.Iterable

    """

    __slots__ = ("_it", "_next")

    def __init__(self, iterable: ty.Iterable[T]):
        """Constructor for :class:`none.collection.i.xlast`."""
        self._it = iter(iterable)
        self._next = missing

    def __iter__(self) -> "xlast":
        """Return the iterator."""
        return self

    def __next__(self) -> T:
        """Return the next value of this iterator."""
        if self._next is missing:
            self._next = next(self._it)
        current, self._next = self._next, next(self._it)
        return current
