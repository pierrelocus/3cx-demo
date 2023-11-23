# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re


class Partner(models.Model):
    _inherit = 'res.partner'

    mobile_1 = fields.Char(unaccent=False, string="Mobile 1")
    phone_1 = fields.Char(unaccent=False, string="Phone 1")
    mobile_format = fields.Char(compute='_get_formatted_numbers', store=True)
    mobile_1_format = fields.Char(compute='_get_formatted_numbers', store=True)
    phone_format = fields.Char(compute='_get_formatted_numbers', store=True)
    phone_1_format = fields.Char(compute='_get_formatted_numbers', store=True)

    @api.depends('phone', 'mobile', 'phone_1', 'mobile_1')
    def _get_formatted_numbers(self):
        for partner in self:
            if partner.mobile:
                partner.mobile_format = re.sub('[^0-9]+', '', partner.mobile)
            else:
                partner.mobile_format = ''
            if partner.mobile_1:
                partner.mobile_1_format = re.sub('[^0-9]+', '', partner.mobile_1)
            else:
                partner.mobile_1_format = ''
            if partner.phone:
                partner.phone_format = re.sub('[^0-9]+', '', partner.phone)
            else:
                partner.phone_format = ''
            if partner.phone_1:
                partner.phone_1_format = re.sub('[^0-9]+', '', partner.phone_1)
            else:
                partner.phone_1_format = ''
