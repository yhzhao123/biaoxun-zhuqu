/**
 * Tests for deer-flow Gateway API client
 * TDD Cycle 18 - Phase 1: RED - Tests that describe expected behavior
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { deerFlowApi, type GatewayHealthResponse, type ModelInfo, type SkillInfo, type McpServerConfig, type ThreadRunRequest, type ThreadRunResponse } from '../services/deerFlowApi';

// Use vi.hoisted to define mocks before vi.mock is evaluated
const { mockGet, mockPost, mockPut, mockDelete } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockPut: vi.fn(),
  mockDelete: vi.fn(),
}));

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: mockGet,
      post: mockPost,
      put: mockPut,
      delete: mockDelete,
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    })),
  },
}));

describe('deerFlowApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('healthCheck', () => {
    it('should return health status when gateway is healthy', async () => {
      const mockResponse: GatewayHealthResponse = { status: 'healthy', service: 'deer-flow-gateway' };
      mockGet.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.healthCheck();

      expect(result).toEqual(mockResponse);
      expect(mockGet).toHaveBeenCalledWith('/health');
    });

    it('should throw error when health check fails', async () => {
      mockGet.mockRejectedValue(new Error('Network error'));

      await expect(deerFlowApi.healthCheck()).rejects.toThrow('Network error');
    });
  });

  describe('getModels', () => {
    it('should return list of models', async () => {
      const mockResponse = {
        models: [
          {
            name: 'gpt-4',
            model: 'gpt-4',
            display_name: 'GPT-4',
            description: 'OpenAI GPT-4 model',
            supports_thinking: false,
            supports_reasoning_effort: false,
          },
        ],
      };
      mockGet.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.getModels();

      expect(result).toEqual(mockResponse.models);
      expect(mockGet).toHaveBeenCalledWith('/api/models');
    });

    it('should return empty array when no models', async () => {
      mockGet.mockResolvedValue({ data: { models: [] } });

      const result = await deerFlowApi.getModels();

      expect(result).toEqual([]);
    });

    it('should throw error when request fails', async () => {
      mockGet.mockRejectedValue(new Error('Request failed'));

      await expect(deerFlowApi.getModels()).rejects.toThrow('Request failed');
    });
  });

  describe('getModel', () => {
    it('should return model details by name', async () => {
      const mockResponse: ModelInfo = {
        name: 'gpt-4',
        model: 'gpt-4',
        display_name: 'GPT-4',
        description: 'OpenAI GPT-4 model',
        supports_thinking: false,
        supports_reasoning_effort: false,
      };
      mockGet.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.getModel('gpt-4');

      expect(result).toEqual(mockResponse);
      expect(mockGet).toHaveBeenCalledWith('/api/models/gpt-4');
    });

    it('should throw 404 error when model not found', async () => {
      const error = { response: { status: 404, data: { detail: "Model 'unknown' not found" } } };
      mockGet.mockRejectedValue(error);

      await expect(deerFlowApi.getModel('unknown')).rejects.toEqual(error);
    });
  });

  describe('getMcpConfig', () => {
    it('should return MCP configuration', async () => {
      const mockResponse = {
        mcp_servers: {
          github: {
            enabled: true,
            type: 'stdio',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-github'],
            env: { GITHUB_TOKEN: 'ghp_xxx' },
            url: null,
            headers: {},
            oauth: null,
            description: 'GitHub MCP server',
          },
        },
      };
      mockGet.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.getMcpConfig();

      expect(result).toEqual(mockResponse.mcp_servers);
      expect(mockGet).toHaveBeenCalledWith('/api/mcp/config');
    });

    it('should return empty object when no MCP servers', async () => {
      mockGet.mockResolvedValue({ data: { mcp_servers: {} } });

      const result = await deerFlowApi.getMcpConfig();

      expect(result).toEqual({});
    });
  });

  describe('updateMcpConfig', () => {
    it('should update MCP configuration', async () => {
      const mockConfig: Record<string, McpServerConfig> = {
        github: {
          enabled: true,
          type: 'stdio',
          command: 'npx',
          args: ['-y', '@modelcontextprotocol/server-github'],
          env: {},
          url: null,
          headers: {},
          oauth: null,
          description: 'GitHub MCP server',
        },
      };
      const mockResponse = { mcp_servers: mockConfig };
      mockPut.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.updateMcpConfig(mockConfig);

      expect(result).toEqual(mockConfig);
      expect(mockPut).toHaveBeenCalledWith('/api/mcp/config', { mcp_servers: mockConfig });
    });
  });

  describe('getSkills', () => {
    it('should return list of skills', async () => {
      const mockResponse = {
        skills: [
          {
            name: 'tender-extraction',
            description: 'Extract tender information from documents',
            license: 'MIT',
            category: 'public',
            enabled: true,
          },
        ],
      };
      mockGet.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.getSkills();

      expect(result).toEqual(mockResponse.skills);
      expect(mockGet).toHaveBeenCalledWith('/api/skills');
    });

    it('should return empty array when no skills', async () => {
      mockGet.mockResolvedValue({ data: { skills: [] } });

      const result = await deerFlowApi.getSkills();

      expect(result).toEqual([]);
    });
  });

  describe('getSkill', () => {
    it('should return skill details by name', async () => {
      const mockResponse: SkillInfo = {
        name: 'tender-extraction',
        description: 'Extract tender information from documents',
        license: 'MIT',
        category: 'public',
        enabled: true,
      };
      mockGet.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.getSkill('tender-extraction');

      expect(result).toEqual(mockResponse);
      expect(mockGet).toHaveBeenCalledWith('/api/skills/tender-extraction');
    });

    it('should throw 404 error when skill not found', async () => {
      const error = { response: { status: 404, data: { detail: "Skill 'unknown' not found" } } };
      mockGet.mockRejectedValue(error);

      await expect(deerFlowApi.getSkill('unknown')).rejects.toEqual(error);
    });
  });

  describe('updateSkill', () => {
    it('should update skill enabled status', async () => {
      const mockResponse: SkillInfo = {
        name: 'tender-extraction',
        description: 'Extract tender information from documents',
        license: 'MIT',
        category: 'public',
        enabled: false,
      };
      mockPut.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.updateSkill('tender-extraction', false);

      expect(result).toEqual(mockResponse);
      expect(mockPut).toHaveBeenCalledWith('/api/skills/tender-extraction', { enabled: false });
    });
  });

  describe('installSkill', () => {
    it('should install skill from archive', async () => {
      const mockResponse = {
        success: true,
        skill_name: 'new-skill',
        message: 'Skill installed successfully',
      };
      mockPost.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.installSkill('thread-123', '/mnt/user-data/outputs/new-skill.skill');

      expect(result).toEqual(mockResponse);
      expect(mockPost).toHaveBeenCalledWith('/api/skills/install', {
        thread_id: 'thread-123',
        path: '/mnt/user-data/outputs/new-skill.skill',
      });
    });

    it('should throw error when skill already exists', async () => {
      const error = { response: { status: 409, data: { detail: 'Skill already exists' } } };
      mockPost.mockRejectedValue(error);

      await expect(deerFlowApi.installSkill('thread-123', '/path')).rejects.toEqual(error);
    });
  });

  describe('runThread', () => {
    it('should execute agent run with message', async () => {
      const request: ThreadRunRequest = {
        message: 'Extract tender information from the PDF',
      };
      const mockResponse = {
        thread_id: 'thread-123',
        run_id: 'run-456',
      };
      mockPost.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.runThread('thread-123', request);

      expect(result).toEqual(mockResponse);
      expect(mockPost).toHaveBeenCalledWith('/api/threads/thread-123/runs', request);
    });

    it('should include config in request when provided', async () => {
      const request: ThreadRunRequest = {
        message: 'Test message',
        config: {
          configurable: {
            model_name: 'gpt-4',
            thinking_enabled: true,
          },
        },
      };
      const mockResponse = {
        thread_id: 'thread-123',
        run_id: 'run-456',
      };
      mockPost.mockResolvedValue({ data: mockResponse });

      const result = await deerFlowApi.runThread('thread-123', request);

      expect(result).toEqual(mockResponse);
      expect(mockPost).toHaveBeenCalledWith('/api/threads/thread-123/runs', request);
    });
  });
});

describe('Type definitions', () => {
  it('should have correct GatewayHealthResponse type', () => {
    const health: GatewayHealthResponse = {
      status: 'healthy',
      service: 'deer-flow-gateway',
    };
    expect(health.status).toBe('healthy');
    expect(health.service).toBe('deer-flow-gateway');
  });

  it('should have correct ModelInfo type', () => {
    const model: ModelInfo = {
      name: 'gpt-4',
      model: 'gpt-4',
      display_name: 'GPT-4',
      description: 'OpenAI model',
      supports_thinking: false,
      supports_reasoning_effort: false,
    };
    expect(model.name).toBe('gpt-4');
  });

  it('should have correct SkillInfo type', () => {
    const skill: SkillInfo = {
      name: 'test-skill',
      description: 'Test skill',
      license: 'MIT',
      category: 'public',
      enabled: true,
    };
    expect(skill.name).toBe('test-skill');
    expect(skill.enabled).toBe(true);
  });

  it('should have correct ThreadRunRequest type', () => {
    const request: ThreadRunRequest = {
      message: 'Hello',
    };
    expect(request.message).toBe('Hello');
  });

  it('should have correct ThreadRunResponse type', () => {
    const response: ThreadRunResponse = {
      thread_id: 'thread-1',
      run_id: 'run-1',
    };
    expect(response.thread_id).toBe('thread-1');
    expect(response.run_id).toBe('run-1');
  });
});