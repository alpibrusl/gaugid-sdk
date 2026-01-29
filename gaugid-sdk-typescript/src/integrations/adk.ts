/**
 * GaugidMemoryService - Google ADK MemoryService implementation using Gaugid SDK
 *
 * This module provides a MemoryService implementation for Google ADK that uses
 * Gaugid profiles for memory management.
 */

import { GaugidClient } from "../client.js";
import { getLogger } from "../logger.js";

const logger = getLogger("integrations.adk");

/**
 * Google ADK MemoryService interface (simplified).
 * In production, import from @google-cloud/adk.
 */
export interface MemoryService {
  saveMemory(userId: string, memory: Memory): Promise<void>;
  getMemories(userId: string, query?: MemoryQuery): Promise<Memory[]>;
  deleteMemory(userId: string, memoryId: string): Promise<void>;
}

export interface Memory {
  id?: string;
  content: string;
  metadata?: Record<string, unknown>;
  timestamp?: number;
}

export interface MemoryQuery {
  limit?: number;
  offset?: number;
  filter?: Record<string, unknown>;
}

/**
 * Google ADK MemoryService implementation using Gaugid SDK.
 *
 * This service allows Google ADK agents to use Gaugid profiles for memory management.
 *
 * @example
 * ```typescript
 * import { Agent } from "@google-cloud/adk";
 * import { GaugidMemoryService } from "@gaugid/sdk/integrations/adk";
 *
 * const memoryService = new GaugidMemoryService({
 *   connectionToken: "gaugid_conn_xxx"
 * });
 *
 * const agent = new Agent({
 *   memoryService,
 *   // ... other config
 * });
 * ```
 */
export class GaugidMemoryService implements MemoryService {
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
   * Save a memory for a user.
   */
  async saveMemory(userId: string, memory: Memory): Promise<void> {
    try {
      await this.client.proposeMemory({
        content: memory.content,
        category: "a2p:memories:adk",
        context: JSON.stringify({
          id: memory.id,
          metadata: memory.metadata,
          timestamp: memory.timestamp,
        }),
      });
    } catch (error) {
      logger.error(`Failed to save memory: ${error}`);
      throw error;
    }
  }

  /**
   * Get memories for a user.
   */
  async getMemories(userId: string, query?: MemoryQuery): Promise<Memory[]> {
    try {
      const profile = await this.client.getProfile({
        userDid: userId,
        scopes: ["a2p:memories:adk"],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      let results = memories.map((m) => ({
        id: m.id as string | undefined,
        content: m.content as string,
        metadata: m.metadata as Record<string, unknown> | undefined,
        timestamp: m.timestamp as number | undefined,
      }));

      // Apply query filters
      if (query?.filter) {
        results = results.filter((m) => {
          for (const [key, value] of Object.entries(query.filter!)) {
            if (m.metadata?.[key] !== value) {
              return false;
            }
          }
          return true;
        });
      }

      // Apply pagination
      if (query?.offset) {
        results = results.slice(query.offset);
      }
      if (query?.limit) {
        results = results.slice(0, query.limit);
      }

      return results;
    } catch (error) {
      logger.error(`Failed to get memories: ${error}`);
      throw error;
    }
  }

  /**
   * Delete a memory for a user.
   */
  async deleteMemory(userId: string, memoryId: string): Promise<void> {
    // Note: Gaugid doesn't support direct deletion of memories
    // This would require API support for memory deletion
    logger.warn("Memory deletion not yet supported by Gaugid API");
  }
}
