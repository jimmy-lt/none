# none/url.py
# ===========
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
import socket
import typing as ty
import urllib.parse

import rfc3986

from rfc3986 import normalizers


#: List of campaign tracking query parameters.
URL_QUERY_SOCIAL_PARAM = (
    "ncid",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
)


def canonical_host(host: ty.Optional[str]) -> ty.Optional[str]:
    """Normalize a host name to its canonical form by translating unicode names
    to the Internationalizing Domain Names in Applications (IDNA) notation and
    by making sure it is lower cased.


    :param host: The host name to be normalized.
    :type host: ~typing.Optional[str]


    :returns: The normalized host name.
    :rtype: str

    """
    if host is not None:
        return str(host).encode("idna").decode("utf-8").strip(".").lower()


def canonical_path(path: ty.Optional[str]) -> str:
    """Normalize a URL path to it's canonical form by escaping URL unsafe
    characters using the URL encoding (``%XX``). A default path set to ``/`` is
    returned when none is provided.


    :param path: The path to be normalized.
    :type path: ~typing.Optional[str]


    :returns: The transformed path.
    :rtype: str

    """
    return urllib.parse.quote(urllib.parse.unquote(str(path or "/")), safe="-./_~")


def canonical_port(port: ty.Optional[int], scheme: str) -> ty.Optional[int]:
    """Normalize a port to its canonical form. If given port is the scheme's
    default port number, ``None`` is returned.


    :param port: The protocol port number to be normalized.
    :type port: ~typing.Optional[int]

    :param scheme: The protocol naming `scheme
                   <https://en.wikipedia.org/wiki/Uniform_Resource_Identifier#Generic_syntax>`_
                   with which the port number is associated.
    :type scheme: ~typing.Optional[str]


    :returns: The port number as is when it is not the default port for the
              provided scheme. ``None`` is returned when the port number is the
              default port for the scheme.
    :rtype: ~typing.Optional[int]

    """
    if port is None or not scheme:
        return None

    port = int(port)
    try:
        if port == socket.getservbyname(scheme.lower()):
            return None
    except OSError:
        return None

    return port


def canonical_query(query: ty.Optional[str], keep_utm: bool = True) -> ty.Optional[str]:
    """Normalize an URL query string to its canonical form by applying the
    following transformations:

    - Sort query keys alphanumerically.
    - Remove duplicate query parameters.
    - Remove campaign tracking query parameters (when requested).

    If the query string is empty, ``None`` is returned.


    :param query: The query string to be normalized.
    :type query: ~typing.Optional[str]

    :param keep_utm: Whether or not to keep campaign tracking query parameters.
    :type keep_utm: bool


    :returns: The transformed query string or ``None`` if it's empty.
    :rtype: ~typing.Optional[str]

    """
    buffer = set()
    buf_add = buffer.add

    for k, v in urllib.parse.parse_qsl(query):
        if k in URL_QUERY_SOCIAL_PARAM and not keep_utm:
            continue
        buf_add(urllib.parse.quote_plus(str(k)) + "=" + urllib.parse.quote_plus(str(v)))

    if buffer:
        return "&".join(sorted(buffer))


def normalize(url: str, keep_utm: bool = True) -> str:
    """Normalize the provided URL.


    :param url: The URL to be normalized.
    :type url: str

    :param keep_utm: Whether or not to keep campaign tracking query parameters.
    :type keep_utm: bool


    :returns: A normalized URL.
    :rtype: str

    """
    # We have to clean the host name first otherwise ``authority_info()`` bellow
    # will complain.
    scheme, netloc, *remaining = split(url)
    url = rfc3986.uri_reference(
        urllib.parse.urlunsplit((scheme, canonical_host(netloc), *remaining))
    )

    # Make sure protocol's default port number is stripped away.
    # TODO: Make sure to properly parse user credentials information.
    auth = url.authority_info()
    auth["port"] = canonical_port(auth["port"], url.scheme)

    return url.copy_with(
        scheme=normalizers.normalize_scheme(url.scheme or ""),
        authority=normalizers.normalize_authority(
            (auth["userinfo"], auth["host"], auth["port"])
        ),
        path=normalizers.normalize_path(canonical_path(url.path) or ""),
        query=normalizers.normalize_query(
            canonical_query(url.query, keep_utm=keep_utm)
        ),
        fragment=normalizers.normalize_fragment(url.fragment or None),
    ).unsplit()


def split(url: str) -> urllib.parse.SplitResult:
    """Split given URL into its several components.


    :param url: The URL to be exploded.
    :type url: str


    :returns: A parsed list of the URL's components.
    :rtype: ~urllib.parse.SplitResult

    """
    return urllib.parse.urlsplit(url)
