# tests/test_url.py
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
"""Test cases for :mod:`none.url`."""
import typing as ty

from urllib.parse import SplitResult

import pytest

from rfc3986.builder import URIBuilder

import none


# fmt: off
#: List of internationalized domain names with their expected IDNA encoding.
# Source: https://en.wikipedia.org/wiki/IDN_Test_TLDs
DOMAIN_IDNA_EXPECTED = (
    ("παράδειγμα.δοκιμή",     "xn--hxajbheg2az3al.xn--jxalpdlp"),
    ("пример.испытание",      "xn--e1afmkfd.xn--80akhbyknj4f"),
    ("בײַשפּיל.טעסט",           "xn--fdbk5d8ap9b8a8d.xn--deba0ad"),
    ("مثال.آزمایشی",          "xn--mgbh0fb.xn--hgbk6aj7f53bba"),
    ("مثال.إختبار",           "xn--mgbh0fb.xn--kgbechtv"),
    ("उदाहरण.परीक्षा",       "xn--p1b6ci4b4b3a.xn--11b5bs3a9aj6g"),
    ("உதாரணம்.பரிட்சை", "xn--zkc6cc5bi7f6e.xn--hlcj6aya9esc7a"),
    ("例え.テスト",           "xn--r8jz45g.xn--zckzah"),
    ("例子.測試",             "xn--fsqu00a.xn--g6w251d"),
    ("실례.테스트",           "xn--9n2bp8q.xn--9t4b11yi5a"),
)

#: Set of expected values when a path is normalized.
PATH_NORMALIZE_EXPECTED = (
    ("",                          "/"),
    ("/%",                        "/%25"),
    ("/%20%25",                   "/%20%25"),
    ("/%20/%",                    "/%20/%25"),
    ("/%21%22%23%ah%12%ff",       "/%21%22%23%25ah%12%EF%BF%BD"),
    ("/%7Eusername",              "/~username"),
    ("/%a",                       "/%25a"),
    ("/../foo/bar",               "/../foo/bar"),
    ("/./foo/bar",                "/./foo/bar"),
    ("/a/./b/../b/%63/%7Bfoo%7D", "/a/./b/../b/c/%7Bfoo%7D"),
    ("/a/b/c/./../../g",          "/a/b/c/./../../g"),
    ("/foo bar/biz%2abaz",        "/foo%20bar/biz%2Abaz"),
    ("/foo/bar",                  "/foo/bar"),
    ("/foo/bar/",                 "/foo/bar/"),
    ("/foo/bar/.",                "/foo/bar/."),
    ("/mid/content=5/../6",       "/mid/content%3D5/../6"),
    ("/~username",                "/~username"),
)

#: Set of expected values when a port is normalized against its scheme.
PORT_NORMALIZE_EXPECTED = (
    ("http",  80,   None),
    ("http",  8080, 8080),
    ("https", 443,  None),
    ("https", 8443, 8443),
)

#: Set of expected values when a query string with social parameters is
#: normalized.
QUERY_NORMALIZE_UTM_EXPECTED = (
    (
        "",
        None,
    ),
    (
        "a=1&ncid=1&a=1",
        "a=1",
    ),
    (
        "a=1&utm_campaign=my-campaign&b=&utm_source=my-source&c=3",
        "a=1&c=3",
    ),
    (
        "d=4&ncid=1&c=3&utm_campaign=my-campaign&b=2&utm_source=my-source&a=1&utm_medium=my-medium",
        "a=1&b=2&c=3&d=4",
    ),
    (
        "utm_campaign=my-campaign&utm_source=my-source",
        None,
    ),
    (
        "utm_medium=my-medium",
        None,
    ),
    (
        "utm-medium=my-medium",
        "utm-medium=my-medium",
    ),
    (
        "utm_media=my-media&utm_source=my-source&utm_medium=my-medium",
        "utm_media=my-media",
    ),
)

#: A test suites of the various parts of an URL along with their expected
#: normalized values.
URL_NORMALIZE_EXPECTED = {
    "scheme": [
        ("HTTP",                      "http"),
        ("hTtPs",                     "https"),
        ("https",                     "https"),
    ],
    "authority": [
        ("127.0.0.1",                 "127.0.0.1"),
        ("[::1]",                     "[::1]"),
        ("ExAmPlE.cOm",               "example.com"),
        ("example.com",               "example.com"),
        ("LOCALHOST",                 "localhost"),
        ("www.example.com.",          "www.example.com"),
        ("über.example.com",          "xn--ber-goa.example.com"),
    ],
    "path": [
        ("",                          "/"),
        ("/%",                        "/%25"),
        ("/%20%25",                   "/%20%25"),
        ("/%20/%",                    "/%2520/%25"),
        ("/%21%22%23%ah%12%ff",       "/%2521%2522%2523%25ah%2512%25ff"),
        ("/%7Eusername",              "/~username"),
        ("/%a",                       "/%25a"),
        ("/../foo/bar",               "/foo/bar"),
        ("/./foo/bar",                "/foo/bar"),
        ("/a/./b/../b/%63/%7Bfoo%7D", "/a/b/c/%7Bfoo%7D"),
        ("/a/b/c/./../../g",          "/a/g"),
        ("/foo bar/biz%2abaz",        "/foo%20bar/biz%2Abaz"),
        ("/foo/bar",                  "/foo/bar"),
        ("/foo/bar/",                 "/foo/bar/"),
        ("/foo/bar/.",                "/foo/bar/"),
        ("/mid/content=5/../6",       "/mid/6"),
        ("/~username",                "/~username"),
    ],
    "query": [
        ("",                          None),
        ("D=4&C=3&B=2&A=1",           "A=1&B=2&C=3&D=4"),
        ("a=1&a=1",                   "a=1"),
        ("a=1&b=&c=3",                "a=1&c=3"),
        ("d=4&c=3&b=2&a=1",           "a=1&b=2&c=3&d=4"),
        ("my param=val",              "my+param=val"),
        ("param=one value",           "param=one+value"),
        ("user=user%2aname",          "user=user%2Aname"),
        ("user=user*name",            "user=user%2Aname"),
        ("a=1&ncid=1&a=1",            "a=1&ncid=1"),
        ("utm_medium=my-medium",      "utm_medium=my-medium"),
        (
            "a=1&utm_campaign=my-campaign&b=&utm_source=my-source&c=3",
            "a=1&c=3&utm_campaign=my-campaign&utm_source=my-source",
        ),
        (
            "d=4&ncid=1&c=3&utm_campaign=my-campaign&b=2&utm_source=my-source&a=1&utm_medium=my-medium",
            "a=1&b=2&c=3&d=4&ncid=1&utm_campaign=my-campaign&utm_medium=my-medium&utm_source=my-source",
        ),
        (
            "utm_media=my-media&utm_source=my-source&utm_medium=my-medium",
            "utm_media=my-media&utm_medium=my-medium&utm_source=my-source",
        ),
    ],
    "fragment": [
        ("",                          None),
        ("a",                         "a"),
        ("A",                         "A"),
        ("my fragment",               "my%20fragment"),
        ("my%2afragment",             "my%2Afragment"),
        ("my-fragment",               "my-fragment"),
    ],
}

#: A set of normalized URL schemes.
URL_NORMALIZED_SCHEMES     = set(x[1] for x in URL_NORMALIZE_EXPECTED["scheme"])
#: A set of normalized URL fragments.
URL_NORMALIZED_FRAGMENTS   = set(x[1] for x in URL_NORMALIZE_EXPECTED["fragment"])
#: A set of normalized URL authorities.
URL_NORMALIZED_AUTHORITIES = set(x[1] for x in URL_NORMALIZE_EXPECTED["authority"])
#: A set of normalized URL paths.
URL_NORMALIZED_PATHS       = set(x[1] for x in URL_NORMALIZE_EXPECTED["path"])
#: A set of normalized URL queries.
URL_NORMALIZED_QUERIES     = set(x[1] for x in URL_NORMALIZE_EXPECTED["query"])
# fmt: on


def _gen_test_urls() -> ty.Generator[ty.Tuple[str, str], None, None]:
    """Generate test URLs along with their expected normalization."""
    for scheme, xpt_scheme in URL_NORMALIZE_EXPECTED["scheme"]:
        for auth, xpt_auth in URL_NORMALIZE_EXPECTED["authority"]:
            for path, xpt_path in URL_NORMALIZE_EXPECTED["path"]:
                for query, xpt_query in URL_NORMALIZE_EXPECTED["query"]:
                    for frag, xpt_frag in URL_NORMALIZE_EXPECTED["fragment"]:
                        url = (
                            URIBuilder(
                                scheme=scheme,
                                host=auth,
                                path=path,
                                query=query,
                                fragment=frag,
                            )
                            .finalize()
                            .unsplit()
                        )

                        expected = (
                            URIBuilder(
                                scheme=xpt_scheme,
                                host=xpt_auth,
                                path=xpt_path,
                                query=xpt_query,
                                fragment=xpt_frag,
                            )
                            .finalize()
                            .unsplit()
                        )

                        yield url, expected


def _gen_normalized_urls() -> ty.Generator[ty.Tuple[str, SplitResult], None, None]:
    """Generate normalized URLs along with their composing parts."""
    for scheme in URL_NORMALIZED_SCHEMES:
        for auth in URL_NORMALIZED_AUTHORITIES:
            for path in URL_NORMALIZED_PATHS:
                for query in URL_NORMALIZED_QUERIES:
                    for frag in URL_NORMALIZED_FRAGMENTS:
                        url = (
                            URIBuilder(
                                scheme=scheme,
                                host=auth,
                                path=path,
                                query=query,
                                fragment=frag,
                            )
                            .finalize()
                            .unsplit()
                        )

                        yield url, SplitResult(scheme, auth, path, query, frag)


@pytest.mark.parametrize("idna,expected", DOMAIN_IDNA_EXPECTED)
def test_canonical_host_expected_idna_normalization(idna: str, expected: str):
    """Test func:`none.url.canonical_host` for expected IDNA normalization."""
    assert none.url.canonical_host(idna) == expected


@pytest.mark.parametrize("auth,expected", URL_NORMALIZE_EXPECTED["authority"])
def test_canonical_host_expected(auth: str, expected: str):
    """Test :func:`none.url.canonical_host` for expected host normalization."""
    assert none.url.canonical_host(auth) == expected


@pytest.mark.parametrize("path,expected", PATH_NORMALIZE_EXPECTED)
def test_canonical_path_expected(path, expected):
    """Test :func:`none.url.canonical_path` for expected path normalization."""
    assert none.url.canonical_path(path) == expected


@pytest.mark.parametrize("scheme,port,expected", PORT_NORMALIZE_EXPECTED)
def test_canonical_port_expected(scheme: str, port: int, expected: ty.Optional[int]):
    """Test :func:`none.url.canonical_port` for expected port normalization."""
    assert none.url.canonical_port(port, scheme) == expected


@pytest.mark.parametrize("query,expected", URL_NORMALIZE_EXPECTED["query"])
def test_canonical_query_expected_with_utm(query: str, expected: str):
    """Test :func:`none.url.canonical_query` for expected query normalization
    while keeping UTM parameters.

    """
    assert none.url.canonical_query(query, keep_utm=True) == expected


@pytest.mark.parametrize("query,expected", QUERY_NORMALIZE_UTM_EXPECTED)
def test_canonical_query_expected_without_utm(query: str, expected: ty.Optional[str]):
    """Test :func:`none.url.canonical_query` for expected query normalization
    while removing UTM parameters.

    """
    assert none.url.canonical_query(query, keep_utm=False) == expected


@pytest.mark.parametrize("url,expected", _gen_test_urls())
def test_normalize_expected(url: str, expected: str):
    """Test :func:`none.url.normalize` for expected URL cases."""
    assert none.url.normalize(url) == expected


@pytest.mark.parametrize("url,them_parts", _gen_normalized_urls())
def test_split_expected(url: str, them_parts: SplitResult):
    """Test :func:`none.url.split` for expected results."""
    my_parts = none.url.split(url)
    assert my_parts.scheme == them_parts.scheme
    assert my_parts.netloc == them_parts.netloc
    assert my_parts.path == them_parts.path

    # Special cases where split returns an empty string instead of ``None``.
    them_query = "" if them_parts.query is None else them_parts.query
    them_fragment = "" if them_parts.fragment is None else them_parts.fragment

    assert my_parts.query == them_query
    assert my_parts.fragment == them_fragment
