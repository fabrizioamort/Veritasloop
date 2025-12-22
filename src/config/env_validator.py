"""Environment variable validation for VeritasLoop.

This module validates required and optional environment variables
on application startup to ensure proper configuration.
"""

import os
import sys
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


def validate_required_env_vars() -> None:
    """Validate required environment variables on startup.

    If any required variables are missing, the application will exit with an error.
    Optional variables will generate warnings if missing.

    Raises:
        SystemExit: If any required environment variables are missing.
    """
    # Required environment variables (critical for operation)
    required_vars = [
        'OPENAI_API_KEY',
        'BRAVE_SEARCH_API_KEY',
    ]

    # Optional environment variables (enhance functionality but not critical)
    optional_vars = [
        'NEWS_API_KEY',
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'GEMINI_API_KEY',
    ]

    # Check for missing required variables
    missing_required = [var for var in required_vars if not os.getenv(var)]

    if missing_required:
        error_message = (
            f"\n{'='*70}\n"
            f"ERROR: Missing required environment variables:\n"
            f"  - {', '.join(missing_required)}\n\n"
            f"Please ensure your .env file exists and contains all required keys.\n"
            f"You can use .env.example as a template.\n"
            f"{'='*70}\n"
        )
        print(error_message, file=sys.stderr)
        logger.error(f"Missing required environment variables: {missing_required}")
        sys.exit(1)

    # Check for missing optional variables (warn but don't exit)
    missing_optional = [var for var in optional_vars if not os.getenv(var)]

    if missing_optional:
        warning_message = (
            f"\n{'='*70}\n"
            f"WARNING: Missing optional environment variables:\n"
            f"  - {', '.join(missing_optional)}\n\n"
            f"Some features may not work correctly without these variables.\n"
            f"See .env.example for more information.\n"
            f"{'='*70}\n"
        )
        print(warning_message)
        logger.warning(f"Missing optional environment variables: {missing_optional}")

    # Log success
    logger.info("Environment variable validation completed successfully")
    logger.info(f"Required variables present: {', '.join(required_vars)}")
    if not missing_optional:
        logger.info(f"Optional variables present: {', '.join(optional_vars)}")


def validate_config_values() -> List[Tuple[str, str]]:
    """Validate configuration values for correctness.

    Returns:
        List of (variable_name, error_message) tuples for invalid values.
    """
    errors = []

    # Validate ENVIRONMENT
    env = os.getenv('ENVIRONMENT', 'development').lower()
    if env not in ['development', 'staging', 'production']:
        errors.append((
            'ENVIRONMENT',
            f"Invalid value '{env}'. Must be 'development', 'staging', or 'production'."
        ))

    # Validate numeric values
    try:
        api_port = int(os.getenv('API_PORT', '8000'))
        if not (1 <= api_port <= 65535):
            errors.append(('API_PORT', f"Invalid port {api_port}. Must be between 1 and 65535."))
    except ValueError:
        errors.append(('API_PORT', "Must be a valid integer."))

    try:
        phoenix_port = int(os.getenv('PHOENIX_PORT', '6006'))
        if not (1 <= phoenix_port <= 65535):
            errors.append(('PHOENIX_PORT', f"Invalid port {phoenix_port}. Must be between 1 and 65535."))
    except ValueError:
        errors.append(('PHOENIX_PORT', "Must be a valid integer."))

    try:
        request_timeout = int(os.getenv('REQUEST_TIMEOUT', '10'))
        if not (1 <= request_timeout <= 300):
            errors.append(('REQUEST_TIMEOUT', f"Invalid timeout {request_timeout}. Should be between 1 and 300 seconds."))
    except ValueError:
        errors.append(('REQUEST_TIMEOUT', "Must be a valid integer."))

    # Validate boolean values
    phoenix_enabled = os.getenv('PHOENIX_ENABLED', 'true').lower()
    if phoenix_enabled not in ['true', 'false', '1', '0', 'yes', 'no']:
        errors.append(('PHOENIX_ENABLED', f"Invalid value '{phoenix_enabled}'. Must be 'true' or 'false'."))

    if errors:
        logger.warning(f"Configuration validation found {len(errors)} issue(s)")
        for var_name, error_msg in errors:
            logger.warning(f"  {var_name}: {error_msg}")

    return errors


def validate_all() -> None:
    """Run all validation checks.

    This is the main entry point for environment validation.
    Validates both presence and correctness of environment variables.
    """
    # First check required variables exist
    validate_required_env_vars()

    # Then validate configuration values
    config_errors = validate_config_values()

    if config_errors:
        warning_message = (
            f"\n{'='*70}\n"
            f"WARNING: Configuration value issues detected:\n"
        )
        for var_name, error_msg in config_errors:
            warning_message += f"  {var_name}: {error_msg}\n"
        warning_message += (
            f"\nThe application will continue but may not behave as expected.\n"
            f"Please review your .env file.\n"
            f"{'='*70}\n"
        )
        print(warning_message)
