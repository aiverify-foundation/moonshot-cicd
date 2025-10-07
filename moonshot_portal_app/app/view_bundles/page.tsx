"use client"
import React from 'react';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Spinner } from "@/components/ui/spinner"
import { FileTerminal, RefreshCw, AlertCircle, CheckSquare, Square } from 'lucide-react';
import { Provider } from 'react-redux';
import store, { setBundleSelected } from '../../store';
import { useAppSelector, useAppDispatch } from '../../hooks/reduxHooks';
import { useBundles } from '../../hooks/useBundles';

// ...existing code...
function ViewBundlesInner() {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  const dispatch = useAppDispatch();
  const { bundles, loading, error, refetch } = useBundles();

  interface CardProps {
    name: string;
    description: string;
    tests: Array<{
      name: string;
      dataset: {
        id: string;
        name: string;
        description: string;
      };
    }>;
  }

  function CheckboxToggleButton({ children, checked, onCheckedChange, ...props }: { children: React.ReactNode; checked: boolean; onCheckedChange: (checked: boolean) => void; [key: string]: unknown }) {
  return (
    <Button
      variant={checked ? "default" : "outline"}
      onClick={() => onCheckedChange(!checked)}
      className="gap-2 w-28 justify-start"
      {...props}
    >
      <div className="flex items-center">
        {checked ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
      </div>
      <div className="flex items-center">
        {checked ? "Selected" : "Select"}
      </div>
    </Button>
  );
  }

  function renderCard(bundle: any) {
    const { name, description, tests, prompt_count } = bundle;
    const selected = bundleSelection[name] || false;
    return (
      <Card style={{ width: '400px', height: '450px', display: 'flex', flexDirection: 'column' }}>
        <CardHeader>
          <CardTitle>{name}</CardTitle>
          <CardDescription>
            <div className="line-clamp-2">
              {description}
            </div>
            <div className="grid grid-cols-3 gap-2 p-0 mt-2">
              {/* First Row - Text */}
              <div className="text-left">Tests</div>
              <div className="text-left">Prompts</div>
              <div></div>

              {/* Second Row - Numbers */}
              <div className="text-left">{tests.length}</div>
              <div className="text-left">{prompt_count || 0}</div>
              <div></div>
            </div>
          </CardDescription>

        </CardHeader>
        <Separator style={{ width: 'calc(100% - 2rem)', margin: '0 1rem' }} />
        <CardContent style={{ flex: 1 }}>
          <div style={{ marginBottom: '1rem' }}>Includes:</div>
          <ul style={{ padding: 0, margin: 0 }}>
            {tests.slice(0, 2).map((test: any, idx: number) => (
              <li
                key={name + '-' + test.name + '-' + idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1rem',
                  listStyle: 'none'
                }}
              >
                <FileTerminal />
                <span>{test.name}</span>
              </li>
            ))}
            {tests.length > 2 && (
              <li style={{ listStyle: 'none', color: '#888', marginLeft: '2rem' }}>
                + {tests.length - 2} more
              </li>
            )}
          </ul>
        </CardContent>
        <CardFooter className="flex items-center justify-between gap-2">
          <CheckboxToggleButton
            checked={selected}
            onCheckedChange={(checked: boolean) => dispatch(setBundleSelected({ bundleId: name, selected: checked }))}
          >
            selected
          </CheckboxToggleButton>
          <p className="ml-auto">Learn More</p>
        </CardFooter>
      </Card>
    );
  }

  if (loading) {
    return (
      <main className="p-8">
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
          <Spinner className="h-12 w-12" />
          <p className="text-lg text-gray-600">Loading bundles...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="p-8">
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
          <AlertCircle className="h-16 w-16 text-red-500" />
          <h2 className="text-xl font-semibold text-red-600">Error Loading Bundles</h2>
          <p className="text-gray-600 text-center max-w-md">{error}</p>
          <Button onClick={refetch} className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Try Again
          </Button>
        </div>
      </main>
    );
  }

  return (
    <main className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">View Bundles</h1>
          <p className="text-gray-600">Select bundles to run benchmark tests</p>
        </div>
        <Button onClick={refetch} variant="outline" className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>
      
      {bundles.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
          <FileTerminal className="h-16 w-16 text-gray-400" />
          <h2 className="text-xl font-semibold text-gray-600">No Bundles Available</h2>
          <p className="text-gray-500 text-center max-w-md">
            No bundles were found. Make sure the API backend is running and has bundles configured.
          </p>
          <Button onClick={refetch} className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
          {bundles.map((bundle, idx) => (
            <React.Fragment key={bundle.name + '-' + idx}>
              {renderCard(bundle)}
            </React.Fragment>
          ))}
        </div>
      )}
    </main>
  );
}

const ViewBundles = () => (
  <Provider store={store}>
    <ViewBundlesInner />
  </Provider>
);

export default ViewBundles;
