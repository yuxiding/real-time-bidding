import { NextRequest } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase';

async function getUserFromRequest(request: NextRequest) {
  const supabase = createServerSupabaseClient();
  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    const token = authHeader.replace('Bearer ', '');
    const { data: { user } } = await supabase.auth.getUser(token);
    return { supabase, user };
  }
  // Try cookie-based session
  const { data: { user } } = await supabase.auth.getUser();
  return { supabase, user };
}

export async function GET(request: NextRequest) {
  try {
    const { supabase, user } = await getUserFromRequest(request);
    if (!user) {
      return Response.json({ trips: [] });
    }

    const { data, error } = await supabase
      .from('trips')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (error) throw error;

    const trips = (data ?? []).map((row: Record<string, unknown>) => ({
      ...(row.itinerary_json as object),
      id: row.id,
      createdAt: row.created_at,
    }));

    return Response.json({ trips });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return Response.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { supabase, user } = await getUserFromRequest(request);

    if (!user) {
      return Response.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { data, error } = await supabase.from('trips').insert({
      user_id: user.id,
      title: body.title,
      cities: body.cities,
      start_date: body.startDate,
      end_date: body.endDate,
      budget: body.budget,
      interests: body.interests,
      itinerary_json: body,
    }).select().single();

    if (error) throw error;

    return Response.json({ trip: data });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return Response.json({ error: message }, { status: 500 });
  }
}
