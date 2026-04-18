#!/usr/bin/env node

const { spawnSync } = require("child_process");
const fs = require("fs");

const { currentTarget, installedBinaryPath } = require("../shared");

function main() {
  const targetInfo = currentTarget();
  if (!targetInfo) {
    console.error(
      `Unsupported platform for ai-wiki-toolkit npm wrapper: ${process.platform}-${process.arch}`,
    );
    process.exit(1);
  }

  const binaryPath = installedBinaryPath(targetInfo);
  if (!fs.existsSync(binaryPath)) {
    console.error(
      "ai-wiki-toolkit binary is not installed. Reinstall the npm package to download the release asset.",
    );
    process.exit(1);
  }

  const result = spawnSync(binaryPath, process.argv.slice(2), {
    stdio: "inherit",
  });

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }

  process.exit(result.status ?? 0);
}

main();
