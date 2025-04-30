# -*- coding: utf-8 -*-
{
    "name": "Contratos de Venta",
    "summary": "Cotización anual inalterable con generación de órdenes de servicio o excedente",
    "version": "0.1",
    "author": "ALPHAQUEB CONSULTING",
    "category": "Sales",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv", 
        "views/sale_contract_menus.xml",
        "views/sale_contract_views.xml",
        # Se omiten reglas de seguridad para simplificar la demo
    ],
    "installable": True,
    "application": True,
}
