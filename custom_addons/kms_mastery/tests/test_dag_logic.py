# Part of KMS Mastery Learning. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestDAGLogic(TransactionCase):
    """Test DAG (Directed Acyclic Graph) constraint enforcement."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Node = cls.env['kms.node']
        cls.node_a = Node.create({'name': 'Node A'})
        cls.node_b = Node.create({
            'name': 'Node B',
            'prerequisite_ids': [(4, cls.node_a.id)],
        })
        cls.node_c = Node.create({
            'name': 'Node C',
            'prerequisite_ids': [(4, cls.node_b.id)],
        })

    def test_valid_linear_chain(self):
        """A→B→C should be valid (no cycle)."""
        # If we got here, the chain was created without error
        self.assertEqual(len(self.node_c.prerequisite_ids), 1)
        self.assertEqual(self.node_c.prerequisite_ids[0].id, self.node_b.id)

    def test_cycle_detection_direct(self):
        """Adding C→A should raise a ValidationError (creates cycle A→B→C→A)."""
        with self.assertRaises(ValidationError):
            self.node_a.write({
                'prerequisite_ids': [(4, self.node_c.id)],
            })

    def test_self_referential_prerequisite(self):
        """A node cannot be its own prerequisite."""
        with self.assertRaises(ValidationError):
            self.node_a.write({
                'prerequisite_ids': [(4, self.node_a.id)],
            })

    def test_remove_prerequisite_link(self):
        """Removing a prerequisite link should work without error."""
        self.node_b.write({
            'prerequisite_ids': [(3, self.node_a.id)],
        })
        self.assertFalse(self.node_b.prerequisite_ids)

    def test_multiple_prerequisites(self):
        """A node can have multiple valid prerequisites."""
        node_d = self.env['kms.node'].create({'name': 'Node D'})
        node_e = self.env['kms.node'].create({
            'name': 'Node E',
            'prerequisite_ids': [(4, self.node_a.id), (4, node_d.id)],
        })
        self.assertEqual(len(node_e.prerequisite_ids), 2)

    def test_dependent_ids_inverse(self):
        """dependent_ids should be the inverse of prerequisite_ids."""
        self.assertIn(self.node_b, self.node_a.dependent_ids)
        self.assertIn(self.node_c, self.node_b.dependent_ids)
