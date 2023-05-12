# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import PoolMeta


class ConfigurationFacturae(metaclass=PoolMeta):
    __name__ = 'account.configuration.facturae'

    @classmethod
    def __setup__(cls):
        super(ConfigurationFacturae, cls).__setup__()
        cls.facturae_service.selection += [('pimec', 'Pimec')]
