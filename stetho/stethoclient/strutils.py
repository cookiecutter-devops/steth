# Copyright 2015 UnitedStack, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys


def safe_decode(text, incoming=None, errors="strict"):
    if not isinstance(text, (str, bytes)):
        raise TypeError("%s can't be decoded" % type(text))

    if isinstance(text, str):
        return text

    if not incoming:
        incoming = sys.stdin.encoding or sys.getdefaultencoding()

    try:
        return text.decode(incoming, errors)
    except UnicodeDecodeError:
        return text.decode("utf-8", errors)
