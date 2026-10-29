import type { ClientLoaderFunctionArgs } from "react-router";
import { useParams } from "react-router";
import { requireRole } from "~/guards/requireRole";
import { ApplyFormView } from "~/features/candidate/components/apply/ApplyFormView";

export const clientLoader = ({ request }: ClientLoaderFunctionArgs) => {
  const url = new URL(request.url);
  const returnTo = `${url.pathname}${url.search}`;
  const { user } = requireRole(["candidate"], returnTo);
  return { user };
};

export default function ApplyFormPage() {
  const { jobId = "" } = useParams();
  return <ApplyFormView jobId={jobId} />;
}
