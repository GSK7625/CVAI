export interface AuthResponseDto {
  accessToken: string;
  accessTokenExpiresAt?: string;
  refreshToken: string;
  role: "candidate" | "employer" | "admin";
  id?: string;
  email?: string;
  fullName?: string;
  user?: {
    id?: string;
    email?: string;
    fullName?: string;
  };
}

export interface LoginDto {
  email: string;
  password: string;
}

export interface RegisterCandidateDto {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
  phoneNumber?: string;
}

export interface RegisterEmployerDto {
  email: string;
  password: string;
  confirmPassword: string;
  fullName: string;
  phone: string;
  gender: string;
  companyName: string;
  locationId?: string;
  wardName?: string;
}

export interface ForgotPasswordDto {
  email: string;
}

export interface ResetPasswordDto {
  email: string;
  token: string;
  newPassword: string;
  confirmNewPassword: string;
}

export interface MessageDto {
  message: string;
}
