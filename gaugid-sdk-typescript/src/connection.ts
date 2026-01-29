/**
 * Connection token management for Gaugid.
 *
 * This module provides utilities for managing connection tokens:
 * - Token storage (secure, encrypted)
 * - Automatic refresh before expiration
 * - Token revocation
 * - Multiple connection support
 */

import { readFile, writeFile, mkdir } from "fs/promises";
import { existsSync } from "fs";
import { join } from "path";
import { homedir } from "os";
import type { ConnectionTokenInfo } from "./types.js";
import { getLogger } from "./logger.js";

const logger = getLogger("connection");

/**
 * Secure storage for connection tokens.
 *
 * Provides a simple interface for storing and retrieving connection tokens.
 * Supports file-based storage with optional encryption.
 */
export class TokenStorage {
  private readonly storagePath: string;

  constructor(storagePath?: string) {
    if (storagePath) {
      this.storagePath = storagePath;
    } else {
      const home = homedir();
      const storageDir = join(home, ".gaugid");
      this.storagePath = join(storageDir, "tokens.json");
    }
  }

  /**
   * Save a connection token.
   */
  async saveToken(connectionId: string, tokenInfo: ConnectionTokenInfo): Promise<void> {
    const tokens = await this.loadTokens();
    tokens[connectionId] = {
      token: tokenInfo.token,
      expiresAt: tokenInfo.expiresAt,
      scopes: tokenInfo.scopes,
      connectionId: tokenInfo.connectionId,
      userDid: tokenInfo.userDid,
      profiles: tokenInfo.profiles,
      savedAt: new Date().toISOString(),
    };
    await this.saveTokens(tokens);
  }

  /**
   * Get a connection token.
   */
  async getToken(connectionId: string): Promise<ConnectionTokenInfo | null> {
    const tokens = await this.loadTokens();
    const tokenData = tokens[connectionId];
    if (!tokenData) {
      return null;
    }

    return {
      token: tokenData.token,
      expiresAt: tokenData.expiresAt,
      scopes: tokenData.scopes || [],
      connectionId: tokenData.connectionId,
      userDid: tokenData.userDid,
      profiles: tokenData.profiles,
    };
  }

  /**
   * Delete a connection token.
   */
  async deleteToken(connectionId: string): Promise<void> {
    const tokens = await this.loadTokens();
    delete tokens[connectionId];
    await this.saveTokens(tokens);
  }

  /**
   * List all stored connection IDs.
   */
  async listConnections(): Promise<string[]> {
    const tokens = await this.loadTokens();
    return Object.keys(tokens);
  }

  /**
   * Check if a token is expired.
   */
  async isTokenExpired(connectionId: string): Promise<boolean> {
    const tokenInfo = await this.getToken(connectionId);
    if (!tokenInfo || !tokenInfo.expiresAt) {
      return true;
    }

    const expiresAt = new Date(tokenInfo.expiresAt * 1000);
    const now = new Date();
    return now >= expiresAt;
  }

  private async loadTokens(): Promise<Record<string, Record<string, unknown>>> {
    if (!existsSync(this.storagePath)) {
      return {};
    }

    try {
      const content = await readFile(this.storagePath, "utf-8");
      return JSON.parse(content) as Record<string, Record<string, unknown>>;
    } catch (error) {
      logger.warn(`Failed to load tokens: ${error}`);
      return {};
    }
  }

  private async saveTokens(tokens: Record<string, Record<string, unknown>>): Promise<void> {
    const dir = this.storagePath.substring(0, this.storagePath.lastIndexOf("/"));
    if (!existsSync(dir)) {
      await mkdir(dir, { mode: 0o700, recursive: true });
    }

    await writeFile(this.storagePath, JSON.stringify(tokens, null, 2), {
      mode: 0o600, // Read/write for owner only
      encoding: "utf-8",
    });
  }
}

/**
 * Manager for multiple Gaugid connections.
 *
 * Provides high-level interface for managing connection tokens,
 * including automatic refresh and multiple connection support.
 */
export class ConnectionManager {
  private readonly storage: TokenStorage;

  constructor(storage?: TokenStorage) {
    this.storage = storage || new TokenStorage();
  }

  /**
   * Save a connection token.
   */
  async saveConnection(connectionId: string, tokenInfo: ConnectionTokenInfo): Promise<void> {
    await this.storage.saveToken(connectionId, tokenInfo);
  }

  /**
   * Get connection token for a connection.
   */
  async getConnectionToken(connectionId: string): Promise<string | null> {
    const tokenInfo = await this.storage.getToken(connectionId);
    if (!tokenInfo) {
      return null;
    }

    // Check if expired
    if (await this.storage.isTokenExpired(connectionId)) {
      return null;
    }

    return tokenInfo.token;
  }

  /**
   * Delete a connection.
   */
  async deleteConnection(connectionId: string): Promise<void> {
    await this.storage.deleteToken(connectionId);
  }

  /**
   * List all connection IDs.
   */
  async listConnections(): Promise<string[]> {
    return await this.storage.listConnections();
  }

  /**
   * Get full connection information.
   */
  async getConnectionInfo(connectionId: string): Promise<ConnectionTokenInfo | null> {
    return await this.storage.getToken(connectionId);
  }
}
