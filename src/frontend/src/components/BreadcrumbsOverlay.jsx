import { breadcrumbsAtom } from "@/data/atoms";
import { useAtom } from "jotai";

export default function BreadcrumbOverlay({}) {
  const [breadcrumbs] = useAtom(breadcrumbsAtom);

  const withoutMostRecentBreadcrumb = breadcrumbs.slice(0, -1);

  return (
    <>
      <div className="opacity-60 hover:opacity-100">
        {withoutMostRecentBreadcrumb.length != 0 ? (
          <div className="max-w-5 max-h-5 mb-4 ms-20">
            <svg
              viewBox="0 0 100 265"
              xmlns="http://www.w3.org/2000/svg"
              className="w-full h-full"
            >
              <rect height="100" width="23" y="90" x="38.5" fill="#016630" />
              <ellipse ry="30" rx="30" cy="60" cx="50" fill="#016630" />{" "}
            </svg>
          </div>
        ) : null}
        {withoutMostRecentBreadcrumb.map((breadcrumb) => {
          return (
            <div
              key={breadcrumb.historyId}
              className="text-green-800 bg-white border-green-700  border-2 rounded-lg p-3 mb-5 max-w-50 min-w-50"
            >
              {breadcrumb.label}
            </div>
          );
        })}
      </div>
    </>
  );
}
