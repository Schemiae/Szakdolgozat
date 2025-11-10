def validate_fields(data, required_fields: dict):
    errors = []

    for field, expected_type in required_fields.items():
        if field not in data:
            errors.append(f"{field} is missing")
        elif not isinstance(data[field], expected_type):
            # Allow int when float is expected
            if not (expected_type == float and isinstance(data[field], int)):
                print(field)
                print(expected_type)
                errors.append(f"{field} must be {expected_type.__name__}")

    if errors:
        raise ValueError("; ".join(errors))
