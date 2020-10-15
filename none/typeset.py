# none/typeset.py
# ===============
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

from collections.abc import Callable


#: A callable type.
C = ty.TypeVar("C", bound=Callable)
#: Any number.
N = ty.TypeVar("N", float, int)
#: Generic return type.
R = ty.TypeVar("R")
#: Generic type.
T = ty.TypeVar("T")

# FIXME: Allow specification of the parameters and return type.
#: An asynchronous callable.
AsyncCallable = ty.Callable[..., ty.Awaitable[R]]

#: Sentinel object to represent missing values.
missing = object()
