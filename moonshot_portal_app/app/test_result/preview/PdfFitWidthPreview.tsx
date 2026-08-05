/**
 * PDF preview feature — delete this entire preview/ directory to remove.
 * Renders PDF pages to canvas at a fixed width (Chrome ignores #view=FitH on blob iframes).
 */
"use client";

import React, { useEffect, useState } from "react";

/** Fixed preview column width in CSS pixels. */
const PREVIEW_WIDTH_PX = 960;

type PageImage = {
  pageNumber: number;
  src: string;
};

type PdfFitWidthPreviewProps = {
  url: string;
};

export default function PdfFitWidthPreview({ url }: PdfFitWidthPreviewProps) {
  const [pages, setPages] = useState<PageImage[]>([]);
  const [rendering, setRendering] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!url) return;

    let cancelled = false;

    const renderPages = async () => {
      setRendering(true);
      setError(null);

      try {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
          "pdfjs-dist/build/pdf.worker.min.mjs",
          import.meta.url
        ).toString();

        const pdfBytes = new Uint8Array(await (await fetch(url)).arrayBuffer());
        const doc = await pdfjs.getDocument({ data: pdfBytes }).promise;
        if (cancelled) return;

        const nextPages: PageImage[] = [];

        for (let pageNum = 1; pageNum <= doc.numPages; pageNum++) {
          const page = await doc.getPage(pageNum);
          if (cancelled) return;

          const baseViewport = page.getViewport({ scale: 1 });
          const scale = PREVIEW_WIDTH_PX / baseViewport.width;
          const viewport = page.getViewport({ scale });

          const canvas = document.createElement("canvas");
          canvas.width = Math.floor(viewport.width);
          canvas.height = Math.floor(viewport.height);
          const ctx = canvas.getContext("2d");
          if (!ctx) throw new Error("Canvas is not supported in this browser");

          const task = page.render({ canvasContext: ctx, viewport, canvas });
          await task.promise;
          if (cancelled) return;

          nextPages.push({
            pageNumber: pageNum,
            src: canvas.toDataURL("image/png"),
          });
        }

        if (!cancelled) setPages(nextPages);
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof Error ? e.message : "Failed to render PDF preview"
          );
          setPages([]);
        }
      } finally {
        if (!cancelled) setRendering(false);
      }
    };

    void renderPages();

    return () => {
      cancelled = true;
    };
  }, [url]);

  return (
    <div className="min-h-0 w-full flex-1 overflow-y-auto bg-slate-200 px-4 py-6">
      {rendering && pages.length === 0 && !error && (
        <p className="text-center text-sm text-slate-600">Rendering pages…</p>
      )}
      {error && (
        <p className="text-center text-sm text-red-800">{error}</p>
      )}
      <div
        className="mx-auto flex flex-col gap-6"
        style={{ width: PREVIEW_WIDTH_PX, maxWidth: "100%" }}
      >
        {pages.map((page) => (
          // eslint-disable-next-line @next/next/no-img-element -- blob/data URLs from PDF canvas rendering
          <img
            key={page.pageNumber}
            src={page.src}
            alt={`Report page ${page.pageNumber}`}
            width={PREVIEW_WIDTH_PX}
            className="block rounded-sm bg-white shadow-md"
          />
        ))}
      </div>
    </div>
  );
}
