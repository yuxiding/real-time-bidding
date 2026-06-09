export interface Activity {
  time: string;
  title: string;
  description: string;
  location: string;
  lat?: number;
  lng?: number;
  duration: string;
  cost?: number;
  type: 'sightseeing' | 'food' | 'shopping' | 'transport' | 'accommodation' | 'nature' | 'culture';
}

export interface DayItinerary {
  day: number;
  date: string;
  city: string;
  title: string;
  activities: Activity[];
}

export interface Hotel {
  name: string;
  city: string;
  pricePerNight: number;
  description: string;
  amenities: string[];
  rating: number;
  lat?: number;
  lng?: number;
}

export interface Transportation {
  from: string;
  to: string;
  method: string;
  duration: string;
  cost: number;
  notes: string;
}

export interface BudgetBreakdown {
  accommodation: number;
  food: number;
  transportation: number;
  activities: number;
  shopping: number;
  miscellaneous: number;
  total: number;
}

export interface TripPlan {
  id?: string;
  title: string;
  cities: string[];
  startDate: string;
  endDate: string;
  budget: number;
  interests: string[];
  days: DayItinerary[];
  hotels: Hotel[];
  transportation: Transportation[];
  budgetBreakdown: BudgetBreakdown;
  tips: string[];
  createdAt?: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name?: string;
  avatarUrl?: string;
}

export interface FavoritePlace {
  id?: string;
  userId?: string;
  placeName: string;
  placeType: string;
  notes?: string;
  locationLat?: number;
  locationLng?: number;
  city?: string;
  createdAt?: string;
}

export interface TripFormData {
  cities: string[];
  startDate: string;
  endDate: string;
  budget: number;
  interests: string[];
}
