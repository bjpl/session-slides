#!/usr/bin/env node

/**
 * session-slides CLI
 *
 * Node.js wrapper that invokes the Python session-slides tool.
 * Handles cross-platform Python detection and argument passthrough.
 */

'use strict';

const spawn = require('cross-spawn');
const path = require('path');
const fs = require('fs');

const SCRIPT_NAME = 'generate_slides.py';
const MIN_PYTHON_VERSION = [3, 8];

/**
 * Parse Python version string into [major, minor] array.
 * @param {string} versionOutput - Output from `python --version`
 * @returns {number[]|null} - [major, minor] or null if parsing fails
 */
function parsePythonVersion(versionOutput) {
  const match = versionOutput.match(/Python\s+(\d+)\.(\d+)/i);
  if (match) {
    return [parseInt(match[1], 10), parseInt(match[2], 10)];
  }
  return null;
}

/**
 * Check if a Python version meets minimum requirements.
 * @param {number[]} version - [major, minor]
 * @returns {boolean}
 */
function meetsMinVersion(version) {
  if (!version) return false;
  if (version[0] > MIN_PYTHON_VERSION[0]) return true;
  if (version[0] < MIN_PYTHON_VERSION[0]) return false;
  return version[1] >= MIN_PYTHON_VERSION[1];
}

/**
 * Attempt to detect a working Python 3 executable.
 * @returns {{cmd: string, args: string[]}|null} - Command and args, or null if not found
 */
function detectPython() {
  // Allow environment variable override
  const envPython = process.env.SESSION_SLIDES_PYTHON || process.env.PYTHON3;
  if (envPython) {
    return { cmd: envPython, args: [] };
  }

  // Platform-specific candidate order
  const isWindows = process.platform === 'win32';
  const candidates = isWindows
    ? [
        { cmd: 'python', args: [] },
        { cmd: 'python3', args: [] },
        { cmd: 'py', args: ['-3'] }
      ]
    : [
        { cmd: 'python3', args: [] },
        { cmd: 'python', args: [] }
      ];

  for (const candidate of candidates) {
    try {
      const result = spawn.sync(candidate.cmd, [...candidate.args, '--version'], {
        encoding: 'utf8',
        stdio: 'pipe',
        timeout: 5000
      });

      if (result.status === 0) {
        const output = (result.stdout || result.stderr || '').toString();
        const version = parsePythonVersion(output);

        if (meetsMinVersion(version)) {
          return candidate;
        }
      }
    } catch (e) {
      // Command not found, continue to next candidate
    }
  }

  return null;
}

/**
 * Print error message and exit.
 * @param {string} message
 * @param {number} code
 */
function exitWithError(message, code = 1) {
  console.error(`\x1b[31mError:\x1b[0m ${message}`);
  process.exit(code);
}

/**
 * Print help for Python installation.
 */
function printPythonHelp() {
  console.error(`
\x1b[33mPython ${MIN_PYTHON_VERSION.join('.')}+ is required but was not found.\x1b[0m

Install Python:
  macOS:   brew install python3
  Ubuntu:  sudo apt install python3
  Windows: https://www.python.org/downloads/

Or set SESSION_SLIDES_PYTHON environment variable to your Python path.
`);
}

/**
 * Main entry point.
 */
function main() {
  // Detect Python
  const python = detectPython();

  if (!python) {
    printPythonHelp();
    process.exit(1);
  }

  // Locate Python script
  const scriptPath = path.join(__dirname, '..', 'scripts', SCRIPT_NAME);

  if (!fs.existsSync(scriptPath)) {
    exitWithError(`Python script not found: ${scriptPath}\n\nThis may indicate a corrupt installation. Try reinstalling:\n  npm uninstall -g @bjpl/session-slides && npm install -g @bjpl/session-slides`);
  }

  // Build arguments: python args + script path + user args
  const args = [...python.args, scriptPath, ...process.argv.slice(2)];

  // Spawn Python process with inherited stdio for proper terminal handling
  const child = spawn(python.cmd, args, {
    stdio: 'inherit',
    windowsHide: false
  });

  // Handle spawn errors
  child.on('error', (err) => {
    if (err.code === 'ENOENT') {
      exitWithError(`Could not execute Python: ${python.cmd}`);
    } else {
      exitWithError(`Failed to start Python: ${err.message}`);
    }
  });

  // Propagate exit code
  child.on('close', (code) => {
    process.exit(code || 0);
  });

  // Forward termination signals to child process
  const signals = ['SIGINT', 'SIGTERM', 'SIGHUP'];
  for (const signal of signals) {
    process.on(signal, () => {
      if (!child.killed) {
        child.kill(signal);
      }
    });
  }
}

main();
