#!/usr/bin/env node

const { spawnSync } = require("child_process");
const fs = require("fs");

const { currentTarget, installedBinaryPath } = require("../shared");

function main() {
  const targetInfo = currentTarget();
  if (!targetInfo) {
    console.error(
      `Unsupported platform for ai-wiki-toolkit npm package: ${process.platform}-${process.arch}`,
    );
    process.exit(1);
  }

  let binaryPath;
  try {
    binaryPath = installedBinaryPath(targetInfo);
  } catch (error) {
    console.error(
      [
        `The platform package ${targetInfo.package_name} is not installed.`,
        "Reinstall ai-wiki-toolkit with npm so the matching optional dependency is available.",
      ].join(" "),
    );
    process.exit(1);
  }

  if (!fs.existsSync(binaryPath)) {
    console.error(
      [
        `Expected ai-wiki-toolkit binary at ${binaryPath}, but it was not found.`,
        "Reinstall ai-wiki-toolkit with npm to restore the matching platform package.",
      ].join(" "),
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
