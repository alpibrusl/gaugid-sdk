/**
 * GaugidMemoryBlock - LlamaIndex Memory Block implementation using Gaugid SDK
 *
 * This module provides a memory block implementation for LlamaIndex that uses
 * Gaugid profiles for long-term memory storage.
 */

import { GaugidClient } from "../client.js";
import { getLogger } from "../logger.js";

const logger = getLogger("integrations.llama_index");

/**
 * LlamaIndex BaseMemoryBlock interface (simplified).
 * In production, import from llama-index-core.
 */
export interface MemoryBlock {
  getContent(): Promise<string>;
  setContent(content: string): Promise<void>;
  getId(): string;
}

/**
 * LlamaIndex Memory Block implementation using Gaugid SDK.
 *
 * This block allows LlamaIndex to use Gaugid profiles for long-term memory storage.
 *
 * @example
 * ```typescript
 * import { VectorStoreIndex } from "llama-index";
 * import { GaugidMemoryBlock } from "@gaugid/sdk/integrations/llama_index";
 *
 * const memoryBlock = new GaugidMemoryBlock({
 *   connectionToken: "gaugid_conn_xxx",
 *   blockId: "user-memories"
 * });
 *
 * // Use with LlamaIndex
 * ```
 */
export class GaugidMemoryBlock implements MemoryBlock {
  private readonly client: GaugidClient;
  private readonly blockId: string;

  constructor(config: {
    connectionToken: string;
    blockId: string;
    apiUrl?: string;
    agentDid?: string;
  }) {
    this.client = new GaugidClient({
      connectionToken: config.connectionToken,
      apiUrl: config.apiUrl,
      agentDid: config.agentDid,
    });
    this.blockId = config.blockId;
  }

  /**
   * Get the content of the memory block.
   */
  async getContent(): Promise<string> {
    try {
      const profile = await this.client.getCurrentProfile({
        scopes: ["a2p:memories:llama-index"],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      const blockKey = `block:${this.blockId}`;

      const blockMemory = memories.find((m) => (m.key as string) === blockKey);
      if (!blockMemory) {
        return "";
      }

      return (blockMemory.content as string) || "";
    } catch (error) {
      logger.error(`Failed to get memory block content: ${error}`);
      throw error;
    }
  }

  /**
   * Set the content of the memory block.
   */
  async setContent(content: string): Promise<void> {
    try {
      const blockKey = `block:${this.blockId}`;

      await this.client.proposeMemoryToCurrent({
        content,
        category: "a2p:memories:llama-index",
        context: JSON.stringify({ key: blockKey, type: "llama-index-block" }),
      });
    } catch (error) {
      logger.error(`Failed to set memory block content: ${error}`);
      throw error;
    }
  }

  /**
   * Get the ID of the memory block.
   */
  getId(): string {
    return this.blockId;
  }
}
