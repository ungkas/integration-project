import re
import json

from odoo import http
from odoo.http import (
    Response, 
    request
)


def parse_header():
    try:
        auth = request.httprequest.headers.get("Authorization")
        auth_prefix = auth.split(' ')[0]

        if auth_prefix == 'Bearer':
            return auth.split(' ')[1]
    except Exception:
        pass

def parse_body():
    return json.loads(request.httprequest.data.decode("utf-8"))

def get_config():
    return request.env['ir.config_parameter'].sudo().get_param('external.client_token')

def response(code=200, success=True, message='', data={}):
    headers = {"Content-Type": "application/json"}
    content = {"success": success}

    if message:
        content["message"] = message
    if data:
        content["data"] = data

    return Response(
        json.dumps(content),
        headers=headers,
        status=code
    )


class JsonControllerMixin(object):
    @staticmethod
    def patch_for_json(path_re):
        path_re = re.compile(path_re)
        orig_get_request = http.Root.get_request

        def get_request(self, httprequest):
            if path_re.match(httprequest.path):
                return http.HttpRequest(httprequest)
            return orig_get_request(self, httprequest)

        http.Root.get_request = get_request
