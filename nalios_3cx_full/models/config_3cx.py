# -*- coding: utf-8 -*-

from odoo import models, fields
from markupsafe import Markup
import uuid
import base64


class Config3CX(models.TransientModel):
    _name = 'config.3cx'

    def _get_db_token(self):
        api_key = self.env['ir.config_parameter'].get_param('3cx.api.token', False)
        if not api_key:
            api_key = uuid.uuid4()
            self.env['ir.config_parameter'].set_param('3cx.api.token', api_key)
        return api_key

    configuration = fields.Binary()
    filename = fields.Char(default='Odoo_3CX_Template_Config.xml')
    db_url = fields.Char(default=lambda self: self.env['ir.config_parameter'].get_param('web.base.url'))
    db_token = fields.Char(default=_get_db_token)

    def generate_configuration(self):
        api_key = self._get_db_token()
        if self.db_token != api_key:
            api_key = self.db_token
            self.env['ir.config_parameter'].set_param('3cx.api.token', api_key)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url = base_url.rstrip('/') + '/'
        config_template = Markup('<?xml version="1.0"?>' + "\n")
        config_template += self.env['ir.qweb']._render('nalios_3cx_full.3cx_template', {'base_url': base_url, 'api_key': api_key})
        self.configuration = base64.encodebytes(config_template.encode('utf-8'))
        return {
            'type': 'ir.actions.act_window',
            'name': '3CX Configuration',
            'view_mode': 'form',
            'res_model': 'config.3cx',
            'res_id': self.id,
            'target': 'new',
        }
