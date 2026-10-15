# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase

from odoo.addons.auditlog.models.auditlog_rule import ThrowAwayCache


class TestThrowAwayCache(TransactionCase):
    """Odoo 20 environments cache references to transaction containers
    (env._protected, env._field_dirty). The throwaway cache must swap them
    in and out together with the transaction attributes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Throw Away"})

    @property
    def name_field(self):
        # Not a class attribute. A Field is a descriptor, reading it from the
        # test case would call Field.__get__ with the test case as record.
        return self.env["res.partner"]._fields["name"]

    def test_outer_protection_not_visible_inside(self):
        env = self.env
        with env.protecting([self.name_field], self.partner):
            self.assertTrue(env.is_protected(self.name_field, self.partner))
            outer_maps = [dict(m) for m in env._protected._maps]
            with ThrowAwayCache(env):
                self.assertFalse(env.is_protected(self.name_field, self.partner))
                self.assertIs(env._protected, env.transaction.protected)
            # the outer protection is in effect again, unchanged
            self.assertEqual([dict(m) for m in env._protected._maps], outer_maps)
            self.assertTrue(env.is_protected(self.name_field, self.partner))
            self.assertIs(env._protected, env.transaction.protected)
        self.assertFalse(env.is_protected(self.name_field, self.partner))

    def test_inner_protection_dropped_on_exit(self):
        env = self.env
        outer = env._protected
        cache = ThrowAwayCache(env)
        cache.__enter__()
        inner = env._protected
        self.assertIsNot(inner, outer)
        protecting = env.protecting([self.name_field], self.partner)
        protecting.__enter__()
        self.assertTrue(env.is_protected(self.name_field, self.partner))
        cache.__exit__(None, None, None)
        # the protection set inside does not leak into the outer scope
        self.assertIs(env._protected, outer)
        self.assertFalse(env.is_protected(self.name_field, self.partner))
        protecting.__exit__(None, None, None)
        self.assertFalse(env.is_protected(self.name_field, self.partner))

    def test_dirty_fields_isolated(self):
        env = self.env
        outer = env._field_dirty
        self.assertIs(outer, env.transaction.field_dirty)
        with ThrowAwayCache(env):
            self.assertIs(env._field_dirty, env.transaction.field_dirty)
            self.assertIsNot(env._field_dirty, outer)
            self.assertFalse(env._field_dirty)
        self.assertIs(env._field_dirty, outer)
        self.assertIs(env.transaction.field_dirty, outer)
