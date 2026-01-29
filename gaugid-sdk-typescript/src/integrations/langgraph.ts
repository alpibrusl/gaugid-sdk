/**
 * GaugidStore - LangGraph BaseStore implementation using Gaugid SDK
 *
 * This module provides a BaseStore implementation for LangGraph that uses
 * Gaugid profiles as the persistent key-value store.
 */

import { GaugidClient } from "../client.js";
import { getLogger } from "../logger.js";

const logger = getLogger("integrations.langgraph");

/**
 * LangGraph BaseStore interface (simplified).
 * In production, import from @langchain/langgraph.
 */
export interface BaseStore {
  get(namespace: string[], key: string): Promise<unknown>;
  put(namespace: string[], key: string, value: unknown): Promise<void>;
  delete(namespace: string[], key: string): Promise<void>;
  list(namespace: string[]): Promise<string[]>;
}

/**
 * LangGraph BaseStore implementation using Gaugid SDK.
 *
 * This store allows LangGraph agents to use Gaugid profiles as their
 * persistent key-value store.
 *
 * @example
 * ```typescript
 * import { StateGraph } from "@langchain/langgraph";
 * import { GaugidStore } from "@gaugid/sdk/integrations/langgraph";
 *
 * const store = new GaugidStore({
 *   connectionToken: "gaugid_conn_xxx",
 *   namespacePrefix: ["langgraph", "my-app"]
 * });
 *
 * const graph = new StateGraph(...);
 * const app = graph.compile({ checkpointer: store });
 * ```
 */
export class GaugidStore implements BaseStore {
  private readonly client: GaugidClient;
  private readonly namespacePrefix: string[];

  constructor(config: {
    connectionToken: string;
    namespacePrefix?: string[];
    apiUrl?: string;
    agentDid?: string;
  }) {
    this.client = new GaugidClient({
      connectionToken: config.connectionToken,
      apiUrl: config.apiUrl,
      agentDid: config.agentDid,
    });
    this.namespacePrefix = config.namespacePrefix || ["langgraph"];
  }

  /**
   * Get a value from the store.
   */
  async get(namespace: string[], key: string): Promise<unknown> {
    const fullNamespace = [...this.namespacePrefix, ...namespace];
    const category = fullNamespace.join(":");
    const memoryKey = `store:${category}:${key}`;

    try {
      const profile = await this.client.getCurrentProfile({
        scopes: [`a2p:memories:${category}`],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      const memory = memories.find((m) => (m.key as string) === memoryKey);

      if (!memory) {
        return undefined;
      }

      // Parse stored value
      try {
        return JSON.parse(memory.content as string);
      } catch {
        return memory.content;
      }
    } catch (error) {
      logger.error(`Failed to get value from store: ${error}`);
      throw error;
    }
  }

  /**
   * Put a value into the store.
   */
  async put(namespace: string[], key: string, value: unknown): Promise<void> {
    const fullNamespace = [...this.namespacePrefix, ...namespace];
    const category = fullNamespace.join(":");
    const memoryKey = `store:${category}:${key}`;

    try {
      const content = typeof value === "string" ? value : JSON.stringify(value);

      await this.client.proposeMemoryToCurrent({
        content,
        category: `a2p:memories:${category}`,
        context: JSON.stringify({ key: memoryKey, type: "langgraph-store" }),
      });
    } catch (error) {
      logger.error(`Failed to put value to store: ${error}`);
      throw error;
    }
  }

  /**
   * Delete a value from the store.
   */
  async delete(namespace: string[], key: string): Promise<void> {
    // Note: Gaugid doesn't support direct deletion of memories
    // This would require API support for memory deletion
    logger.warn("Memory deletion not yet supported by Gaugid API");
  }

  /**
   * List all keys in a namespace.
   */
  async list(namespace: string[]): Promise<string[]> {
    const fullNamespace = [...this.namespacePrefix, ...namespace];
    const category = fullNamespace.join(":");

    try {
      const profile = await this.client.getCurrentProfile({
        scopes: [`a2p:memories:${category}`],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      const prefix = `store:${category}:`;

      return memories
        .filter((m) => {
          const key = m.key as string | undefined;
          return key?.startsWith(prefix);
        })
        .map((m) => {
          const key = m.key as string;
          return key.substring(prefix.length);
        });
    } catch (error) {
      logger.error(`Failed to list keys from store: ${error}`);
      throw error;
    }
  }

  /**
   * Close the store and cleanup resources.
   */
  async close(): Promise<void> {
    await this.client.close();
  }
}
