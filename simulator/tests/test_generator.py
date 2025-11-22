from simulator.sim_core.generator import SimSignalGenerator
from simulator.sim_core.schema import Tag


def build_tags():
    return [
        Tag(
            name="foo",
            topic="foo/topic",
            unit="C",
            min=0,
            max=100,
            baseline=50,
            noise=5,
        )
    ]


def test_next_batch_bounds_values():
    generator = SimSignalGenerator(build_tags(), seed=42)
    batch = generator.next_batch()
    assert len(batch) == 1
    value = batch[0].value
    assert 0 <= value <= 100


def test_stream_yields_batches():
    generator = SimSignalGenerator(build_tags(), seed=7)
    iterator = generator.stream(interval=0.0)
    batch = next(iterator)
    assert batch[0].tag.name == "foo"
