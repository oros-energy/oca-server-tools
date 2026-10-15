# Copyright 2026 Oros Energy Europe GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools.sql import table_exists


class IrModel(models.Model):
    _inherit = "ir.model"

    @api.ondelete(at_uninstall=True)
    def _unlink_auditlog_actions(self):
        """Unlink the "View logs" actions of the rules before the model.

        Deleting the model fires several foreign key actions on auditlog_rule
        and ir_act_window. Depending on their order, the delete can fail on
        auditlog_rule_action_id_fkey, so the actions are removed first. When
        auditlog itself is uninstalled, the rule table may be dropped already.
        """
        if not table_exists(self.env.cr, "auditlog_rule"):
            return
        self.env["auditlog.rule"].sudo().search(
            [("model_id", "in", self.ids), ("action_id", "!=", False)]
        ).action_id.unlink()
