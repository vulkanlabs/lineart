# Vulkan Imaegs

This folder holds the code for Vulkan images.

## What each image has

* **Application Server (`app`)**: This is the main backend app.
    * Image: `ghcr.io/vulkanlabs/app`
* **Dagster Orchestrator (`dagster`)**: Dagster-based runner. Used in runs via the API.
    * Image: `ghcr.io/vulkanlabs/dagster`
* **Dagster Database (`dagster-db`)**: PostgresQL database for dagster.
    * Image: `ghcr.io/vulkanlabs/dagster-db`

## How are the images built?

We use a GitHub Actions workflow to build and publish images. 
You can check it out right here: `.github/workflows/docker-build.yaml`

This workflow runs when:
    - We push stuff to the main branch.
    - We push a Git tag that looks like v*.*.* (think v1.0.0 or v1.1.0).
    - Someone manually starts it from the GitHub Actions page.

## How We Tag Images

We like to keep our image tags straightforward:

* `latest`: Newest build from our main branch.
* `vX.Y.Z`: Git tag for a specific version (e.g., `v1.0.0`, `v1.2.3`)
* `sha-<commit_hash>`: Specific version tied to a Git commit.

## Using the images

### Pulling Images from GHCR

To grab the `latest` version of an image:

```bash
docker pull ghcr.io/vulkanlabs/app:latest
docker pull ghcr.io/vulkanlabs/app:v1.0.0
docker pull ghcr.io/vulkanlabs/app:sha-<commit_hash>
# And you get the idea for the others!
```
