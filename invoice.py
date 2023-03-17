# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import base64
import requests
import socket

from logging import getLogger

from trytond.pool import PoolMeta
from trytond import backend
from trytond.config import config as config_
from trytond.modules.account_invoice_facturae import FACTURAE_SCHEMA_VERSION

PIMEFACTURA_PROD = config_.getboolean('pimefactura', 'production', default=False)
PIMEFACTURA_USER = config_.get('pimefactura', 'user', default=None)
PIMEFACTURA_PASSWORD = config_.get('pimefactura', 'password', default=None)
PIMEFACTURA_BASEURL = ('https://www.pimefactura.com/'
    if PIMEFACTURA_PROD else 'http://new.pimefactura.com/')

_logger = getLogger(__name__)

def basic_auth(username, password):
    token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def generate_facturae_pimec(cls, invoices, certificate=None,
            certificate_password=None):
        url = '%s/uploadinvoice' % PIMEFACTURA_BASEURL

        to_write = ([],)
        for invoice in invoices:
            if invoice.invoice_facturae:
                continue

            facturae_content = invoice.get_facturae()
            invoice._validate_facturae(facturae_content)

            if backend.name != 'sqlite':
                invoice_facturae = invoice._sign_facturae(
                    facturae_content, 'pimec', certificate, certificate_password)
            else:
                invoice_facturae = facturae_content

            xml = '''
                <UploadInvoiceRequest>
                    <invoicetype>facturae</invoicetype>
                    <invoicetypeversion>%(version)s</invoicetypeversion>
                    <invoiceb64>%(invoiceb64)s</invoiceb64>
                    <certificateid></certificateid>
                    <certificatepassword></certificatepassword>
                    <outchannelid></outchannelid>
                </UploadInvoiceRequest>
                ''' % {
                    'version': FACTURAE_SCHEMA_VERSION,
                    'invoiceb64': base64.b64encode(invoice_facturae),
                    # 'certificateid': '',
                    # 'certificatepassword': '',
                }

            headers = {
                'Content-Type': 'application/xml; charset=utf-8',
                "Authorization": basic_auth(PIMEFACTURA_USER, PIMEFACTURA_PASSWORD),
                }

            try:
                rqst = requests.post(url, data=bytes(xml.encode('utf-8')), headers=headers)
            except Exception:
                _logger.info('Error send Pimec factura-e: %s' % invoice.rec_name)
                continue

            try:
                if not rqst.status_code != 200:
                    _logger.info('Error send Pimec factura-e status code: %s' % rqst.status_code)
                # response = rqst.content
            except socket.timeout as err:
                _logger.info('Error send Pimec factura-e timeout: %s' % invoice.rec_name)
                _logger.error('%s' % str(err))
                continue
            except socket.error as err:
                _logger.info('Error send Pimec factura-e: %s' % invoice.rec_name)
                _logger.error('%s' % str(err))
                continue

            to_write.extend(([invoice], {
                'invoice_facturae': invoice_facturae,
                }))

        if to_write:
            cls.write(*to_write)


class GenerateFacturaeStart(metaclass=PoolMeta):
    __name__ = 'account.invoice.generate_facturae.start'

    @classmethod
    def __setup__(cls):
        super(GenerateFacturaeStart, cls).__setup__()
        cls.service.selection += [('pimec', 'Pimec')]
