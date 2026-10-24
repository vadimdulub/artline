// Run a source snapshot in the OS temp directory. Existing dev servers, generated
// type declarations and build caches in the user's checkout remain untouched.
import { cp, mkdir, mkdtemp, readFile, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";

const source = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const workspace = await mkdtemp(join(tmpdir(), "artline-responsive-web-"));
const snapshot = join(workspace, "apps", "web");
await mkdir(snapshot, { recursive: true });
for (const name of ["app", "components", "lib", "package.json", "next.config.ts", "tsconfig.json", "next-env.d.ts", "vitest.setup.ts"]) await cp(join(source, name), join(snapshot, name), { recursive: true });
for (const name of ["node_modules", "public", "content"]) await symlink(join(source, name), join(snapshot, name));
// Test the production bundle with next start. Standalone deployment packaging
// cannot copy traced files across the snapshot's read-only module symlinks.
const configPath = join(snapshot, "next.config.ts");
const config = await readFile(configPath, "utf8");
if (!config.includes("export default nextConfig;")) throw new Error("Update the responsive snapshot config adapter for the current Next config export.");
await writeFile(configPath, config.replace("export default nextConfig;", "export default { ...nextConfig, output: undefined };"));
// Static catalogue/image trees contain no application TypeScript and can be
// large or changing during research. Keep the compiler's scan bounded to code.
const tsconfigPath = join(snapshot, "tsconfig.json");
const tsconfig = JSON.parse(await readFile(tsconfigPath, "utf8"));
tsconfig.include = ["next-env.d.ts", "vitest.setup.ts", "app/**/*.ts", "app/**/*.tsx", "components/**/*.ts", "components/**/*.tsx", "lib/**/*.ts", "lib/**/*.tsx", ".next/types/**/*.ts"];
await writeFile(tsconfigPath, JSON.stringify(tsconfig, null, 2) + "\n");
// Preserve relative imports used by the existing source/type checks.
await symlink(resolve(source, "../server"), join(workspace, "apps", "server"));
for (const name of ["docs", "content"]) await symlink(resolve(source, "../..", name), join(workspace, name));
const awake = process.platform === "darwin" ? spawn("/usr/bin/caffeinate", ["-i"], { stdio: "ignore" }) : undefined;
let child, stopping = false;
for (const signal of ["SIGTERM", "SIGINT"]) process.on(signal, () => { stopping = true; child?.kill(signal); });
async function next(args) {
  return new Promise((resolveCode, reject) => {
    child = spawn(process.execPath, [join(source, "node_modules/next/dist/bin/next"), ...args], { cwd: snapshot, stdio: "inherit", env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" } });
    child.once("error", reject);
    child.once("exit", code => resolveCode(code ?? 0));
  });
}
try {
  const built = await next(["build", snapshot, "--webpack"]);
  process.exitCode = built;
  if (!built && !stopping) process.exitCode = await next(["start", snapshot, "--hostname", "127.0.0.1", "--port", "3097"]);
} finally {
  awake?.kill();
  await rm(workspace, { recursive: true, force: true });
}
