# This file is part account_invoice_facturae_pimec module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import configuration
from . import invoice


def register():
    Pool.register(
        configuration.ConfigurationFacturae,
        invoice.Invoice,
        invoice.GenerateFacturaeStart,
        module='account_invoice_facturae_pimec', type_='model')
