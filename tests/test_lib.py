# tests/test_lib.py
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
import hashlib


def test_data_checksum(lib_data_metadata, lib_data):
    """Make sure that the content of our test data did not change."""
    name, fp = lib_data
    for h_name, h_value in lib_data_metadata["files"][name]["checksum"].items():
        hash = hashlib.new(h_name)
        hash.update(fp.read())

        assert f"${hash.name}${hash.hexdigest()}" == h_value
