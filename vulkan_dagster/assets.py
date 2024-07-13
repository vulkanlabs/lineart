from vulkan_dagster.policy import demo_policy

# Should include all user policies to be loaded.
# In the future we may want to scan the user code for policy definitions
# and automatically load them into this asset.
policies = [demo_policy]
