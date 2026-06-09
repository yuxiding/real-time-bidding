import { NextRequest } from 'next/server';
import { generateItinerary } from '@/lib/openai';
import { createServerSupabaseClient } from '@/lib/supabase';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { cities, startDate, endDate, budget, interests } = body;

    if (!cities?.length || !startDate || !endDate || !interests?.length) {
      return Response.json({ error: 'Missing required fields' }, { status: 400 });
    }

    const itinerary = await generateItinerary({ cities, startDate, endDate, budget: budget ?? 300000, interests });

    // Optionally save to Supabase if user is authenticated
    try {
      const supabase = createServerSupabaseClient();
      const authHeader = request.headers.get('authorization');
      if (authHeader) {
        const token = authHeader.replace('Bearer ', '');
        const { data: { user } } = await supabase.auth.getUser(token);
        if (user) {
          await supabase.from('trips').insert({
            user_id: user.id,
            title: itinerary.title,
            cities: itinerary.cities,
            start_date: itinerary.startDate,
            end_date: itinerary.endDate,
            budget: itinerary.budget,
            interests: itinerary.interests,
            itinerary_json: itinerary,
          });
        }
      }
    } catch {
      // Non-fatal — continue even if save fails
    }

    return Response.json({ itinerary });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return Response.json({ error: message }, { status: 500 });
  }
}
