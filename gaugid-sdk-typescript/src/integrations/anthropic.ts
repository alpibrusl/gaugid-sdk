/**
 * GaugidMemoryTool - Anthropic Claude Memory Tool implementation using Gaugid SDK
 *
 * This module provides a memory tool backend for Anthropic's Claude memory tool.
 */

import { GaugidClient } from "../client.js";
import { getLogger } from "../logger.js";

const logger = getLogger("integrations.anthropic");

/**
 * Anthropic Memory Tool interface (simplified).
 * In production, import from @anthropic-ai/sdk.
 */
export interface MemoryTool {
  create(memory: Memory): Promise<Memory>;
  update(memoryId: string, memory: Partial<Memory>): Promise<Memory>;
  delete(memoryId: string): Promise<void>;
  search(query: string): Promise<Memory[]>;
}

export interface Memory {
  id: string;
  content: string;
  metadata?: Record<string, unknown>;
}

/**
 * Anthropic Claude Memory Tool implementation using Gaugid SDK.
 *
 * This tool allows Claude to use Gaugid profiles for persistent memory storage.
 *
 * @example
 * ```typescript
 * import { Anthropic } from "@anthropic-ai/sdk";
 * import { GaugidMemoryTool } from "@gaugid/sdk/integrations/anthropic";
 *
 * const memoryTool = new GaugidMemoryTool({
 *   connectionToken: "gaugid_conn_xxx"
 * });
 *
 * const client = new Anthropic({
 *   apiKey: process.env.ANTHROPIC_API_KEY,
 * });
 *
 * // Use memory tool with Claude
 * ```
 */
export class GaugidMemoryTool implements MemoryTool {
  private readonly client: GaugidClient;

  constructor(config: {
    connectionToken: string;
    apiUrl?: string;
    agentDid?: string;
  }) {
    this.client = new GaugidClient({
      connectionToken: config.connectionToken,
      apiUrl: config.apiUrl,
      agentDid: config.agentDid,
    });
  }

  /**
   * Create a new memory.
   */
  async create(memory: Memory): Promise<Memory> {
    try {
      await this.client.proposeMemoryToCurrent({
        content: memory.content,
        category: "a2p:memories:anthropic",
        context: JSON.stringify({
          id: memory.id,
          metadata: memory.metadata,
        }),
      });

      return memory;
    } catch (error) {
      logger.error(`Failed to create memory: ${error}`);
      throw error;
    }
  }

  /**
   * Update an existing memory.
   */
  async update(memoryId: string, memory: Partial<Memory>): Promise<Memory> {
    // Note: Gaugid doesn't support direct memory updates
    // This would require creating a new memory with updated content
    logger.warn("Memory updates not yet fully supported by Gaugid API");
    
    const existing = await this.get(memoryId);
    const updated: Memory = {
      ...existing,
      ...memory,
      id: memoryId,
    };

    return await this.create(updated);
  }

  /**
   * Delete a memory.
   */
  async delete(memoryId: string): Promise<void> {
    // Note: Gaugid doesn't support direct deletion of memories
    logger.warn("Memory deletion not yet supported by Gaugid API");
  }

  /**
   * Search for memories.
   */
  async search(query: string): Promise<Memory[]> {
    try {
      const profile = await this.client.getCurrentProfile({
        scopes: ["a2p:memories:anthropic"],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      
      // Simple text search in memory content
      const results = memories
        .filter((m) => {
          const content = (m.content as string) || "";
          return content.toLowerCase().includes(query.toLowerCase());
        })
        .map((m) => ({
          id: (m.id as string) || "",
          content: m.content as string,
          metadata: m.metadata as Record<string, unknown> | undefined,
        }));

      return results;
    } catch (error) {
      logger.error(`Failed to search memories: ${error}`);
      throw error;
    }
  }

  /**
   * Get a specific memory by ID.
   */
  private async get(memoryId: string): Promise<Memory> {
    const memories = await this.search("");
    const memory = memories.find((m) => m.id === memoryId);
    if (!memory) {
      throw new Error(`Memory not found: ${memoryId}`);
    }
    return memory;
  }
}
