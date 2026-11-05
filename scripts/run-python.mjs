#!/usr/bin/env node
/**
 * Run a backend Python command with the repository virtualenv.
 *
 * This keeps root npm scripts working on Windows and POSIX without requiring
 * the developer to activate the virtualenv in every shell.
 */
import { existsSync } from "node:fs"
import { spawn } from "node:child_process"
import { fileURLToPath } from "node:url"
import path from "node:path"

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const isWindows = process.platform === "win32"
const venvPython = path.join(
  repoRoot,
  "backend",
  ".venv",
  isWindows ? "Scripts" : "bin",
  isWindows ? "python.exe" : "python",
)
const python = process.env.PYTHON || venvPython

if (!existsSync(python)) {
  console.error(
    [
      "Backend virtualenv not found.",
      `Expected: ${python}`,
      "Create it with:",
      "  py -3.11 -m venv backend/.venv",
      "  backend/.venv/Scripts/python -m pip install -r backend/requirements-dev.txt",
    ].join("\n"),
  )
  process.exit(1)
}

const child = spawn(python, process.argv.slice(2), {
  cwd: process.cwd(),
  stdio: "inherit",
  shell: false,
  env: process.env,
})

child.on("error", (error) => {
  console.error(`Unable to start Python: ${error.message}`)
  process.exit(1)
})

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal)
    return
  }
  process.exit(code ?? 1)
})
