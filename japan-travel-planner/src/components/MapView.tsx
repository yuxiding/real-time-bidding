'use client';

import { useState, useCallback } from 'react';
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from '@react-google-maps/api';
import type { Activity } from '@/lib/types';

interface Props {
  activities: Activity[];
}

const mapContainerStyle = { width: '100%', height: '320px' };

const mapDarkStyle = [
  { elementType: 'geometry', stylers: [{ color: '#1d2c4d' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#8ec3b9' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#1a3646' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0e1626' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#304a7d' }] },
  { featureType: 'poi', elementType: 'geometry', stylers: [{ color: '#283d6a' }] },
];

const typeIcons: Record<string, string> = {
  food: '🍜',
  sightseeing: '📍',
  shopping: '🛍️',
  culture: '⛩️',
  nature: '🌸',
  transport: '🚄',
  accommodation: '🏨',
};

export default function MapView({ activities }: Props) {
  const [selected, setSelected] = useState<Activity | null>(null);
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || '';

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: apiKey,
  });

  const validActivities = activities.filter(a => a.lat && a.lng);

  const center = useCallback(() => {
    if (validActivities.length === 0) return { lat: 35.6762, lng: 139.6503 };
    const lat = validActivities.reduce((s, a) => s + (a.lat ?? 0), 0) / validActivities.length;
    const lng = validActivities.reduce((s, a) => s + (a.lng ?? 0), 0) / validActivities.length;
    return { lat, lng };
  }, [validActivities]);

  if (!apiKey) {
    return (
      <div className="h-48 flex items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-400 text-sm">
        Google Maps API key not configured
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="h-48 flex items-center justify-center bg-gray-100 dark:bg-gray-800 text-red-400 text-sm">
        Failed to load map
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="h-48 flex items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-400 text-sm">
        Loading map…
      </div>
    );
  }

  return (
    <GoogleMap
      mapContainerStyle={mapContainerStyle}
      center={center()}
      zoom={13}
      options={{
        styles: mapDarkStyle,
        disableDefaultUI: false,
        zoomControl: true,
        mapTypeControl: false,
        streetViewControl: false,
      }}
    >
      {validActivities.map((activity, i) => (
        <Marker
          key={i}
          position={{ lat: activity.lat!, lng: activity.lng! }}
          label={{
            text: typeIcons[activity.type] ?? '📍',
            fontSize: '16px',
          }}
          onClick={() => setSelected(activity)}
        />
      ))}

      {selected && selected.lat && selected.lng && (
        <InfoWindow
          position={{ lat: selected.lat, lng: selected.lng }}
          onCloseClick={() => setSelected(null)}
        >
          <div className="max-w-[200px] p-1">
            <div className="font-bold text-gray-900 text-sm mb-1">{selected.title}</div>
            <div className="text-xs text-gray-600 mb-1">{selected.time} · {selected.duration}</div>
            <div className="text-xs text-gray-500 line-clamp-2">{selected.description}</div>
            {selected.cost !== undefined && selected.cost > 0 && (
              <div className="text-xs font-medium text-green-700 mt-1">¥{selected.cost.toLocaleString()}</div>
            )}
          </div>
        </InfoWindow>
      )}
    </GoogleMap>
  );
}
