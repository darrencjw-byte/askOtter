"use client";

import { useEffect, useState } from "react";

const THINKING_MESSAGES = [
  "Mulling over your request...",
  "Rearranging pixels...",
  "Brewing fresh components...",
  "Convincing TypeScript...",
  "Polishing the corners...",
  "Aligning the divs...",
  "Negotiating with the compiler...",
  "Painting with Tailwind...",
  "Celebrating small victories...",
  "Almost gallery-worthy...",
  "Whispering to the server...",
  "Herding semicolons...",
  "Debating with the linter...",
  "Fluffing up the UI...",
  "Calibrating hover states...",
  "Warming up the render engine...",
  "Tidying the component tree...",
  "Sprinkling design tokens...",
  "Measuring whitespace...",
  "Tuning the grid system...",
  "Feeding the build pipeline...",
  "Stitching layouts together...",
  "Coaxing React into cooperation...",
  "Minding the gap...",
  "Sharpening the typography...",
  "Orchestrating state changes...",
  "Massaging the margins...",
  "Double-checking the palette...",
  "Consulting the Tailwind docs...",
  "Shuffling z-indexes...",
  "Reticulating splines...",
  "Balancing visual weight...",
  "Composing the layout...",
  "Ironing out the wrinkles...",
  "Wrangling flexbox...",
  "Harmonizing the colors...",
  "Sketching in code...",
  "Crunching the styles...",
  "Befriending the bundler...",
  "Refining the details...",
  "Pondering the padding...",
  "Daydreaming in JSX...",
  "Knitting components together...",
  "Choreographing transitions...",
  "Tidying up the edges...",
  "Consulting the design gods...",
  "Tuning border radii...",
  "Perfecting the shadows...",
  "Counting pixels...",
  "Giving the buttons a pep talk...",
  "Making the fonts feel at home...",
  "Adjusting the contrast...",
  "Drafting the blueprint...",
  "Sweeping under the rug...",
  "Fine-tuning responsiveness...",
  "Taming the cascade...",
  "Conjuring up interfaces...",
  "Stretching the viewport...",
  "Letting the code breathe...",
  "Curating the component library...",
  "Smoothing out the animations...",
  "Running a vibe check...",
  "Channeling good UX energy...",
  "Dotting the i's in the UI...",
  "Polishing until it shines...",
  "Asking the icons to line up...",
  "Debouncing the excitement...",
  "Queueing up the magic...",
  "Spacing things out nicely...",
  "Baking the layout...",
  "Rotating through options...",
  "Cross-referencing best practices...",
  "Applying a coat of polish...",
  "Contemplating the void...",
  "Calculating the golden ratio...",
  "Meditating on user flows...",
  "Sketching wireframes mentally...",
  "Auditing the accessibility...",
  "Recruiting helper functions...",
  "Buffing the surface...",
  "Rehearsing the render...",
  "Weighing the trade-offs...",
  "Mixing the perfect gradient...",
  "Letting the types settle...",
  "Connecting the dots...",
  "Building with intention...",
  "Crafting the experience...",
  "Giving it one last look...",
  "Shipping something beautiful...",
  "Wrapping it up with care...",
  "Adding that chef's kiss...",
  "Making it pixel-perfect...",
  "Trusting the process...",
  "Manifesting clean code...",
  "Turning caffeine into UI...",
  "Assembling the masterpiece...",
  "Almost ready for the spotlight...",
];

function useRotatingMessage(messages: string[], intervalMs = 2000) {
  const [index, setIndex] = useState(() =>
    Math.floor(Math.random() * messages.length)
  );
  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % messages.length);
    }, intervalMs);
    return () => clearInterval(timer);
  }, [messages, intervalMs]);
  return messages[index];
}

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const message = useRotatingMessage(THINKING_MESSAGES);

  useEffect(() => {
    console.error("[app error]", error);
  }, [error]);

  useEffect(() => {
    const timer = setTimeout(() => reset(), 3000);
    return () => clearTimeout(timer);
  }, [reset]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="text-center space-y-3 px-6">
        {/* Pulsing dots */}
        <div className="mx-auto flex items-center justify-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-zinc-400 animate-[pulse_1.4s_ease-in-out_infinite]" />
          <span className="h-1.5 w-1.5 rounded-full bg-zinc-300 animate-[pulse_1.4s_ease-in-out_0.2s_infinite]" />
          <span className="h-1.5 w-1.5 rounded-full bg-zinc-200 animate-[pulse_1.4s_ease-in-out_0.4s_infinite]" />
        </div>

        {/* Rotating message */}
        <p className="text-sm text-muted-foreground font-medium">
          {message}
        </p>

        <button
          onClick={() => reset()}
          className="text-xs text-primary underline underline-offset-4 hover:text-primary/80"
        >
          Retry now
        </button>
      </div>
    </div>
  );
}
