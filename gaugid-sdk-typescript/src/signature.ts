/**
 * A2P-Signature authentication utilities for protocol-compliant authentication.
 *
 * This module provides functions for generating A2P-Signature headers as required
 * by the a2p protocol specification.
 */

import { createHash, randomBytes } from "crypto";

export interface Ed25519KeyPair {
  privateKey: Uint8Array;
  publicKey: Uint8Array;
}

/**
 * Generate an A2P-Signature authorization header for protocol-compliant authentication.
 *
 * @param agentDid - Agent DID (e.g., "did:a2p:agent:gaugid:my-agent")
 * @param privateKey - Ed25519 private key (32-byte Uint8Array)
 * @param method - HTTP method (e.g., "GET", "POST")
 * @param path - Request path (e.g., "/a2p/v1/profile/did:a2p:user:gaugid:alice")
 * @param body - Optional request body bytes
 * @param timestamp - Optional Unix timestamp (defaults to current time)
 * @param nonce - Optional random nonce (auto-generated if not provided)
 * @param expiration - Optional expiration timestamp in seconds (defaults to 300 seconds)
 * @returns Authorization header value: 'A2P-Signature did="...",sig="...",ts="...",nonce="..."'
 *
 * @example
 * ```typescript
 * const privateKey = generateEd25519Keypair().privateKey;
 * const header = generateA2PSignatureHeader(
 *   "did:a2p:agent:gaugid:my-agent",
 *   privateKey,
 *   "GET",
 *   "/a2p/v1/profile/did:a2p:user:gaugid:alice"
 * );
 * // Use in request: headers["Authorization"] = header;
 * ```
 */
export function generateA2PSignatureHeader(
  agentDid: string,
  privateKey: Uint8Array,
  method: string,
  path: string,
  body?: Uint8Array,
  timestamp?: number,
  nonce?: string,
  expiration?: number
): string {
  // Validate private key length
  if (privateKey.length !== 32) {
    throw new Error("Private key must be 32 bytes");
  }

  // Generate timestamp and nonce if not provided
  const ts = timestamp || Math.floor(Date.now() / 1000);
  const n = nonce || randomBytes(32).toString("base64url");
  const exp = expiration || ts + 300; // 5 minutes default

  // Build signature string (canonical request format)
  // Format: method\npath\nbody_hash\ntimestamp\nnonce\nexpiration
  let bodyHash = "";
  if (body && body.length > 0) {
    const hash = createHash("sha256").update(body).digest();
    bodyHash = hash.toString("base64");
  }

  const signatureString = `${method}\n${path}\n${bodyHash}\n${ts}\n${n}\n${exp}`;

  // Sign the canonical string using Ed25519
  // Note: In a real implementation, you would use a proper Ed25519 library
  // like @noble/ed25519 or tweetnacl
  const signature = signEd25519(signatureString, privateKey);
  const signatureB64 = Buffer.from(signature).toString("base64");

  // Build authorization header
  const headerParts = [
    `did="${agentDid}"`,
    `sig="${signatureB64}"`,
    `ts="${ts}"`,
    `nonce="${n}"`,
    `exp="${exp}"`,
  ];

  return `A2P-Signature ${headerParts.join(", ")}`;
}

/**
 * Generate a new Ed25519 keypair for agent authentication.
 *
 * @returns Object with privateKey and publicKey as Uint8Array
 *
 * @example
 * ```typescript
 * const { privateKey, publicKey } = generateEd25519Keypair();
 * // Store privateKey securely
 * // Register publicKey with agent DID
 * const publicKeyB64 = Buffer.from(publicKey).toString("base64");
 * ```
 */
export function generateEd25519Keypair(): Ed25519KeyPair {
  // Generate 32 random bytes for private key
  const privateKey = randomBytes(32);
  
  // Derive public key from private key
  // Note: In a real implementation, you would use a proper Ed25519 library
  // This is a placeholder - you should use @noble/ed25519 or similar
  const publicKey = derivePublicKey(privateKey);

  return {
    privateKey: new Uint8Array(privateKey),
    publicKey: new Uint8Array(publicKey),
  };
}

/**
 * Convert Ed25519PrivateKey to PEM format for storage.
 *
 * @param privateKey - Ed25519 private key as Uint8Array
 * @returns PEM-formatted private key string
 *
 * @example
 * ```typescript
 * const { privateKey } = generateEd25519Keypair();
 * const pem = privateKeyToPem(privateKey);
 * // Store pem string securely
 * ```
 */
export function privateKeyToPem(privateKey: Uint8Array): string {
  // Convert to PEM format
  // Note: In a real implementation, you would use a proper Ed25519 library
  // This is a simplified version
  const keyBase64 = Buffer.from(privateKey).toString("base64");
  const lines = keyBase64.match(/.{1,64}/g) || [];
  return `-----BEGIN PRIVATE KEY-----\n${lines.join("\n")}\n-----END PRIVATE KEY-----`;
}

/**
 * Sign a message using Ed25519.
 * 
 * Note: This requires @noble/ed25519 to be installed.
 * Install it with: npm install @noble/ed25519
 */
function signEd25519(message: string, privateKey: Uint8Array): Uint8Array {
  // Try to use @noble/ed25519 if available
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { sign } = require("@noble/ed25519");
    return sign(message, privateKey);
  } catch {
    throw new Error(
      "Ed25519 signing requires @noble/ed25519. Install it with: npm install @noble/ed25519"
    );
  }
}

/**
 * Derive public key from private key.
 * 
 * Note: This requires @noble/ed25519 to be installed.
 */
function derivePublicKey(privateKey: Uint8Array): Uint8Array {
  // Try to use @noble/ed25519 if available
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { getPublicKey } = require("@noble/ed25519");
    return getPublicKey(privateKey);
  } catch {
    throw new Error(
      "Ed25519 key derivation requires @noble/ed25519. Install it with: npm install @noble/ed25519"
    );
  }
}
