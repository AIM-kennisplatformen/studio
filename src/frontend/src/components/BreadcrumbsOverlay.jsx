import { breadcrumbsAtom, centerNodeAtom } from "@/data/atoms";
import { useAtom } from "jotai";

export default function BreadcrumbOverlay({}) {
  const [breadcrumbs] = useAtom(breadcrumbsAtom);
  const [, setCenterNodeId] = useAtom(centerNodeAtom);

  const withoutMostRecentBreadcrumb = breadcrumbs.slice(0, -1);

  return (
    <div className="flex flex-col items-center opacity-60 hover:opacity-100">
      {withoutMostRecentBreadcrumb.length != 0 ? (
        <div className="-mb-[2px] flex w-50 items-center justify-center">
          <svg
            viewBox="8 30 84 175"
            xmlns="http://www.w3.org/2000/svg"
            className="h-8 w-6"
            style={{ display: "block" }}>
            <rect height="115" width="23" y="90" x="38.5" fill="#016630" />
            <ellipse ry="30" rx="30" cy="60" cx="50" fill="#016630" />
          </svg>
        </div>
      ) : null}
      {withoutMostRecentBreadcrumb.map((breadcrumb, index) => {
        return (
          <div
            key={breadcrumb.historyId}
            className={`max-w-50 min-w-50 cursor-default rounded-lg border-2 border-green-700 bg-white p-3 text-green-800 last:cursor-pointer ${index < withoutMostRecentBreadcrumb.length - 1 ? "mb-2" : ""}`}
            onClick={() => setCenterNodeId(breadcrumb.originNodeId)}>
            {breadcrumb.label}
          </div>
        );
      })}
    </div>
  );
}
