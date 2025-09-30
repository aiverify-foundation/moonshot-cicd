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
import { FileTerminal } from 'lucide-react';
import { Provider } from 'react-redux';
import store, { setBundleSelected } from '../../store';
import { useAppSelector, useAppDispatch } from '../../hooks/reduxHooks';
//<FileTerminal />

// ...existing code...
function ViewBundlesInner() {
  const bundleSelection = useAppSelector((state) => state.bundleSelection);
  const dispatch = useAppDispatch();

  interface CardProps {
    bundle_name: string;
    description: string;
    recipe_list: string[];
  }

  function CheckboxToggleButton({ children, checked, onCheckedChange, ...props }: { children: React.ReactNode; checked: boolean; onCheckedChange: (checked: boolean) => void; [key: string]: unknown }) {
  return (
    <Button
      variant={checked ? "secondary" : "outline"}
      onClick={() => onCheckedChange(!checked)}
      className="flex items-center gap-2 px-4 py-2"
      {...props}
    >
      <Checkbox 
        checked={checked}
        onCheckedChange={onCheckedChange}
        onClick={(e) => e.stopPropagation()} // Prevent double toggle
        className="pointer-events-none" // Let button handle the click
      />
      {children}
    </Button>
  );
  }

  function renderCard({ bundle_name, description, recipe_list }: CardProps) {
    const selected = bundleSelection[bundle_name] || false;
    return (
      <Card style={{ width: '400px', height: '450px', display: 'flex', flexDirection: 'column' }}>
        <CardHeader>
          <CardTitle>{bundle_name}</CardTitle>
          <CardDescription>
            <div className="line-clamp-2">
              {description}
            </div>
            <div className="grid grid-cols-3 gap-2 p-0 mt-2">
              {/* First Row - Text */}
              <div className="text-left">Recipes</div>
              <div className="text-left">Prompts</div>
              <div></div>

              {/* Second Row - Numbers */}
              <div className="text-left">123</div>
              <div className="text-left">456</div>
              <div></div>
            </div>
          </CardDescription>

        </CardHeader>
        <Separator style={{ width: 'calc(100% - 2rem)', margin: '0 1rem' }} />
        <CardContent style={{ flex: 1 }}>
          <div style={{ marginBottom: '1rem' }}>Includes:</div>
          <ul style={{ padding: 0, margin: 0 }}>
            {recipe_list.slice(0, 2).map((item, idx) => (
              <li
                key={bundle_name + '-' + item + '-' + idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1rem',
                  listStyle: 'none'
                }}
              >
                <FileTerminal />
                <span>{item}</span>
              </li>
            ))}
            {recipe_list.length > 2 && (
              <li style={{ listStyle: 'none', color: '#888', marginLeft: '2rem' }}>
                + {recipe_list.length - 2} more
              </li>
            )}
          </ul>
        </CardContent>
        <CardFooter className="flex items-center justify-between gap-2">
          <CheckboxToggleButton
            checked={selected}
            onCheckedChange={(checked: boolean) => dispatch(setBundleSelected({ bundleId: bundle_name, selected: checked }))}
          >
            selected
          </CheckboxToggleButton>
          <p className="ml-auto">Learn More</p>
        </CardFooter>
      </Card>
    );
  }

  const cards = [
    {
      bundle_name: "Card Title 1",
      description: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer a sodales dui. Ut et nisl non sapien mattis vehicula. Maecenas malesuada sagittis tellus eget vehicula. Ut aliquet aliquam arcu, ut sollicitudin augue porta sed. Duis lobortis odio ante, non dignissim elit lacinia a. Curabitur dictum lacus non augue tincidunt, ut ultricies ex posuere. Quisque volutpat consequat metus facilisis faucibus. Praesent pharetra enim vitae fringilla vulputate. Nulla imperdiet lectus quis est fringilla consectetur. Aliquam at massa tortor. Etiam et leo purus. Sed at cursus lorem. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Fusce eu sollicitudin enim. Proin turpis lorem, sollicitudin at posuere vel, varius ac orci. Donec nec facilisis dolor, non dictum tellus. ",
      recipe_list: ["Recipe 1", "Recipe 2", "Recipe 3"]
    },
    {
      bundle_name: "Card Title 2",
      description: "Card Description 2",
      recipe_list: ["Recipe 4", "Recipe 5", "Recipe 6"]
    },
    {
      bundle_name: "Card Title 3",
      description: "Card Description 3",
      recipe_list: ["Recipe 7", "Recipe 8", "Recipe 9"]
    },
    {
      bundle_name: "Card Title 4",
      description: "Card Description 4",
      recipe_list: ["Recipe 10", "Recipe 11", "Recipe 12"]
    }
  ];

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-4">View Bundles</h1>
      <p>This is the View Bundles page.</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem' }}>
        {cards.map((card, idx) => (
          <React.Fragment key={card.bundle_name + '-' + idx}>
            {renderCard(card)}
          </React.Fragment>
        ))}
      </div>
      <Link href="/">Back to Home</Link>
    </main>
  );
}

const ViewBundles = () => (
  <Provider store={store}>
    <ViewBundlesInner />
  </Provider>
);

export default ViewBundles;
