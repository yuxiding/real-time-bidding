'use client';

import Link from 'next/link';
import { MapPin, Calendar, Wallet, Sparkles, Star, Compass } from 'lucide-react';

const features = [
  {
    icon: Sparkles,
    title: 'AI-Powered Itineraries',
    description: 'GPT-4o crafts personalized day-by-day plans tailored to your interests, budget, and travel style.',
  },
  {
    icon: MapPin,
    title: 'Interactive Maps',
    description: 'Visualize your entire trip on Google Maps with pins for every activity, restaurant, and hotel.',
  },
  {
    icon: Wallet,
    title: 'Smart Budget Planning',
    description: 'Get a detailed breakdown of accommodation, food, transport, and activities—no surprises.',
  },
  {
    icon: Calendar,
    title: 'Flexible Scheduling',
    description: 'Adjust dates and let the AI re-plan instantly. From weekend getaways to month-long adventures.',
  },
  {
    icon: Star,
    title: 'Save Favorites',
    description: 'Bookmark restaurants, temples, and hidden gems to revisit later or share with friends.',
  },
  {
    icon: Compass,
    title: 'Local Expertise',
    description: 'Discover authentic experiences beyond tourist traps: local izakayas, hidden shrines, onsen towns.',
  },
];

const destinations = [
  { name: 'Tokyo', emoji: '🏙️', desc: 'Neon lights & anime culture' },
  { name: 'Kyoto', emoji: '⛩️', desc: 'Ancient temples & geisha districts' },
  { name: 'Osaka', emoji: '🍜', desc: 'Street food paradise' },
  { name: 'Hiroshima', emoji: '🕊️', desc: 'History & island beauty' },
  { name: 'Nara', emoji: '🦌', desc: 'Sacred deer & giant Buddha' },
  { name: 'Hakone', emoji: '🗻', desc: 'Mt. Fuji views & onsen' },
];

export default function HomePage() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-950 via-indigo-900 to-purple-900 dark:from-indigo-950 dark:via-indigo-900 dark:to-purple-950 text-white">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_top_right,_#ff7eb3_0%,_transparent_60%)]" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-36 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 backdrop-blur text-sm font-medium mb-6 border border-white/20">
            <Sparkles size={14} className="text-pink-300" />
            Powered by GPT-4o
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight">
            Your Perfect{' '}
            <span className="bg-gradient-to-r from-pink-300 to-purple-300 bg-clip-text text-transparent">
              Japan Trip
            </span>
            <br />Starts Here
          </h1>
          <p className="text-xl md:text-2xl text-indigo-200 max-w-3xl mx-auto mb-10 leading-relaxed">
            Tell us your cities, dates, budget, and interests. Our AI builds a complete itinerary with hotels, transport, and a day-by-day guide—in seconds.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/plan"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-400 hover:to-purple-500 text-white font-bold text-lg transition-all shadow-lg shadow-purple-900/50 hover:shadow-purple-700/60 hover:-translate-y-0.5"
            >
              <Sparkles size={20} />
              Plan My Trip
            </Link>
            <Link
              href="/trips"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl bg-white/10 hover:bg-white/20 backdrop-blur border border-white/20 text-white font-bold text-lg transition-all"
            >
              View Sample Trips
            </Link>
          </div>
        </div>
        {/* Decorative sakura petals */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-pink-400/50 to-transparent" />
      </section>

      {/* Popular Destinations */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-3xl font-bold text-center mb-2 text-gray-900 dark:text-white">
          Popular Destinations
        </h2>
        <p className="text-center text-gray-500 dark:text-gray-400 mb-10">
          Explore Japan's most iconic cities and hidden gems
        </p>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {destinations.map(({ name, emoji, desc }) => (
            <Link
              key={name}
              href={`/plan?city=${name}`}
              className="group flex flex-col items-center p-5 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 hover:border-pink-300 dark:hover:border-pink-600 hover:shadow-lg transition-all text-center"
            >
              <span className="text-4xl mb-3">{emoji}</span>
              <span className="font-bold text-gray-900 dark:text-white group-hover:text-pink-600 dark:group-hover:text-pink-400 transition-colors">
                {name}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">{desc}</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-white dark:bg-gray-900 border-y border-gray-200 dark:border-gray-800 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-2 text-gray-900 dark:text-white">
            Everything You Need
          </h2>
          <p className="text-center text-gray-500 dark:text-gray-400 mb-12">
            From first idea to boarding pass
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map(({ icon: Icon, title, description }) => (
              <div key={title} className="flex gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
                  <Icon size={22} className="text-indigo-600 dark:text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white mb-1">{title}</h3>
                  <p className="text-gray-500 dark:text-gray-400 text-sm leading-relaxed">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 py-20 text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4 text-gray-900 dark:text-white">
          Ready to discover Japan?
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-8 text-lg">
          Join thousands of travelers who planned unforgettable Japan trips with our AI planner.
        </p>
        <Link
          href="/plan"
          className="inline-flex items-center gap-2 px-10 py-4 rounded-2xl bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-400 hover:to-purple-500 text-white font-bold text-lg transition-all shadow-lg hover:-translate-y-0.5"
        >
          <Sparkles size={20} />
          Start Planning for Free
        </Link>
      </section>
    </div>
  );
}
