'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Sparkles, Loader2, MapPin, Calendar, Wallet, Heart } from 'lucide-react';
import type { TripPlan, TripFormData } from '@/lib/types';
import ItineraryDisplay from '@/components/ItineraryDisplay';

const JAPAN_CITIES = [
  'Tokyo', 'Kyoto', 'Osaka', 'Hiroshima', 'Nara', 'Hakone',
  'Nikko', 'Kamakura', 'Yokohama', 'Nagoya', 'Kanazawa',
  'Sapporo', 'Fukuoka', 'Nagasaki', 'Okinawa', 'Sendai',
  'Kobe', 'Nikkō', 'Matsuyama', 'Takayama',
];

const INTERESTS = [
  { id: 'food', label: '🍜 Food & Cuisine' },
  { id: 'temples', label: '⛩️ Temples & Shrines' },
  { id: 'nature', label: '🌸 Nature & Parks' },
  { id: 'anime', label: '🎌 Anime & Manga' },
  { id: 'shopping', label: '🛍️ Shopping' },
  { id: 'onsen', label: '♨️ Onsen & Wellness' },
  { id: 'nightlife', label: '🍶 Nightlife & Bars' },
  { id: 'history', label: '🏯 History & Culture' },
];

const DEFAULT_FORM: TripFormData = {
  cities: [],
  startDate: '',
  endDate: '',
  budget: 300000,
  interests: [],
};

function PlanPage() {
  const searchParams = useSearchParams();
  const [form, setForm] = useState<TripFormData>(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [itinerary, setItinerary] = useState<TripPlan | null>(null);

  useEffect(() => {
    const city = searchParams.get('city');
    if (city && JAPAN_CITIES.includes(city)) {
      setForm(prev => ({ ...prev, cities: [city] }));
    }
  }, [searchParams]);

  const toggleCity = (city: string) => {
    setForm(prev => ({
      ...prev,
      cities: prev.cities.includes(city)
        ? prev.cities.filter(c => c !== city)
        : [...prev.cities, city],
    }));
  };

  const toggleInterest = (id: string) => {
    setForm(prev => ({
      ...prev,
      interests: prev.interests.includes(id)
        ? prev.interests.filter(i => i !== id)
        : [...prev.interests, id],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.cities.length === 0) { setError('Please select at least one city.'); return; }
    if (!form.startDate || !form.endDate) { setError('Please select travel dates.'); return; }
    if (form.interests.length === 0) { setError('Please select at least one interest.'); return; }
    setError('');
    setLoading(true);
    setItinerary(null);
    try {
      const res = await fetch('/api/generate-itinerary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Failed to generate itinerary');
      }
      const data = await res.json();
      setItinerary(data.itinerary);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  if (itinerary) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Your Itinerary</h1>
          <button
            onClick={() => setItinerary(null)}
            className="px-4 py-2 rounded-xl border border-gray-300 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            ← Plan Another Trip
          </button>
        </div>
        <ItineraryDisplay trip={itinerary} />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center mb-10">
        <h1 className="text-4xl font-extrabold text-gray-900 dark:text-white mb-3">
          Plan Your Japan Adventure
        </h1>
        <p className="text-gray-500 dark:text-gray-400 text-lg">
          Fill in your details and let AI craft your perfect itinerary
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Cities */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center gap-2 mb-4">
            <MapPin size={20} className="text-pink-500" />
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Destination Cities</h2>
            <span className="text-sm text-gray-400">({form.cities.length} selected)</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {JAPAN_CITIES.map(city => (
              <button
                key={city}
                type="button"
                onClick={() => toggleCity(city)}
                className={`px-3 py-2 rounded-xl text-sm font-medium border transition-all ${
                  form.cities.includes(city)
                    ? 'bg-pink-500 border-pink-500 text-white shadow-sm'
                    : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-pink-300 dark:hover:border-pink-600'
                }`}
              >
                {city}
              </button>
            ))}
          </div>
        </div>

        {/* Dates */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Calendar size={20} className="text-indigo-500" />
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Travel Dates</h2>
          </div>
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Departure Date</label>
              <input
                type="date"
                value={form.startDate}
                onChange={e => setForm(prev => ({ ...prev, startDate: e.target.value }))}
                min={new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">Return Date</label>
              <input
                type="date"
                value={form.endDate}
                onChange={e => setForm(prev => ({ ...prev, endDate: e.target.value }))}
                min={form.startDate || new Date().toISOString().split('T')[0]}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </div>
          </div>
        </div>

        {/* Budget */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Wallet size={20} className="text-green-500" />
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Total Budget</h2>
            <span className="ml-auto text-2xl font-bold text-green-600 dark:text-green-400">
              ¥{form.budget.toLocaleString()}
            </span>
          </div>
          <input
            type="range"
            min={50000}
            max={2000000}
            step={10000}
            value={form.budget}
            onChange={e => setForm(prev => ({ ...prev, budget: Number(e.target.value) }))}
            className="w-full h-2 rounded-lg appearance-none cursor-pointer accent-green-500"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>¥50,000 (Budget)</span>
            <span>¥500,000 (Mid-range)</span>
            <span>¥2,000,000 (Luxury)</span>
          </div>
        </div>

        {/* Interests */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Heart size={20} className="text-red-500" />
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Your Interests</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {INTERESTS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => toggleInterest(id)}
                className={`px-3 py-2.5 rounded-xl text-sm font-medium border transition-all text-left ${
                  form.interests.includes(id)
                    ? 'bg-indigo-600 border-indigo-600 text-white shadow-sm'
                    : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-indigo-400 dark:hover:border-indigo-500'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full flex items-center justify-center gap-3 px-8 py-5 rounded-2xl bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-400 hover:to-purple-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold text-xl transition-all shadow-lg"
        >
          {loading ? (
            <>
              <Loader2 size={24} className="animate-spin" />
              Crafting your itinerary…
            </>
          ) : (
            <>
              <Sparkles size={24} />
              Generate AI Itinerary
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default function PlanPageWrapper() {
  return (
    <Suspense fallback={<div className="flex justify-center py-20"><Loader2 size={36} className="animate-spin text-indigo-500" /></div>}>
      <PlanPage />
    </Suspense>
  );
}
