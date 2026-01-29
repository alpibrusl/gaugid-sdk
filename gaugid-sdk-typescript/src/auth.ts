/**
 * OAuth flow helpers for Gaugid service connections.
 *
 * This module provides utilities for implementing the OAuth 2.0 authorization
 * code flow for connecting services to Gaugid.
 */

import { randomBytes } from "crypto";
import { GaugidAPIError, GaugidAuthError, GaugidConnectionError, parseGaugidError, type OAuthTokenResponse, OAuthTokenResponseSchema } from "./types.js";
import { getLogger } from "./logger.js";

const logger = getLogger("auth");

export interface OAuthFlowConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  apiUrl?: string;
  timeout?: number;
}

/**
 * OAuth 2.0 authorization code flow helper for Gaugid.
 *
 * This class simplifies the OAuth flow for service connections:
 * 1. Generate authorization URL
 * 2. User authorizes and redirects back with code
 * 3. Exchange code for connection token
 *
 * @example
 * ```typescript
 * const flow = new OAuthFlow({
 *   clientId: "my-service",
 *   clientSecret: "secret",
 *   redirectUri: "https://myapp.com/callback",
 *   apiUrl: "https://api.gaugid.com"
 * });
 *
 * // Step 1: Get authorization URL
 * const { authUrl, state } = flow.getAuthorizationUrl({
 *   scopes: ["a2p:preferences", "a2p:interests"]
 * });
 *
 * // Step 2: User authorizes, redirects back with code
 * // Step 3: Exchange code for token
 * const tokenResponse = await flow.exchangeCode(code, state);
 * ```
 */
export class OAuthFlow {
  private readonly clientId: string;
  private readonly clientSecret: string;
  private readonly redirectUri: string;
  private readonly apiUrl: string;
  private readonly timeout: number;

  constructor(config: OAuthFlowConfig) {
    this.clientId = config.clientId;
    this.clientSecret = config.clientSecret;
    this.redirectUri = config.redirectUri;
    this.apiUrl = (config.apiUrl || "https://api.gaugid.com").replace(/\/$/, "");
    this.timeout = config.timeout || 30000;
  }

  /**
   * Generate authorization URL for OAuth flow.
   */
  getAuthorizationUrl(options: {
    scopes: string[];
    state?: string;
  }): { authUrl: string; state: string } {
    const state = options.state || randomBytes(32).toString("base64url");

    const params = new URLSearchParams({
      client_id: this.clientId,
      redirect_uri: this.redirectUri,
      response_type: "code",
      scope: options.scopes.join(","),
      state,
    });

    // Support both /connect/authorize and /api/connect/authorize for compatibility
    const authUrl = `${this.apiUrl}/connect/authorize?${params.toString()}`;
    return { authUrl, state };
  }

  /**
   * Parse authorization code from redirect URL.
   */
  parseAuthorizationResponse(redirectUrl: string, expectedState: string): string {
    const url = new URL(redirectUrl);
    const params = url.searchParams;

    // Check for errors
    const error = params.get("error");
    if (error) {
      const errorDescription = params.get("error_description") || "";
      throw new GaugidAuthError(`OAuth error: ${error} - ${errorDescription}`);
    }

    // Verify state
    const state = params.get("state");
    if (state !== expectedState) {
      throw new GaugidAuthError("State mismatch in OAuth callback");
    }

    // Get code
    const code = params.get("code");
    if (!code) {
      throw new GaugidAuthError("Authorization code not found in redirect URL");
    }

    return code;
  }

  /**
   * Exchange authorization code for connection token.
   */
  async exchangeCode(code: string, state?: string): Promise<OAuthTokenResponse> {
    // Support both /connect/token and /api/connect/token for compatibility
    const tokenUrl = `${this.apiUrl}/connect/token`;

    const payload = {
      grant_type: "authorization_code",
      code,
      client_id: this.clientId,
      client_secret: this.clientSecret,
      redirect_uri: this.redirectUri,
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(tokenUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.status === 401) {
        throw new GaugidAuthError("Invalid client credentials");
      }

      if (response.status === 400) {
        let message = "Token exchange failed";
        try {
          const errorData = await response.json();
          const errorObj = errorData.error;
          if (errorObj && typeof errorObj === "object") {
            message = (errorObj.message as string) || message;
          } else if (errorObj) {
            message = String(errorObj);
          }
        } catch {
          // Ignore JSON parse errors
        }
        throw new GaugidAuthError(message);
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }

      const data = await response.json();
      return OAuthTokenResponseSchema.parse(data);
    } catch (error) {
      if (error instanceof GaugidAuthError || error instanceof GaugidAPIError) {
        throw error;
      }
      if (error instanceof Error && error.name === "AbortError") {
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
   * Revoke a connection token.
   */
  async revokeToken(token: string): Promise<void> {
    // Support both /connect/revoke and /api/connect/revoke for compatibility
    const revokeUrl = `${this.apiUrl}/connect/revoke`;

    const payload = {
      token,
      client_id: this.clientId,
      client_secret: this.clientSecret,
    };

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(revokeUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.status === 401) {
        throw new GaugidAuthError("Invalid client credentials");
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw parseGaugidError(response, errorData);
      }
    } catch (error) {
      if (error instanceof GaugidAuthError || error instanceof GaugidAPIError) {
        throw error;
      }
      if (error instanceof Error && error.name === "AbortError") {
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
}
