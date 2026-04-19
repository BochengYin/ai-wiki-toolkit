const path = require("path");
const TARGETS = require("./platform-targets.json");

function currentTarget(platform = process.platform, arch = process.arch) {
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
  currentTarget,
  installedBinaryPath,
  resolvePlatformPackageRoot,
};
