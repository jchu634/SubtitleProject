import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const response = await fetch('http://localhost:6789/api/get_sound_devices');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching devices:', error);
    return NextResponse.json({ error: 'Failed to fetch devices' }, { status: 500 });
  }
}