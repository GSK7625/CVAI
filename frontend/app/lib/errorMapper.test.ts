import assert from "node:assert/strict";
import test from "node:test";
import { translateErrorMessage, getStatusFallbackMessage } from "./errorMapper.ts";

test("translates exact auth error messages", () => {
  assert.equal(
    translateErrorMessage("Invalid email or password."),
    "Email hoặc mật khẩu không chính xác.",
  );
  assert.equal(
    translateErrorMessage("Account has been disabled. Please contact support."),
    "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ hỗ trợ.",
  );
  assert.equal(
    translateErrorMessage("ACCOUNT_ALREADY_EXISTS"),
    "Email này đã được đăng ký trên hệ thống.",
  );
  assert.equal(
    translateErrorMessage("A valid email address is required."),
    "Địa chỉ email không đúng định dạng.",
  );
  assert.equal(
    translateErrorMessage("Email is required."),
    "Vui lòng nhập địa chỉ email.",
  );
});

test("translates ASP.NET Identity password requirements", () => {
  assert.equal(
    translateErrorMessage("Passwords must have at least one non alphanumeric character."),
    "Mật khẩu phải chứa ít nhất một ký tự đặc biệt (!@#$%^&*...).",
  );
  assert.equal(
    translateErrorMessage("Passwords must have at least one digit ('0'-'9')."),
    "Mật khẩu phải chứa ít nhất một chữ số (0-9).",
  );
  assert.equal(
    translateErrorMessage("Passwords must be at least 6 characters."),
    "Mật khẩu phải có độ dài tối thiểu 6 ký tự.",
  );
});

test("translates regex pattern based messages", () => {
  assert.equal(
    translateErrorMessage("Email 'candidate@futurecv.vn' is already taken."),
    'Email "candidate@futurecv.vn" đã được sử dụng bởi tài khoản khác.',
  );
  assert.equal(
    translateErrorMessage("Cannot withdraw an application currently in 'Accepted' status."),
    'Không thể rút đơn ứng tuyển đang ở trạng thái "Accepted".',
  );
  assert.equal(
    translateErrorMessage("The Email field is required."),
    'Trường "Email" không được để trống.',
  );
});

test("translates CV and file upload errors", () => {
  assert.equal(
    translateErrorMessage("CV file size must not exceed 5 MB."),
    "Dung lượng tệp CV không được vượt quá 5MB.",
  );
  assert.equal(
    translateErrorMessage("Only PDF files are accepted."),
    "Chỉ chấp nhận tệp định dạng PDF.",
  );
  assert.equal(
    translateErrorMessage("Avatar must be a JPG or PNG file."),
    "Ảnh đại diện phải có định dạng JPG hoặc PNG.",
  );
});

test("preserves existing Vietnamese messages", () => {
  const vn = "Tải lên CV mới thành công!";
  assert.equal(translateErrorMessage(vn), vn);
});

test("provides status code fallbacks for unknown or empty messages", () => {
  assert.equal(
    translateErrorMessage("", 404),
    "Không tìm thấy dữ liệu yêu cầu.",
  );
  assert.equal(
    getStatusFallbackMessage(401),
    "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  );
  assert.equal(
    getStatusFallbackMessage(500),
    "Hệ thống đang gặp sự cố. Vui lòng thử lại sau ít phút.",
  );
});
