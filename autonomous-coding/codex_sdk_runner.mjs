#!/usr/bin/env node

import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import { Codex } from "@openai/codex-sdk";

const SANDBOX_MODES = new Set([
  "read-only",
  "workspace-write",
  "danger-full-access",
]);
const REASONING_EFFORTS = new Set(["minimal", "low", "medium", "high", "xhigh"]);

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      throw new Error(`Unexpected positional argument: ${token}`);
    }
    const key = token.slice(2);
    const value = argv[i + 1];
    if (value === undefined || value.startsWith("--")) {
      throw new Error(`Missing value for --${key}`);
    }
    args[key] = value;
    i += 1;
  }
  return args;
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function readThreadId(stateFile) {
  try {
    const state = JSON.parse(await readFile(stateFile, "utf8"));
    return typeof state.threadId === "string" && state.threadId ? state.threadId : null;
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return null;
    }
    throw new Error(`Unable to read Codex thread state at ${stateFile}: ${error.message}`);
  }
}

async function writeThreadId(stateFile, threadId) {
  if (!threadId) {
    return;
  }
  await mkdir(path.dirname(stateFile), { recursive: true });
  await writeFile(
    stateFile,
    `${JSON.stringify({ threadId }, null, 2)}\n`,
    "utf8",
  );
}

function cleanThreadOptions(options) {
  return Object.fromEntries(
    Object.entries(options).filter(([, value]) => value !== undefined && value !== ""),
  );
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args["project-dir"]) {
    throw new Error("Missing required --project-dir");
  }

  const prompt = (await readStdin()).trim();
  if (!prompt) {
    throw new Error("No prompt was provided on stdin");
  }

  const projectDir = path.resolve(args["project-dir"]);
  const stateFile = path.resolve(
    args["state-file"] || path.join(projectDir, ".codex-thread.json"),
  );
  const sandboxMode = args.sandbox || "workspace-write";
  const reasoningEffort = args["reasoning-effort"] || "high";

  if (!SANDBOX_MODES.has(sandboxMode)) {
    throw new Error(`Unsupported sandbox mode: ${sandboxMode}`);
  }
  if (!REASONING_EFFORTS.has(reasoningEffort)) {
    throw new Error(`Unsupported reasoning effort: ${reasoningEffort}`);
  }

  const codex = new Codex();
  const threadOptions = cleanThreadOptions({
    workingDirectory: projectDir,
    skipGitRepoCheck: true,
    model: args.model,
    sandboxMode,
    modelReasoningEffort: reasoningEffort,
    approvalPolicy: "never",
  });
  const threadId = await readThreadId(stateFile);
  const thread = threadId
    ? codex.resumeThread(threadId, threadOptions)
    : codex.startThread(threadOptions);

  const turn = await thread.run(prompt);
  await writeThreadId(stateFile, thread.id);

  if (turn.finalResponse) {
    console.log(turn.finalResponse);
  }
}

main().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
