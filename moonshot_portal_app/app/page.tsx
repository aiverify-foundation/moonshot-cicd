import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm">
        <h1 className="text-4xl font-bold text-center mb-8">
          Hello World! 🌙
        </h1>
        <p className="text-lg text-center text-gray-600">
          Welcome to the Moonshot Portal App
        </p>
        <div className="mt-8 p-6 bg-blue-50 rounded-lg border border-blue-200">
          <p className="text-blue-800">
            This is a Next.js application with TypeScript and Tailwind CSS.
          </p>
        </div>
        <div className="mt-8 flex gap-4">
          <Button>Default Button</Button>
          <Button variant="secondary">Secondary Button</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="destructive">Destructive Button</Button>
        </div>
      </div>
    </main>
  )
}
