/**
 * @file errorMapper.ts
 * @description Bộ từ điển ánh xạ và chuẩn hóa thông báo lỗi từ Backend / Identity / RFC 7807
 * sang tiếng Việt tự nhiên, chuẩn mực và thân thiện với người dùng.
 */

/** Danh sách ánh xạ chính xác (Exact match, không phân biệt hoa thường) */
const EXACT_ERROR_MAP: Record<string, string> = {
  // --- Auth & Identity ---
  "invalid email or password.": "Email hoặc mật khẩu không chính xác.",
  "invalid email or password": "Email hoặc mật khẩu không chính xác.",
  "account has been disabled. please contact support.": "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ hỗ trợ.",
  "account has been disabled.": "Tài khoản của bạn đã bị khóa.",
  "user account is currently active.": "Tài khoản người dùng đang hoạt động.",
  "invalid or expired reset token.": "Mã xác thực đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.",
  "refresh token is required.": "Yêu cầu mã làm mới phiên đăng nhập.",
  "invalid or expired refresh token.": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.",
  "refresh token has expired. please log in again.": "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  "account_already_exists": "Email này đã được đăng ký trên hệ thống.",
  "account already exists.": "Tài khoản này đã tồn tại trên hệ thống.",
  "target user not found.": "Không tìm thấy thông tin người dùng.",
  "passwords must have at least one non alphanumeric character.": "Mật khẩu phải chứa ít nhất một ký tự đặc biệt (!@#$%^&*...).",
  "passwords must have at least one digit ('0'-'9').": "Mật khẩu phải chứa ít nhất một chữ số (0-9).",
  "passwords must have at least one uppercase ('a'-'z').": "Mật khẩu phải chứa ít nhất một chữ cái in hoa (A-Z).",
  "passwords must have at least one lowercase ('a'-'z').": "Mật khẩu phải chứa ít nhất một chữ cái viết thường (a-z).",
  "passwords must be at least 6 characters.": "Mật khẩu phải có độ dài tối thiểu 6 ký tự.",

  // --- Forgot & Reset Password ---
  "email is required.": "Vui lòng nhập địa chỉ email.",
  "a valid email address is required.": "Địa chỉ email không đúng định dạng.",
  "if the email exists, a reset link has been sent.": "Nếu email tồn tại trong hệ thống, liên kết đặt lại mật khẩu đã được gửi.",
  "reset token is required.": "Mã xác thực đặt lại mật khẩu không được để trống.",
  "new password is required.": "Vui lòng nhập mật khẩu mới.",
  "new password must be between 6 and 25 characters.": "Mật khẩu mới phải có độ dài từ 6 đến 25 ký tự.",
  "new password must contain at least one uppercase letter.": "Mật khẩu mới phải chứa ít nhất một chữ cái in hoa (A-Z).",
  "new password must contain at least one lowercase letter.": "Mật khẩu mới phải chứa ít nhất một chữ cái viết thường (a-z).",
  "new password must contain at least one numeric digit.": "Mật khẩu mới phải chứa ít nhất một chữ số (0-9).",
  "passwords do not match.": "Mật khẩu xác nhận không khớp.",

  // --- CV & Profile ---
  "cv file size must not exceed 5 mb.": "Dung lượng tệp CV không được vượt quá 5MB.",
  "only pdf files are accepted.": "Chỉ chấp nhận tệp định dạng PDF.",
  "please select a pdf file to upload.": "Vui lòng chọn một tệp PDF để tải lên.",
  "avatar must be a jpg or png file.": "Ảnh đại diện phải có định dạng JPG hoặc PNG.",
  "avatar file size must not exceed 5 mb.": "Kích thước ảnh đại diện không được vượt quá 5MB.",
  "candidate profile not found.": "Không tìm thấy thông tin hồ sơ ứng viên.",
  "cv not found.": "Không tìm thấy hồ sơ CV trong hệ thống.",
  "target cv not found.": "Không tìm thấy hồ sơ CV được chỉ định.",
  "title is required.": "Vui lòng nhập tiêu đề hồ sơ CV.",
  "primary cv cannot be deleted.": "Không thể xóa CV đang được đặt làm hồ sơ chính.",
  "phone number must be a valid vietnamese number": "Số điện thoại không hợp lệ (cần đúng 10 số bắt đầu bằng 0, ví dụ: 0912345678).",

  // --- Job & Applications ---
  "job is closed, expired, or not approved for applications.": "Công việc này đã đóng, hết hạn hoặc chưa mở nhận hồ sơ ứng tuyển.",
  "you cannot apply to your own job posting.": "Bạn không thể tự ứng tuyển vào tin tuyển dụng do chính mình đăng.",
  "you cannot apply to a job posted by your own company.": "Bạn không thể ứng tuyển vào công việc do công ty của mình đăng tải.",
  "no active cv found. please upload a cv first.": "Không tìm thấy CV hợp lệ. Vui lòng tải lên CV trước khi thực hiện.",
  "application has already been withdrawn.": "Đơn ứng tuyển này đã được rút trước đó.",
  "cannot update status of a withdrawn application.": "Không thể cập nhật trạng thái của đơn ứng tuyển đã được rút.",
  "you cannot report your own job posting.": "Bạn không thể tự báo cáo tin tuyển dụng của mình.",
  "job not found.": "Không tìm thấy thông tin công việc yêu cầu.",
  "application not found.": "Không tìm thấy thông tin đơn ứng tuyển.",
  "job id is required": "Mã việc làm không được để trống.",
  "application id is required": "Mã đơn ứng tuyển không được để trống.",

  // --- Employer & Admin ---
  "employer is not linked to any company. please register company first.": "Tài khoản nhà tuyển dụng chưa liên kết công ty. Vui lòng tạo hồ sơ công ty trước.",
  "employer has no linked company.": "Nhà tuyển dụng chưa liên kết với bất kỳ công ty nào.",
  "employer profile not found.": "Không tìm thấy hồ sơ nhà tuyển dụng.",
  "tax code is already registered by another company.": "Mã số thuế này đã được đăng ký bởi công ty khác.",
  "company not found.": "Không tìm thấy thông tin công ty.",
  "lock reason is required.": "Vui lòng nhập lý do khóa tài khoản.",
  "ban reason is required.": "Vui lòng nhập lý do cấm tài khoản.",
  "status is required.": "Vui lòng chọn trạng thái hợp lệ.",
  "access denied.": "Bạn không có quyền thực hiện thao tác này.",
  "domain rule violation": "Dữ liệu không đáp ứng quy tắc nghiệp vụ.",
  "one or more validation errors occurred.": "Dữ liệu nhập vào chưa hợp lệ. Vui lòng kiểm tra lại.",
};

/** Quy tắc khớp theo biểu thức chính quy (Regex Pattern Matching) */
const PATTERN_RULES: Array<{
  pattern: RegExp;
  replace: (...args: string[]) => string;
}> = [
  // Email taken: "Email 'abc@xyz.com' is already taken."
  {
    pattern: /email\s+'([^']+)'\s+is already taken\./i,
    replace: (_, email) => `Email "${email}" đã được sử dụng bởi tài khoản khác.`,
  },
  // Username taken: "User name 'abc' is already taken."
  {
    pattern: /user\s*name\s+'([^']+)'\s+is already taken\./i,
    replace: (_, username) => `Tên tài khoản "${username}" đã tồn tại.`,
  },
  // Cannot withdraw in status: "Cannot withdraw an application currently in 'Accepted' status."
  {
    pattern: /cannot withdraw an application currently in '([^']+)' status\./i,
    replace: (_, status) => `Không thể rút đơn ứng tuyển đang ở trạng thái "${status}".`,
  },
  // Invalid application status: "Invalid application status: 'Foo'."
  {
    pattern: /invalid application status:\s*'([^']*)'\./i,
    replace: (_, status) => `Trạng thái ứng tuyển "${status}" không hợp lệ.`,
  },
  // Failed to upload avatar: "Failed to upload avatar: ..."
  {
    pattern: /failed to upload avatar:\s*(.*)/i,
    replace: () => "Tải ảnh đại diện lên máy chủ thất bại. Vui lòng thử lại.",
  },
  // Failed to lock/unlock user: "Failed to lock user: ..."
  {
    pattern: /failed to lock user:\s*(.*)/i,
    replace: () => "Khóa tài khoản thất bại. Vui lòng thử lại.",
  },
  {
    pattern: /failed to unlock user:\s*(.*)/i,
    replace: () => "Mở khóa tài khoản thất bại. Vui lòng thử lại.",
  },
  // ASP.NET DataAnnotations: "The {Field} field is required."
  {
    pattern: /the\s+([a-zA-Z0-9_]+)\s+field is required\./i,
    replace: (_, field) => `Trường "${field}" không được để trống.`,
  },
  // ASP.NET DataAnnotations: "The {Field} field is not a valid e-mail address."
  {
    pattern: /the\s+([a-zA-Z0-9_]+)\s+field is not a valid e-mail address\./i,
    replace: () => "Địa chỉ email không đúng định dạng.",
  },
];

/** Fallback tiếng Việt theo mã trạng thái HTTP */
export function getStatusFallbackMessage(statusCode?: number): string {
  switch (statusCode) {
    case 400:
      return "Yêu cầu không hợp lệ. Vui lòng kiểm tra lại thông tin.";
    case 401:
      return "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
    case 403:
      return "Bạn không có quyền thực hiện thao tác này.";
    case 404:
      return "Không tìm thấy dữ liệu yêu cầu.";
    case 408:
      return "Hết thời gian chờ phản hồi từ máy chủ.";
    case 409:
      return "Dữ liệu đã tồn tại hoặc đang có xung đột.";
    case 422:
      return "Dữ liệu xử lý không hợp lệ.";
    case 500:
    case 502:
    case 503:
    case 504:
      return "Hệ thống đang gặp sự cố. Vui lòng thử lại sau ít phút.";
    default:
      return statusCode ? `Yêu cầu thất bại (Mã lỗi ${statusCode}).` : "Đã xảy ra lỗi. Vui lòng thử lại.";
  }
}

/**
 * Dịch thông điệp lỗi sang tiếng Việt.
 * Nếu không tìm thấy mapping phù hợp, trả về thông điệp gốc (nếu đã là tiếng Việt)
 * hoặc fallback theo HTTP status code nếu là chuỗi tiếng Anh không xác định.
 */
export function translateErrorMessage(rawMessage?: string | null, statusCode?: number): string {
  if (!rawMessage || typeof rawMessage !== "string") {
    return getStatusFallbackMessage(statusCode);
  }

  const trimmed = rawMessage.trim();
  const lower = trimmed.toLowerCase();

  // 1. Khớp chính xác trong từ điển
  if (EXACT_ERROR_MAP[lower]) {
    return EXACT_ERROR_MAP[lower];
  }

  // 2. Khớp theo regex pattern
  for (const { pattern, replace } of PATTERN_RULES) {
    const match = trimmed.match(pattern);
    if (match) {
      return replace(...match);
    }
  }

  // 3. Nếu chuỗi đã chứa tiếng Việt có dấu, giữ nguyên chuỗi
  const hasVietnameseAccent = /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(trimmed);
  if (hasVietnameseAccent) {
    return trimmed;
  }

  // 4. Nếu là chuỗi tiếng Anh chung chung từ server hoặc status text
  if (lower === "not found" || lower === "not found.") return "Không tìm thấy dữ liệu yêu cầu.";
  if (lower === "unauthorized" || lower === "unauthorized.") return "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";
  if (lower === "forbidden" || lower === "forbidden.") return "Bạn không có quyền thực hiện thao tác này.";
  if (lower === "bad request" || lower === "bad request.") return "Dữ liệu yêu cầu không hợp lệ.";
  if (lower === "internal server error" || lower === "internal server error.") return "Hệ thống đang gặp sự cố. Vui lòng thử lại sau.";

  // 5. Nếu có statusCode xác định, ưu tiên trả về thông điệp thân thiện theo status
  if (statusCode && statusCode >= 400) {
    return getStatusFallbackMessage(statusCode);
  }

  return trimmed;
}
