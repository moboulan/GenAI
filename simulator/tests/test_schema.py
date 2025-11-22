from pathlib import Path

from simulator.sim_core.schema import load_tags


def test_load_tags_returns_all_entries():
    tags = load_tags(Path(__file__).parents[1] / "schemas" / "tags.yaml")
    assert len(tags) >= 3
    assert {t.name for t in tags} >= {"reactor_temperature", "acid_flow"}
