import logging
logger = logging.getLogger(__name__)

def get_model_fields(model, exclude=None, field_order=None):
    exclude = exclude or []
    field_order = field_order or []

    fields = []

    # If field_order is provided, use that order
    if field_order:
        for field_name in field_order:
            if field_name not in exclude:
                try:
                    field = model._meta.get_field(field_name)
                    fields.append(
                        {"name": field.name, "label": format_field_name(field.name)}
                    )
                except Exception as e:
                    logger.warning(f"Could not resolve field '{field_name}': {e}")

    else:
        for field in model._meta.fields:
            if field.name not in exclude:
                fields.append(
                    {"name": field.name, "label": format_field_name(field.name)}
                )

    return fields


def format_field_name(field_name: str) -> str:
    return field_name.replace("_", " ").upper()
