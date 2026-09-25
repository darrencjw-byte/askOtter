"use client";

import { useEffect, useState } from "react";

const THINKING_MESSAGES = [
  "Mulling over your request...",
  "Rearranging pixels...",
  "Consulting the style guide...",
  "Brewing fresh components...",
  "Untangling dependencies...",
  "Polishing the corners...",
  "Summoning the right imports...",
  "Convincing TypeScript...",
  "Aligning the divs...",
  "Celebrating small victories...",
  "Teaching buttons to behave...",
  "Negotiating with the compiler...",
  "Painting with Tailwind...",
  "Almost gallery-worthy...",
  "Putting the finishing touches...",
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

function useRotatingMessage(messages: string[], intervalMs = 2400) {
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

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const message = useRotatingMessage(THINKING_MESSAGES);
  const [dots, setDots] = useState("");

  useEffect(() => {
    const timer = setInterval(() => {
      setDots((d) => (d.length >= 3 ? "" : d + "."));
    }, 500);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => reset(), 3000);
    return () => clearTimeout(timer);
  }, [reset]);

  return (
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center bg-zinc-50">
        <div className="text-center space-y-4 px-6">
          {/* Animated dots indicator */}
          <div className="mx-auto flex items-center justify-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-zinc-400 animate-[pulse_1.4s_ease-in-out_infinite]" />
            <span className="h-2 w-2 rounded-full bg-zinc-300 animate-[pulse_1.4s_ease-in-out_0.2s_infinite]" />
            <span className="h-2 w-2 rounded-full bg-zinc-200 animate-[pulse_1.4s_ease-in-out_0.4s_infinite]" />
          </div>

          {/* Rotating thinking message */}
          <h2 className="text-sm font-medium text-zinc-900 transition-opacity duration-300">
            {message}
          </h2>

          <p className="text-xs text-zinc-500 max-w-xs mx-auto">
            Rabbit is updating your project{dots}
          </p>

          <button
            onClick={() => reset()}
            className="mt-4 inline-flex items-center rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-zinc-800 transition-colors"
          >
            Retry
          </button>
        </div>
      </body>
    </html>
  );
}
