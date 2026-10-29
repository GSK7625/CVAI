import { fetcher } from "~/lib/fetcher";
import type { AuthResponseDto, ForgotPasswordDto, LoginDto, MessageDto, RegisterCandidateDto, RegisterEmployerDto, ResetPasswordDto } from "../types";

export function authService() {
  return {
    login: (dto: LoginDto) =>
      fetcher<AuthResponseDto>("/api/auth/login", { method: "POST", body: dto }),

    registerCandidate: (dto: RegisterCandidateDto) =>
      fetcher<AuthResponseDto>("/api/auth/register/candidate", { method: "POST", body: dto }),

    registerEmployer: (dto: RegisterEmployerDto) =>
      fetcher<AuthResponseDto>("/api/auth/register/employer", { method: "POST", body: dto }),

    forgotPassword: (dto: ForgotPasswordDto) =>
      fetcher<MessageDto>("/api/auth/forgot-password", { method: "POST", body: dto }),

    resetPassword: (dto: ResetPasswordDto) =>
      fetcher<MessageDto>("/api/auth/reset-password", { method: "POST", body: dto }),

    logout: (refreshToken: string | null) =>
      fetcher<MessageDto>("/api/auth/logout", { method: "POST", body: { refreshToken }, auth: true }),
  };
}
