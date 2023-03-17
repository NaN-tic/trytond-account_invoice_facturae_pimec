# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta


class CertificateService(metaclass=PoolMeta):
    __name__ = 'certificate.service'

    @classmethod
    def __setup__(cls):
        super(CertificateService, cls).__setup__()
        cls.service.selection += [('pimec', 'Pimec')]
