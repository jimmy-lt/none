# tests/hash/test_tree.py
# =======================
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
import json
import random
import typing as ty
import hashlib
import itertools

import pytest
import pkg_resources

from hypothesis import given, assume, strategies as st

import none


@pytest.fixture
def meta() -> ty.Dict[str, ty.Any]:
    return json.load(
        pkg_resources.resource_stream("tests.lib", "hash/tree/merkle.json")
    )


@pytest.fixture(
    scope="module",
    params=filter(
        # Shake algorithms expect a parameter for their digest method and we
        # do not support this.
        lambda x: x not in {"shake_128", "shake_256"},
        hashlib.algorithms_guaranteed,
    ),
)
def hash_name(request):
    return request.param


@pytest.fixture(scope="module", params=("block_size", "digest_size", "name"))
def hash_property(request):
    return request.param


class TestMerkle(object):
    """Test cases for :class:`none.hash.tree.Merkle`."""

    def test___init___hash_name(self, hash_name: str):
        """A hash name string is accepted when initializing the tree."""
        assert none.hash.tree.Merkle(hash_name).name == hashlib.new(hash_name).name

    def test___init___hash_type(self, hash_name: str):
        """A hash class is accepted when initializing the tree."""
        hash = getattr(hashlib, hash_name)
        assert none.hash.tree.Merkle(hash).name == hash().name

    def test___init___hash_object(self, hash_name: str):
        """A hash object is accepted when initializing the tree."""
        hash = hashlib.new(hash_name)
        assert none.hash.tree.Merkle(hash).name == hash.name

    @given(iterable=st.iterables(st.binary()))
    def test___init___bytes_iterable(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """A bytes iterable can be provided when initializing the tree."""
        a, b = itertools.tee(iterable, 2)
        assert len(none.hash.tree.Merkle(hash_name, iterable=a)) == len(list(b))

    @given(iterable=st.iterables(st.binary()))
    def test___iter___return_hashes_of_ingested_data(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """The tree can be iterated over the hashes of its leaves."""
        hash = hashlib.new(hash_name)
        a, b = itertools.tee(iterable, 2)

        tree = none.hash.tree.Merkle(hash_name, iterable=a)
        result = list(iter(tree))
        target = []
        for data in b:
            h = hash.copy()
            h.update(tree.LEAF_SEED + data)
            target.append(h.digest())

        assert result == target

    @given(iterable=st.iterables(st.binary(), min_size=2))
    def test___delitem___whithin_bounds(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Leaves can be removed from the tree."""
        a, b = itertools.tee(iterable, 2)
        tree = none.hash.tree.Merkle(hash_name, iterable=a)

        b_len = len(list(b))
        # Select a random number of random indices to remove.
        remove = [
            random.randrange(b_len - x) for x in range(random.randrange(1, b_len))
        ]

        for idx in remove:
            del tree[idx]

        assert len(tree) == b_len - len(remove)

    @given(iterable=st.iterables(st.binary()))
    def test___delitem___out_of_bounds_index_error(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Trying to remove a leaf out of bound should raise ``IndexError``."""
        tree = none.hash.tree.Merkle(hash_name, iterable=iterable)
        with pytest.raises(IndexError):
            del tree[len(tree) + 1]

    @given(iterable=st.iterables(st.binary(), min_size=1))
    def test___getitem___return_hash_of_ingested_data(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Getting a leaf should return its hash."""
        hash = hashlib.new(hash_name)
        a, b = itertools.tee(iterable, 2)

        tree = none.hash.tree.Merkle(hash_name, iterable=a)
        target = []
        for data in b:
            h = hash.copy()
            h.update(tree.LEAF_SEED + data)
            target.append(h.digest())

        target_idx = random.randrange(len(target))

        assert len(tree) == len(target)
        assert tree[target_idx] == target[target_idx]

    @given(iterable=st.iterables(st.binary()))
    def test___getitem___out_of_bounds_index_error(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Trying to get a leaf out of bound should raise ``IndexError``."""
        tree = none.hash.tree.Merkle(hash_name, iterable=iterable)
        with pytest.raises(IndexError):
            tree[len(tree) + 1]

    @given(iterable=st.iterables(st.binary(), min_size=1), binary=st.binary())
    def test___setitem___set_hash_of_ingested_data(
        self, hash_name: str, iterable: ty.Iterable[bytes], binary: bytes
    ):
        """Setting a leave should replace the existing content."""
        a, b = itertools.tee(iterable, 2)

        tree = none.hash.tree.Merkle(hash_name, iterable=a)
        target_idx = random.randrange(len(list(b)))

        hash = hashlib.new(hash_name)
        hash.update(tree.LEAF_SEED + binary)
        target_hash = hash.digest()

        tree[target_idx] = binary
        assert tree[target_idx] == target_hash

    @given(
        iterable=st.iterables(st.binary()), binary=st.binary(),
    )
    def test___setitem___out_of_bounds_index_error(
        self, hash_name: str, iterable: ty.Iterable[bytes], binary: bytes
    ):
        """Trying to get a leaf out of bound should raise ``IndexError``."""
        tree = none.hash.tree.Merkle(hash_name, iterable=iterable)
        with pytest.raises(IndexError):
            tree[len(tree) + 1] = binary

    def test_properties_should_match_embedded_hash(
        self, hash_name: str, hash_property: str
    ):
        """The properties of the tree must match the embedded hash' properties."""
        target = hashlib.new(hash_name)
        result = none.hash.tree.Merkle(hash_name)

        assert getattr(result, hash_property) == getattr(target, hash_property)

    @given(binary=st.binary())
    def test__digest_leaf_should_prepend_null_byte(self, hash_name: str, binary: bytes):
        """A null-byte (``\x00``) must be prepended to leaves before hashing."""
        hash = hashlib.new(hash_name)
        tree = none.hash.tree.Merkle(hash_name)

        hash.update(tree.LEAF_SEED + binary)
        target = hash.digest()

        assert tree._digest_leaf(binary) == target

    @given(iterable=st.iterables(st.binary()))
    def test_copy_should_provide_same_hash(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """A copy of the tree should provide an identical hash compared to its
        parent.
        """
        parent = none.hash.tree.Merkle(hash_name, iterable=iterable)
        child = parent.copy()

        assert child.hexdigest() == parent.hexdigest()

    def test_digest_known_data_chunks(self, meta, lib_data):
        """Test to digest the data of known files."""
        name, data = lib_data[0], lib_data[1].read()
        ours = meta["files"][name]["checksum"]["merkle"]

        tree = none.hash.tree.Merkle(ours.split("$")[1])
        for start, end, ck_hash in meta["files"][name]["chunks"]:
            chunk = data[start:end]

            hash = hashlib.new(ck_hash.split("$")[1])
            hash.update(chunk)
            assert f"${hash.name}${hash.hexdigest()}" == ck_hash

            tree.update(chunk)

        assert f"${tree.name}${tree.digest().hex()}" == ours

    @given(iterable=st.iterables(st.binary(), min_size=1))
    def test_digest_return_hash_of_ingested_data(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Providing an index to digest should return the hash of the leaf at
        this index.

        """
        hash = hashlib.new(hash_name)
        a, b = itertools.tee(iterable, 2)

        tree = none.hash.tree.Merkle(hash_name, iterable=a)
        target = []
        for data in b:
            h = hash.copy()
            h.update(tree.LEAF_SEED + data)
            target.append(h.digest())

        target_idx = random.randrange(len(target))

        assert len(tree) == len(target)
        assert tree.digest(target_idx) == target[target_idx]

    @given(iterable=st.iterables(st.binary()))
    def test_digest_out_of_bounds_index_error(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Providing an out of bound index to digest should raise an
        ``IndexError``.

        """
        tree = none.hash.tree.Merkle(hash_name, iterable=iterable)
        with pytest.raises(IndexError):
            tree.digest(len(tree) + 1)

    def test_digest_empty_tree(self, hash_name):
        """Calling digest on an empty tree must return the empty hash of the
        embedded hash.

        """
        assert (
            none.hash.tree.Merkle(hash_name).digest() == hashlib.new(hash_name).digest()
        )

    def test_hexdigest_known_data_chunks(self, meta, lib_data):
        """Test to digest the data of known files."""
        name, data = lib_data[0], lib_data[1].read()
        ours = meta["files"][name]["checksum"]["merkle"]

        tree = none.hash.tree.Merkle(ours.split("$")[1])
        for start, end, ck_hash in meta["files"][name]["chunks"]:
            chunk = data[start:end]

            hash = hashlib.new(ck_hash.split("$")[1])
            hash.update(chunk)
            assert f"${hash.name}${hash.hexdigest()}" == ck_hash

            tree.update(chunk)

        assert f"${tree.name}${tree.hexdigest()}" == ours

    @given(iterable=st.iterables(st.binary(), min_size=1))
    def test_hexdigest_return_hash_of_ingested_data(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Providing an index to hexdigest should return the hash of the leaf at
        this index.

        """
        hash = hashlib.new(hash_name)
        a, b = itertools.tee(iterable, 2)

        tree = none.hash.tree.Merkle(hash_name, iterable=a)
        target = []
        for data in b:
            h = hash.copy()
            h.update(tree.LEAF_SEED + data)
            target.append(h.hexdigest())

        target_idx = random.randrange(len(target))

        assert len(tree) == len(target)
        assert tree.hexdigest(target_idx) == target[target_idx]

    @given(iterable=st.iterables(st.binary(), min_size=1))
    def test_hexdigest_equals_to_digest(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Calling hexdigest is the equivalent of digest in hexadecimal."""
        tree = none.hash.tree.Merkle(hash_name, iterable=iterable)
        assert tree.hexdigest() == tree.digest().hex()

    @given(iterable=st.iterables(st.binary()))
    def test_hexdigest_out_of_bounds_index_error(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Providing an out of bound index to digest should raise an
        ``IndexError``.

        """
        tree = none.hash.tree.Merkle(hash_name, iterable=iterable)
        with pytest.raises(IndexError):
            tree.hexdigest(len(tree) + 1)

    def test_hexdigest_empty_tree(self, hash_name):
        """Calling hexdigest on an empty tree must return the empty hash of the
        embedded hash.

        """
        assert (
            none.hash.tree.Merkle(hash_name).hexdigest()
            == hashlib.new(hash_name).hexdigest()
        )

    @given(iterable=st.iterables(st.binary(), min_size=1))
    def test_clear_empties_tree(self, hash_name: str, iterable: ty.Iterable[bytes]):
        """Clear should remove all leaves from the tree."""
        a, b = itertools.tee(iterable, 2)

        assert len(list(a)) > 0
        tree = none.hash.tree.Merkle(hash_name, iterable=b)
        tree.clear()

        assert len(tree) == 0

    @given(iterable=st.iterables(st.binary()), binary=st.binary())
    def test_append_add_leaf_at_the_end(
        self, hash_name, iterable: ty.Iterable[bytes], binary: bytes
    ):
        """Ensure that the appended data is found at the end of the leaves
        sequence.

        """
        a, b = itertools.tee(iterable, 2)
        target_len = target_idx = len(list(a))

        tree = none.hash.tree.Merkle(hash_name, iterable=b)
        assert len(tree) == target_len

        hash = hashlib.new(hash_name)
        hash.update(tree.LEAF_SEED + binary)
        target_hash = hash.digest()

        tree.append(binary)
        assert len(tree) == target_len + 1

        assert tree[target_idx] == target_hash
        assert tree[-1] == target_hash

    @given(iterable_1=st.iterables(st.binary()), iterable_2=st.iterables(st.binary()))
    def test_extend_add_leaves_at_the_end(
        self, hash_name, iterable_1: ty.Iterable[bytes], iterable_2: ty.Iterable[bytes]
    ):
        """Ensure that the appended data iterable is found at the end of the
        leaves sequence.

        """
        a_1, b_1 = itertools.tee(iterable_1, 2)
        a_2, b_2, c_2 = itertools.tee(iterable_2, 3)

        iterable_1_len = len(list(a_1))
        iterable_2_len = len(list(a_2))

        tree = none.hash.tree.Merkle(hash_name, iterable=b_1)
        assert len(tree) == iterable_1_len

        target_hash = []
        for x in b_2:
            hash = hashlib.new(hash_name)
            hash.update(tree.LEAF_SEED + x)
            target_hash.append(hash.digest())

        tree.extend(c_2)
        assert len(tree) == iterable_1_len + iterable_2_len

        for i, h in enumerate(target_hash):
            assert tree[iterable_1_len + i] == h

    @given(
        iterable=st.iterables(st.binary(), min_size=1), binary=st.binary(),
    )
    def test_insert_data_is_found_at_expected_index(
        self, hash_name: str, iterable: ty.Iterable[bytes], binary: bytes
    ):
        """Ensure that the inserted data is found at the expected index."""
        a, b = itertools.tee(iterable, 2)
        target_len = len(list(a))
        target_idx = random.randrange(target_len)

        tree = none.hash.tree.Merkle(hash_name, iterable=b)

        hash = hashlib.new(hash_name)
        hash.update(tree.LEAF_SEED + binary)
        target = hash.digest()

        tree.insert(target_idx, binary)
        assert len(tree) == target_len + 1

        assert tree[target_idx] == target

    @given(iterable=st.iterables(st.binary(), min_size=1))
    def test_pop_given_index(self, hash_name: str, iterable: ty.Iterable[bytes]):
        """Ensure that the retreived data is what we expected at the provided
        index.

        """
        a, b = itertools.tee(iterable, 2)
        tree = none.hash.tree.Merkle(hash_name, iterable=b)

        target = []
        for x in a:
            hash = hashlib.new(hash_name)
            hash.update(tree.LEAF_SEED + x)
            target.append(hash.digest())

        target_idx = random.randrange(len(target))
        assert tree.pop(target_idx) == target.pop(target_idx)

    @given(iterable=st.iterables(st.binary(), min_size=1))
    def test_pop_no_index(self, hash_name: str, iterable: ty.Iterable[bytes]):
        """When no index is provided, the last element must be returned."""
        a, b = itertools.tee(iterable, 2)
        tree = none.hash.tree.Merkle(hash_name, iterable=b)

        target = []
        for x in a:
            hash = hashlib.new(hash_name)
            hash.update(tree.LEAF_SEED + x)
            target.append(hash.digest())

        assert tree.pop() == target.pop()

    @given(iterable=st.iterables(st.binary()))
    def test_pop_out_of_bounds_index_error(
        self, hash_name: str, iterable: ty.Iterable[bytes]
    ):
        """Trying to pop out of bound should raise an ``IndexError``."""
        tree = none.hash.tree.Merkle(hash_name, iterable=iterable)
        with pytest.raises(IndexError):
            tree.pop(len(tree) + 1)
