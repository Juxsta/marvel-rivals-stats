"""Type conversion utilities for ensuring Python-native types.

This module provides utilities to convert numpy types to Python native types
before database operations or JSON serialization. This prevents issues with
PostgreSQL (which can't serialize numpy types directly) and ensures JSON
compatibility.
"""

from typing import Any
import numpy as np


def convert_numpy_types(value: Any) -> Any:
    """Convert numpy types to Python native types recursively.

    This function handles:
    - numpy integers → Python int
    - numpy floats → Python float
    - numpy bools → Python bool
    - numpy arrays → Python list
    - Nested structures (lists, dicts) → recursively converted
    - Non-numpy types → returned unchanged

    Args:
        value: Any value that may contain numpy types

    Returns:
        The same value with all numpy types converted to Python native types

    Examples:
        >>> import numpy as np
        >>> convert_numpy_types(np.int64(42))
        42
        >>> convert_numpy_types(np.float64(3.14))
        3.14
        >>> convert_numpy_types([np.int32(1), np.float32(2.5)])
        [1, 2.5]
    """
    # Handle None
    if value is None:
        return None

    # Handle numpy integer types
    if isinstance(value, np.integer):
        return int(value)

    # Handle numpy floating types
    if isinstance(value, np.floating):
        return float(value)

    # Handle numpy boolean
    if isinstance(value, np.bool_):
        return bool(value)

    # Handle numpy arrays
    if isinstance(value, np.ndarray):
        return [convert_numpy_types(item) for item in value.tolist()]

    # Handle lists recursively
    if isinstance(value, list):
        return [convert_numpy_types(item) for item in value]

    # Handle tuples recursively
    if isinstance(value, tuple):
        return tuple(convert_numpy_types(item) for item in value)

    # Handle dicts recursively
    if isinstance(value, dict):
        return {key: convert_numpy_types(val) for key, val in value.items()}

    # Return unchanged for Python native types
    return value


def ensure_python_types(data: dict) -> dict:
    """Ensure all values in a dictionary are Python native types.

    This is a convenience wrapper around convert_numpy_types for dictionaries.
    Useful for ensuring database records or JSON payloads don't contain numpy types.

    Args:
        data: Dictionary that may contain numpy types

    Returns:
        Dictionary with all numpy types converted to Python native types

    Example:
        >>> import numpy as np
        >>> ensure_python_types({"score": np.float64(0.95), "count": np.int64(42)})
        {"score": 0.95, "count": 42}
    """
    return convert_numpy_types(data)
