'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

const PRESETS = [
  {
    id: 'wedding',
    label: 'Wedding',
    data: {
      event_type: 'wedding',
      hero_section: {
        event_name: "Rishabh weds Sheetal",
        event_date: "February 24, 2026",
        event_venue: "Gangotri Resort, Nagpur"
      }
    }
  },
  {
    id: 'birthday',
    label: 'Birthday',
    data: {
      event_type: 'birthday',
      hero_section: {
        event_name: "John's 30th Birthday",
        event_date: "March 15, 2026",
        event_venue: "City Club, New York"
      }
    }
  },
  {
    id: 'corporate',
    label: 'Corporate',
    data: {
      event_type: 'corporate',
      hero_section: {
        event_name: "Tech Innovators Summit",
        event_date: "April 10, 2026",
        event_venue: "Convention Center, SF"
      }
    }
  }
];

export default function LandingPage() {
  const router = useRouter();
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [designerComments, setDesignerComments] = useState('');
  const [slug, setSlug] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePlaceOrder = async () => {
    if (!selectedPreset || !designerComments.trim() || !slug.trim()) return;

    setLoading(true);
    setError('');

    const userId = `user_${Math.random().toString(36).substr(2, 9)}`;

    const payload = {
      userId: userId,
      orderData: selectedPreset.data,
      metadata: {
        designer_comments: designerComments,
        slug: slug,
        // Dummy data for required fields
        name: "John Doe",
        email: "john.doe@example.com",
        contact: "+1234567890",
        billing_address: {
          line1: "123 Main St",
          city: "New York",
          state: "NY",
          zipcode: "10001",
          country: "USA"
        },
        product_type: selectedPreset.label,
        occasion: selectedPreset.id,
        product_life: "30days",
        style_preference: "modern",
        budget_preference: "standard",
        service_interests: ["design"],
        design_manual: "https://example.com/manual.pdf"
      }
    };

    try {
      const apiKey = process.env.NEXT_PUBLIC_API_KEY || 'test';

      const res = await fetch('/api/createOrder', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Api-Key': apiKey
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || 'Failed to place order');
      }

      const data = await res.json();
      const orderId = data.orderId;

      localStorage.setItem('user_id', orderId);
      router.push(`/monitor?autoRun=true&prompt=${orderId}`);

    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const isFormValid = selectedPreset && designerComments.trim() && slug.trim();

  return (
    <div className="h-full w-full overflow-y-auto p-8 flex flex-col items-center">
      <div className="bg-black/30 backdrop-blur-xl border border-white/10 p-8 rounded-2xl shadow-2xl w-full max-w-3xl space-y-8 animate-in fade-in zoom-in duration-500">
        <h1 className="text-4xl font-bold mb-8 text-center bg-clip-text text-transparent bg-gradient-to-r from-blue-300 to-purple-300">
          Create New Order
        </h1>

        {/* Presets */}
        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-200">1. Select Data Preset</h2>
          <div className="grid grid-cols-3 gap-4">
            {PRESETS.map((preset) => (
              <button
                key={preset.id}
                onClick={() => setSelectedPreset(preset)}
                className={`p-4 rounded-xl border transition-all backdrop-blur-sm ${selectedPreset?.id === preset.id
                  ? 'bg-blue-600/80 border-blue-400 text-white shadow-[0_0_15px_rgba(37,99,235,0.5)] scale-105'
                  : 'bg-white/5 border-white/10 hover:bg-white/10 text-gray-300 hover:border-white/20'
                  }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Inputs */}
        <div>
          <h2 className="text-xl font-semibold mb-4 text-gray-200">2. Enter Details</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Designer Comments</label>
              <textarea
                value={designerComments}
                onChange={(e) => setDesignerComments(e.target.value)}
                className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus:bg-white/10 transition-colors"
                rows="3"
                placeholder="Enter comments for the designer..."
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Slug</label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="w-full p-3 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:border-blue-500 focus:bg-white/10 transition-colors"
                placeholder="e.g., my-event-2026"
              />
            </div>
          </div>
        </div>

        {/* Action */}
        <div className="pt-4">
          {error && <p className="text-red-400 mb-4 bg-red-900/20 p-2 rounded border border-red-500/50">{error}</p>}
          <button
            onClick={handlePlaceOrder}
            disabled={!isFormValid || loading}
            className={`w-full py-4 rounded-xl font-bold text-lg transition-all shadow-lg ${isFormValid && !loading
              ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white hover:shadow-green-900/50'
              : 'bg-gray-800/50 text-gray-500 cursor-not-allowed border border-white/5'
              }`}
          >
            {loading ? 'Processing...' : 'Place Order'}
          </button>
        </div>

        <div className="text-center mt-4">
          <Link href="/monitor" className="text-blue-300 hover:text-blue-200 hover:underline transition-colors">
            Go to Monitor Page
          </Link>
        </div>
      </div>
    </div>
  );
}
