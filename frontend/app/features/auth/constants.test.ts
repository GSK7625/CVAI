import assert from "node:assert/strict";
import test from "node:test";
import {
  isLoginRoute,
  getDefaultDashboard,
  getSafeReturnUrl,
  LOGIN_ROUTES,
} from "./constants.ts";

test("identifies login routes correctly", () => {
  assert.equal(isLoginRoute("/login"), true);
  assert.equal(isLoginRoute("/login-employer"), true);
  assert.equal(isLoginRoute("/login-admin"), true);
  // trailing slash normalization
  assert.equal(isLoginRoute("/login/"), true);
  assert.equal(isLoginRoute("/login-employer/"), true);

  // non-login auth routes
  assert.equal(isLoginRoute("/register"), false);
  assert.equal(isLoginRoute("/forgot-password"), false);
  assert.equal(isLoginRoute("/"), false);
  assert.equal(isLoginRoute("/hr"), false);
});

test("returns correct default dashboard by role", () => {
  assert.equal(getDefaultDashboard("candidate"), "/");
  assert.equal(getDefaultDashboard("employer"), "/hr");
  assert.equal(getDefaultDashboard("admin"), "/admin");
});

test("validates safe returnTo urls and prevents open redirect", () => {
  // Valid internal paths
  assert.equal(getSafeReturnUrl("/candidate/applications"), "/candidate/applications");
  assert.equal(getSafeReturnUrl("/hr/jobs?page=2"), "/hr/jobs?page=2");
  assert.equal(getSafeReturnUrl("/"), "/");

  // Malicious open redirect attacks
  assert.equal(getSafeReturnUrl("//evil.com"), null);
  assert.equal(getSafeReturnUrl("/\\evil.com"), null);
  assert.equal(getSafeReturnUrl("https://evil.com"), null);
  assert.equal(getSafeReturnUrl("http://evil.com"), null);
  assert.equal(getSafeReturnUrl("javascript:alert(1)"), null);
  assert.equal(getSafeReturnUrl(""), null);
  assert.equal(getSafeReturnUrl(null), null);
  assert.equal(getSafeReturnUrl(undefined), null);
});
