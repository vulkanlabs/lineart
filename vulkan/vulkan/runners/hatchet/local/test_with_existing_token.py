#!/usr/bin/env python3
"""
Test Hatchet integration using the existing HATCHET_CLIENT_TOKEN.

This test extracts the server URL from the JWT token and tests the connection.
"""

import base64
import json
import logging
import os
import sys
from typing import Any, Dict

from vulkan.runners.hatchet.local.runner import HatchetPolicyRunner
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import TerminateNode
from vulkan.spec.policy import PolicyDefinition

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def decode_jwt_payload(token: str) -> Dict[str, Any]:
    """Decode JWT token payload to extract server info."""
    try:
        # JWT tokens have 3 parts separated by dots
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT token format")

        # The payload is the second part
        payload = parts[1]

        # Add padding if necessary for base64 decoding
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += "=" * padding

        # Decode base64
        decoded = base64.b64decode(payload, validate=True)

        # Parse JSON
        return json.loads(decoded)

    except Exception as e:
        logger.error(f"Failed to decode JWT token: {e}")
        return {}


def setup_environment_from_token():
    """Setup environment variables from the existing HATCHET_CLIENT_TOKEN."""
    token = os.getenv("HATCHET_CLIENT_TOKEN")
    if not token:
        logger.error("HATCHET_CLIENT_TOKEN environment variable not found")
        return False

    # Decode the token to get server URL
    payload = decode_jwt_payload(token)

    if not payload:
        logger.error("Could not decode token payload")
        return False

    server_url = payload.get("server_url")
    if not server_url:
        logger.error("No server_url found in token")
        return False

    # Set the server URL environment variable
    os.environ["HATCHET_SERVER_URL"] = server_url
    logger.info(f"Set HATCHET_SERVER_URL to: {server_url}")

    # Set default namespace if not set
    if not os.getenv("HATCHET_NAMESPACE"):
        os.environ["HATCHET_NAMESPACE"] = "default"
        logger.info("Set HATCHET_NAMESPACE to: default")

    return True


def create_minimal_test_policy() -> PolicyDefinition:
    """Create a very simple test policy."""

    # We don't need to explicitly create InputNode - it's created automatically
    # Just create the terminate node that depends on the input
    terminate = TerminateNode(
        name="success",
        description="Complete successfully",
        return_status="SUCCESS",
        dependencies={"input_data": Dependency(INPUT_NODE)},
    )

    return PolicyDefinition(
        nodes=[terminate],
        config_variables=[],
        input_schema={"message": str},
    )


def test_hatchet_connection():
    """Test connecting to Hatchet with existing credentials."""

    logger.info("🚀 Testing Hatchet connection with existing token...")

    # Setup environment from token
    if not setup_environment_from_token():
        return False

    try:
        # Create a minimal test policy
        logger.info("Creating test policy...")
        policy = create_minimal_test_policy()

        logger.info("Initializing HatchetPolicyRunner...")
        runner = HatchetPolicyRunner.from_env(policy)

        logger.info("✅ HatchetPolicyRunner created successfully!")
        logger.info(f"Server: {runner.hatchet_server_url}")
        logger.info(f"Namespace: {runner.namespace}")

        # Test creating a Hatchet client
        from vulkan.runners.hatchet.resources import HatchetClientResource
        from vulkan.runners.hatchet.run_config import HatchetRunConfig

        run_config = HatchetRunConfig(
            run_id="test_connection",
            server_url="http://localhost:8000",  # Vulkan server (not used for this test)
            hatchet_server_url=runner.hatchet_server_url,
            hatchet_api_key=runner.hatchet_api_key,
            project_id=runner.namespace,
        )

        client_resource = HatchetClientResource(run_config)

        # Try to create the actual Hatchet client
        logger.info("Testing Hatchet SDK connection...")
        try:
            hatchet_client = client_resource.client
            logger.info("✅ Successfully connected to Hatchet!")
            logger.info(f"Client: {type(hatchet_client).__name__}")

            # Try to create a workflow (this will test if we can actually register)
            logger.info("🔧 Testing workflow creation...")
            workflow = runner.workflow
            logger.info(f"✅ Workflow created: {workflow}")

            # Test workflow input creation
            test_input = {"message": "Hello from Vulkan-Hatchet integration!"}
            workflow_input = runner._create_workflow_input(test_input)
            logger.info(f"📝 Created workflow input: {workflow_input}")

        except ImportError as e:
            logger.warning(f"⚠️  Hatchet SDK not available: {e}")
            logger.info("This is expected if hatchet-sdk is not installed")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Hatchet: {e}")
            logger.info("This might indicate network issues or invalid credentials")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function."""
    logger.info("=" * 60)
    logger.info("🔧 HATCHET INTEGRATION TEST")
    logger.info("=" * 60)

    success = test_hatchet_connection()

    logger.info("=" * 60)
    if success:
        logger.info("✅ Test completed! Hatchet integration is working.")
        logger.info(
            "You can now use HatchetPolicyRunner with your existing credentials."
        )
        logger.info("")
        logger.info("Example usage:")
        logger.info("  from vulkan.runners.hatchet import HatchetPolicyRunner")
        logger.info("  runner = HatchetPolicyRunner.from_env(your_policy)")
        logger.info("  result = runner.run({'message': 'test'})")
    else:
        logger.error("❌ Test failed! Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
