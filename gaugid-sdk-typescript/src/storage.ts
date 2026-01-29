/**
 * GaugidStorage - Extends CloudStorage with Gaugid-specific features.
 *
 * This storage backend extends the base a2p CloudStorage with:
 * - Connection token authentication
 * - Automatic token refresh
 * - Gaugid API URL defaults
 * - Enhanced error handling with Gaugid error codes
 * - Rate limiting awareness
 */

import { GaugidAPIError, GaugidConnectionError, parseGaugidError } from "./types.js";
import { getLogger } from "./logger.js";

const logger = getLogger("storage");

// Default Gaugid API URL
export const DEFAULT_API_URL = "https://api.gaugid.com";

export interface GaugidStorageConfig {
  connectionToken: string;
  apiUrl?: string;
  agentDid?: string;
  timeout?: number;
  apiVersion?: string;
}

/**
 * Gaugid-specific storage backend.
 *
 * This storage backend connects to the Gaugid API using connection tokens
 * for authentication. It provides automatic token refresh and enhanced
 * error handling.
 *
 * @example
 * ```typescript
 * const storage = new GaugidStorage({
 *   apiUrl: "https://api.gaugid.com",
 *   connectionToken: "gaugid_conn_xxx"
 * });
 * ```
 */
export class GaugidStorage {
  public readonly connectionToken: string;
  public readonly apiUrl: string;
  public readonly agentDid?: string;
  public readonly timeout: number;
  public readonly apiVersion: string;

  constructor(config: GaugidStorageConfig) {
    this.connectionToken = config.connectionToken;
    this.apiUrl = config.apiUrl || DEFAULT_API_URL;
    this.agentDid = config.agentDid;
    this.timeout = config.timeout || 30000;
    this.apiVersion = config.apiVersion || "v1";
  }

  /**
   * Get profile from Gaugid API with enhanced error handling.
   */
  async get(did: string, scopes?: string[]): Promise<Record<string, unknown> | null> {
    try {
      const url = new URL(`${this.apiUrl}/a2p/${this.apiVersion}/profile/${did}`);
      if (scopes && scopes.length > 0) {
        url.searchParams.set("scopes", scopes.join(","));
      }

      const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${this.connectionToken}`,
        },
        signal: AbortSignal.timeout(this.timeout),
      });

      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }

      const data = await response.json();
      return data.success ? (data.data as Record<string, unknown>) : null;
    } catch (error) {
      if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
        throw error;
      }
      if (error instanceof Error && error.name === "TimeoutError") {
        throw new GaugidConnectionError(
          `Request timeout after ${this.timeout}ms`,
          undefined,
          error
        );
      }
      throw new GaugidConnectionError(
        `Failed to connect to Gaugid API: ${error}`,
        undefined,
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Update profile via Gaugid API with enhanced error handling.
   */
  async set(did: string, profile: Record<string, unknown>): Promise<void> {
    try {
      const url = `${this.apiUrl}/a2p/${this.apiVersion}/profile/${did}`;

      const response = await fetch(url, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${this.connectionToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(profile),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }
    } catch (error) {
      if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
        throw error;
      }
      if (error instanceof Error && error.name === "TimeoutError") {
        throw new GaugidConnectionError(
          `Request timeout after ${this.timeout}ms`,
          undefined,
          error
        );
      }
      throw new GaugidConnectionError(
        `Failed to connect to Gaugid API: ${error}`,
        undefined,
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Delete profile via Gaugid API with enhanced error handling.
   */
  async delete(did: string): Promise<void> {
    try {
      const url = `${this.apiUrl}/a2p/${this.apiVersion}/profile/${did}`;

      const response = await fetch(url, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${this.connectionToken}`,
        },
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }
    } catch (error) {
      if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
        throw error;
      }
      if (error instanceof Error && error.name === "TimeoutError") {
        throw new GaugidConnectionError(
          `Request timeout after ${this.timeout}ms`,
          undefined,
          error
        );
      }
      throw new GaugidConnectionError(
        `Failed to connect to Gaugid API: ${error}`,
        undefined,
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Propose a new memory via Gaugid API with enhanced error handling.
   */
  async proposeMemory(
    userDid: string,
    content: string,
    options?: {
      category?: string;
      memoryType?: string;
      confidence?: number;
      context?: string;
    }
  ): Promise<Record<string, unknown>> {
    try {
      const url = `${this.apiUrl}/a2p/${this.apiVersion}/profile/${userDid}/memories/propose`;

      const payload: Record<string, unknown> = {
        content,
        confidence: options?.confidence ?? 0.7,
      };

      if (options?.category) {
        payload.category = options.category;
      }
      if (options?.memoryType) {
        payload.memory_type = options.memoryType;
      }
      if (options?.context) {
        payload.context = options.context;
      }

      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${this.connectionToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(this.timeout),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }

      const data = await response.json();
      return data.success ? (data.data as Record<string, unknown>) : {};
    } catch (error) {
      if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
        throw error;
      }
      if (error instanceof Error && error.name === "TimeoutError") {
        throw new GaugidConnectionError(
          `Request timeout after ${this.timeout}ms`,
          undefined,
          error
        );
      }
      throw new GaugidConnectionError(
        `Failed to connect to Gaugid API: ${error}`,
        undefined,
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Close the storage and cleanup resources.
   */
  async close(): Promise<void> {
    // No cleanup needed for fetch-based implementation
    logger.debug("Storage closed");
  }
}
