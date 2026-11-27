"""Integration tests verifying GymManagementApp sidebar shell and all 7 routes."""

import os
import tempfile
import unittest

from src.main import GymManagementApp, NAV_ITEMS


class TestAppNavigation(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.app = GymManagementApp(db_path=self._tmp.name)
        self.app.root.withdraw()

    def tearDown(self) -> None:
        if self.app.root.winfo_exists():
            self.app.root.destroy()
        if os.path.exists(self._tmp.name):
            os.remove(self._tmp.name)

    def test_all_seven_routes_mounted_and_refresh_cleanly(self) -> None:
        self.assertEqual(len(NAV_ITEMS), 7)

        mid = self.app.member_repo.create("Usman Tariq", "0301-7778899")
        fee_type_id = self.app.fee_repo.get_fee_types()[0].fee_type_id
        fee_id = self.app.fee_repo.assign_fee(mid, fee_type_id, 4000.0)
        self.app.payment_repo.record_payment(fee_id, 1500.0, "Cash")

        self.app.refresh_all()
        self.assertEqual(self.app.dashboard_view.total_members_card.value_var.get(), "1")
        self.assertEqual(self.app.dashboard_view.pending_count_card.value_var.get(), "1")
        self.assertEqual(len(self.app.member_view.members_table.tree.get_children()), 1)
        self.assertEqual(len(self.app.fees_view.fees_table.tree.get_children()), 1)
        self.assertEqual(len(self.app.history_view.history_table.tree.get_children()), 1)
        self.assertEqual(len(self.app.search_view.results_table.tree.get_children()), 1)

        for item in NAV_ITEMS:
            self.app.select_route(item.key)
            self.app.root.update_idletasks()
            self.assertEqual(self.app.sidebar.get_selected(), item.key)
            self.assertEqual(self.app.topbar_title_var.get(), item.label)


if __name__ == "__main__":
    unittest.main()
