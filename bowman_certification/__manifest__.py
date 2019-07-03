# -*- coding: utf-8 -*-
{
    'name': 'Bowman: Certification',
    'summary': 'Bowman (kAlpha Ray): Certification Flow',
    'description': """
    [2003850]
    """,
    'license': 'OEEL-1',
    'author': 'Odoo Inc',
    'version': '0.1',
    'depends': ['sale_stock', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/stock_location_views.xml',
        'views/stock_production_views.xml',
        'views/stock_move_views.xml',
        'views/certification_views.xml',
    ],
}
