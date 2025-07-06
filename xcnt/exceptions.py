from typing import Any, Dict, Type

from ninja import schema


class HttpExceptionMeta(type):
    """Metaclass to automatically generate schema and properties for exception classes."""

    # Track registered error types to prevent duplicates
    error_types: Dict[str, str] = {}

    def __new__(cls, name: str, bases: tuple, class_dict: dict):  # type: ignore
        """Dynamically constructs exception classes with validations and property injections."""

        # Skip validations for the base class
        if name == "HttpException":
            return super().__new__(cls, name, bases, class_dict)

        # Extract parameters from the class's `__init__` method (if defined)
        ctx_fields: Dict[str, Any] = cls._extract_init_params(class_dict)

        # Perform error type validation
        cls._validate_error_type(name, class_dict)

        # Ensure at least one of `error_message` or `error_template` is defined
        cls._validate_error_message_or_template(name, class_dict)

        class_dict["ctx_fields"] = ctx_fields
        class_dict["Schema"] = cls.generate_schema(
            name, class_dict["error_type"], ctx_fields
        )

        cls._inject_auto_init(class_dict, ctx_fields)
        # Create the new exception class
        new_class = super().__new__(cls, name, bases, class_dict)

        return new_class

    @staticmethod
    def _inject_auto_init(class_dict, ctx_fields: Dict[str, Any]) -> None:  # type: ignore[no-untyped-def]
        """Injects an automatic `__init__` method to set instance attributes and populate ctx_fields."""
        if not ctx_fields and "__init__" not in class_dict:
            return  # Do not inject if neither ctx_fields nor __init__ is defined

        original_init = class_dict.get("__init__", None)  # Get the existing `__init__`

        def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            # Call the original `__init__` if it exists
            if original_init:
                original_init(self, *args, **kwargs)
            # Store provided arguments in ctx_fields and set them as attributes
            self.ctx_fields = {}
            arg_iter = iter(args)

            for index, field in enumerate(ctx_fields):
                if index < len(args):
                    value = next(arg_iter)  # Get the positional argument
                else:
                    value = kwargs.get(field)  # Fallback to keyword arguments
                self.ctx_fields[field] = value  # Store in ctx_fields
                setattr(self, field, value)  # Store as a direct attribute
            # Generate `error_message` from `error_template` if applicable
            if hasattr(self, "error_template"):
                self.error_message = self.error_template.format(**self.ctx_fields)

        class_dict["__init__"] = __init__

    @staticmethod
    def _extract_init_params(class_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts the parameters from the class `__init__` function annotations."""
        init_fn = class_dict.get("__init__", {})
        if not init_fn:
            return {}

        return {
            param: annotation
            for param, annotation in init_fn.__annotations__.items()
            if param not in {"return", "self"}
        }

    @classmethod
    def _validate_error_type(cls, name: str, class_dict: Dict[str, Any]) -> None:
        """Ensures that the `error_type` attribute is defined and unique."""
        error_type = class_dict.get("error_type", None)
        if not isinstance(error_type, str):
            raise TypeError(
                f"Class '{name}' must define a string attribute 'error_type'."
            )

        if error_type and error_type in cls.error_types:
            raise TypeError(
                f"Error type '{error_type}' is already defined in class: {name}."
            )

        cls.error_types[error_type] = name  # Register the error type

    @staticmethod
    def _validate_error_message_or_template(
        name: str, class_dict: Dict[str, Any]
    ) -> None:
        """Ensures that either `error_message` or `error_template` is defined."""
        has_error_message = isinstance(class_dict.get("error_message", None), str)
        has_error_template = isinstance(class_dict.get("error_template", None), str)

        if not (has_error_message or has_error_template) or (
            has_error_template and has_error_message
        ):
            raise TypeError(
                f"Class '{name}' must define either 'error_message' or 'error_template'."
            )

    @staticmethod
    def generate_schema(
        name: str, error_type: str, ctx_fields: dict[str, type] = {}
    ) -> Any:
        """Dynamically creates a Pydantic schema class for an exception."""
        class_name = f"{name}Schema"
        class_dict: Dict[str, Any] = {
            "type": error_type,
            "__annotations__": {
                "type": str,
                "msg": str,
            },
        }

        if ctx_fields:
            class_dict["__annotations__"]["ctx"] = type(
                f"{name}CtxSchema",
                (schema.Schema,),
                {
                    "__annotations__": ctx_fields,
                },
            )

        return type(
            class_name,
            (schema.Schema,),
            class_dict,
        )


class HttpException(Exception, metaclass=HttpExceptionMeta):
    Schema: Type[schema.Schema]  # Explicitly define Schema
    error_message: str
    error_template: str
    error_type: str

    def to_schema(self) -> schema.Schema:
        ctx_fields: Dict[str, Any] = getattr(self, "ctx_fields", {})
        ctx: Dict[str, Any] = (
            {field: getattr(self, field, None) for field in ctx_fields}
            if ctx_fields
            else {}
        )
        schema_data: Dict[str, Any] = {
            "type": self.error_type,
            "msg": str(self.error_message),
        }
        if ctx:
            schema_data["ctx"] = ctx
        return self.Schema(**schema_data)

    def __str__(self) -> str:
        return self.error_message

    def __repr__(self) -> str:
        return self.error_message
