const hrWorkspacePaths = new Set([
  "/hr",
  "/hr/jobs",
  "/hr/pipeline",
  "/hr/interviews",
  "/hr/company",
  "/hr/profile",
]);

/** Keep an authenticated Employer within the registered HR workspace screens. */
export function getHrWorkspaceRedirect(role: string | null | undefined, pathname: string): "/hr" | null {
  if (role !== "employer") return null;
  const path = pathname.replace(/\/+$/, "");
  return hrWorkspacePaths.has(path) ? null : "/hr";
}
