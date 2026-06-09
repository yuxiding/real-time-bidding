'use client';

import { useState } from 'react';
import { MapPin, Clock, DollarSign, Hotel, Train, Bookmark, Heart, Check, ChevronDown, ChevronUp } from 'lucide-react';
import type { TripPlan, Activity, Hotel as HotelType, FavoritePlace } from '@/lib/types';
import MapView from './MapView';

interface Props {
  trip: TripPlan;
}

const activityTypeColors: Record<string, string> = {
  sightseeing: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  food: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
  shopping: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  transport: 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400',
  accommodation: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
  nature: 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300',
  culture: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300',
};

export default function ItineraryDisplay({ trip }: Props) {
  const [activeDay, setActiveDay] = useState(0);
  const [savedTrip, setSavedTrip] = useState(false);
  const [savingTrip, setSavingTrip] = useState(false);
  const [savedActivities, setSavedActivities] = useState<Set<string>>(new Set());
  const [showBudget, setShowBudget] = useState(false);
  const [showTips, setShowTips] = useState(false);

  const currentDay = trip.days[activeDay];
  const allActivities = currentDay?.activities.filter(a => a.lat && a.lng) ?? [];

  const handleSaveTrip = async () => {
    setSavingTrip(true);
    try {
      await fetch('/api/trips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trip),
      });
      setSavedTrip(true);
    } finally {
      setSavingTrip(false);
    }
  };

  const handleSaveFavorite = async (activity: Activity) => {
    const key = activity.title;
    if (savedActivities.has(key)) return;
    const fav: FavoritePlace = {
      placeName: activity.title,
      placeType: activity.type === 'food' ? 'restaurant' : activity.type === 'nature' ? 'nature' : activity.type === 'culture' ? 'temple' : 'attraction',
      notes: activity.description,
      locationLat: activity.lat,
      locationLng: activity.lng,
      city: currentDay?.city,
    };
    await fetch('/api/favorites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fav),
    });
    setSavedActivities(prev => new Set(prev).add(key));
  };

  const budgetCategories = [
    { label: 'Accommodation', value: trip.budgetBreakdown.accommodation, color: 'bg-purple-500' },
    { label: 'Food', value: trip.budgetBreakdown.food, color: 'bg-orange-500' },
    { label: 'Transportation', value: trip.budgetBreakdown.transportation, color: 'bg-blue-500' },
    { label: 'Activities', value: trip.budgetBreakdown.activities, color: 'bg-green-500' },
    { label: 'Shopping', value: trip.budgetBreakdown.shopping, color: 'bg-pink-500' },
    { label: 'Miscellaneous', value: trip.budgetBreakdown.miscellaneous, color: 'bg-gray-400' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-extrabold mb-2">{trip.title}</h1>
        <div className="flex flex-wrap gap-4 text-sm text-indigo-200">
          <span className="flex items-center gap-1"><MapPin size={14} />{trip.cities.join(' · ')}</span>
          <span className="flex items-center gap-1"><Clock size={14} />{trip.days.length} days</span>
          <span className="flex items-center gap-1"><DollarSign size={14} />¥{trip.budget.toLocaleString()}</span>
        </div>
        <div className="flex gap-3 mt-4">
          <button
            onClick={handleSaveTrip}
            disabled={savedTrip || savingTrip}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/20 hover:bg-white/30 disabled:opacity-60 text-white text-sm font-medium transition-colors"
          >
            {savedTrip ? <><Check size={15} /> Saved!</> : savingTrip ? 'Saving…' : <><Bookmark size={15} /> Save Trip</>}
          </button>
        </div>
      </div>

      {/* Day Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {trip.days.map((day, i) => (
          <button
            key={i}
            onClick={() => setActiveDay(i)}
            className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
              activeDay === i
                ? 'bg-indigo-600 text-white'
                : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:border-indigo-400'
            }`}
          >
            Day {day.day}
          </button>
        ))}
      </div>

      {currentDay && (
        <div className="grid lg:grid-cols-5 gap-6">
          {/* Activities */}
          <div className="lg:col-span-3 space-y-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
              <h2 className="font-bold text-gray-900 dark:text-white text-lg mb-1">
                Day {currentDay.day}: {currentDay.title}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{currentDay.city} · {currentDay.date}</p>
              <div className="space-y-4">
                {currentDay.activities.map((activity, i) => (
                  <ActivityCard
                    key={i}
                    activity={activity}
                    saved={savedActivities.has(activity.title)}
                    onSave={() => handleSaveFavorite(activity)}
                  />
                ))}
              </div>
            </div>
          </div>

          {/* Map + Hotel */}
          <div className="lg:col-span-2 space-y-4">
            {allActivities.length > 0 && (
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
                <MapView activities={allActivities} />
              </div>
            )}

            {/* Hotel for this city */}
            {trip.hotels.filter(h => h.city === currentDay.city).map((hotel, i) => (
              <HotelCard key={i} hotel={hotel} />
            ))}
          </div>
        </div>
      )}

      {/* Transportation */}
      {trip.transportation.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
          <h2 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Train size={18} className="text-indigo-500" /> Transportation
          </h2>
          <div className="space-y-3">
            {trip.transportation.map((t, i) => (
              <div key={i} className="flex items-start gap-4 p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
                <div className="flex-1">
                  <div className="font-medium text-gray-900 dark:text-white text-sm">
                    {t.from} → {t.to}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t.method} · {t.duration}</div>
                  {t.notes && <div className="text-xs text-gray-400 mt-1">{t.notes}</div>}
                </div>
                <div className="text-sm font-bold text-green-600 dark:text-green-400 flex-shrink-0">
                  ¥{t.cost.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Budget Breakdown */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
        <button
          onClick={() => setShowBudget(!showBudget)}
          className="w-full flex items-center justify-between"
        >
          <h2 className="font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <DollarSign size={18} className="text-green-500" /> Budget Breakdown
            <span className="text-green-600 dark:text-green-400">¥{trip.budgetBreakdown.total.toLocaleString()}</span>
          </h2>
          {showBudget ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
        </button>
        {showBudget && (
          <div className="mt-4 space-y-3">
            {budgetCategories.map(({ label, value, color }) => {
              const pct = trip.budgetBreakdown.total > 0 ? Math.round((value / trip.budgetBreakdown.total) * 100) : 0;
              return (
                <div key={label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 dark:text-gray-300">{label}</span>
                    <span className="font-medium text-gray-900 dark:text-white">¥{value.toLocaleString()} ({pct}%)</span>
                  </div>
                  <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                    <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Tips */}
      {trip.tips && trip.tips.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
          <button
            onClick={() => setShowTips(!showTips)}
            className="w-full flex items-center justify-between"
          >
            <h2 className="font-bold text-gray-900 dark:text-white">💡 Travel Tips</h2>
            {showTips ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
          </button>
          {showTips && (
            <ul className="mt-4 space-y-2">
              {trip.tips.map((tip, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-700 dark:text-gray-300">
                  <span className="text-pink-500 flex-shrink-0">•</span>
                  {tip}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function ActivityCard({ activity, saved, onSave }: { activity: Activity; saved: boolean; onSave: () => void }) {
  return (
    <div className="flex gap-4 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group">
      <div className="flex-shrink-0 w-14 text-center">
        <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">{activity.time}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2 justify-between">
          <h4 className="font-semibold text-gray-900 dark:text-white text-sm">{activity.title}</h4>
          <button
            onClick={onSave}
            disabled={saved}
            className={`flex-shrink-0 p-1 rounded-lg transition-colors ${
              saved ? 'text-pink-500' : 'text-gray-300 dark:text-gray-600 hover:text-pink-400 group-hover:text-gray-400'
            }`}
            title="Save to favorites"
          >
            <Heart size={14} fill={saved ? 'currentColor' : 'none'} />
          </button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">{activity.description}</p>
        <div className="flex flex-wrap gap-2 mt-2">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${activityTypeColors[activity.type] ?? 'bg-gray-100 text-gray-600'}`}>
            {activity.type}
          </span>
          {activity.duration && (
            <span className="text-xs text-gray-400 flex items-center gap-1"><Clock size={11} />{activity.duration}</span>
          )}
          {activity.cost !== undefined && activity.cost > 0 && (
            <span className="text-xs text-green-600 dark:text-green-400 font-medium">¥{activity.cost.toLocaleString()}</span>
          )}
          {activity.location && (
            <span className="text-xs text-gray-400 flex items-center gap-1 truncate max-w-[180px]"><MapPin size={11} />{activity.location}</span>
          )}
        </div>
      </div>
    </div>
  );
}

function HotelCard({ hotel }: { hotel: HotelType }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-5">
      <div className="flex items-start gap-2 mb-2">
        <Hotel size={18} className="text-purple-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-gray-900 dark:text-white text-sm">{hotel.name}</h3>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs text-gray-500 dark:text-gray-400">{hotel.city}</span>
            <span className="text-xs text-yellow-500">{'★'.repeat(Math.round(hotel.rating))}</span>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className="text-sm font-bold text-green-600 dark:text-green-400">¥{hotel.pricePerNight.toLocaleString()}</div>
          <div className="text-xs text-gray-400">/ night</div>
        </div>
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 line-clamp-2">{hotel.description}</p>
      {hotel.amenities?.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {hotel.amenities.slice(0, 4).map(a => (
            <span key={a} className="px-2 py-0.5 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300">{a}</span>
          ))}
        </div>
      )}
    </div>
  );
}
