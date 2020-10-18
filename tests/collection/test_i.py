# tests/collection/test_i.py
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
import itertools

from hypothesis import given, strategies as st

import none


@given(iterable=st.iterables(st.integers()))
def test_onexlast_list_expected(iterable):
    """At least one item from a given iterable should be returned except the
    last element.

    """
    a, b = itertools.tee(iterable, 2)
    target = list(b)
    if len(target) > 1:
        assert list(none.collection.i.onexlast(a)) == target[:-1]
    else:
        assert list(none.collection.i.onexlast(a)) == target


@given(iterable=st.iterables(st.integers()))
def test_xlast_list_expected(iterable):
    """All items from a given iterable should be returned except the last
    element.

    """
    a, b = itertools.tee(iterable, 2)
    assert list(none.collection.i.xlast(a)) == list(b)[:-1]
