const path = require("path");
const fs = require("fs");
const TARGETS = require("./platform-targets.json");

function detectLibc(platform = process.platform) {
  if (platform !== "linux") {
    return null;
  }

  try {
    if (process.report && typeof process.report.getReport === "function") {
      const report = process.report.getReport();
      if (report && report.header && report.header.glibcVersionRuntime) {
        return "glibc";
      }
    }
  } catch (_error) {
    // Fall through to file-based heuristics.
  }

  try {
    if (fs.existsSync("/etc/alpine-release")) {
      return "musl";
    }
  } catch (_error) {
    // Ignore file access failures and keep falling back.
  }

  return "glibc";
}

function currentTarget(platform = process.platform, arch = process.arch, libc = detectLibc(platform)) {
  const qualifiedKey = libc ? `${platform}-${arch}-${libc}` : null;
  if (qualifiedKey && TARGETS[qualifiedKey]) {
    return TARGETS[qualifiedKey];
  }
  return TARGETS[`${platform}-${arch}`] || null;
}

function resolvePlatformPackageRoot(targetInfo) {
  const packageJsonPath = require.resolve(`${targetInfo.package_name}/package.json`, {
    paths: [path.join(__dirname, "..")],
  });
  return path.dirname(packageJsonPath);
}

function installedBinaryPath(targetInfo) {
  return path.join(
    resolvePlatformPackageRoot(targetInfo),
    "bin",
    targetInfo.binary_name,
  );
}

module.exports = {
  TARGETS,
  detectLibc,
  currentTarget,
  installedBinaryPath,
  resolvePlatformPackageRoot,
};
