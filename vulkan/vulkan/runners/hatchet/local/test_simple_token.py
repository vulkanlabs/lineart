#!/usr/bin/env python3
"""
Simple test using only HATCHET_CLIENT_TOKEN.
"""

import logging
import os
import sys

from vulkan.runners.hatchet.local.runner import HatchetPolicyRunner
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import TerminateNode
from vulkan.spec.policy import PolicyDefinition

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_simple_policy() -> PolicyDefinition:
    """Create a minimal test policy."""

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


def main():
    """Test with just the HATCHET_CLIENT_TOKEN."""

    logger.info("🚀 Testing Hatchet with token-only authentication...")

    # Check if token exists
    token = os.getenv("HATCHET_CLIENT_TOKEN")
    if not token:
        logger.error("❌ HATCHET_CLIENT_TOKEN environment variable not found")
        logger.error("Please ensure your Hatchet token is set.")
        sys.exit(1)

    logger.info("✅ Found HATCHET_CLIENT_TOKEN")

    try:
        # Create test policy
        logger.info("Creating test policy...")
        policy = create_simple_policy()

        # Create runner using only the token
        logger.info("Creating HatchetPolicyRunner...")
        runner = HatchetPolicyRunner.from_env(policy)

        logger.info("✅ HatchetPolicyRunner created successfully!")
        logger.info(f"Namespace: {runner.namespace}")

        # Test creating Hatchet client resource
        from vulkan.runners.hatchet.resources import HatchetClientResource
        from vulkan.runners.hatchet.run_config import HatchetRunConfig

        run_config = HatchetRunConfig(
            run_id="test",
            server_url="http://localhost:8000",
            hatchet_server_url=runner.hatchet_server_url,
            hatchet_api_key=runner.hatchet_api_key,
            namespace=runner.namespace,
        )

        client_resource = HatchetClientResource(run_config)

        # Try to create the Hatchet client
        logger.info("🔧 Testing Hatchet SDK connection...")
        try:
            hatchet_client = client_resource.client
            logger.info("✅ Hatchet client created successfully!")
            logger.info(f"Client type: {type(hatchet_client).__name__}")

            # Try to create workflow
            logger.info("🔧 Testing workflow creation...")
            workflow = runner.workflow
            logger.info(f"✅ Workflow created: {type(workflow).__name__}")

            # Test with sample input
            test_input = {"message": "Hello Hatchet!"}
            workflow_input = runner._create_workflow_input(test_input)
            logger.info(f"📝 Sample workflow input: {workflow_input}")

            logger.info("")
            logger.info(
                "🎉 SUCCESS! Hatchet integration is working with token-only auth!"
            )
            logger.info("")
            logger.info("You can now run workflows like this:")
            logger.info("  runner = HatchetPolicyRunner.from_env(your_policy)")
            logger.info("  result = runner.run({'message': 'test data'})")

        except ImportError as e:
            logger.warning(f"⚠️  Hatchet SDK not available: {e}")
            logger.info("Install with: pip install hatchet-sdk")
        except Exception as e:
            logger.error(f"❌ Hatchet connection failed: {e}")
            import traceback

            traceback.print_exc()

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
