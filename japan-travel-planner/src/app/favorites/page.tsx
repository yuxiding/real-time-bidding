'use client';

import { useState, useEffect, useCallback } from 'react';
import { Heart, MapPin, Trash2, Loader2, Plus } from 'lucide-react';
import type { FavoritePlace } from '@/lib/types';

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<FavoritePlace[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState<string | null>(null);

  const fetchFavorites = useCallback(async () => {
    try {
      const res = await fetch('/api/favorites');
      if (!res.ok) throw new Error('Failed to load favorites');
      const data = await res.json();
      setFavorites(data.favorites || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load favorites');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchFavorites(); }, [fetchFavorites]);

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      const res = await fetch(`/api/favorites?id=${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete');
      setFavorites(prev => prev.filter(f => f.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    } finally {
      setDeleting(null);
    }
  };

  const typeColors: Record<string, string> = {
    restaurant: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
    temple: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
    hotel: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    attraction: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
    shop: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    nature: 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300',
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <Heart size={28} className="text-pink-500" />
            Favorite Places
          </h1>
          <p className="text-gray-500 dark:text-gray-400">Your saved spots across Japan</p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 size={36} className="animate-spin text-pink-500" />
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400">
          {error}
        </div>
      ) : favorites.length === 0 ? (
        <div className="text-center py-20 text-gray-500 dark:text-gray-400">
          <Heart size={48} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium mb-2">No favorites yet</p>
          <p className="text-sm mb-6">Save places from your itineraries to see them here.</p>
          <a
            href="/plan"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-pink-500 hover:bg-pink-600 text-white font-semibold transition-colors"
          >
            <Plus size={18} />
            Plan a Trip
          </a>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {favorites.map(place => (
            <div
              key={place.id}
              className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5 flex flex-col gap-3 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-bold text-gray-900 dark:text-white leading-snug">{place.placeName}</h3>
                <button
                  onClick={() => place.id && handleDelete(place.id)}
                  disabled={deleting === place.id}
                  className="flex-shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                  aria-label="Remove favorite"
                >
                  {deleting === place.id ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Trash2 size={16} />
                  )}
                </button>
              </div>

              {place.placeType && (
                <span className={`self-start px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${typeColors[place.placeType] ?? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'}`}>
                  {place.placeType}
                </span>
              )}

              {place.city && (
                <div className="flex items-center gap-1.5 text-sm text-gray-500 dark:text-gray-400">
                  <MapPin size={13} className="text-pink-400" />
                  {place.city}
                </div>
              )}

              {place.notes && (
                <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed line-clamp-3">
                  {place.notes}
                </p>
              )}

              {(place.locationLat && place.locationLng) && (
                <a
                  href={`https://maps.google.com/?q=${place.locationLat},${place.locationLng}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                >
                  Open in Google Maps →
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
