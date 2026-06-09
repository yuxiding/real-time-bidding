import OpenAI from 'openai';
import { TripPlan } from './types';

function getOpenAIClient() {
  return new OpenAI({
    apiKey: process.env.OPENAI_API_KEY || 'placeholder',
  });
}

export interface GenerateItineraryParams {
  cities: string[];
  startDate: string;
  endDate: string;
  budget: number;
  interests: string[];
}

export async function generateItinerary(params: GenerateItineraryParams): Promise<TripPlan> {
  const { cities, startDate, endDate, budget, interests } = params;

  const start = new Date(startDate);
  const end = new Date(endDate);
  const numDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;

  const systemPrompt = `You are an expert Japan travel planner with deep knowledge of Japanese culture, geography, cuisine, and attractions. You create detailed, realistic, and exciting travel itineraries for Japan.

Always respond with valid JSON matching this exact structure:
{
  "title": "string - catchy trip title",
  "days": [
    {
      "day": 1,
      "date": "YYYY-MM-DD",
      "city": "string",
      "title": "string - day theme",
      "activities": [
        {
          "time": "HH:MM",
          "title": "string",
          "description": "string - 2-3 sentences",
          "location": "string - address or landmark name",
          "lat": number,
          "lng": number,
          "duration": "string e.g. '2 hours'",
          "cost": number (in JPY),
          "type": "sightseeing|food|shopping|transport|accommodation|nature|culture"
        }
      ]
    }
  ],
  "hotels": [
    {
      "name": "string",
      "city": "string",
      "pricePerNight": number (JPY),
      "description": "string",
      "amenities": ["string"],
      "rating": number (1-5),
      "lat": number,
      "lng": number
    }
  ],
  "transportation": [
    {
      "from": "string",
      "to": "string",
      "method": "string e.g. Shinkansen, subway, bus",
      "duration": "string",
      "cost": number (JPY),
      "notes": "string"
    }
  ],
  "budgetBreakdown": {
    "accommodation": number,
    "food": number,
    "transportation": number,
    "activities": number,
    "shopping": number,
    "miscellaneous": number,
    "total": number
  },
  "tips": ["string - practical travel tips"]
}`;

  const userPrompt = `Create a ${numDays}-day Japan travel itinerary with these details:
- Cities to visit: ${cities.join(', ')}
- Travel dates: ${startDate} to ${endDate}
- Total budget: ¥${budget.toLocaleString()} JPY
- Interests: ${interests.join(', ')}

Please create a detailed day-by-day itinerary that:
1. Starts each day with breakfast and ends with dinner
2. Includes 4-6 activities per day
3. Respects the budget constraints
4. Focuses on the specified interests
5. Includes realistic travel times between locations
6. Suggests authentic local experiences
7. Provides accurate GPS coordinates for each location
8. Recommends one hotel per city
9. Details all transportation between cities
10. Creates a realistic budget breakdown`;

  const openai = getOpenAIClient();
  const response = await openai.chat.completions.create({
    model: 'gpt-4o',
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ],
    response_format: { type: 'json_object' },
    temperature: 0.7,
    max_tokens: 4000,
  });

  const content = response.choices[0].message.content;
  if (!content) {
    throw new Error('No response from OpenAI');
  }

  const itinerary = JSON.parse(content) as Omit<TripPlan, 'cities' | 'startDate' | 'endDate' | 'budget' | 'interests'>;

  return {
    ...itinerary,
    cities,
    startDate,
    endDate,
    budget,
    interests,
  };
}

export default getOpenAIClient;
