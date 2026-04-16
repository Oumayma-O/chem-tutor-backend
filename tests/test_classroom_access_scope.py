"""Classroom access scope regression tests."""

from types import SimpleNamespace

from app.api.v1.classroom_access import _admin_may_access_classroom


def test_admin_may_access_classroom_when_school_and_district_match() -> None:
    admin = SimpleNamespace(district="CA", school="Roosevelt High")
    owner = SimpleNamespace(district="CA", school="Roosevelt High")
    assert _admin_may_access_classroom(admin, owner) is True


def test_admin_may_access_classroom_denies_when_school_missing() -> None:
    admin = SimpleNamespace(district="CA", school=None)
    owner = SimpleNamespace(district="CA", school="Roosevelt High")
    assert _admin_may_access_classroom(admin, owner) is False


def test_admin_may_access_classroom_denies_on_district_mismatch() -> None:
    admin = SimpleNamespace(district="CA", school="Roosevelt High")
    owner = SimpleNamespace(district="NY", school="Roosevelt High")
    assert _admin_may_access_classroom(admin, owner) is False
