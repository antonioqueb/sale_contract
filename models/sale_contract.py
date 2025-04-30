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
