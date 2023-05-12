# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import base64
import requests
import socket

from logging import getLogger

from trytond.pool import PoolMeta
from trytond.config import config as config_
from trytond.modules.account_invoice_facturae import FACTURAE_SCHEMA_VERSION

PIMEFACTURA_PROD = config_.getboolean('pimefactura', 'production', default=False)
PIMEFACTURA_USER = config_.get('pimefactura', 'user', default=None)
PIMEFACTURA_PASSWORD = config_.get('pimefactura', 'password', default=None)
PIMEFACTURA_BASEURL = ('https://www.pimefactura.com'
    if PIMEFACTURA_PROD else 'http://new.pimefactura.com')

_logger = getLogger(__name__)

def basic_auth(username, password):
    token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    @classmethod
    def send_facturae_pimec(cls, invoices):
        url = '%s/uploadinvoice' % PIMEFACTURA_BASEURL

        to_write = []
        for invoice in invoices:
            if invoice.invoice_facturae_send:
                continue

            invoice_facturae = invoice.invoice_facturae

            headers = {
                'Content-Type': 'application/xml',
                "Authorization": basic_auth(PIMEFACTURA_USER, PIMEFACTURA_PASSWORD),
                }

            data = '''
                <UploadInvoiceRequest>
                    <invoicetype>facturae</invoicetype>
                    <invoicetypeversion>%(version)s</invoicetypeversion>
                    <invoiceb64>%(invoiceb64)s</invoiceb64>
                </UploadInvoiceRequest>
                ''' % {
                    'version': FACTURAE_SCHEMA_VERSION,
                    'invoiceb64': base64.b64encode(invoice_facturae).decode('utf-8'),
                }

            try:
                rqst = requests.put(
                    url,
                    data=data,
                    headers=headers
                    )
            except Exception:
                _logger.warning('Error send Pimec factura-e: %s' % invoice.rec_name)
                continue

            try:
                if rqst.status_code == 200 or rqst.status_code == 201:
                    to_write.extend(([invoice], {
                        'invoice_facturae_send': True,
                        }))
                else:
                    _logger.warning('Error send Pimec factura-e status code: %s %s' % (rqst.status_code, rqst.text))
            except socket.timeout as err:
                _logger.warning('Error send Pimec factura-e timeout: %s' % invoice.rec_name)
                _logger.error('%s' % str(err))
                continue
            except socket.error as err:
                _logger.warning('Error send Pimec factura-e: %s' % invoice.rec_name)
                _logger.error('%s' % str(err))
                continue

        if to_write:
            cls.write(*to_write)


class GenerateFacturaeStart(metaclass=PoolMeta):
    __name__ = 'account.invoice.generate_facturae.start'

    @classmethod
    def __setup__(cls):
        super(GenerateFacturaeStart, cls).__setup__()
        cls.service.selection += [('pimec', 'Pimec')]
