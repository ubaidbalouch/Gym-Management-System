"""Unit tests for database schema migrations and feature repositories."""

import os
import tempfile
import unittest

from src.common.database import DatabaseConnection, initialize_schema
from src.features.dashboard.dashboard_repository import DashboardRepository
from src.features.fees.fee_repository import FeeRepository
from src.features.members.member_repository import MemberRepository
from src.features.payments.payment_repository import PaymentRepository
from src.features.search.search_repository import SearchRepository


class TestRepositories(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.db = DatabaseConnection(self._tmp.name)
        initialize_schema(self.db)

        self.members = MemberRepository(self.db)
        self.fees = FeeRepository(self.db)
        self.payments = PaymentRepository(self.db)
        self.dashboard = DashboardRepository(self.db)
        self.search = SearchRepository(self.db)

    def tearDown(self) -> None:
        if os.path.exists(self._tmp.name):
            os.remove(self._tmp.name)

    def test_default_fee_types_seeded_idempotently(self) -> None:
        initialize_schema(self.db)
        types = self.fees.get_fee_types()
        names = [ft.fee_name for ft in types]
        self.assertEqual(
            names,
            ["Monthly Fee", "Admission Fee", "Personal Training", "Supplement Fee"],
        )

    def test_member_crud_and_cascading_delete(self) -> None:
        mid = self.members.create("Ali Raza", "0300-1112233")
        member = self.members.get_by_id(mid)
        self.assertIsNotNone(member)
        self.assertEqual(member.name, "Ali Raza")

        self.assertTrue(self.members.update(mid, "Ali Khan", "0300-9998877"))
        updated = self.members.get_by_id(mid)
        self.assertEqual(updated.name, "Ali Khan")
        self.assertEqual(updated.phone, "0300-9998877")

        fee_type_id = self.fees.get_fee_types()[0].fee_type_id
        fee_id = self.fees.assign_fee(mid, fee_type_id, 5000.0, "2026-11-01", "Nov fee")
        self.payments.record_payment(fee_id, 2000.0, "Cash")

        self.assertTrue(self.members.delete(mid))
        self.assertIsNone(self.members.get_by_id(mid))
        self.assertEqual(self.fees.get_all_fees(), [])

        with self.db.session() as conn:
            payment_rows = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        self.assertEqual(payment_rows, 0)

    def test_fee_payment_status_transitions_and_dashboard_stats(self) -> None:
        mid = self.members.create("Sara Ahmed", "0321-5556677")
        fee_type_id = self.fees.get_fee_types()[0].fee_type_id
        fee_id = self.fees.assign_fee(mid, fee_type_id, 3000.0)

        stats_initial = self.dashboard.get_stats()
        self.assertEqual(stats_initial.total_members, 1)
        self.assertEqual(stats_initial.pending_count, 1)
        self.assertEqual(stats_initial.total_fees, 3000.0)
        self.assertEqual(stats_initial.total_paid, 0.0)
        self.assertEqual(stats_initial.total_pending, 3000.0)

        status_partial = self.payments.record_payment(fee_id, 1000.0, "Jazz Cash")
        self.assertEqual(status_partial, "Partial")

        stats_partial = self.dashboard.get_stats()
        self.assertEqual(stats_partial.pending_count, 1)
        self.assertEqual(stats_partial.total_paid, 1000.0)
        self.assertEqual(stats_partial.total_pending, 2000.0)

        status_paid = self.payments.record_payment(fee_id, 2000.0, "Cash")
        self.assertEqual(status_paid, "Paid")

        stats_paid = self.dashboard.get_stats()
        self.assertEqual(stats_paid.pending_count, 0)
        self.assertEqual(stats_paid.total_paid, 3000.0)
        self.assertEqual(stats_paid.total_pending, 0.0)
        self.assertEqual(stats_paid.status_breakdown.get("Paid"), 1)

    def test_search_and_comprehensive_details(self) -> None:
        mid = self.members.create("Bilal Tariq", "0333-4445566")
        fee_type_id = self.fees.get_fee_types()[1].fee_type_id
        fee_id = self.fees.assign_fee(mid, fee_type_id, 2500.0)
        self.payments.record_payment(fee_id, 1000.0, "Card")

        by_name = self.search.search_members("Bilal")
        self.assertEqual(len(by_name), 1)
        by_id = self.search.search_members(str(mid))
        self.assertEqual(len(by_id), 1)

        details = self.search.get_member_comprehensive_details(mid)
        self.assertIsNotNone(details)
        self.assertEqual(details.overall_status, "Partial")
        self.assertEqual(details.total_fees, 2500.0)
        self.assertEqual(details.paid_amount, 1000.0)
        self.assertEqual(details.pending_amount, 1500.0)
        self.assertEqual(len(details.fees), 1)


if __name__ == "__main__":
    unittest.main()
