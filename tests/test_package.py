"""Base checks for the Layer 1 package structure."""

from confidential_model_delivery_poc import bundle, consumer, producer


def test_layer1_modules_are_importable() -> None:
    """Future workflow modules exist without triggering network or model I/O."""
    assert bundle.__doc__
    assert consumer.__doc__
    assert producer.__doc__
