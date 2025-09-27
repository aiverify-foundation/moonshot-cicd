import Link from 'next/link';

export default function ViewBundles() {
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">View Bundles</h1>
      <p>This is the View Bundles page.</p>
      <Link href="/">Back to Home</Link>
    </main>
  );
}
