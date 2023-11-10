# -*- coding: utf-8 -*-
{
    'name': 'Bowman: Certification',
    'summary': 'Bowman (kAlpha Ray): Certification Flow',
    'description': """
    [2003850]
    """,
    'license': 'OPL-1',
    'author': 'Odoo Inc',
    'version': '3.0.1',
    'depends': ['sale_stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'views/stock_location_views.xml',
        'views/stock_production_views.xml',
        'views/stock_move_views.xml',
        'views/certification_views.xml',
    ],
}
