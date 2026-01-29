/**
 * GaugidClient - High-level client for Gaugid service integration.
 *
 * This client provides a simplified interface for working with Gaugid profiles and memories.
 */

import { GaugidStorage } from "./storage.js";
import { GaugidError, GaugidAPIError, GaugidConnectionError, parseGaugidError, type OAuthTokenResponse } from "./types.js";
import { generateAgentDid, validateGaugidDid } from "./utils.js";
import { getLogger } from "./logger.js";

const logger = getLogger("client");

export interface GaugidClientConfig {
  connectionToken: string;
  apiUrl?: string;
  agentDid?: string;
  namespace?: string;
  timeout?: number;
}

/**
 * High-level client for interacting with Gaugid service.
 *
 * @example
 * ```typescript
 * // Basic usage (manual DID)
 * const client = new GaugidClient({
 *   connectionToken: "gaugid_conn_xxx"
 * });
 * const profile = await client.getProfile({
 *   userDid: "did:a2p:user:gaugid:alice",
 *   scopes: ["a2p:preferences", "a2p:interests"]
 * });
 *
 * // User-friendly usage (from OAuth)
 * const flow = new OAuthFlow({...});
 * const tokenResponse = await flow.exchangeCode(code, state);
 *
 * // Create client with user account info
 * const client = GaugidClient.fromOAuthResponse(tokenResponse);
 *
 * // List and select profile
 * const profiles = await client.listProfiles();
 * if (profiles.length > 0) {
 *   client.selectProfile(profiles[0].did);
 * }
 *
 * // Use selected profile (no DID needed!)
 * const profile = await client.getCurrentProfile({
 *   scopes: ["a2p:preferences"]
 * });
 * ```
 */
export class GaugidClient {
  public readonly storage: GaugidStorage;
  public readonly connectionToken: string;

  private _userDid?: string;
  private _availableProfiles: Array<Record<string, unknown>> = [];
  private _selectedProfileDid?: string;

  constructor(config: GaugidClientConfig) {
    // Validate agent_did if provided
    let agentDid = config.agentDid;
    if (agentDid) {
      const [isValid, error] = validateGaugidDid(agentDid);
      if (!isValid) {
        throw new Error(`Invalid agent DID: ${error}`);
      }
    } else {
      // Generate default agent DID with namespace
      agentDid = generateAgentDid("default", config.namespace);
    }

    // Create GaugidStorage with connection token
    this.storage = new GaugidStorage({
      connectionToken: config.connectionToken,
      apiUrl: config.apiUrl,
      agentDid,
      timeout: config.timeout ? config.timeout * 1000 : undefined,
    });

    this.connectionToken = config.connectionToken;
  }

  /**
   * Create a GaugidClient from an OAuth token response.
   */
  static fromOAuthResponse(
    oauthResponse: OAuthTokenResponse,
    config?: Omit<GaugidClientConfig, "connectionToken">
  ): GaugidClient {
    const client = new GaugidClient({
      connectionToken: oauthResponse.access_token,
      ...config,
    });

    // Set user account information from OAuth response
    client._userDid = oauthResponse.user_did;
    client._availableProfiles = (oauthResponse.profiles || []) as Array<Record<string, unknown>>;

    // Auto-select if only one profile
    if (client._availableProfiles.length === 1) {
      const profileDid = client._availableProfiles[0]?.did as string | undefined;
      if (profileDid) {
        client._selectedProfileDid = profileDid;
      }
    }

    return client;
  }

  /**
   * Get a user's profile with the specified scopes.
   *
   * Supports both DID mode and connection token mode:
   * - DID mode: Provide userDid to get a specific profile
   * - Connection token mode: Omit userDid to get profile from token context
   */
  async getProfile(options?: {
    userDid?: string;
    scopes?: string[];
    subProfile?: string;
  }): Promise<Record<string, unknown>> {
    const { userDid, scopes = [], subProfile } = options || {};

    // Connection token mode: no DID required
    if (!userDid) {
      const url = new URL(`${this.storage.apiUrl}/a2p/v1/profile`);
      if (scopes.length > 0) {
        url.searchParams.set("scopes", scopes.join(","));
      }

      try {
        const response = await fetch(url.toString(), {
          method: "GET",
          headers: {
            Authorization: `Bearer ${this.connectionToken}`,
          },
          signal: AbortSignal.timeout(this.storage.timeout),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw parseGaugidError(response, errorData);
        }

        const data = await response.json();
        if (!data.success) {
          throw parseGaugidError(response, data);
        }

        return (data.data || {}) as Record<string, unknown>;
      } catch (error) {
        if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
          throw error;
        }
        if (error instanceof Error && error.name === "TimeoutError") {
          throw new GaugidConnectionError(
            `Request timeout after ${this.storage.timeout}ms`,
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

    // DID mode: validate and use storage
    const [isValid, error] = validateGaugidDid(userDid);
    if (!isValid) {
      throw new Error(`Invalid user DID: ${error}`);
    }

    try {
      const profile = await this.storage.get(userDid, scopes);
      if (!profile) {
        throw new GaugidAPIError("Profile not found", "A2P003", 404);
      }
      return profile;
    } catch (err) {
      if (err instanceof GaugidError) {
        throw err;
      }
      throw new GaugidError(`Failed to get profile: ${err}`);
    }
  }

  /**
   * Request access to additional scopes.
   */
  async requestAccess(options: {
    scopes: string[];
    userDid?: string;
    subProfile?: string;
    purpose?: {
      type?: string;
      description?: string;
      legalBasis?: string;
    };
  }): Promise<Record<string, unknown>> {
    const { scopes, userDid, subProfile, purpose } = options;

    // Connection token mode: no DID required
    if (!userDid) {
      const url = `${this.storage.apiUrl}/a2p/v1/profile/access`;

      const payload: Record<string, unknown> = { scopes };
      if (purpose) {
        payload.purpose = purpose;
      }

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this.connectionToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(this.storage.timeout),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw parseGaugidError(response, errorData);
        }

        const data = await response.json();
        if (!data.success) {
          throw parseGaugidError(response, data);
        }

        return (data.data || {}) as Record<string, unknown>;
      } catch (error) {
        if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
          throw error;
        }
        if (error instanceof Error && error.name === "TimeoutError") {
          throw new GaugidConnectionError(
            `Request timeout after ${this.storage.timeout}ms`,
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

    // DID mode: validate and use storage
    const [isValid, error] = validateGaugidDid(userDid);
    if (!isValid) {
      throw new Error(`Invalid user DID: ${error}`);
    }

    // Note: This would require A2P client integration
    throw new Error("DID mode request_access not yet implemented");
  }

  /**
   * Check if agent has a specific permission for a user.
   */
  async checkPermission(options: {
    userDid: string;
    permission: string;
    scope?: string;
  }): Promise<boolean> {
    const { userDid, permission, scope } = options;

    // Validate user DID format
    const [isValid, error] = validateGaugidDid(userDid);
    if (!isValid) {
      throw new Error(`Invalid user DID: ${error}`);
    }

    try {
      // Note: This would require A2P client integration
      // For now, we'll make a direct API call
      const url = new URL(
        `${this.storage.apiUrl}/a2p/v1/profile/${userDid}/permissions/check`
      );
      url.searchParams.set("permission", permission);
      if (scope) {
        url.searchParams.set("scope", scope);
      }

      const response = await fetch(url.toString(), {
        method: "GET",
        headers: {
          Authorization: `Bearer ${this.connectionToken}`,
        },
        signal: AbortSignal.timeout(this.storage.timeout),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }

      const data = await response.json();
      if (!data.success) {
        throw parseGaugidError(response, data);
      }

      return (data.data?.granted as boolean) ?? false;
    } catch (error) {
      if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
        throw error;
      }
      if (error instanceof Error && error.name === "TimeoutError") {
        throw new GaugidConnectionError(
          `Request timeout after ${this.storage.timeout}ms`,
          undefined,
          error
        );
      }
      throw new GaugidError(`Failed to check permission: ${error}`);
    }
  }

  /**
   * Propose a new memory to a user's profile.
   */
  async proposeMemory(options: {
    content: string;
    userDid?: string;
    category?: string;
    memoryType?: string;
    confidence?: number;
    context?: string;
  }): Promise<Record<string, unknown>> {
    const { content, userDid, category, memoryType, confidence, context } = options;

    // Connection token mode: no DID required
    if (!userDid) {
      const url = `${this.storage.apiUrl}/a2p/v1/profile/memories/propose`;

      const payload: Record<string, unknown> = {
        content,
        confidence: confidence ?? 0.7,
      };
      if (category) payload.category = category;
      if (memoryType) payload.memory_type = memoryType;
      if (context) payload.context = context;

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${this.connectionToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
          signal: AbortSignal.timeout(this.storage.timeout),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw parseGaugidError(response, errorData);
        }

        const data = await response.json();
        if (!data.success) {
          throw parseGaugidError(response, data);
        }

        return (data.data || {}) as Record<string, unknown>;
      } catch (error) {
        if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
          throw error;
        }
        if (error instanceof Error && error.name === "TimeoutError") {
          throw new GaugidConnectionError(
            `Request timeout after ${this.storage.timeout}ms`,
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

    // DID mode: validate and use storage
    const [isValid, error] = validateGaugidDid(userDid);
    if (!isValid) {
      throw new Error(`Invalid user DID: ${error}`);
    }

    return await this.storage.proposeMemory(userDid, content, {
      category,
      memoryType,
      confidence,
      context,
    });
  }

  /**
   * List available profiles for the authenticated user.
   */
  async listProfiles(): Promise<Array<Record<string, unknown>>> {
    // If we have profiles from OAuth, return them
    if (this._availableProfiles.length > 0) {
      return this._availableProfiles;
    }

    // Otherwise, if we have user_did, return it as the only profile
    if (this._userDid) {
      return [{ did: this._userDid, type: "user" }];
    }

    // No profiles available
    return [];
  }

  /**
   * Select a profile to use for subsequent operations.
   */
  selectProfile(profileDid: string): void {
    // Validate DID format
    const [isValid, error] = validateGaugidDid(profileDid);
    if (!isValid) {
      throw new Error(`Invalid profile DID: ${error}`);
    }

    // Check if profile is available
    const availableDids = this._availableProfiles
      .map((p) => p.did as string | undefined)
      .filter((did): did is string => !!did);
    if (this._userDid) {
      availableDids.push(this._userDid);
    }

    if (!availableDids.includes(profileDid)) {
      throw new Error(
        `Profile ${profileDid} is not available. Available profiles: ${availableDids.join(", ")}`
      );
    }

    this._selectedProfileDid = profileDid;
  }

  /**
   * Get the currently selected profile DID.
   */
  getCurrentProfileDid(): string | undefined {
    return this._selectedProfileDid || this._userDid;
  }

  /**
   * Get the currently selected profile.
   */
  async getCurrentProfile(options: {
    scopes: string[];
    subProfile?: string;
  }): Promise<Record<string, unknown>> {
    const profileDid = this.getCurrentProfileDid();

    // If no profile selected, use connection token mode (no DID)
    if (!profileDid) {
      return await this.getProfile({
        scopes: options.scopes,
        subProfile: options.subProfile,
      });
    }

    return await this.getProfile({
      userDid: profileDid,
      scopes: options.scopes,
      subProfile: options.subProfile,
    });
  }

  /**
   * Propose a memory to the currently selected profile.
   */
  async proposeMemoryToCurrent(options: {
    content: string;
    category?: string;
    memoryType?: string;
    confidence?: number;
    context?: string;
  }): Promise<Record<string, unknown>> {
    const profileDid = this.getCurrentProfileDid();

    // If no profile selected, use connection token mode (no DID)
    if (!profileDid) {
      return await this.proposeMemory({
        content: options.content,
        category: options.category,
        memoryType: options.memoryType,
        confidence: options.confidence,
        context: options.context,
      });
    }

    return await this.proposeMemory({
      content: options.content,
      userDid: profileDid,
      category: options.category,
      memoryType: options.memoryType,
      confidence: options.confidence,
      context: options.context,
    });
  }

  /**
   * Resolve a DID to its DID document (protocol-compliant).
   */
  async resolveDid(did: string): Promise<Record<string, unknown>> {
    // Validate DID format
    const [isValid, error] = validateGaugidDid(did);
    if (!isValid) {
      throw new Error(`Invalid DID: ${error}`);
    }

    // DID resolution is a public endpoint (no auth required)
    const url = `${this.storage.apiUrl}/a2p/v1/did/${did}`;

    try {
      const response = await fetch(url, {
        method: "GET",
        signal: AbortSignal.timeout(this.storage.timeout),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }

      const data = await response.json();
      if (!data.success) {
        throw new GaugidAPIError(
          (data.error?.message as string) || "DID resolution failed",
          data.error?.code as string | undefined,
          response.status
        );
      }

      return (data.data || {}) as Record<string, unknown>;
    } catch (error) {
      if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
        throw error;
      }
      if (error instanceof Error && error.name === "TimeoutError") {
        throw new GaugidConnectionError(
          `Request timeout after ${this.storage.timeout}ms`,
          undefined,
          error
        );
      }
      throw new GaugidConnectionError(
        `Failed to resolve DID: ${error}`,
        undefined,
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Register an agent with Gaugid (protocol-compliant).
   */
  async registerAgent(options: {
    agentDid: string;
    name: string;
    description?: string;
    ownerEmail?: string;
    publicKey?: string;
    generateKeys?: boolean;
  }): Promise<Record<string, unknown>> {
    const { agentDid, name, description, ownerEmail, publicKey, generateKeys } = options;

    // Validate agent DID format
    const [isValid, error] = validateGaugidDid(agentDid);
    if (!isValid) {
      throw new Error(`Invalid agent DID: ${error}`);
    }

    // Build request payload
    const payload: Record<string, unknown> = {
      did: agentDid,
      name,
      keyType: "Ed25519",
      generateKeys: generateKeys ?? false,
    };

    if (description) payload.description = description;
    if (ownerEmail) payload.ownerEmail = ownerEmail;
    if (publicKey) payload.publicKey = publicKey;

    // Use protocol-compliant endpoint
    const url = `${this.storage.apiUrl}/a2p/v1/agents/register`;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${this.connectionToken}`,
        },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(this.storage.timeout),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }

      const data = await response.json();
      if (!data.success) {
        throw new GaugidAPIError(
          (data.error?.message as string) || "Agent registration failed",
          data.error?.code as string | undefined,
          response.status
        );
      }

      return (data.data || {}) as Record<string, unknown>;
    } catch (error) {
      if (error instanceof GaugidAPIError || error instanceof GaugidConnectionError) {
        throw error;
      }
      if (error instanceof Error && error.name === "TimeoutError") {
        throw new GaugidConnectionError(
          `Request timeout after ${this.storage.timeout}ms`,
          undefined,
          error
        );
      }
      throw new GaugidConnectionError(
        `Failed to register agent: ${error}`,
        undefined,
        error instanceof Error ? error : new Error(String(error))
      );
    }
  }

  /**
   * Close the client and cleanup resources.
   */
  async close(): Promise<void> {
    await this.storage.close();
  }
}
