# tests/conftest.py
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
import json
import typing as ty

import pytest
import pkg_resources


#: File name given to the file providing metadata about the test data files.
DATA_META_FNAME = "metadata.json"


@pytest.fixture
def lib_data_metadata():
    """Load the metadata about embedded test data files."""
    return json.load(
        pkg_resources.resource_stream("tests.lib", f"data/{DATA_META_FNAME}")
    )


@pytest.fixture(
    params=filter(
        lambda x: x != DATA_META_FNAME,
        pkg_resources.resource_listdir("tests.lib", "data"),
    )
)
def lib_data(request) -> ty.Tuple[str, ty.BinaryIO]:
    """Generate a stream of test data files names an file pointers."""
    name = f"data/{request.param}"
    return name, pkg_resources.resource_stream("tests.lib", name)
