# none/text/case.py
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
"""String capitalization facilities."""
import re


# ((0|a)_A_)|((0)_a_)|((0|A)_Aa_)
#: Regular expression to catch a camel cased string.
_CAMEL_TO_SNAKE_RE = re.compile(
    r"(((?<=[0-9a-z])[A-Z])|((?<=[0-9])[a-z])|((?<=[0-9A-Z])[A-Z][a-z]))",
)


def camel2kebab(string: str) -> str:
    """Convert a ``CamelCased`` string to a ``kebab-cased`` one.


    :param string: String to be converted.
    :type string: str


    :returns: The given string converted to kebab case.
    :rtype: str

    """
    return snake2kebab(camel2snake(string))


def camel2snake(string: str) -> str:
    """Convert a ``CamelCased`` string to a ``snake_cased`` one.


    :param string: String to be converted.
    :type string: str


    :returns: The given string converted to snake case.
    :rtype: str

    """
    return _CAMEL_TO_SNAKE_RE.sub(r"_\1", string).lower().strip("_")


def kebab2camel(string: str, capitalize: bool = True) -> str:
    """Convert a ``kebab-cased`` string to a ``CamelCased`` one.


    :param string: String to be converted.
    :type string: str

    :param capitalize: Whether to capitalize the first word of the returned
                       string. When set to ``True`` the string is returned
                       as ``CamelCase`` otherwise when set to ``False``, the
                       string is returned as ``camelCase``.
    :type capitalize: bool


    :returns: The given string converted to snake case.
    :rtype: str

    """
    return snake2camel(kebab2snake(string), capitalize=capitalize)


def kebab2snake(string: str) -> str:
    """Convert a ``kebab-cased`` string to a ``snake_cased`` one.


    :param string: String to be converted.
    :type string: str


    :returns: The given string converted to snake case.
    :rtype: str

    """
    return string.replace("-", "_")


def snake2camel(string: str, capitalize: bool = True) -> str:
    """Convert a ``snake_cased`` string to a ``CamelCased`` one.


    :param string: String to be converted.
    :type string: str

    :param capitalize: Whether to capitalize the first word of the returned
                       string. When set to ``True`` the string is returned
                       as ``CamelCase`` otherwise when set to ``False``, the
                       string is returned as ``camelCase``.
    :type capitalize: bool


    :returns: The given string converted to camel case.
    :rtype: str

    """
    head, *tail = string.lower().split("_")
    return (head.capitalize() if capitalize else head) + "".join(
        map(str.capitalize, tail)
    )


def snake2kebab(string: str) -> str:
    """Convert a ``snake_cased`` string to a ``kebab-cased`` one.


    :param string: String to be converted.
    :type string: str


    :returns: The given string converted to snake case.
    :rtype: str

    """
    return string.replace("_", "-")
