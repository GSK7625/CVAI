import assert from "node:assert/strict";
import test from "node:test";
import { QueryClient, MutationObserver } from "@tanstack/query-core";
import type { JobMatchPreviewResponse } from "../types";
import { previewMatchMutationOptions } from "./previewMatchMutation.ts";

const result = (cvId: string) => ({ cvId, jobId: "job" }) as JobMatchPreviewResponse;

test("repeated analysis sends the selected CV id on every call", async () => {
  const ids: string[] = [];
  const options = previewMatchMutationOptions("job", async (_, id) => { ids.push(id); return result(id); });
  await options.mutationFn("cv-intern2");
  await options.mutationFn("cv-intern2");
  assert.deepEqual(ids, ["cv-intern2", "cv-intern2"]);
});

test("newly uploaded CV is sent explicitly rather than the previous selection", async () => {
  const ids: string[] = [];
  const options = previewMatchMutationOptions("job", async (_, id) => { ids.push(id); return result(id); });
  await options.mutationFn("old-cv");
  await options.mutationFn("new-upload");
  assert.deepEqual(ids, ["old-cv", "new-upload"]);
});

test("click events and mismatched response identities cannot become a CV result", async () => {
  let called = false;
  const options = previewMatchMutationOptions("job", async () => { called = true; return result("wrong-cv"); });
  await assert.rejects(options.mutationFn({ type: "click" } as unknown as string), /chọn CV/);
  assert.equal(called, false);
  await assert.rejects(options.mutationFn("cv-intern2"), /không thuộc/);
});

test("a slow previous request cannot overwrite the latest selected CV result", async () => {
  const resolvers = new Map<string, (value: JobMatchPreviewResponse) => void>();
  const client = new QueryClient();
  const observer = new MutationObserver(client, previewMatchMutationOptions("job", (_, id) =>
    new Promise<JobMatchPreviewResponse>(resolve => resolvers.set(id, resolve))));
  const unsubscribe = observer.subscribe(() => {});
  try {
    const old = observer.mutate("old-cv");
    await new Promise(resolve => setTimeout(resolve, 0));
    const latest = observer.mutate("new-cv");
    await new Promise(resolve => setTimeout(resolve, 0));
    resolvers.get("new-cv")!(result("new-cv"));
    await latest;
    resolvers.get("old-cv")!(result("old-cv"));
    await old;
    assert.equal(observer.getCurrentResult().data?.cvId, "new-cv");
  } finally { unsubscribe(); client.clear(); }
});
