/**
 * Gaugid-specific types and error classes.
 */

import { z } from "zod";

// Error codes from Gaugid API
export const ERROR_CODES: Record<string, string> = {
  A2P000: "Internal server error",
  A2P001: "Not authorized",
  A2P002: "Invalid public key format",
  A2P003: "Profile not found",
  A2P006: "Invalid request",
  A2P009: "User already exists",
  A2P013: "Authenticated DID must match",
  A2P014: "Service not found",
  A2P015: "Invalid redirect_uri",
  A2P016: "Invalid scopes",
  A2P017: "Invalid authorization code",
  A2P018: "Authorization code expired",
  A2P019: "Invalid or expired connection token",
  A2P020: "Connection has been revoked",
  A2P021: "Connection token required",
  A2P022: "Service DID mismatch",
  A2P023: "Rate limit exceeded",
  A2P024: "Export limit exceeded",
  A2P025: "Import limit exceeded",
  A2P026: "Data import completed with errors",
};

/**
 * Base exception for all Gaugid SDK errors.
 */
export class GaugidError extends Error {
  public readonly code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.name = "GaugidError";
    this.code = code;
    Object.setPrototypeOf(this, GaugidError.prototype);
  }
}

/**
 * Error raised when the Gaugid API returns an error response.
 */
export class GaugidAPIError extends GaugidError {
  public readonly statusCode?: number;
  public readonly response?: Record<string, unknown>;

  constructor(
    message: string,
    code?: string,
    statusCode?: number,
    response?: Record<string, unknown>
  ) {
    super(message, code);
    this.name = "GaugidAPIError";
    this.statusCode = statusCode;
    this.response = response;
    Object.setPrototypeOf(this, GaugidAPIError.prototype);
  }
}

/**
 * Error raised when authentication fails.
 */
export class GaugidAuthError extends GaugidError {
  constructor(message: string, code?: string) {
    super(message, code);
    this.name = "GaugidAuthError";
    Object.setPrototypeOf(this, GaugidAuthError.prototype);
  }
}

/**
 * Error raised when connection to Gaugid API fails.
 */
export class GaugidConnectionError extends GaugidError {
  public readonly originalError?: Error;

  constructor(message: string, code?: string, originalError?: Error) {
    super(message, code);
    this.name = "GaugidConnectionError";
    this.originalError = originalError;
    Object.setPrototypeOf(this, GaugidConnectionError.prototype);
  }
}

/**
 * Information about a connection token.
 */
export const ConnectionTokenInfoSchema = z.object({
  token: z.string(),
  expiresAt: z.number().optional(),
  scopes: z.array(z.string()).default([]),
  connectionId: z.string().optional(),
  userDid: z.string().optional(),
  profiles: z.array(z.record(z.unknown())).optional(),
});

export type ConnectionTokenInfo = z.infer<typeof ConnectionTokenInfoSchema>;

/**
 * Response from OAuth token exchange.
 */
export const OAuthTokenResponseSchema = z.object({
  access_token: z.string(),
  token_type: z.string().default("Bearer"),
  expires_in: z.number(),
  scope: z.string(),
  connection_id: z.string().optional(),
  user_did: z.string().optional(),
  profiles: z.array(z.record(z.unknown())).optional(),
});

export type OAuthTokenResponse = z.infer<typeof OAuthTokenResponseSchema>;

/**
 * Parse a Gaugid API error response into a GaugidAPIError.
 */
export function parseGaugidError(
  response: Response,
  errorData?: Record<string, unknown>
): GaugidAPIError {
  const errorObj = errorData?.error as Record<string, unknown> | undefined;
  let code: string | undefined;
  let message: string;

  if (errorObj && typeof errorObj === "object") {
    code = errorObj.code as string | undefined;
    message = (errorObj.message as string) || response.statusText || "Unknown error";
  } else {
    code = undefined;
    message = response.statusText || "Unknown error";
  }

  // Enhance message with error code description if available
  if (code && ERROR_CODES[code]) {
    const description = ERROR_CODES[code];
    if (!message.includes(description)) {
      message = `${message} (${description})`;
    }
  }

  // Map specific error codes to more specific exceptions
  if (code === "A2P001" || code === "A2P019" || code === "A2P020" || code === "A2P021") {
    // Authentication/authorization errors
    return new GaugidAuthError(message, code);
  }

  return new GaugidAPIError(message, code, response.status, errorData);
}
