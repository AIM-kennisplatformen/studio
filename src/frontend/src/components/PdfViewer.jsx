import { useAtom } from "jotai";
import { pdfViewerAtom } from "../data/atoms";
import { X, ExternalLink, FileText } from "lucide-react";

export default function PdfViewer() {
  const [pdfUrl, setPdfUrl] = useAtom(pdfViewerAtom);

  if (!pdfUrl) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
        onClick={() => setPdfUrl(null)}
      />

      {/* Dialog */}
      <div className="fixed inset-8 z-50 flex flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xl">

        {/* Header */}
        <div className="flex flex-shrink-0 items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <FileText size={15} className="text-gray-400" />
            View document
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPdfUrl(null)}
              className="rounded p-1.5 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
              title="Close"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* PDF */}
<iframe
  key={pdfUrl}
  src={`/pdfjs/web/viewer.html?file=${encodeURIComponent(pdfUrl)}`}
  className="h-full w-full flex-1 border-0"
  title="Source PDF"
/>
      </div>
    </>
  );
}
