#!/usr/bin/env node

const fs = require("fs");
const http = require("http");
const https = require("https");
const os = require("os");
const path = require("path");
const { pipeline } = require("stream/promises");

const extractZip = require("extract-zip");
const tar = require("tar");

const {
  currentTarget,
  installDirectory,
  installedBinaryPath,
  releaseAssetUrl,
  releaseVersion,
} = require("./shared");

async function downloadFile(url, destination) {
  await fs.promises.mkdir(path.dirname(destination), { recursive: true });

  return new Promise((resolve, reject) => {
    const client = new URL(url).protocol === "http:" ? http : https;
    client
      .get(url, (response) => {
        if (
          response.statusCode &&
          response.statusCode >= 300 &&
          response.statusCode < 400 &&
          response.headers.location
        ) {
          downloadFile(new URL(response.headers.location, url).toString(), destination)
            .then(resolve)
            .catch(reject);
          return;
        }

        if (response.statusCode !== 200) {
          reject(new Error(`Download failed for ${url}: HTTP ${response.statusCode}`));
          return;
        }

        const output = fs.createWriteStream(destination);
        pipeline(response, output).then(resolve).catch(reject);
      })
      .on("error", reject);
  });
}

async function extractArchive(archivePath, targetInfo) {
  const outputDir = installDirectory(targetInfo);
  await fs.promises.rm(outputDir, { recursive: true, force: true });
  await fs.promises.mkdir(outputDir, { recursive: true });

  if (targetInfo.archiveExtension === "zip") {
    await extractZip(archivePath, { dir: outputDir });
  } else {
    await tar.x({
      file: archivePath,
      cwd: outputDir,
      gzip: true,
    });
  }

  if (process.platform !== "win32") {
    await fs.promises.chmod(installedBinaryPath(targetInfo), 0o755);
  }
}

async function main() {
  const targetInfo = currentTarget();
  if (!targetInfo) {
    console.error(
      `Unsupported platform for ai-wiki-toolkit npm wrapper: ${process.platform}-${process.arch}`,
    );
    process.exit(1);
  }

  const version = releaseVersion();
  const url = releaseAssetUrl(version, targetInfo);
  const tempDir = await fs.promises.mkdtemp(path.join(os.tmpdir(), "aiwiki-toolkit-"));
  const archivePath = path.join(tempDir, `download.${targetInfo.archiveExtension}`);

  try {
    await downloadFile(url, archivePath);
    await extractArchive(archivePath, targetInfo);

    console.log(`Installed ai-wiki-toolkit binary for ${targetInfo.target}`);
  } finally {
    await fs.promises.rm(tempDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
