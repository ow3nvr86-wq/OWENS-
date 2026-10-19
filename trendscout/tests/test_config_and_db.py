import logging
import tomllib
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings, load_settings
from app.database import Database
from app.logging_config import JsonFormatter, Redactor
from app.services import controls

CONFIG = Path(__file__).resolve().parent.parent / "config" / "trendscout.toml"


def raw():
    with CONFIG.open("rb") as f:
        return tomllib.load(f)


def test_default_config_is_valid_and_safe():
    s = load_settings(CONFIG)
    assert s.publishing.require_human_approval is True
    assert s.publishing.auto_publish is False
    assert s.publishing.dry_run is True
    assert "bluesky" in s.enabled_platforms
    assert abs(sum(s.scoring.weights.normalized().values()) - 1) < 1e-9


@pytest.mark.parametrize("path, value, message", [
    (("schedule", "timezone"), "Mars/Olympus", "unknown time zone"),
    (("schedule", "discovery_times"), ["25:00"], "HH:MM"),
    (("platforms", "myspace"), {"enabled": True}, "unknown platforms"),
    (("safety", "policy"), {"vibes": "exclude"}, "unknown safety categories"),
])
def test_invalid_config_is_rejected(path, value, message):
    data = raw()
    data[path[0]][path[1]] = value
    with pytest.raises(ValidationError, match=message):
        Settings.model_validate(data)


def test_weights_cannot_all_be_zero():
    data = raw()
    data["scoring"]["weights"] = {k: 0 for k in data["scoring"]["weights"]}
    with pytest.raises(ValidationError, match="positive"):
        Settings.model_validate(data)


def test_niche_is_configurable():
    data = raw()
    data["account"].update(name="Garden Notes", niche="home gardening", categories=["vegetables", "soil"])
    s = Settings.model_validate(data)
    assert s.account.niche == "home gardening"


def test_auto_publish_needs_approval_off(db, settings):
    settings.publishing.auto_publish = True
    assert controls.auto_publish_state(db, settings)[0] is False  # approval still required
    settings.publishing.require_human_approval = False
    assert controls.auto_publish_state(db, settings)[0] is True
    controls.set_auto_publish(db, False, "test")
    assert controls.auto_publish_state(db, settings)[0] is False
    controls.set_auto_publish(db, True, "test")
    controls.pause(db, "test", "maintenance")
    assert controls.auto_publish_state(db, settings)[0] is False


def test_state_survives_restart(tmp_path):
    path = tmp_path / "persist.db"
    a = Database(path)
    a.migrate()
    controls.pause(a, "test", "kill switch")
    a.execute("INSERT INTO covered_topics (cluster_key, title, first_covered_at, last_covered_at) VALUES ('k', 't', 'x', 'x')")
    b = Database(path)  # a new process opening the same file
    assert b.migrate() == []  # already applied, idempotent
    assert controls.is_paused(b)
    assert b.scalar("SELECT COUNT(*) FROM covered_topics") == 1


def test_lock_excludes_second_holder(db):
    from datetime import timedelta
    with controls.locked(db, "x", timedelta(minutes=5)) as first:
        assert first
        with controls.locked(db, "x", timedelta(minutes=5)) as second:
            assert second is None
    with controls.locked(db, "x", timedelta(minutes=5)) as again:
        assert again  # released


def test_secrets_are_redacted_from_logs(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-supersecretvalue123")
    r = Redactor()
    record = logging.LogRecord("x", logging.ERROR, __file__, 1, "call failed with key sk-ant-supersecretvalue123", (), None)
    r.filter(record)
    out = JsonFormatter(r).format(record)
    assert "supersecret" not in out and "[redacted]" in out
    assert "abcdefgh12345" not in r.scrub("Authorization: Bearer abcdefgh12345")
