/**
 * GaugidDb - Agno AsyncBaseDb implementation using Gaugid SDK
 *
 * This module provides a database implementation for Agno that uses
 * Gaugid profiles for memory management.
 */

import { GaugidClient } from "../client.js";
import { getLogger } from "../logger.js";

const logger = getLogger("integrations.agno");

/**
 * Agno AsyncBaseDb interface (simplified).
 * In production, import from agno.
 */
export interface AsyncBaseDb {
  get(key: string): Promise<unknown>;
  set(key: string, value: unknown): Promise<void>;
  delete(key: string): Promise<void>;
  list(prefix?: string): Promise<string[]>;
}

/**
 * Agno AsyncBaseDb implementation using Gaugid SDK.
 *
 * This database allows Agno to use Gaugid profiles for memory management.
 *
 * @example
 * ```typescript
 * import { MemoryManager } from "agno";
 * import { GaugidDb } from "@gaugid/sdk/integrations/agno";
 *
 * const db = new GaugidDb({
 *   connectionToken: "gaugid_conn_xxx"
 * });
 *
 * const memoryManager = new MemoryManager({ db });
 * ```
 */
export class GaugidDb implements AsyncBaseDb {
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
   * Get a value from the database.
   */
  async get(key: string): Promise<unknown> {
    try {
      const profile = await this.client.getCurrentProfile({
        scopes: ["a2p:memories:agno"],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      const dbKey = `db:${key}`;

      const memory = memories.find((m) => (m.key as string) === dbKey);
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
      logger.error(`Failed to get value from database: ${error}`);
      throw error;
    }
  }

  /**
   * Set a value in the database.
   */
  async set(key: string, value: unknown): Promise<void> {
    try {
      const dbKey = `db:${key}`;
      const content = typeof value === "string" ? value : JSON.stringify(value);

      await this.client.proposeMemoryToCurrent({
        content,
        category: "a2p:memories:agno",
        context: JSON.stringify({ key: dbKey, type: "agno-db" }),
      });
    } catch (error) {
      logger.error(`Failed to set value in database: ${error}`);
      throw error;
    }
  }

  /**
   * Delete a value from the database.
   */
  async delete(key: string): Promise<void> {
    // Note: Gaugid doesn't support direct deletion of memories
    logger.warn("Memory deletion not yet supported by Gaugid API");
  }

  /**
   * List all keys in the database (optionally filtered by prefix).
   */
  async list(prefix?: string): Promise<string[]> {
    try {
      const profile = await this.client.getCurrentProfile({
        scopes: ["a2p:memories:agno"],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      const dbPrefix = "db:";

      let keys = memories
        .filter((m) => {
          const key = m.key as string | undefined;
          return key?.startsWith(dbPrefix);
        })
        .map((m) => {
          const key = m.key as string;
          return key.substring(dbPrefix.length);
        });

      // Apply prefix filter if provided
      if (prefix) {
        keys = keys.filter((key) => key.startsWith(prefix));
      }

      return keys;
    } catch (error) {
      logger.error(`Failed to list keys from database: ${error}`);
      throw error;
    }
  }
}
