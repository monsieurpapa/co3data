# src/integrations/mambu.py
# ─────────────────────────────────────────────────────────────────────────────
# CoopData – Mambu SACCO Platform Integration Client
# TOR §3.2 – "API Integration with existing SACCO software platforms (e.g. Mambu)"
#
# Usage:
#   from integrations.mambu import MambuClient
#   client = MambuClient()
#   loans = client.get_loans_for_branch(branch_key="XYZ123")
#
# Celery task (tasks.py) calls sync_cooperative_from_mambu(cooperative_id)
# periodically (configurable via MAMBU_SYNC_INTERVAL_MINUTES in .env).
# ─────────────────────────────────────────────────────────────────────────────

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class MambuAPIError(Exception):
    """Raised when the Mambu API returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Mambu API error {status_code}: {detail}")


class MambuClient:
    """
    Thin wrapper around the Mambu v2 REST API.

    All requests are authenticated via the API key defined in settings
    (MAMBU_API_KEY from .env).  Timeouts and retries are configured
    to be resilient in low-bandwidth environments (TOR §3.3).
    """

    BASE_URL: str = getattr(settings, "MAMBU_BASE_URL", "")
    API_KEY: str = getattr(settings, "MAMBU_API_KEY", "")
    DEFAULT_TIMEOUT: int = 30   # seconds – tolerant of slow connections
    PAGE_SIZE: int = 100

    def __init__(self):
        if not self.BASE_URL or not self.API_KEY:
            raise RuntimeError(
                "MAMBU_BASE_URL and MAMBU_API_KEY must be set in environment."
            )
        self._session = requests.Session()
        self._session.headers.update(
            {
                "apiKey": self.API_KEY,
                "Accept": "application/vnd.mambu.v2+json",
                "Content-Type": "application/json",
            }
        )

    # ── Low-level helpers ─────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.BASE_URL.rstrip('/')}/{path.lstrip('/')}"
        try:
            resp = self._session.get(url, params=params, timeout=self.DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as exc:
            raise MambuAPIError(exc.response.status_code, exc.response.text) from exc
        except requests.RequestException as exc:
            raise MambuAPIError(0, str(exc)) from exc

    def _paginate(self, path: str, params: dict | None = None) -> list[dict]:
        """Fetch all pages from a paginated Mambu endpoint."""
        params = params or {}
        params["paginationDetails"] = "ON"
        params["limit"] = self.PAGE_SIZE
        offset = 0
        results: list[dict] = []
        while True:
            params["offset"] = offset
            data = self._get(path, params)
            if not data:
                break
            results.extend(data if isinstance(data, list) else [data])
            if len(data) < self.PAGE_SIZE:
                break
            offset += self.PAGE_SIZE
        return results

    # ── Branch / Cooperative ──────────────────────────────────────────────────

    def get_branch(self, branch_encoded_key: str) -> dict:
        """Fetch a Mambu branch record (maps to a Cooperative)."""
        return self._get(f"branches/{branch_encoded_key}")

    def list_branches(self) -> list[dict]:
        return self._paginate("branches")

    # ── Members / Clients ─────────────────────────────────────────────────────

    def get_clients_for_branch(self, branch_encoded_key: str) -> list[dict]:
        """Return all clients (members) in a branch."""
        return self._paginate(
            "clients",
            params={"branchId": branch_encoded_key, "sortBy": "id:ASC"},
        )

    # ── Loan Accounts ─────────────────────────────────────────────────────────

    def get_loans_for_branch(
        self,
        branch_encoded_key: str,
        states: list[str] | None = None,
    ) -> list[dict]:
        """
        Fetch loan accounts for a branch.

        states: Mambu loan states to filter by, e.g.
            ['ACTIVE', 'IN_ARREARS', 'ACTIVE_IN_GRACE_PERIOD']
        """
        params = {"branchId": branch_encoded_key}
        if states:
            params["accountState"] = ",".join(states)
        return self._paginate("loans", params=params)

    def get_loan_details(self, loan_encoded_key: str) -> dict:
        return self._get(f"loans/{loan_encoded_key}")

    # ── Savings / Deposits ────────────────────────────────────────────────────

    def get_savings_for_branch(self, branch_encoded_key: str) -> list[dict]:
        return self._paginate(
            "savings", params={"branchId": branch_encoded_key}
        )

    # ── Transactions ──────────────────────────────────────────────────────────

    def get_loan_transactions(
        self,
        loan_encoded_key: str,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[dict]:
        params: dict = {}
        if from_date:
            params["from"] = from_date.isoformat()
        if to_date:
            params["to"] = to_date.isoformat()
        return self._paginate(
            f"loans/{loan_encoded_key}/transactions", params=params
        )


# ─────────────────────────────────────────────────────────────────────────────
# Sync helpers  (called by Celery tasks)
# ─────────────────────────────────────────────────────────────────────────────

def sync_cooperative_from_mambu(cooperative_id: int) -> dict:
    """
    Pull the latest data from Mambu for a given Cooperative and update
    the local CoopData models accordingly.

    Returns a summary dict: {members_synced, loans_synced, savings_synced, errors}
    Called by Celery task: tasks.sync_mambu_cooperative
    """
    from cooperatives.models import (
        Cooperative,
        LoanAccount,
        Member,
        SavingsAccount,
    )

    summary: dict = {
        "cooperative_id": cooperative_id,
        "members_synced": 0,
        "loans_synced": 0,
        "savings_synced": 0,
        "errors": [],
    }

    try:
        coop = Cooperative.objects.get(pk=cooperative_id)
    except Cooperative.DoesNotExist:
        summary["errors"].append(f"Cooperative #{cooperative_id} not found.")
        return summary

    if not coop.mambu_encoded_key:
        summary["errors"].append(
            f"Cooperative '{coop.name}' has no mambu_encoded_key configured."
        )
        return summary

    client = MambuClient()

    # ── Sync Clients / Members ────────────────────────────────────────────────
    try:
        mambu_clients = client.get_clients_for_branch(coop.mambu_encoded_key)
        for mc in mambu_clients:
            _upsert_member(coop, mc)
            summary["members_synced"] += 1
    except MambuAPIError as exc:
        logger.error("Mambu client sync error for %s: %s", coop.name, exc)
        summary["errors"].append(f"Members: {exc}")

    # ── Sync Loan Accounts ────────────────────────────────────────────────────
    try:
        mambu_loans = client.get_loans_for_branch(
            coop.mambu_encoded_key,
            states=["ACTIVE", "IN_ARREARS", "ACTIVE_IN_GRACE_PERIOD", "CLOSED"],
        )
        for ml in mambu_loans:
            _upsert_loan(coop, ml)
            summary["loans_synced"] += 1
    except MambuAPIError as exc:
        logger.error("Mambu loan sync error for %s: %s", coop.name, exc)
        summary["errors"].append(f"Loans: {exc}")

    # ── Sync Savings Accounts ─────────────────────────────────────────────────
    try:
        mambu_savings = client.get_savings_for_branch(coop.mambu_encoded_key)
        for ms in mambu_savings:
            _upsert_savings(coop, ms)
            summary["savings_synced"] += 1
    except MambuAPIError as exc:
        logger.error("Mambu savings sync error for %s: %s", coop.name, exc)
        summary["errors"].append(f"Savings: {exc}")

    # Update last-synced timestamp
    coop.mambu_last_synced = timezone.now()
    coop.save(update_fields=["mambu_last_synced"])

    logger.info("Mambu sync complete for %s: %s", coop.name, summary)
    return summary


# ── Private upsert helpers ────────────────────────────────────────────────────

def _upsert_member(coop, mc: dict) -> None:
    from cooperatives.models import Member

    Member.objects.update_or_create(
        cooperative=coop,
        member_id=mc.get("id", mc.get("encodedKey", "")),
        defaults={
            "first_name": mc.get("firstName", ""),
            "last_name": mc.get("lastName", ""),
            "phone_number": mc.get("mobilePhone", "") or mc.get("homePhone", ""),
            "email": mc.get("emailAddress", "") or "",
            "gender": _map_gender(mc.get("gender", "")),
        },
    )


def _upsert_loan(coop, ml: dict) -> None:
    from cooperatives.models import LoanAccount, Member

    client_key = ml.get("accountHolder", {}).get("encodedKey", "")
    member = Member.objects.filter(
        cooperative=coop, member_id=client_key
    ).first()
    if not member:
        return  # skip orphaned loans

    status_map = {
        "ACTIVE": LoanAccount.STATUS_ACTIVE,
        "IN_ARREARS": LoanAccount.STATUS_ACTIVE,
        "ACTIVE_IN_GRACE_PERIOD": LoanAccount.STATUS_ACTIVE,
        "CLOSED": LoanAccount.STATUS_CLOSED,
        "WRITTEN_OFF": LoanAccount.STATUS_WRITTEN_OFF,
    }

    LoanAccount.objects.update_or_create(
        loan_id=ml.get("id", ml.get("encodedKey", "")),
        defaults={
            "member": member,
            "outstanding_balance": ml.get("balances", {}).get("principalBalance", 0),
            "arrears_amount": ml.get("balances", {}).get("feesBalance", 0),
            "days_in_arrears": ml.get("daysInArrears", 0),
            "status": status_map.get(ml.get("accountState", ""), LoanAccount.STATUS_ACTIVE),
            "mambu_encoded_key": ml.get("encodedKey", ""),
        },
    )


def _upsert_savings(coop, ms: dict) -> None:
    from cooperatives.models import Member, SavingsAccount

    holder_key = ms.get("accountHolder", {}).get("encodedKey", "")
    member = Member.objects.filter(cooperative=coop, member_id=holder_key).first()
    if not member:
        return

    SavingsAccount.objects.update_or_create(
        member=member,
        account_number=ms.get("id", ms.get("encodedKey", "")),
        defaults={
            "balance": ms.get("balances", {}).get("totalBalance", 0),
            "is_active": ms.get("accountState", "") == "ACTIVE",
            "mambu_encoded_key": ms.get("encodedKey", ""),
        },
    )


def _map_gender(mambu_gender: str) -> str:
    return {"MALE": "male", "FEMALE": "female"}.get(mambu_gender.upper(), "other")