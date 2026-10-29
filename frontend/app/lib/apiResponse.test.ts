import assert from "node:assert/strict";
import test from "node:test";
import { readApiResponse, readApiError } from "./apiResponse.ts";

test("reads JSON DTOs and plain text upload responses", async () => {
  assert.deepEqual(await readApiResponse(Response.json({ totalApplications: 3 })), { totalApplications: 3 });
  assert.equal(await readApiResponse(new Response("https://files.example/avatar.png")), "https://files.example/avatar.png");
  assert.equal(await readApiResponse(new Response(null, { status: 204 })), undefined);
});

test("downloads CSV as a Blob preserving Vietnamese text and content type", async () => {
  const csv = "Tên,Trạng thái\r\nNguyễn Văn A,Screening\r\n";
  const blob = await readApiResponse(new Response(csv, { headers: { "Content-Type": "text/csv; charset=utf-8" } }), "blob");
  assert.ok(blob instanceof Blob);
  assert.equal(await blob.text(), csv);
  assert.equal(blob.type.replace(/\s/g, ""), "text/csv;charset=utf-8");
});

test("shows ProblemDetails, validation errors and legacy messages", async () => {
  assert.equal(await readApiError(Response.json({ detail: "Không thể chuyển trạng thái", title: "Validation" }, { status: 400 })), "Không thể chuyển trạng thái");
  assert.equal(await readApiError(Response.json({ title: "Không có quyền" }, { status: 403 })), "Không có quyền");
  assert.equal(await readApiError(Response.json({ errors: { Rating: ["Chọn từ 1 đến 5 sao"] } }, { status: 400 })), "Chọn từ 1 đến 5 sao");
  assert.equal(await readApiError(Response.json({ message: "Job not found" }, { status: 404 })), "Job not found");
  assert.equal(await readApiError(new Response("Bad gateway", { status: 502 })), "Yêu cầu thất bại (502)");
});
