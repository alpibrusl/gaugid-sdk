/**
 * Gaugid-specific utilities for DID generation and validation.
 *
 * This module provides helper functions for working with a2p DIDs.
 * Namespace must be explicitly provided - no default is set.
 */

/**
 * Generate a user DID with namespace.
 *
 * @param namespace - Provider namespace (required, or set GAUGID_NAMESPACE env var)
 * @param identifier - Unique identifier (auto-generated if not provided)
 * @returns User DID in format: did:a2p:user:<namespace>:<identifier>
 * @throws {Error} If namespace is not provided and not set in environment
 *
 * @example
 * ```typescript
 * generateUserDid("gaugid");
 * // Returns: 'did:a2p:user:gaugid:AbC123XyZ789'
 *
 * generateUserDid("company-a", "alice");
 * // Returns: 'did:a2p:user:company-a:alice'
 * ```
 */
export function generateUserDid(
  namespace?: string,
  identifier?: string
): string {
  const ns = namespace || process.env.GAUGID_NAMESPACE;
  if (!ns) {
    throw new Error(
      "Namespace is required. Provide it as argument or set GAUGID_NAMESPACE environment variable."
    );
  }

  // Generate identifier if not provided
  if (!identifier) {
    identifier = generateRandomIdentifier();
  }

  return `did:a2p:user:${ns}:${identifier}`;
}

/**
 * Generate an agent DID with namespace.
 *
 * @param name - Agent name (will be sanitized if provided)
 * @param namespace - Provider namespace (required, or set GAUGID_NAMESPACE env var)
 * @param identifier - Unique identifier (auto-generated if not provided)
 * @returns Agent DID in format: did:a2p:agent:<namespace>:<identifier>
 * @throws {Error} If namespace is not provided and not set in environment
 *
 * @example
 * ```typescript
 * generateAgentDid("my-assistant", "gaugid");
 * // Returns: 'did:a2p:agent:gaugid:my-assistant'
 *
 * generateAgentDid("my-assistant", "local");
 * // Returns: 'did:a2p:agent:local:my-assistant'
 * ```
 */
export function generateAgentDid(
  name?: string,
  namespace?: string,
  identifier?: string
): string {
  const ns = namespace || process.env.GAUGID_NAMESPACE;
  if (!ns) {
    throw new Error(
      "Namespace is required. Provide it as argument or set GAUGID_NAMESPACE environment variable."
    );
  }

  // Use name as identifier if provided, otherwise generate
  const id = identifier || (name ? sanitizeIdentifier(name) : generateRandomIdentifier());

  return `did:a2p:agent:${ns}:${id}`;
}

/**
 * Validate a DID and ensure it has a namespace.
 *
 * @param did - DID string to validate
 * @returns Tuple of [isValid, errorMessage]
 *   - isValid: true if DID is valid, false otherwise
 *   - errorMessage: Error message if invalid, undefined if valid
 *
 * @example
 * ```typescript
 * validateGaugidDid("did:a2p:user:gaugid:alice");
 * // Returns: [true, undefined]
 *
 * validateGaugidDid("did:a2p:user:alice");
 * // Returns: [false, 'Namespace is required in DID: did:a2p:user:alice']
 * ```
 */
export function validateGaugidDid(did: string): [boolean, string | undefined] {
  // Basic DID format validation
  const didPattern = /^did:a2p:(user|agent):([^:]+):(.+)$/;
  if (!didPattern.test(did)) {
    return [
      false,
      `Invalid DID format: ${did}. Required format: did:a2p:<type>:<namespace>:<identifier>`,
    ];
  }

  const parts = did.split(":");
  if (parts.length < 5) {
    return [
      false,
      `Namespace is required in DID: ${did}. Format must be: did:a2p:<type>:<namespace>:<identifier>`,
    ];
  }

  // Check that namespace (4th part) is not empty
  const namespace = parts[3];
  if (!namespace || namespace.length === 0) {
    return [
      false,
      `Namespace is required in DID: ${did}. Format must be: did:a2p:<type>:<namespace>:<identifier>`,
    ];
  }

  return [true, undefined];
}

/**
 * Parse a DID into its components.
 */
export function parseDid(did: string): {
  method: string;
  type: string;
  namespace: string;
  identifier: string;
} | null {
  const match = did.match(/^did:(a2p):(user|agent):([^:]+):(.+)$/);
  if (!match) {
    return null;
  }

  return {
    method: match[1],
    type: match[2],
    namespace: match[3],
    identifier: match[4],
  };
}

/**
 * Get namespace from a DID.
 */
export function getNamespace(did: string): string | null {
  const parsed = parseDid(did);
  return parsed?.namespace || null;
}

/**
 * Parse a DID into its components (re-exported for convenience).
 */
export { parseDid };

/**
 * Generate a random identifier.
 */
function generateRandomIdentifier(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 12; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

/**
 * Sanitize an identifier to be DID-safe.
 */
function sanitizeIdentifier(name: string): string {
  // Convert to lowercase, replace spaces and special chars with hyphens
  return name
    .toLowerCase()
    .replace(/[^a-z0-9-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}
