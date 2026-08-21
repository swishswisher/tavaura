import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";

const projectRoot = process.cwd();
const apiRoot = path.join(projectRoot, "src", "app", "api");
const signupPage = path.join(projectRoot, "src", "app", "signup", "page.tsx");

function findRouteHandlers(directory) {
  if (!existsSync(directory)) {
    return [];
  }

  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      return findRouteHandlers(entryPath);
    }

    return entry.name === "route.ts" ? [path.relative(projectRoot, entryPath)] : [];
  });
}

test("the frontend exposes no unauthenticated mutation route handlers", () => {
  assert.deepEqual(findRouteHandlers(apiRoot), []);
});

test("signup is a static invitation-only page", () => {
  const source = readFileSync(signupPage, "utf8");
  assert.match(source, /invitation-only/i);
  assert.doesNotMatch(source, /fetch\s*\(/);
  assert.doesNotMatch(source, /console\.log/);
  assert.doesNotMatch(source, /<form/i);
});
