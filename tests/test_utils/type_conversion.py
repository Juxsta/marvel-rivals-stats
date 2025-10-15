"""Type conversion utilities for test fixtures.

Handles conversion of numpy types to Python native types for database operations.
PostgreSQL/psycopg2 cannot handle numpy types directly, causing errors like
"schema 'np' does not exist".
"""

from typing import Any

import numpy as np


def convert_numpy_types(value: Any) -> Any:
    """Convert numpy types to Python native types for database compatibility.

    PostgreSQL (via psycopg2) cannot serialize numpy types directly. This function
    converts numpy types to their Python equivalents before database insertion.

    Args:
        value: Value that may be a numpy type or Python type

    Returns:
        Python native type equivalent

    Examples:
        >>> convert_numpy_types(np.int64(42))
        42
        >>> convert_numpy_types(np.float64(3.14))
        3.14
        >>> convert_numpy_types(np.array([1, 2, 3]))
        [1, 2, 3]
        >>> convert_numpy_types("hello")
        'hello'
    """
    # Handle numpy integers (int8, int16, int32, int64, etc.)
    if isinstance(value, np.integer):
        return int(value)

    # Handle numpy floats (float16, float32, float64, etc.)
    elif isinstance(value, np.floating):
        return float(value)

    # Handle numpy arrays
    elif isinstance(value, np.ndarray):
        return value.tolist()

    # Handle numpy bool
    elif isinstance(value, np.bool_):
        return bool(value)

    # Already a Python native type
    return value


def convert_dict_numpy_types(data: dict) -> dict:
    """Convert all numpy types in a dictionary to Python native types.

    Recursively processes dictionaries and lists to convert all numpy types.

    Args:
        data: Dictionary potentially containing numpy types

    Returns:
        Dictionary with all numpy types converted to Python types

    Examples:
        >>> convert_dict_numpy_types({'a': np.int64(1), 'b': [np.float64(2.0)]})
        {'a': 1, 'b': [2.0]}
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = convert_dict_numpy_types(value)
        elif isinstance(value, list):
            result[key] = [convert_numpy_types(item) for item in value]
        else:
            result[key] = convert_numpy_types(value)
    return result


def convert_tuple_numpy_types(data: tuple) -> tuple:
    """Convert all numpy types in a tuple to Python native types.

    Args:
        data: Tuple potentially containing numpy types

    Returns:
        Tuple with all numpy types converted to Python types

    Examples:
        >>> convert_tuple_numpy_types((np.int64(1), np.float64(2.0)))
        (1, 2.0)
    """
    return tuple(convert_numpy_types(item) for item in data)
