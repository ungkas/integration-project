# -*- coding: utf-8 -*-
import json
import logging
import requests

from odoo import models, fields, api

logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        # Publish to interceptor webhook
        res = super().create(vals)

        params_obj = self.env['ir.config_parameter'].sudo()
        key = params_obj.get_param('interceptor.webhook_token')
        url = params_obj.get_param('interceptor.webhook_url')   
        headers = {'Content-Type': 'application/json', 'Authorization': key}

        try:
            data = {
                "event" : "service.sales_order_created",
                "payload" : vals
            }
            requests.post(url, data=json.dumps(data), headers=headers, timeout=1.0)
        except Exception as e:
            logger.error("Failed to send notif : %s", e)

        return res

    def write(self, vals):
        # Publish to interceptor webhook
        res = super().write(vals)

        if vals.get('state'):
            params_obj = self.env['ir.config_parameter'].sudo()
            key = params_obj.get_param('interceptor.webhook_token')
            url = params_obj.get_param('interceptor.webhook_url')   
            headers = {'Content-Type': 'application/json', 'Authorization': key}

            try:
                data = {
                    "event" : "service.sales_order_updated",
                    "payload" : vals
                }
                requests.post(url, data=json.dumps(data), headers=headers, timeout=1.0)
            except Exception as e:
                logger.error("Failed to send notif : %s", e)

        return res
