import {
  breadcrumbsAtom,
  centerNodeAtom,
  lastCrumbScreenCenterAtom,
  selectedNodeVerticalPositionAtom,
} from "@/data/atoms";
import { useAtom, useAtomValue, useSetAtom } from "jotai";
import { useLayoutEffect, useRef } from "react";

export default function BreadcrumbOverlay({}) {
  const [breadcrumbs] = useAtom(breadcrumbsAtom);
  const [, setCenterNodeId] = useAtom(centerNodeAtom);
  const setLastCrumbScreenCenter = useSetAtom(lastCrumbScreenCenterAtom);
  // The overlay slides vertically with this value, so recompute the crumb's
  // rect whenever it changes (i.e. on pan/zoom).
  const selectedNodeVerticalPosition = useAtomValue(
    selectedNodeVerticalPositionAtom
  );
  const lastCrumbRef = useRef(null);

  const withoutMostRecentBreadcrumb = breadcrumbs.slice(0, -1);

  // Debug: publish the last rendered crumb's on-screen center from its DOM rect.
  useLayoutEffect(() => {
    if (!lastCrumbRef.current) {
      setLastCrumbScreenCenter(null);
      return;
    }
    const r = lastCrumbRef.current.getBoundingClientRect();
    setLastCrumbScreenCenter({
      x: r.left + r.width / 2,
      y: r.top + r.height / 2,
    });
  }, [
    setLastCrumbScreenCenter,
    selectedNodeVerticalPosition,
    withoutMostRecentBreadcrumb.length,
  ]);

  return (
    <div className="flex flex-col items-center opacity-60 hover:opacity-100">
      {withoutMostRecentBreadcrumb.length != 0 ? (
        <div className="-mb-0.5 flex w-50 items-center justify-center">
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
        const isLast = index === withoutMostRecentBreadcrumb.length - 1;
        return (
          <div
            key={breadcrumb.historyId}
            className="flex flex-col items-center">
            <div
              ref={isLast ? lastCrumbRef : null}
              className="max-w-50 min-w-50 cursor-default rounded-lg border-2 border-green-700 bg-white p-3 text-green-800 last:cursor-pointer"
              onClick={() => setCenterNodeId(breadcrumb.originNodeId)}>
              {breadcrumb.label}
            </div>
            {!isLast && (
              <svg
                width="4"
                height="16"
                xmlns="http://www.w3.org/2000/svg"
                className="block"
                style={{ display: "block" }}>
                <line
                  x1="2"
                  y1="0"
                  x2="2"
                  y2="16"
                  stroke="#016630"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </div>
        );
      })}
    </div>
  );
}
