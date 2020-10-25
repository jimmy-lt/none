# none/hash/tree.py
# =================
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
import hashlib

from itertools import zip_longest
from collections import deque
from collections.abc import MutableSequence

from _hashlib import HASH


class Merkle(MutableSequence):
    """A binary tree in which every leaf node is labelled with the cryptographic
    hash of a given data block and every non-leaf node is labelled with the
    cryptographic hash of the labels of its child nodes.


    ..code-block:

                          ---------------
                         |     Root      |
                         |---------------|
                         | hash(n0 + n1) |
                          ---------------
                         /               \
             ---------------           ---------------
            |    Node 0     |         |    Node 1     |
            |---------------|         |---------------|
            | hash(l0 + l1) |         | hash(l2 + l3) |
             ---------------           ---------------
              /          \\             /          \\
         ----------   ----------   ----------   ----------
        |  Leaf 0  | |  Leaf 1  | |  Leaf 2  | |  Leaf 3  |
        |----------| |----------| |----------| |----------|
        | hash(d0) | | hash(d1) | | hash(d2) | | hash(d3) |
         ----------   ----------   ----------   ----------
              |            |            |            |
         -------------------------------------------------
        |    d0     |     d1     |     d2     |     d3    |
         -------------------------------------------------
                            data blocks


    The tree is managed as a sequence where leaves are added or removed and
    therefore supports a subset of the :class:`~collections.abc.MutableSequence`
    operations.

    The tree also acts as a conventional :mod:`hashlib` object.


    :param hash: Hash function to use.
    :type hash: ~typing.Union[str, ~_hashlib.HASH, ~typing.Type[~_hashlib.HASH]]

    :param iterable: An iterable with the data to initialize the tree with.
    :type iterable: ~typing.Optional[~typing.Iterable[bytes]]

    """

    __slots__ = ("_hash", "_leaves")

    # Prepend hashed nodes with a byte string to prevent second preimage
    # attack.
    #
    # See: https://tools.ietf.org/html/rfc6962#section-2.1

    #: Byte string prepended to a leaf before being hashed.
    LEAF_SEED = b"\x00"
    #: Byte string prepended to a node before being hashed.
    NODE_SEED = b"\x01"

    def __init__(
        self,
        hash: ty.Union[str, HASH, ty.Type[HASH]],
        iterable: ty.Optional[ty.Iterable[bytes]] = None,
    ):
        """Constructor for :class:`none.hash.tree.Merkle`."""
        self._leaves = deque()

        # Generate hash object to reuse it when needed.
        # WARNING: Never update this hash object. Always use a copy.
        if isinstance(hash, str):
            self._hash = hashlib.new(hash)
        else:
            try:
                self._hash = hash()
            except TypeError:
                self._hash = hash

        if iterable is not None:
            self.extend(iterable)

    def __iter__(self) -> ty.Iterator[bytes]:
        """Return an iterator over the digest of the data passed to the tree's
        leaf. Theses are bytes objects of size
        :meth:`~none.hash.tree.Merkle.digest_size`.


        :returns: An iterator over the leaf hash bytes.
        :rtype: ~typing.Iterator[bytes]

        """
        return iter(self._leaves)

    def __len__(self) -> int:
        """Get the number of leaves stored in the hash tree.


        :returns: Number of leaves stored in the hash tree.
        :rtype: int

        """
        return len(self._leaves)

    def __delitem__(self, i: int) -> None:
        """Remove a leaf from the tree.


        :param i: Index of the leaf to be removed.
        :type i: int


        :raises IndexError: When given index is out of range.

        """
        del self._leaves[i]

    def __getitem__(self, i: int) -> bytes:
        """Get the digest of the data passed to the tree's leaf at given index.
        This is a bytes object of size
        :meth:`~none.hash.tree.Merkle.digest_size`.


        :param i: Index of the requested leaf digest.
        :type i: int


        :returns: The leaf hash bytes.
        :rtype: bytes


        :raises IndexError: When given index is out of range.

        """
        return self._leaves[i]

    def __setitem__(self, i: int, data: bytes):
        """Set a leaf in the tree.


        :param i: Index at which the leaf must be set.
        :type i: int

        :param data: The actual leaf data to be hashed.
        :type data: bytes


        :raises IndexError: When given index is out of range.

        :raises TypeError: When given data does not support the buffer protocol.

        """
        self._leaves[i] = self._digest_leaf(data)

    @property
    def block_size(self) -> int:
        """The internal block size of the hash algorithm in bytes."""
        return self._hash.block_size

    @property
    def digest_size(self) -> int:
        """The size of the resulting hash in bytes."""
        return self._hash.digest_size

    @property
    def name(self) -> int:
        """The canonical name of this hash, always lowercase."""
        return self._hash.name

    def _digest_leaf(self, data: bytes) -> bytes:
        """Digest given data using the tree's hash object.


        :param data: The data to be digested.
        :type data: bytes


        :returns: A bytes digest of the data of size
                  :meth:`~none.hash.tree.Merkle.digest_size`.
        :rtype: bytes


        :raises TypeError: When given data does not support the buffer protocol.

        """
        hash = self._hash.copy()
        hash.update(self.LEAF_SEED)
        hash.update(data)

        return hash.digest()

    def copy(self) -> "Merkle":
        """Return a copy (“clone”) of the hash tree object. This can be used to
        efficiently compute the digests of data sharing a common initial
        leaves.


        :returns: A copy of the hash tree object.
        :rtype: ~none.hash.tree.Merkle

        """
        tree = Merkle(hash=self._hash.copy())
        tree._leaves = self._leaves.copy()
        return tree

    def digest(self, i: ty.Optional[int] = None) -> bytes:
        """Return the digest of the data passed to the
        :meth:`~none.hash.tree.Merkle.update` method so far. This is a bytes
        object of size :meth:`~none.hash.tree.Merkle.digest_size` which may
        contain bytes in the whole range from 0 to 255.


        :param i: When provided, return the digest of the data for the leaf at
                  this index.
        :type i: ~typing.Optional[int]


        :returns: A bytes digest of the data of size
                  :meth:`~none.hash.tree.Merkle.digest_size` which may contain
                  bytes in the whole range from 0 to 255.
        :rtype: bytes


        :raises IndexError: When given index is out of range.

        """
        if i is not None:
            return self[i]

        stack = self._leaves.copy()
        while len(stack) > 1:
            nodes = deque()  # Data structure to keep intermediate nodes.
            # Take leaves by groups of 2.
            for left, right in zip_longest(*([iter(stack)] * 2)):
                hash = self._hash.copy()
                hash.update(self.NODE_SEED)
                hash.update(left)
                if right is not None:
                    hash.update(right)

                nodes.append(hash.digest())
            # end for
            stack = nodes.copy()
        # end while

        try:
            return stack.pop()
        except IndexError:
            # If the stack is empty, we return the digest of the base hash.
            return self._hash.digest()

    def hexdigest(self, i: ty.Optional[int] = None) -> str:
        """Like :meth:`~none.hash.tree.Merkle.digest` except the digest is
        returned as a string object of double length, containing only
        hexadecimal digits.

        This may be used to exchange the value safely in email or other
        non-binary environments.


        :param i: When provided, return the digest of the data for the leaf at
                  this index.
        :type i: ~typing.Optional[int]


        :returns: A hexadecimal string digest of the data.
        :rtype: str


        :raises IndexError: When given index is out of range.

        """
        return self.digest(i).hex()

    def update(self, data: bytes) -> None:
        """Update the hash tree object with the bytes-like object.


        :param data: Leaf data to be added to the tree.
        :type data: bytes


        :raises TypeError: When given data does not support the buffer protocol.

        """
        return self.append(data)

    def clear(self) -> None:
        """Remove all leaves from the tree."""
        self._leaves.clear()

    def append(self, data) -> None:
        """Add a new leaf to the right side of the tree.


        :param data: Leaf data to be added to the tree.
        :type data: bytes


        :raises TypeError: When given data does not support the buffer protocol.

        """
        self._leaves.append(self._digest_leaf(data))

    def extend(self, iterable: ty.Iterable[bytes]) -> None:
        """Extend the right side of the tree by appending elements from the
        given iterable.


        :param iterable: An iterable with the data to be added to the tree.
        :type iterable: ~typing.Iterable[bytes]


        :raises TypeError: When given iterable does not contain data supporting
                           the buffer protocol.

        """
        self._leaves.extend(map(self._digest_leaf, iterable))

    def insert(self, i: int, data: bytes) -> None:
        """Insert a new leaf at the given index.


        :param i: Index at which the leaf must be inserted.
        :type i: int

        :param data: Leaf data to be inserted into the tree.
        :type data: bytes


        :raises TypeError: When given data does not support the buffer protocol.

        """
        self._leaves.insert(i, self._digest_leaf(data))

    def pop(self, i: ty.Optional[int] = None) -> bytes:
        """Remove and return an element from the right side of the tree.


        :param i: Index of the leaf to be removed.
        :type i: ~typing.Optional[int]


        :returns: A bytes digest of the data for the the removed leaf.
        :rtype: bytes


        :raises IndexError: When no elements are present into the tree.

        """
        if i is None:
            return self._leaves.pop()
        else:
            item = self[i]
            del self[i]

            return item
