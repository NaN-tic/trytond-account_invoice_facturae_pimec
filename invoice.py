# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import base64
import requests
import socket

from logging import getLogger

from trytond.pool import PoolMeta
from trytond.i18n import gettext
from trytond.exceptions import UserError
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

    def send_facturae_pimec(self):
        url = '%s/uploadinvoice' % PIMEFACTURA_BASEURL

        if self.invoice_facturae_sent:
            return

        invoice_facturae = self.invoice_facturae

        headers = {
            'Content-Type': 'application/xml',
            "Authorization": basic_auth(PIMEFACTURA_USER, PIMEFACTURA_PASSWORD),
            }

        #  The outchannel (pimefactura, AOCeFACT, FACe, FACeB2B, Osakidetza, ...)
        outchannel = self.invoice_address.facturae_outchannel
        if not outchannel:
            outchannel = 'pimefactura'
        elif outchannel == 'AOC':
            outchannel = 'AOCeFACT'

        data = '''
            <UploadInvoiceRequest>
                <invoicetype>facturae</invoicetype>
                <invoicetypeversion>%(version)s</invoicetypeversion>
                <invoiceb64>%(invoiceb64)s</invoiceb64>
                <outchannelid>%(outchannel)s</outchannelid>
            </UploadInvoiceRequest>
            ''' % {
                'version': FACTURAE_SCHEMA_VERSION,
                'invoiceb64': base64.b64encode(invoice_facturae).decode('utf-8'),
                'outchannel': outchannel,
            }

        try:
            rqst = requests.put(
                url,
                data=data,
                headers=headers
                )
        except Exception as message:
            _logger.warning('Error send Pimec factura-e: %s' % self.rec_name)
            raise UserError(gettext('account_invoice_facturae_pimec.msg_error_send_pimec',
                invoice=self.rec_name,
                error=message))
        except:
            _logger.warning('Error send Pimec factura-e: %s' % self.rec_name)
            raise UserError(gettext('account_invoice_facturae_pimec.msg_error_send_pimec',
                invoice=self.rec_name,
                error=''))

        try:
            if rqst.status_code == 200 or rqst.status_code == 201:
                self.invoice_facturae_sent = True
                self.save()
            else:
                _logger.warning('Error send Pimec factura-e status code: %s %s' % (rqst.status_code, rqst.text))
                raise UserError(gettext('account_invoice_facturae_pimec.msg_error_send_pimec_status',
                    status_code=rqst.status_code,
                    text=rqst.text))
        except socket.timeout as err:
            _logger.warning('Error send Pimec factura-e timeout: %s' % self.rec_name)
            _logger.error('%s' % str(err))
            raise UserError(gettext('account_invoice_facturae_pimec.msg_error_send_pimec_timeout',
                invoice=self.rec_name,
                error=str(err)))
        except socket.error as err:
            _logger.warning('Error send Pimec factura-e: %s' % self.rec_name)
            _logger.error('%s' % str(err))
            raise UserError(gettext('account_invoice_facturae_pimec.msg_error_send_pimec_error',
                invoice=self.rec_name,
                error=str(err)))


class GenerateFacturaeStart(metaclass=PoolMeta):
    __name__ = 'account.invoice.generate_facturae.start'

    @classmethod
    def __setup__(cls):
        super(GenerateFacturaeStart, cls).__setup__()
        cls.service.selection += [('pimec', 'Pimec')]
