import assert from "node:assert/strict";
import test from "node:test";
import { buildBuilderCvPlainText } from "./cvBuilderText.ts";

test("formats Builder CV sections into readable Vietnamese plain text", () => {
  const text = buildBuilderCvPlainText({
    personalInfo: {
      fullName: "Nguyễn Văn A",
      title: "Backend Developer",
      email: "a@example.com",
      phone: "0901234567",
      location: "Hà Nội",
      website: "https://github.com/nguyenvana",
      summary: "3 năm kinh nghiệm phát triển hệ thống .NET và PostgreSQL.",
    },
    experiences: [
      {
        role: "Software Engineer",
        company: "Techcom",
        startDate: "2023",
        endDate: "Hiện tại",
        description: "Xây dựng API tuyển dụng và tối ưu truy vấn SQL.",
      },
    ],
    educations: [
      {
        degree: "Kỹ sư CNTT",
        school: "ĐH Bách Khoa",
        startDate: "2018",
        endDate: "2022",
        gpa: "3.5/4.0",
      },
    ],
    skills: ["C#", ".NET", "PostgreSQL"],
  });

  assert.match(text, /Nguyễn Văn A/);
  assert.match(text, /SUMMARY[\s\S]*3 năm kinh nghiệm/);
  assert.match(text, /EXPERIENCE[\s\S]*Software Engineer - Techcom \(2023 - Hiện tại\)/);
  assert.match(text, /EDUCATION[\s\S]*Kỹ sư CNTT - ĐH Bách Khoa/);
  assert.match(text, /SKILLS[\s\S]*C#, \.NET, PostgreSQL/);
  assert.equal(text.startsWith("{"), false);
  assert.equal(text.startsWith("["), false);
});

test("omits empty sections and clamps output to 30000 characters", () => {
  const emptyText = buildBuilderCvPlainText({
    personalInfo: {},
    experiences: [{ role: "", company: "", description: "" }],
    educations: [{ degree: "", school: "" }],
    skills: ["  ", ""],
  });
  assert.equal(emptyText, "");

  const longSummary = "A".repeat(35000);
  const clamped = buildBuilderCvPlainText({
    personalInfo: { fullName: "Candidate", summary: longSummary },
    experiences: [],
    educations: [],
    skills: [],
  });
  assert.equal(clamped.length, 30000);
});
