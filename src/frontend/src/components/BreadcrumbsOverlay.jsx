import { breadcrumbsAtom } from "@/data/atoms";
import { useAtom } from "jotai";

export default function BreadcrumbOverlay({}) {
  const [breadcrumbs, setBreadcrumbs] = useAtom(breadcrumbsAtom);

  return (
    <>
      <div className="opacity-60 hover:opacity-100">
        {breadcrumbs.map((breadcrumb) => {
          return (
            <p
              key={breadcrumb.historyId}
              className="text-green-800 bg-white border-green-700  border-2 rounded-lg p-3 mb-5 max-w-50"
            >
              {breadcrumb.label}
            </p>
          );
        })}
      </div>
    </>
  );
}
