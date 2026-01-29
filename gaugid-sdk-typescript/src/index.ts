/**
 * Gaugid SDK - TypeScript client library for Gaugid (a2p-cloud) service integration.
 *
 * This SDK extends the base a2p protocol SDK with Gaugid-specific features like
 * OAuth flows, connection tokens, and service-specific utilities.
 */

export { GaugidClient } from "./client.js";
export { GaugidStorage } from "./storage.js";
export {
  GaugidError,
  GaugidAPIError,
  GaugidAuthError,
  GaugidConnectionError,
  type ConnectionTokenInfo,
  type OAuthTokenResponse,
} from "./types.js";
export {
  generateUserDid,
  generateAgentDid,
  validateGaugidDid,
  parseDid,
  getNamespace,
} from "./utils.js";
export {
  generateA2PSignatureHeader,
  generateEd25519Keypair,
  privateKeyToPem,
} from "./signature.js";
export { getLogger, setupLogging } from "./logger.js";

// Export auth and connection modules
export * as auth from "./auth.js";
export * as connection from "./connection.js";

// Integration exports (require peer dependencies for full functionality)

// Re-export integration classes
export { GaugidStore } from "./integrations/langgraph.js";
export { GaugidMemoryService } from "./integrations/adk.js";
export { GaugidMemoryTool } from "./integrations/anthropic.js";
export { GaugidSession } from "./integrations/openai.js";
export { GaugidMemoryBlock } from "./integrations/llama_index.js";
export { GaugidDb } from "./integrations/agno.js";
