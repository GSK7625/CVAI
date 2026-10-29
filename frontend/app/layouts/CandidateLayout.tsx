import type { ClientLoaderFunctionArgs } from "react-router";
import { Outlet } from "react-router";
import { requireRole } from "~/guards/requireRole";
import { PublicHeader } from "./public/PublicHeader";
import { PublicFooter } from "./public/PublicFooter";

export const clientLoader = ({ request }: ClientLoaderFunctionArgs) => {
  const url = new URL(request.url);
  const returnTo = `${url.pathname}${url.search}`;
  const { user } = requireRole(["candidate"], returnTo);
  return { user };
};

export default function CandidateLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-background print:bg-white">
      <div className="print:hidden">
        <PublicHeader />
      </div>

      <main className="container-page mx-auto flex-1 px-margin-mobile py-8 md:px-margin-desktop print:p-0 print:m-0 print:max-w-none print:w-full">
        <Outlet />
      </main>

      <div className="print:hidden">
        <PublicFooter />
      </div>
    </div>
  );
}
