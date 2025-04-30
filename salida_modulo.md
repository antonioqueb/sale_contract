-e ### models/__init__.py
```
# -*- coding: utf-8 -*-
from . import sale_contract
```

-e ### models/sale_contract.py
```
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date

class SaleContract(models.Model):
    _name = "sale.contract"
    _description = "Contrato de venta"

    name = fields.Char(string="Referencia", copy=False, default=lambda self: _("Nuevo"))
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)
    date_start = fields.Date(string="Vigencia desde", default=fields.Date.context_today)
    date_end   = fields.Date(string="Vigencia hasta")
    state = fields.Selection([
        ("draft",     "Borrador"),
        ("active",    "Vigente"),
        ("expired",   "Vencido"),
        ("cancelled", "Cancelado"),
    ], default="draft", string="Estado")

    line_ids = fields.One2many(
        "sale.contract.line",
        "contract_id",
        string="Residuos autorizados"
    )

    # -- Acciones -----------------------------------------------------------
    def action_confirm(self):
        """Aprueba el contrato y lo marca como vigente."""
        for contract in self:
            contract.state = "active"

    def action_generate_service(self):
        """Genera una orden de venta de servicio normal."""
        return self._create_sale_order(order_type="service")

    def action_generate_excess(self):
        """Genera una orden de venta de excedente."""
        return self._create_sale_order(order_type="excess")

    # -- Lógica interna -----------------------------------------------------
    def _create_sale_order(self, order_type="service"):
        self.ensure_one()
        order = self.env["sale.order"].create({
            "partner_id": self.partner_id.id,
            "origin":     self.name,
            "contract_id": self.id,
            "order_type":  order_type,
            "order_line": [
                (0, 0, {
                    "product_id":  line.product_id.id,
                    "name":        line.product_id.display_name,
                    "price_unit":  line.price_unit,
                    "product_uom_qty": 1.0,
                }) for line in self.line_ids
            ],
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Orden de venta"),
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": order.id,
        }

    # -- Auxiliar: caducar automáticamente (opcional) -----------------------
    @api.model
    def _cron_expire_contracts(self):
        today = date.today()
        self.search([
            ("state", "=", "active"),
            ("date_end", "<", today)
        ]).write({"state": "expired"})


class SaleContractLine(models.Model):
    _name = "sale.contract.line"
    _description = "Línea de contrato de venta"

    contract_id = fields.Many2one("sale.contract", string="Contrato", required=True, ondelete="cascade")
    product_id  = fields.Many2one("product.product", string="Residuo autorizado", required=True)
    price_unit  = fields.Float(string="Precio unitario")
    quantity    = fields.Float(string="Cantidad de referencia", default=1.0)
    uom_id      = fields.Many2one(
        "uom.uom",
        string="UoM",
        related="product_id.uom_id",
        readonly=True
    )


class SaleOrder(models.Model):
    _inherit = "sale.order"

    contract_id = fields.Many2one("sale.contract", string="Contrato de venta", readonly=True)
    order_type = fields.Selection([
        ("service",   "Servicio"),
        ("excess",    "Excedente"),
    ], default="service", string="Tipo de orden", readonly=True)
```

-e ### views/sale_contract_menus.xml
```
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>

        <!-- Acción que abre la vista de contratos -->
        <record id="action_sale_contracts" model="ir.actions.act_window">
            <field name="name">Contratos de venta</field>
            <field name="res_model">sale.contract</field>
            <field name="view_mode">tree,form</field>
        </record>

        <!-- Menú principal -->
        <menuitem id="menu_contract_root"
                  name="Contratos"
                  sequence="50"/>

        <!-- Submenú -->
        <menuitem id="menu_sale_contract"
                  name="Contratos de venta"
                  parent="menu_contract_root"
                  action="action_sale_contracts"
                  sequence="1"/>

    </data>
</odoo>
```

-e ### views/sale_contract_views.xml
```
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data>

        <!-- Vista LISTA (antes “tree”) -->
        <record id="view_sale_contract_list" model="ir.ui.view">
            <field name="name">sale.contract.list</field>
            <field name="model">sale.contract</field>
            <field name="type">list</field>   <!-- 👈 cambio clave -->
            <field name="arch" type="xml">
                <tree string="Contratos de venta">
                    <field name="name"/>
                    <field name="partner_id"/>
                    <field name="date_start"/>
                    <field name="date_end"/>
                    <field name="state"/>
                </tree>
            </field>
        </record>

        <!-- Vista FORMULARIO -->
        <record id="view_sale_contract_form" model="ir.ui.view">
            <field name="name">sale.contract.form</field>
            <field name="model">sale.contract</field>
            <field name="type">form</field>   <!-- 👈 especificado -->
            <field name="arch" type="xml">
                <form string="Contrato de venta">
                    <header>
                        <button name="action_confirm" type="object"
                                states="draft" class="btn-primary"
                                string="Aprobar"/>
                        <button name="action_generate_service" type="object"
                                states="active" class="btn-success"
                                string="Generar Servicio"/>
                        <button name="action_generate_excess" type="object"
                                states="active" class="btn-secondary"
                                string="Generar Excedente"/>
                        <field name="state" widget="statusbar"
                               statusbar_visible="draft,active,expired,cancelled"/>
                    </header>

                    <sheet>
                        <group>
                            <field name="name"/>
                            <field name="partner_id"/>
                            <field name="date_start"/>
                            <field name="date_end"/>
                        </group>

                        <notebook>
                            <page string="Residuos autorizados">
                                <field name="line_ids" context="{'default_contract_id': active_id}">
                                    <tree editable="bottom">
                                        <field name="product_id"/>
                                        <field name="price_unit"/>
                                        <field name="quantity"/>
                                        <field name="uom_id"/>
                                    </tree>
                                </field>
                            </page>
                        </notebook>
                    </sheet>
                </form>
            </field>
        </record>

    </data>
</odoo>
```

### __init__.py
```
# -*- coding: utf-8 -*-
from . import models
```
### __manifest__.py
```
# -*- coding: utf-8 -*-
{
    "name": "Contratos de Venta",
    "summary": "Cotización anual inalterable con generación de órdenes de servicio o excedente",
    "version": "0.1",
    "author": "ALPHAQUEB CONSULTING",
    "category": "Sales",
    "depends": ["sale"],
    "data": [
        "views/sale_contract_menus.xml",
        "views/sale_contract_views.xml",
        # Se omiten reglas de seguridad para simplificar la demo
    ],
    "installable": True,
    "application": True,
}
```
