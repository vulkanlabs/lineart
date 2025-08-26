#!/usr/bin/env python3
"""
Demo showing how to register and run a Vulkan policy with Hatchet.

This demonstrates the complete workflow:
1. Create a Vulkan policy
2. Register it as a Hatchet workflow
3. Execute it with sample data
4. Get results

Prerequisites:
- HATCHET_CLIENT_TOKEN environment variable set
- hatchet-sdk installed (pip install hatchet-sdk)
"""

import logging
import os
import sys
import time

from vulkan.runners.hatchet.local.runner import HatchetPolicyRunner
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import TerminateNode, TransformNode
from vulkan.spec.policy import PolicyDefinition

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def create_demo_policy() -> PolicyDefinition:
    """Create a demo policy that processes some input data."""

    # Simple transform function
    def process_message(input_data, **kwargs):
        """Process the input message and add timestamp."""
        message = input_data.get("message", "No message")
        processed = {
            "original": message,
            "processed": f"Processed: {message.upper()}",
            "timestamp": time.time(),
            "status": "success",
        }
        return processed

    # Transform node that processes input
    transform = TransformNode(
        name="process",
        description="Process the input message",
        func=process_message,
        dependencies={"input_data": Dependency(INPUT_NODE)},
    )

    # Terminate with the processed result
    terminate = TerminateNode(
        name="complete",
        description="Complete with processed result",
        return_status="SUCCESS",
        dependencies={"result": Dependency("process")},
    )

    return PolicyDefinition(
        nodes=[transform, terminate],
        config_variables=[],
        input_schema={"message": str},
    )


def demo_hatchet_workflow():
    """Demonstrate registering and running a workflow with Hatchet."""

    logger.info("🚀 Hatchet + Vulkan Integration Demo")
    logger.info("=" * 50)

    # Check token
    if not os.getenv("HATCHET_CLIENT_TOKEN"):
        logger.error("❌ HATCHET_CLIENT_TOKEN not found")
        logger.error("Please set your Hatchet token first")
        return False

    try:
        # 1. Create Vulkan Policy
        logger.info("📋 Creating Vulkan policy...")
        policy = create_demo_policy()
        logger.info(f"✅ Policy created with {len(policy.nodes)} nodes")

        # 2. Initialize Hatchet Runner
        logger.info("🔧 Initializing Hatchet runner...")
        runner = HatchetPolicyRunner.from_env(policy)
        logger.info("✅ HatchetPolicyRunner initialized")

        # 3. Test workflow creation
        logger.info("📝 Creating Hatchet workflow...")
        workflow = runner.workflow
        logger.info(f"✅ Workflow created: {workflow.name}")

        # 4. Prepare sample data
        sample_data = {"message": "Hello from Vulkan+Hatchet integration!"}
        logger.info(f"📤 Sample input: {sample_data}")

        # 5. Create workflow input
        workflow_input = runner._create_workflow_input(sample_data)
        logger.info("✅ Workflow input prepared")

        # 6. For actual execution, you would do:
        logger.info("🎯 To execute workflow:")
        logger.info("   result = runner.run(sample_data)")
        logger.info("   print(result.data)")

        logger.info("=" * 50)
        logger.info("🎉 Demo completed successfully!")
        logger.info("")
        logger.info("Your Hatchet integration is ready!")
        logger.info("You can now:")
        logger.info("• Create policies using Vulkan syntax")
        logger.info("• Register them as Hatchet workflows")
        logger.info("• Execute them remotely via Hatchet")
        logger.info("• Get results back through the runner")

        return True

    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def show_usage_examples():
    """Show code examples for using the integration."""

    logger.info("\n" + "=" * 50)
    logger.info("📚 USAGE EXAMPLES")
    logger.info("=" * 50)

    examples = """
# 1. Basic Usage
from vulkan.runners.hatchet import HatchetPolicyRunner
from vulkan.spec.policy import PolicyDefinition

runner = HatchetPolicyRunner.from_env(your_policy_definition)
result = runner.run({"message": "test data"})
print(result.data)

# 2. With Configuration Variables  
result = runner.run(
    input_data={"user_id": "123"},
    config_variables={"ENVIRONMENT": "production"}
)

# 3. Batch Processing
result = runner.run_batch(
    input_data_path="batch_data.csv", 
    config_variables={"BATCH_SIZE": "100"}
)

# 4. Custom Hatchet Configuration
runner = HatchetPolicyRunner(
    policy_definition=policy,
    hatchet_server_url="https://your-hatchet.com",
    hatchet_api_key="your-key", 
    namespace="production"
)
"""

    print(examples)


def main():
    """Main demo function."""

    success = demo_hatchet_workflow()

    if success:
        show_usage_examples()
    else:
        logger.error("Demo failed - check the errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
