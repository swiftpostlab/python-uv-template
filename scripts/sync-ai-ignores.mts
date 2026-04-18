/**
 * sync-ai-ignores.mts
 *
 * Reads `.ai-policy.json` (the single source of truth for AI file and command policy)
 * and syncs the relevant parts to agent-specific configuration files:
 *
 * - Gemini: `.aiexclude` → generated from protected + excluded file patterns
 * - Claude Code: `.claude/settings.json` → `permissions.deny` with protected file patterns
 * - GitHub Copilot: `.vscode/settings.json` → protected file associations + command/edit policy
 *
 * Run: `node --experimental-strip-types scripts/sync-ai-ignores.mts`
 * Requires: Node >= 22.6
 */

import type { PathLike } from 'node:fs';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

interface ClaudePermissions {
  deny?: string[];
  allow?: string[];
}

interface ClaudeSettings {
  permissions?: ClaudePermissions;
}

interface TerminalApprovalRule {
  approve: boolean;
  matchCommandLine?: boolean;
}

type TerminalApprovalSetting = boolean | TerminalApprovalRule;

interface AiPolicy {
  protectedFiles: string[];
  excludedFiles: string[];
  terminalAutoApprove: Record<string, TerminalApprovalSetting>;
  editAutoApprove: Record<string, boolean>;
}

interface VscodeSettings {
  'chat.tools.terminal.autoApprove'?: Record<string, TerminalApprovalSetting>;
  'chat.tools.edits.autoApprove'?: Record<string, boolean>;
  'files.associations'?: Record<string, string>;
  'github.copilot.enable'?: Record<string, boolean>;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');
const aiPolicyPath = path.join(rootDir, '.ai-policy.json');
const aiExcludePath = path.join(rootDir, '.aiexclude');
const vscodeSettingsPath = path.join(rootDir, '.vscode', 'settings.json');
const shouldImportVscode = process.argv.includes('--import-vscode');

const readJsonFile = <T>(filePath: PathLike, fallback: T): T => {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }

  const raw = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(raw) as T;
};

const writeJsonFile = (filePath: string, data: unknown): void => {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n');
};

const writeTextFile = (filePath: string, content: string): void => {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(filePath, content);
};

const mergeRecord = <TValue>(
  existing: Record<string, TValue> | undefined,
  managed: Record<string, TValue>,
): Record<string, TValue> => ({
  ...(existing ?? {}),
  ...managed,
});

const mergeUniqueStrings = (existing: string[] | undefined, managed: string[]): string[] => {
  const values = new Set<string>(existing ?? []);

  for (const value of managed) {
    values.add(value);
  }

  return [...values];
};

const buildAiExcludeContent = (policy: AiPolicy): string => {
  const lines = [
    '# ============================================================================== ',
    "# AI EXCLUSION FILE",
    "# Generated from .ai-policy.json",
    "# Protected files are sensitive; excluded files are mostly noise or generated output.",
    '# ==============================================================================',
    '',
    '# --- 1. Protected files ---',
    ...policy.protectedFiles,
    '',
    '# --- 2. Excluded noise / generated output ---',
    ...policy.excludedFiles,
    '',
  ];

  return lines.join('\n');
};

const importPolicyFromVscode = (policy: AiPolicy): AiPolicy => {
  const vscodeSettings = readJsonFile<VscodeSettings>(vscodeSettingsPath, {} as VscodeSettings);

  return {
    ...policy,
    terminalAutoApprove: mergeRecord(policy.terminalAutoApprove, vscodeSettings['chat.tools.terminal.autoApprove'] ?? {}),
    editAutoApprove: mergeRecord(policy.editAutoApprove, vscodeSettings['chat.tools.edits.autoApprove'] ?? {}),
  };
};

if (!fs.existsSync(aiPolicyPath)) {
  console.log('No .ai-policy.json found. Nothing to sync.');
  process.exit(0);
}

const policy = readJsonFile<AiPolicy>(aiPolicyPath, {
  protectedFiles: [],
  excludedFiles: [],
  terminalAutoApprove: {},
  editAutoApprove: {},
});

const effectivePolicy = shouldImportVscode ? importPolicyFromVscode(policy) : policy;

if (shouldImportVscode) {
  writeJsonFile(aiPolicyPath, effectivePolicy);
  console.log('Imported: VS Code approvals into .ai-policy.json');
}

if (effectivePolicy.protectedFiles.length === 0 && effectivePolicy.excludedFiles.length === 0) {
  console.log('.ai-policy.json has no file patterns. Nothing to sync.');
  process.exit(0);
}

writeTextFile(aiExcludePath, buildAiExcludeContent(effectivePolicy));
console.log(
  `Loaded ${String(effectivePolicy.protectedFiles.length)} protected patterns and ${String(effectivePolicy.excludedFiles.length)} excluded patterns`,
);
console.log('Synced: Gemini (.aiexclude)');

const claudeSettingsPath = path.join(rootDir, '.claude', 'settings.json');
const claudeSettings = readJsonFile<ClaudeSettings>(claudeSettingsPath, {} as ClaudeSettings);

claudeSettings.permissions = claudeSettings.permissions ?? {};
claudeSettings.permissions.deny = mergeUniqueStrings(
  claudeSettings.permissions.deny,
  effectivePolicy.protectedFiles.map((pattern) => `Read(${pattern})`),
);

writeJsonFile(claudeSettingsPath, claudeSettings);
console.log('Synced: Claude Code (.claude/settings.json)');

const vscodeSettings = readJsonFile<VscodeSettings>(vscodeSettingsPath, {} as VscodeSettings);
const associations = vscodeSettings['files.associations'] ?? {};
const copilotEnable = vscodeSettings['github.copilot.enable'] ?? {};

for (const pattern of effectivePolicy.protectedFiles) {
  associations[pattern] = 'copilot-restricted-file';
}

copilotEnable['copilot-restricted-file'] = false;

vscodeSettings['chat.tools.terminal.autoApprove'] = mergeRecord(
  vscodeSettings['chat.tools.terminal.autoApprove'],
  effectivePolicy.terminalAutoApprove,
);
vscodeSettings['chat.tools.edits.autoApprove'] = mergeRecord(
  vscodeSettings['chat.tools.edits.autoApprove'],
  effectivePolicy.editAutoApprove,
);
vscodeSettings['files.associations'] = associations;
vscodeSettings['github.copilot.enable'] = mergeRecord(vscodeSettings['github.copilot.enable'], copilotEnable);

writeJsonFile(vscodeSettingsPath, vscodeSettings);
console.log('Synced: Copilot local policy (.vscode/settings.json)');

console.log('Done.');
