import assert from "node:assert/strict";
import test from "node:test";
import { getHrWorkspaceRedirect } from "./hrWorkspace.ts";

test("keeps signed-in HR inside each supported HR screen", () => {
  for (const path of ["/hr", "/hr/jobs", "/hr/pipeline", "/hr/interviews", "/hr/company", "/hr/profile", "/hr/jobs/"]) {
    assert.equal(getHrWorkspaceRedirect("employer", path), null);
  }
});

test("returns HR to its dashboard from public, auth, and other role screens", () => {
  for (const path of ["/", "/jobs/123", "/cv/templates", "/login", "/register", "/candidate", "/admin", "/unknown", "/hr/unknown", "/hr-other"]) {
    assert.equal(getHrWorkspaceRedirect("employer", path), "/hr");
  }
});

test("lets logged-out users reach login and public pages", () => {
  assert.equal(getHrWorkspaceRedirect(null, "/login"), null);
  assert.equal(getHrWorkspaceRedirect(undefined, "/"), null);
});

test("preserves navigation for Candidate and Admin", () => {
  for (const role of ["candidate", "admin"]) {
    assert.equal(getHrWorkspaceRedirect(role, "/"), null);
    assert.equal(getHrWorkspaceRedirect(role, "/candidate"), null);
    assert.equal(getHrWorkspaceRedirect(role, "/admin"), null);
  }
});
