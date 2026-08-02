import requests
from requests import Response

import inspect
import logging


_logger = logging.getLogger(__name__)

def make_request(method: str, url: str, print_err=False, custom_log_msg=None, **kwargs) -> Response | None:
    """
    A wrapper function to make http requests with centralized exception handling.
    Args:
        method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
        url (str): The URL to send the request to.
        **kwargs: Additional keyword arguments to pass to the requests method
                (e.g., params, data, json, headers, timeout, auth).

    Returns:
        requests.Response: The response object from the HTTP request.

    Raises:
        ValueError: If an unsupported HTTP method is provided.
    """
    if not url.startswith('http'):
        url = 'https://' + url
    caller_func = inspect.currentframe().f_back.f_code.co_name
    METHODS = {
        "GET": requests.get,
        "POST": requests.post,
        "PUT": requests.put,
        "DELETE": requests.delete,
        "PATCH": requests.patch,
        "HEAD": requests.head,
        "OPTIONS": requests.options,
    }
    try:
        request = METHODS.get(method.upper())
        if request is None:
            raise ValueError(f"Unsupported HTTP method: {method}")
        response = request(url, **kwargs)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        if custom_log_msg:
            _logger.info(f"{caller_func} {response.status_code} {custom_log_msg}")
        else:
            _logger.info(f"{caller_func} {response.status_code} {method} {url}")
    except requests.exceptions.RequestException as err:
        _logger.error(f"{caller_func} {err}")
        response = getattr(err, "response", None)
        if print_err:
            print(f"{type(err).__name__}: {err}")
    return response

def is_url_available(url):
    """ Check if URL is available. """
    response = make_request('HEAD', url, allow_redirects=True, verify=False)
    if response and response.status_code // 100 == 2:
        return response.url.rstrip('/')
    else:
        return False