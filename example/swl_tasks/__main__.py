## begin license ##
#
# "SWL"(Seecr Web Lib) makes developing webbased apps easier
#
# Copyright (C) 2026 Seecr (Seek You Too B.V.) https://seecr.nl
#
# This file is part of "Seecr Web Lib"
#
# "Seecr Web Lib" is licensed under the MIT License; see the LICENSE file.
# SPDX-License-Identifier: MIT
#
## end license ##

"""Run the example: python -m swl_tasks [--port 8000] [--data-dir ./swl-tasks-data] [--framework swl]"""

import argparse

import uvicorn

from .app import DEMO_PASSWORD, DEMO_USER, create_app


def main():
    parser = argparse.ArgumentParser(description="SWL example: a task list")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--data-dir", default="swl-tasks-data", help="where tasks and users are stored")
    parser.add_argument("--framework", default="swl", choices=["swl", "bootstrap", "tabler", "bulma"],
                        help="the CSS framework (default: %(default)s, SWL's own styles)")
    args = parser.parse_args()

    print(f"SWL Tasks on http://{args.host}:{args.port}/ - log in as {DEMO_USER} / {DEMO_PASSWORD}")
    uvicorn.run(create_app(args.data_dir, framework=args.framework), host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
