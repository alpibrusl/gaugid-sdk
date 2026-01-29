/**
 * GaugidSession - OpenAI Agents SDK Session implementation using Gaugid SDK
 *
 * This module provides a Session implementation for OpenAI Agents SDK that uses
 * Gaugid profiles for conversation history management.
 */

import { GaugidClient } from "../client.js";
import { getLogger } from "../logger.js";

const logger = getLogger("integrations.openai");

/**
 * OpenAI Agents SDK Session interface (simplified).
 * In production, import from @openai/agents.
 */
export interface Session {
  getMessages(): Promise<Message[]>;
  addMessage(message: Message): Promise<void>;
  clear(): Promise<void>;
}

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
}

/**
 * OpenAI Agents SDK Session implementation using Gaugid SDK.
 *
 * This session allows OpenAI Agents to use Gaugid profiles for conversation history.
 *
 * @example
 * ```typescript
 * import { Agent } from "@openai/agents";
 * import { GaugidSession } from "@gaugid/sdk/integrations/openai";
 *
 * const session = new GaugidSession({
 *   connectionToken: "gaugid_conn_xxx"
 * });
 *
 * const agent = new Agent({
 *   session,
 *   // ... other config
 * });
 * ```
 */
export class GaugidSession implements Session {
  private readonly client: GaugidClient;
  private readonly sessionId: string;

  constructor(config: {
    connectionToken: string;
    sessionId?: string;
    apiUrl?: string;
    agentDid?: string;
  }) {
    this.client = new GaugidClient({
      connectionToken: config.connectionToken,
      apiUrl: config.apiUrl,
      agentDid: config.agentDid,
    });
    this.sessionId = config.sessionId || "default";
  }

  /**
   * Get all messages in the session.
   */
  async getMessages(): Promise<Message[]> {
    try {
      const profile = await this.client.getCurrentProfile({
        scopes: ["a2p:memories:openai-session"],
      });

      const memories = (profile.memories as Array<Record<string, unknown>>) || [];
      const sessionKey = `session:${this.sessionId}:messages`;

      const sessionMemory = memories.find((m) => (m.key as string) === sessionKey);
      if (!sessionMemory) {
        return [];
      }

      try {
        const messages = JSON.parse(sessionMemory.content as string) as Message[];
        return messages;
      } catch {
        return [];
      }
    } catch (error) {
      logger.error(`Failed to get messages: ${error}`);
      throw error;
    }
  }

  /**
   * Add a message to the session.
   */
  async addMessage(message: Message): Promise<void> {
    try {
      const messages = await this.getMessages();
      messages.push({
        ...message,
        timestamp: message.timestamp || Date.now(),
      });

      const sessionKey = `session:${this.sessionId}:messages`;
      const content = JSON.stringify(messages);

      await this.client.proposeMemoryToCurrent({
        content,
        category: "a2p:memories:openai-session",
        context: JSON.stringify({ key: sessionKey, type: "openai-session" }),
      });
    } catch (error) {
      logger.error(`Failed to add message: ${error}`);
      throw error;
    }
  }

  /**
   * Clear all messages in the session.
   */
  async clear(): Promise<void> {
    try {
      const sessionKey = `session:${this.sessionId}:messages`;
      await this.client.proposeMemoryToCurrent({
        content: "[]",
        category: "a2p:memories:openai-session",
        context: JSON.stringify({ key: sessionKey, type: "openai-session" }),
      });
    } catch (error) {
      logger.error(`Failed to clear session: ${error}`);
      throw error;
    }
  }
}
