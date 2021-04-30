# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import time
from functools import wraps
from typing import Any, Callable, Dict, Iterator, Sequence, Union

from contextlib2 import contextmanager
from flask import current_app, Response

from superset import is_feature_enabled
from superset.dashboards.commands.exceptions import DashboardAccessDeniedError
from superset.stats_logger import BaseStatsLogger
from superset.utils import core as utils
from superset.utils.dates import now_as_float


@contextmanager
def stats_timing(stats_key: str, stats_logger: BaseStatsLogger) -> Iterator[float]:
    """Provide a transactional scope around a series of operations."""
    start_ts = now_as_float()
    try:
        yield start_ts
    except Exception as ex:
        raise ex
    finally:
        stats_logger.timing(stats_key, now_as_float() - start_ts)


def arghash(args: Any, kwargs: Dict[str, Any]) -> int:
    """Simple argument hash with kwargs sorted."""
    sorted_args = tuple(
        x if hasattr(x, "__repr__") else x for x in [*args, *sorted(kwargs.items())]
    )
    return hash(sorted_args)


def debounce(duration: Union[float, int] = 0.1) -> Callable[..., Any]:
    """Ensure a function called with the same arguments executes only once
    per `duration` (default: 100ms).
    """

    def decorate(f: Callable[..., Any]) -> Callable[..., Any]:
        last: Dict[str, Any] = {"t": None, "input": None, "output": None}

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            now = time.time()
            updated_hash = arghash(args, kwargs)
            if (
                last["t"] is None
                or now - last["t"] >= duration
                or last["input"] != updated_hash
            ):
                result = f(*args, **kwargs)
                last["t"] = time.time()
                last["input"] = updated_hash
                last["output"] = result
                return result
            return last["output"]

        return wrapped

    return decorate


def on_security_exception(self: Any, ex: Exception) -> Response:
    return self.response(403, **{"message": utils.error_msg_from_exception(ex)})


# noinspection PyPackageRequirements
def check_dashboard_access(
    on_error: Callable[..., Any] = on_security_exception
) -> Callable[..., Any]:
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            from superset.models.dashboard import Dashboard

            dashboard = Dashboard.get(str(kwargs["dashboard_id_or_slug"]))
            if is_feature_enabled("DASHBOARD_RBAC"):
                try:
                    current_app.appbuilder.sm.raise_for_dashboard_access(dashboard)
                except DashboardAccessDeniedError as ex:
                    return on_error(self, ex)
                except Exception as exception:
                    raise exception

            return f(self, *args, dashboard=dashboard, **kwargs)

        return wrapper

    return decorator


def conditionally_expose(
    url: str = "/",
    methods: Sequence[str] = ("GET",),
    cond: Callable[[], bool] = lambda: True,
) -> Any:
    """
        Use this decorator to conditionally expose routes.
        If the callable `cond` arg is True, then the underlying
        handler will be invoked. Otherwise, the application will
        respond with a 404 Not Found.

        Example:

            @conditionally_expose("/route", cond=lambda: my_feature_is_enabled())

        :param url:
            Relative URL for the endpoint
        :param methods:
            Allowed HTTP methods. By default only GET is allowed.
        :param only_when:
            Test callable that returns a boolean and determines if
            the route should proceed or respond with a 404.
    """

    def wrap(f: Callable[..., Any]) -> Callable[..., Any]:
        def wrapped(self: Any, *args: Sequence[Any], **kwargs: Dict[Any, Any]) -> Any:
            if cond() is not True:
                message = (
                    "404 Not Found: The requested URL was not found on the server. "
                    "If you entered the URL manually please check your spelling and try again."
                )
                return self.response(404, message=message)
            return f(self, *args, **kwargs)

        urls = f._urls if hasattr(f, "_urls") else []  # type: ignore
        urls.append((url, methods))
        wrapped._urls = urls  # type: ignore

        return wrapped

    return wrap
