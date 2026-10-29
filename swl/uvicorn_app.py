## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2024-2025 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

from uvicorn.config import Config
from uvicorn.server import Server

from .shutdown import Shutdown

import logging

logger = logging.getLogger(__name__)

__all__ = ["uvicorn_main"]


async def uvicorn_main(host, port, create_app, **kwargs):
    deproxy_ips = kwargs.get("deproxy_ips", [])

    logger.debug(
        f"uvicorn_main called with host={host}, port={port}, "
        f"deproxy_ips={deproxy_ips}, kwargs={kwargs}"
    )
    config = Config(
        await create_app(shutdown=Shutdown(), host=host, port=port, **kwargs),
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips=deproxy_ips or [],
    )

    server = Server(config)
    await server.serve()
