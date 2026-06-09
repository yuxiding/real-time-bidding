'use client';

import { useState, useEffect, useCallback } from 'react';
import { Calendar, MapPin, Wallet, ChevronRight, Loader2, Clock } from 'lucide-react';
import type { TripPlan } from '@/lib/types';
import ItineraryDisplay from '@/components/ItineraryDisplay';
import { format } from 'date-fns';

export default function TripsPage() {
  const [trips, setTrips] = useState<TripPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<TripPlan | null>(null);
  const [error, setError] = useState('');

  const fetchTrips = useCallback(async () => {
    try {
      const res = await fetch('/api/trips');
      if (!res.ok) throw new Error('Failed to load trips');
      const data = await res.json();
      setTrips(data.trips || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trips');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTrips(); }, [fetchTrips]);

  if (selected) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => setSelected(null)}
          className="mb-6 flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
        >
          ← Back to My Trips
        </button>
        <ItineraryDisplay trip={selected} />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-2">My Trips</h1>
        <p className="text-gray-500 dark:text-gray-400">Your saved Japan travel plans</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 size={36} className="animate-spin text-indigo-500" />
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400">
          {error}
        </div>
      ) : trips.length === 0 ? (
        <div className="text-center py-20 text-gray-500 dark:text-gray-400">
          <Clock size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium mb-2">No saved trips yet</p>
          <p className="text-sm mb-6">Generate a trip and save it to see it here.</p>
          <a
            href="/plan"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-colors"
          >
            Plan a Trip
          </a>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-6">
          {trips.map((trip, i) => (
            <TripCard key={trip.id ?? i} trip={trip} onClick={() => setSelected(trip)} />
          ))}
        </div>
      )}
    </div>
  );
}

function TripCard({ trip, onClick }: { trip: TripPlan; onClick: () => void }) {
  const nights = trip.days.length;
  const formatDate = (d: string) => {
    try { return format(new Date(d), 'MMM d, yyyy'); } catch { return d; }
  };

  return (
    <button
      onClick={onClick}
      className="text-left group bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 hover:border-indigo-400 dark:hover:border-indigo-500 hover:shadow-lg transition-all"
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-bold text-gray-900 dark:text-white text-lg group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">
          {trip.title}
        </h3>
        <ChevronRight size={20} className="text-gray-400 group-hover:text-indigo-500 flex-shrink-0 mt-0.5 transition-colors" />
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <MapPin size={14} className="text-pink-500 flex-shrink-0" />
          <span className="truncate">{trip.cities.join(' · ')}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <Calendar size={14} className="text-indigo-500 flex-shrink-0" />
          <span>{formatDate(trip.startDate)} – {formatDate(trip.endDate)} ({nights} days)</span>
        </div>
        <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <Wallet size={14} className="text-green-500 flex-shrink-0" />
          <span>¥{trip.budget.toLocaleString()} budget</span>
        </div>
      </div>

      {trip.interests.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {trip.interests.slice(0, 4).map(i => (
            <span key={i} className="px-2 py-0.5 rounded-full text-xs bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300">
              {i}
            </span>
          ))}
        </div>
      )}

      {trip.createdAt && (
        <p className="mt-3 text-xs text-gray-400">
          Saved {format(new Date(trip.createdAt), 'MMM d, yyyy')}
        </p>
      )}
    </button>
  );
}
