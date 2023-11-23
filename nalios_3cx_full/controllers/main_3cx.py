# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request, Response
import base64
import json
import re
import logging
import phonenumbers

_logger = logging.getLogger(__name__)


class Main3CX(http.Controller):
    def _is_3cx_authenticated(self):
        """Checking Authorization header for 3CX Token.
        It's suffixed with :X in 3CX configuration."""
        header = request.httprequest.headers.get('Authorization', False)
        if not header:
            return False
        header = header.replace('Basic ', '').strip()
        decoded = base64.b64decode(header)
        decoded = decoded.decode("utf-8").replace(':X', '')
        stored_api_token = request.env['ir.config_parameter'].sudo().get_param('3cx.api.token')
        if stored_api_token != decoded:
            return False
        return True

    def _bad_request(self):
        _logger.info('Bad request !')
        return Response(json.dumps({'error': 'Bad Request'}), status=400)

    def _unauthorized(self):
        _logger.info('Unauthorized request !')
        return Response(json.dumps({'error': 'Unauthorized'}), status=401)

    def _success_with_data(self, data={}):
        return Response(json.dumps(data), status=200)

    def _load_json_data(self):
        return json.loads(request.httprequest.data)

    def _sanitize_number(self, number):
        """We don't know the country code of the person. So to match any number we remove leading + and 0.
            e.g.: 
            +32477444444
            0032477444444
            or
            +15147577777
            0015147577777
            It's configurable (and recommended) to do 'exact matching' in 3CX (view demo video on store page)."""
        if number:
            if str(number).startswith('+'):
                number = phonenumbers.parse(number)
                return number.national_number
            if str(number).startswith('00'):
                number = '+' + str(number)[2:]
                number = phonenumbers.parse(number)
                return number.national_number
            return str(number).lstrip('0')
        return ''

    def _partner_data_json(self, partner):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url').rstrip('/')
        return {
            'id': partner.id,
            'name': partner.name,
            'company': partner.parent_id and partner.parent_id.name or 'N/A',
            'email': partner.email,
            'phone': partner.phone,
            'phone_1': partner.phone_1,
            'mobile': partner.mobile,
            'mobile_1': partner.mobile_1,
            'show_url': base_url + '/web?#view_type=form&id=%s&model=res.partner' % (partner.id,)
        }

    def _get_livechat_data(self, data):
        msg = "Subject: %s<br/>" % data.get('subject', '')
        msg += "Date: %s<br/>" % data.get('date', '')
        msg += "Duration: %s<br/>" % data.get('duration', '')
        msg += "Agent Name: %s<br/>" % data.get('agentname', '')
        msg += "Agent Phone: %s<br/>" % data.get('agent', '')        
        msg += "Messages: <br/>%s" % data.get('messages', '').replace('\n', '<br/>')
        return msg

    def _get_message_data(self, data):
        msg = "Subject: %s<br/>" % data.get('subject', '')
        msg += "Date: %s<br/>" % data.get('date')
        msg += "Call Type: %s<br/>" % data.get('type', '')
        msg += "Entity: %s<br/>" % data.get('entitytype', '')
        msg += "Agent Name: %s<br/>" % data.get('agentname', '')
        msg += "Agent Phone: %s<br/>" % data.get('agent', '')
        msg += "Details: %s" % data.get(data.get('type', 'no').lower(), '')
        return msg

    @http.route('/3cx/search/email/<string:email>', methods=["GET"], csrf=False, type="http", auth="public")
    def search_3cx_email(self, email):
        """Search an Odoo partner with the given email from 3CX"""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        _logger.info('3CX Search Email called with email %s' % email)
        if not email:
            return self._bad_request()
        if not (partner := request.env['res.partner'].sudo().search([('email', '=', email)])):
            partner = request.env['res.partner'].sudo().create({
                'name': 'New from email: ' + email,
                'email': email,
            })
        return self._success_with_data(self._partner_data_json(partner))

    @http.route('/3cx/search/number/<string:number>/<string:ttype>', methods=["GET"], csrf=False, type="http", auth="public")
    def search_3cx_number(self, number, ttype):
        """Search an Odoo partner with the given number from 3CX.
            The ttype is not used anymore, keeping for compatibility with 3CX Template Generator"""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        if not number:
            return self._bad_request()
        sanitized_number = self._sanitize_number(number)
        if not (partner := request.env['res.partner'].sudo().search(['|', '|', '|', ('mobile_format', 'ilike', str(sanitized_number)), ('mobile_1_format', 'ilike', str(sanitized_number)), ('phone_format', 'ilike', str(sanitized_number)), ('phone_1_format', 'ilike', str(sanitized_number))])):
            partner = request.env['res.partner'].sudo().create({
                'name': 'New contact from number : ' + number,
                'phone': number
            })
        return self._success_with_data(self._partner_data_json(partner))

    @http.route('/3cx/call/log', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_log_call(self):
        """Call log received from 3CX when call is finished."""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        data = self._load_json_data()
        _logger.info('3CX Call Log called with data %s' % data)
        if not data:
            return self._bad_request()
        number = data.get('phone', False)
        if not number:
            return self._bad_request()
        number = self._sanitize_number(number)
        if not (partner := request.env['res.partner'].sudo().search(['|', '|', '|', ('mobile_format', 'ilike', str(number)), ('mobile_1_format', 'ilike', str(number)), ('phone_format', 'ilike', str(number)), ('phone_1_format', 'ilike', str(number))])):
            _logger.info('No partner found for number %s' % number)
            return self._bad_request()
        for p in partner:
            p.message_post(body=self._get_message_data(data))
        return self._success_with_data()

    @http.route('/3cx/chat/create', methods=["POST"], csrf=False, type="json", auth="public")
    def _3cx_create_chat(self):
        """Chat log received from 3CX when a Chat is ticked as 'Dealt With'"""
        if not self._is_3cx_authenticated():
            return self._unauthorized()
        data = self._load_json_data()
        _logger.info('3CX Chat Create called with data %s' % data)
        if not data:
            return self._bad_request()
        email = data.get('email', False)
        if not email:
            return self._bad_request()
        if not (partner := request.env['res.partner'].sudo().search([('email', '=', email)])):
            partner = request.env['res.partner'].sudo().create({
                'name': data.get('name', 'New from Livechat Email : %s' % email),
                'email': email,
                'mobile': data.get('number', ''),
            })
        livechat_body = self._get_livechat_data(data)
        for p in partner:
            p.message_post(body=livechat_body)
        return self._success_with_data()
