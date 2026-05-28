import Link from "next/link";
import { HelpCircle, Bug, Github } from "lucide-react";
import { Button } from "@/components/ui/button";

function QuickStartButton() {
  return (
    <Button
      asChild
      variant="outline"
      className="h-[70px] w-full flex-col items-start p-4 text-left hover:bg-accent whitespace-normal"
      data-testid="benchmark-link"
    >
      <Link href="/benchmark">
        <h3 className="text-base font-semibold text-gray-900 leading-none break-words mb-0">Run a benchmark test</h3>
        <p className="text-sm text-slate-700 leading-tight break-words mt-0">Test your LLM application for trust and safety risks</p>
      </Link>
    </Button>
  );
}

function HowToGuideButton() {
  return (
    <Button
      variant="outline"
      className="h-[70px] w-full flex-col items-start p-4 text-left hover:bg-accent whitespace-normal"
    >
      <h3 className="text-base font-semibold text-gray-900 leading-none break-words mb-0">How-to guide</h3>
      <p className="text-sm text-slate-700 leading-normal break-words mt-0">Understand how the product works step-by-step</p>
    </Button>
  );
}

function IMDAStarterKitButton() {
  return (
    <Button
      asChild
      variant="outline"
      className="h-[70px] w-full flex-col items-start p-4 text-left hover:bg-accent whitespace-normal"
    >
      <a
        href="https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/large-language-model-starter-kit.pdf"
        target="_blank"
        rel="noopener noreferrer"
      >
        <h3 className="text-base font-semibold text-gray-900 leading-none break-words mb-0">{"IMDA's Starter Kit"}</h3>
        <p className="text-sm text-slate-700 leading-normal break-words mt-0">{"Follow IMDA's guidance for safety testing"}</p>
      </a>
    </Button>
  );
}

export default function Home() {
  return (
    <div className="min-h-screen w-[1200px]">
      {/* Header */}
      <div className="flex items-center justify-between w-full py-6 px-6">
        {/* Logo Section */}
        <div className="flex items-center gap-2">
          {/* Logo SVG Code taken from Figma */}
          <svg width="260" height="54" viewBox="0 0 260 54" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="260" height="54" fill="url(#pattern0_2236_39430)"/>
            <defs>
              <pattern id="pattern0_2236_39430" patternContentUnits="objectBoundingBox" width="1" height="1">
                <use href="#image0_2236_39430" transform="matrix(0.000976562 0 0 0.00470197 0 -0.000759549)"/>
              </pattern>
              <image id="image0_2236_39430" width="1024" height="213" preserveAspectRatio="none" href="data:image/png;base64,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"/>
            </defs>
          </svg>
          <div className="flex flex-col">
            <h1 className="text-sm font-semibold text-gray-900 leading-none">
              Moonshot
            </h1>
            <p className="text-xs font-medium text-slate-500 leading-tight">
              0.1.0
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/aiverify-foundation/moonshot-cicd/wiki"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded hover:bg-gray-100 transition-colors"
            aria-label="Open Moonshot wiki"
          >
            <HelpCircle className="w-4 h-4 text-slate-500" />
          </a>
          <a
            href="https://github.com/aiverify-foundation/moonshot-cicd/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded hover:bg-gray-100 transition-colors"
            aria-label="Open Moonshot issues"
          >
            <Bug className="w-4 h-4 text-slate-500" />
          </a>
          <a
            href="https://github.com/aiverify-foundation/moonshot-cicd"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded hover:bg-gray-100 transition-colors"
            aria-label="Open Moonshot GitHub repository"
          >
            <Github className="w-4 h-4 text-slate-500" />
          </a>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        <div className="grid gap-3 grid-cols-3">
          <QuickStartButton />
          <HowToGuideButton />
          <IMDAStarterKitButton />
        </div>
      </div>
    </div>
  );
}
