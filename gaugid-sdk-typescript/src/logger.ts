/**
 * Centralized logging configuration for Gaugid SDK.
 */

export type LogLevel = "DEBUG" | "INFO" | "WARN" | "ERROR";

const LOG_LEVELS: Record<LogLevel, number> = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
};

export interface Logger {
  debug(message: string, ...args: unknown[]): void;
  info(message: string, ...args: unknown[]): void;
  warn(message: string, ...args: unknown[]): void;
  error(message: string, ...args: unknown[]): void;
}

class ConsoleLogger implements Logger {
  private level: LogLevel;
  private name: string;

  constructor(name: string, level: LogLevel = "WARN") {
    this.name = name;
    this.level = level;
  }

  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVELS[level] >= LOG_LEVELS[this.level];
  }

  private formatMessage(level: LogLevel, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level}] [${this.name}] ${message}`;
  }

  debug(message: string, ...args: unknown[]): void {
    if (this.shouldLog("DEBUG")) {
      console.debug(this.formatMessage("DEBUG", message), ...args);
    }
  }

  info(message: string, ...args: unknown[]): void {
    if (this.shouldLog("INFO")) {
      console.info(this.formatMessage("INFO", message), ...args);
    }
  }

  warn(message: string, ...args: unknown[]): void {
    if (this.shouldLog("WARN")) {
      console.warn(this.formatMessage("WARN", message), ...args);
    }
  }

  error(message: string, ...args: unknown[]): void {
    if (this.shouldLog("ERROR")) {
      console.error(this.formatMessage("ERROR", message), ...args);
    }
  }
}

let globalLogLevel: LogLevel = "WARN";
const loggers = new Map<string, Logger>();

/**
 * Get a logger instance for a specific module.
 */
export function getLogger(name?: string): Logger {
  const loggerName = name ? `gaugid.${name}` : "gaugid";
  
  if (!loggers.has(loggerName)) {
    loggers.set(loggerName, new ConsoleLogger(loggerName, globalLogLevel));
  }
  
  return loggers.get(loggerName)!;
}

/**
 * Setup global logging configuration.
 */
export function setupLogging(level: LogLevel = "WARN"): void {
  globalLogLevel = level;
  // Update all existing loggers
  for (const [name, logger] of loggers.entries()) {
    loggers.set(name, new ConsoleLogger(name, level));
  }
}
