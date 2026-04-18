const path = require("path");
const packageJson = require("../package.json");

const BINARY_NAME = "aiwiki-toolkit";
const REPOSITORY = "BochengYin/ai-wiki-toolkit";
const INSTALL_ROOT = path.join(__dirname, "vendor");

const TARGETS = {
  "darwin-arm64": {
    target: "macos-arm64",
    archiveExtension: "tar.gz",
    binaryName: BINARY_NAME,
  },
  "darwin-x64": {
    target: "macos-x64",
    archiveExtension: "tar.gz",
    binaryName: BINARY_NAME,
  },
  "linux-x64": {
    target: "linux-x64",
    archiveExtension: "tar.gz",
    binaryName: BINARY_NAME,
  },
  "win32-x64": {
    target: "windows-x64",
    archiveExtension: "zip",
    binaryName: `${BINARY_NAME}.exe`,
  },
};

function releaseVersion() {
  return packageJson.version.startsWith("v")
    ? packageJson.version
    : `v${packageJson.version}`;
}

function currentTarget(platform = process.platform, arch = process.arch) {
  return TARGETS[`${platform}-${arch}`] || null;
}

function releaseAssetName(version, target, archiveExtension) {
  return `ai-wiki-toolkit-${version}-${target}.${archiveExtension}`;
}

function releaseAssetUrl(version, targetInfo) {
  const filename = releaseAssetName(
    version,
    targetInfo.target,
    targetInfo.archiveExtension,
  );
  return `https://github.com/${REPOSITORY}/releases/download/${version}/${filename}`;
}

function installDirectory(targetInfo) {
  return path.join(INSTALL_ROOT, targetInfo.target);
}

function installedBinaryPath(targetInfo) {
  return path.join(installDirectory(targetInfo), targetInfo.binaryName);
}

module.exports = {
  BINARY_NAME,
  INSTALL_ROOT,
  REPOSITORY,
  TARGETS,
  currentTarget,
  installDirectory,
  installedBinaryPath,
  releaseAssetName,
  releaseAssetUrl,
  releaseVersion,
};
