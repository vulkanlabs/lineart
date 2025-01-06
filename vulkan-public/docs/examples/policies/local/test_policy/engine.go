package main

import "context"

type VulkanEngine interface {
	// Run a single instance of the workflow
	CreateRun(ctx context.Context, data []byte) ([]byte, error)

	// Run multiple instances of the workflow using Beam
	CreateBacktest(ctx context.Context, data []byte) ([]byte, error)
}

// Local implementation of the engine, intended to be run by the user on their local machine
type LocalVulkanEngine struct {
}

func (e *LocalVulkanEngine) CreateRun(ctx context.Context, data []byte) ([]byte, error) {
	return nil, nil
}

func (e *LocalVulkanEngine) CreateBacktest(ctx context.Context, data []byte) ([]byte, error) {
	return nil, nil
}

// Remote implementation of the engine, intended to be run by Vulkan in a scalable infra
type RemoteVulkanEngine struct {
}

func (e *RemoteVulkanEngine) CreateRun(ctx context.Context, data []byte) ([]byte, error) {
	return nil, nil
}

func (e *RemoteVulkanEngine) CreateBacktest(ctx context.Context, data []byte) ([]byte, error) {
	return nil, nil
}
