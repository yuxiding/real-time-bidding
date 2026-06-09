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
  const { data: { user } } = await supabase.auth.getUser();
  return { supabase, user };
}

export async function GET(request: NextRequest) {
  try {
    const { supabase, user } = await getUserFromRequest(request);
    if (!user) {
      return Response.json({ favorites: [] });
    }

    const { data, error } = await supabase
      .from('favorites')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (error) throw error;

    const favorites = (data ?? []).map((row: Record<string, unknown>) => ({
      id: row.id,
      userId: row.user_id,
      placeName: row.place_name,
      placeType: row.place_type,
      notes: row.notes,
      locationLat: row.location_lat,
      locationLng: row.location_lng,
      city: row.city,
      createdAt: row.created_at,
    }));

    return Response.json({ favorites });
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

    const { data, error } = await supabase.from('favorites').insert({
      user_id: user.id,
      place_name: body.placeName,
      place_type: body.placeType,
      notes: body.notes,
      location_lat: body.locationLat,
      location_lng: body.locationLng,
      city: body.city,
    }).select().single();

    if (error) throw error;

    return Response.json({ favorite: data });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return Response.json({ error: message }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const id = url.searchParams.get('id');
    if (!id) return Response.json({ error: 'ID required' }, { status: 400 });

    const { supabase, user } = await getUserFromRequest(request);
    if (!user) return Response.json({ error: 'Unauthorized' }, { status: 401 });

    const { error } = await supabase
      .from('favorites')
      .delete()
      .eq('id', id)
      .eq('user_id', user.id);

    if (error) throw error;

    return Response.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Internal server error';
    return Response.json({ error: message }, { status: 500 });
  }
}
