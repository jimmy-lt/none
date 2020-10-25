# tests/hash/cdc/test_fastcdc.py
# ==============================
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
import typing as ty
import hashlib

import pytest
import pkg_resources

import none


#: The number of elements expected from a gear hash table.
GHASH_TABLE_N_ELEMENTS = 256
#: The maximum number of bits allowed in a gear integer.
GHASH_TABLE_INT_BITS = 64


@pytest.fixture
def meta() -> ty.Dict[str, ty.Any]:
    return json.load(
        pkg_resources.resource_stream("tests.lib", "hash/cdc/fastcdc.json")
    )


@pytest.fixture
def gear_seed(meta) -> int:
    return int(meta["gear"]["seed"], base=16)


@pytest.fixture
def gear_table(meta) -> ty.List[int]:
    return [int(x, base=16) for x in meta["gear"]["table"]]


def test_mkgear_table_length():
    """The gear table must contain 256 elements."""
    assert len(none.hash.cdc.fastcdc.mkgear()) == GHASH_TABLE_N_ELEMENTS


def test_mkgear_generate_64_integers():
    """Ensure the generated integers contains no more than 64 bits."""
    for i in none.hash.cdc.fastcdc.mkgear():
        assert i.bit_length() <= GHASH_TABLE_INT_BITS


def test_ghash_expected_result(gear_table, gear_seed):
    """Test the gear hash function for expected results."""
    our_h = 0
    them_h = 0
    for c in bytes(range(GHASH_TABLE_N_ELEMENTS)):
        our_h = ((our_h << 1) + gear_table[c]) & 0xFFFFFFFFFFFFFFFF
        them_h = none.hash.cdc.fastcdc.ghash(them_h, c, ghash_table=gear_table)

        assert them_h == our_h


def test_ghash_expected_result_with_seed(gear_table, gear_seed):
    """Test the gear hash function for expected results with seed."""
    ours = 0
    theirs = 0
    for c in bytes(range(GHASH_TABLE_N_ELEMENTS)):
        ours = ((ours << 1) + (gear_table[c] ^ gear_seed)) & 0xFFFFFFFFFFFFFFFF
        theirs = none.hash.cdc.fastcdc.ghash(
            theirs, c, ghash_table=gear_table, seed=gear_seed
        )

        assert theirs == ours


def test_find_expected_result(meta, lib_data, gear_table):
    """Make sure that cutting point of defined data files are what we expect."""
    idx = 0
    name, content = lib_data[0], lib_data[1].read()

    ours = [x[1] for x in meta["files"][name]["chunks"]]
    theirs = []
    while idx != len(content):
        idx += none.hash.cdc.fastcdc.find(content[idx:], ghash_table=gear_table)
        theirs.append(idx)

    assert theirs == ours


def test_find_expected_result_with_seed(meta, lib_data, gear_table, gear_seed):
    """Make sure that cutting point of defined data files are what we expect
    with and additional seed value.

    """
    idx = 0
    name, content = lib_data[0], lib_data[1].read()

    ours = [x[1] for x in meta["files"][name]["seeded_chunks"]]
    theirs = []
    while idx != len(content):
        idx += none.hash.cdc.fastcdc.find(
            content[idx:], ghash_table=gear_table, seed=gear_seed
        )
        theirs.append(idx)

    assert theirs == ours


def test_split_expected_result(meta, lib_data, gear_table):
    """Make sure that cutting point of defined data files are what we expect."""
    name, content = lib_data[0], lib_data[1].read()

    ours = [tuple(x) for x in meta["files"][name]["chunks"]]
    theirs = []
    for i, parts in enumerate(
        none.hash.cdc.fastcdc.split(content, ghash_table=gear_table)
    ):
        start, end, chunk = parts

        # Get the expected hash algorithm from our test data.
        h_name = ours[i][-1].split("$")[1]
        h = hashlib.new(h_name)
        h.update(chunk)

        theirs.append((start, end, f"${h_name}${h.hexdigest()}"))

    assert theirs == ours


def test_split_expected_result_with_seed(meta, lib_data, gear_table, gear_seed):
    """Make sure that cutting point of defined data files are what we expect
    with and additional seed value.

    """
    name, content = lib_data[0], lib_data[1].read()

    ours = [tuple(x) for x in meta["files"][name]["seeded_chunks"]]
    theirs = []
    for i, parts in enumerate(
        none.hash.cdc.fastcdc.split(content, ghash_table=gear_table, seed=gear_seed)
    ):
        start, end, chunk = parts

        # Get the expected hash algorithm from our test data.
        h_name = ours[i][-1].split("$")[1]
        h = hashlib.new(h_name)
        h.update(chunk)

        theirs.append((start, end, f"${h_name}${h.hexdigest()}"))

    assert theirs == ours


def test_fastcdc_aggregate_chunk_hashes(lib_data_metadata, lib_data, gear_table):
    """The aggregated hash of all chunks should match the hash of the file."""
    name, fp = lib_data
    for h_name, ours in lib_data_metadata["files"][name]["checksum"].items():
        h = hashlib.new(h_name)
        for _, _, chunk in none.hash.cdc.fastcdc.fastcdc(fp, ghash_table=gear_table):
            h.update(chunk)
        theirs = f"${h_name}${h.hexdigest()}"

        assert theirs == ours


def test_fastcdc_aggregate_chunk_hashes_with_seed(
    lib_data_metadata, lib_data, gear_table, gear_seed
):
    """The aggregated hash of all chunks should match the hash of the file with
    seed.

    """
    name, fp = lib_data
    for h_name, ours in lib_data_metadata["files"][name]["checksum"].items():
        h = hashlib.new(h_name)
        for _, _, chunk in none.hash.cdc.fastcdc.fastcdc(
            fp, ghash_table=gear_table, seed=gear_seed
        ):
            h.update(chunk)
        theirs = f"${h_name}${h.hexdigest()}"

        assert theirs == ours


def test_fastcdc_expected_result(meta, lib_data, gear_table):
    """Make sure that provided chunks of defined data files are what we
    expect.

    """
    name, fp = lib_data

    ours = [tuple(x) for x in meta["files"][name]["chunks"]]
    theirs = []
    for i, parts in enumerate(
        none.hash.cdc.fastcdc.fastcdc(fp, ghash_table=gear_table)
    ):
        start, end, chunk = parts

        # Get the expected hash algorithm from our test data.
        h_name = ours[i][-1].split("$")[1]
        h = hashlib.new(h_name)
        h.update(chunk)

        theirs.append((start, end, f"${h_name}${h.hexdigest()}"))

    assert theirs == ours


def test_fastcdc_expected_result_with_seed(meta, lib_data, gear_table, gear_seed):
    """Make sure that provided chunks of defined data files are what we
    expect with seed.

    """
    name, fp = lib_data

    ours = [tuple(x) for x in meta["files"][name]["seeded_chunks"]]
    theirs = []
    for i, parts in enumerate(
        none.hash.cdc.fastcdc.fastcdc(fp, ghash_table=gear_table, seed=gear_seed)
    ):
        start, end, chunk = parts

        # Get the expected hash algorithm from our test data.
        h_name = ours[i][-1].split("$")[1]
        h = hashlib.new(h_name)
        h.update(chunk)

        theirs.append((start, end, f"${h_name}${h.hexdigest()}"))

    assert theirs == ours
