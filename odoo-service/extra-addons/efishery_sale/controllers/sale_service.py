# -*- coding: utf-8 -*-
import logging
import datetime

from . import handler
from .query_lib import order_query
from .handler import JsonControllerMixin

from odoo import http
from odoo.http import request as rq
from odoo.tools.config import config


logger = logging.getLogger(__name__)


class SaleService(http.Controller):
    JsonControllerMixin.patch_for_json("/order")

    @http.route(
        route=['/order'],
        methods=['POST'],
        auth='public',
        csrf=False
    )
    def action_create_order(self, **kw):
        """
        This service calling from Interceptor
        to create sale order document
        """

        access_token = handler.get_config()
        auth = handler.parse_header()
        body = handler.parse_body()

        if auth == access_token:
            sale_obj = rq.env['sale.order'].sudo()

            invalid = self.validation(body)   
            if invalid:
                return handler.response(code=400, success=False, data=invalid)

            exist = sale_obj.search([
                ('origin', '=', body.get('name'))
            ], limit=1)

            if exist:
                return handler.response(code=409, success=False, data={'name': 'Already exists'})
   
            order_line = [(0, 0, item) for item in body.get('order_line')]
            vals = {
                'origin' : body.get('name'),
                'partner_id' : body.get('partner_id'),
                'date_order' : body.get('date_order'),
                'company_id' : body.get('company_id'),
                'order_line' : order_line
            }

            try:
                sale_obj.create(vals)
                return handler.response(code=200, success=True, message='Success')
            except Exception as e:
                logger.error("Failed to generate order : %s", e)
                return handler.response(code=500, success=False, message='Internal Server Error')
        else:
            return handler.response(code=401, success=False, message='Token Not Found')

    @http.route(
        route=['/order/<int:order_id>'],
        methods=['GET'],
        auth='public',
        csrf=False
    )
    def action_read_order(self, order_id, **kw):
        """
        This service calling from Interceptor
        to get sale order document
        """

        access_token = handler.get_config()
        auth = handler.parse_header()

        if auth == access_token:
            sale_obj = rq.env['sale.order'].sudo()

            try:
                exist = sale_obj.search([('id', '=', order_id)])

                if exist:
                    raw = order_query(rq.cr, order_id)
                    return handler.response(code=200, success=True, message='Data found', data=raw)
                else:
                    return handler.response(code=400, success=False, message='Order id not found')
            except Exception as e:
                logger.error("Failed to search order : %s", e)
                return handler.response(code=500, success=False, message='Internal Server Error')
        else:
            return handler.response(code=401, success=False, message='Token Not Found')

    @http.route(
        route=['/order/<int:order_id>'],
        methods=['PUT'],
        auth='public',
        csrf=False
    )
    def action_update_order(self, order_id, **kw):
        """
        This service calling from Interceptor
        to update sale order document
        """

        access_token = handler.get_config()
        auth = handler.parse_header()
        body = handler.parse_body()

        if auth == access_token:
            sale_obj = rq.env['sale.order'].sudo()

            try:
                exist = sale_obj.search([('id', '=', order_id)])
                if exist:
                    
                    invalid = self.validation(body)   
                    if invalid:
                        return handler.response(code=400, success=False, data=invalid)

                    exist.write({'order_line': [(5, 0, 0)]})
                    order_line = [(0, 0, item) for item in body.get('order_line')]
                    vals = {
                        'origin' : body.get('name'),
                        'partner_id' : body.get('partner_id'),
                        'date_order' : body.get('date_order'),
                        'company_id' : body.get('company_id'),
                        'order_line' : order_line
                    }
                    exist.write(vals)

                    return handler.response(code=200, success=True, message='Success')
                else:
                    return handler.response(code=400, success=False, message='Order id not found')
            except Exception as e:
                logger.error("Failed to update order : %s", e)
                return handler.response(code=500, success=False, message='Internal Server Error')
        else:
            return handler.response(code=401, success=False, message='Token Not Found')

    def validation(self, data):
        res = {}
        company_obj = rq.env['res.company'].sudo()
        partner_obj = rq.env['res.partner'].sudo()

         # name validation
        if ('name' not in data):
            res["name"] = "Required"
        elif not isinstance(data.get("name"), str):
            res["name"] = "Is not string"

        # date order validation        
        if data.get('date_order'):
            try:
                valid_format = "%Y-%m-%d %H:%M:%S"
                datetime.datetime.strptime(data.get('date_order'), valid_format)
            except:
                res["date_order"] = "Invalid format date"

        # company validation
        if ('company_id' not in data):
            res["company_id"] = "Required"
        elif not isinstance(data.get("company_id"), int):
            res["company_id"] = "Is not integer"
        else:
            company_id = company_obj.search([('id', '=', data.get("company_id"))])
            if not company_id:
               res["company_id"] = "Not found"

        # partner validation
        if ('partner_id' not in data):
            res["partner_id"] = "Required" 
        elif not isinstance(data.get("partner_id"), int):
            res["partner_id"] = "Is not integer"
        else:
            partner_id = partner_obj.search([('id', '=', data.get("partner_id"))])
            if not partner_id:
               res["partner_id"] = "Not found"
        
        # order line validation
        if data.get("order_line") and not isinstance(data.get("order_line"), list):
            res["partner_id"] = "Is not array"

        return res
