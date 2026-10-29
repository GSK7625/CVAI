import assert from "node:assert/strict";
import test from "node:test";
import { prepareRequestBody } from "./requestBody.ts";

test("serializes JSON DTOs for the shared fetcher", () => {
  assert.deepEqual(prepareRequestBody({ title: "Frontend Developer" }), {
    body: '{"title":"Frontend Developer"}',
    hasJsonBody: true,
  });
});

test("preserves FormData so the browser can add its multipart boundary", () => {
  const form = new FormData();
  form.append("avatar", new Blob(["avatar"]), "avatar.png");

  const result = prepareRequestBody(form);

  assert.equal(result.body, form);
  assert.equal(result.hasJsonBody, false);
});

test("does not create a body or content type signal for undefined", () => {
  assert.deepEqual(prepareRequestBody(undefined), {
    body: undefined,
    hasJsonBody: false,
  });
});
