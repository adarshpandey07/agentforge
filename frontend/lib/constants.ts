export const BUSINESS_TYPES = [
  "bakery",
  "barber",
  "salon",
  "restaurant",
  "gym",
  "dentist",
  "clinic",
  "lawyer",
  "real_estate",
  "car_dealer",
  "travel_agency",
  "hotel",
  "retail",
  "ecommerce",
  "coaching_institute",
] as const;

export type BusinessType = (typeof BUSINESS_TYPES)[number];

export const BUSINESS_TYPE_LABELS: Record<string, string> = {
  bakery: "Bakery",
  barber: "Barber Shop",
  salon: "Salon & Spa",
  restaurant: "Restaurant",
  gym: "Gym & Fitness",
  dentist: "Dental Practice",
  clinic: "Medical Clinic",
  lawyer: "Law Firm",
  real_estate: "Real Estate",
  car_dealer: "Car Dealership",
  travel_agency: "Travel Agency",
  hotel: "Hotel",
  retail: "Retail Store",
  ecommerce: "E-commerce",
  coaching_institute: "Coaching Institute",
};

export interface IntegrationDef {
  provider: string;
  name: string;
  description: string;
  category: string;
  type: "builtin" | "api" | "webhook";
  fields: { key: string; label: string; placeholder?: string; secret?: boolean }[];
}

export const INTEGRATION_CATALOG: IntegrationDef[] = [
  { provider: "gmail", name: "Gmail", description: "Send and read email on behalf of the business.", category: "Communication", type: "builtin", fields: [{ key: "client_id", label: "OAuth Client ID" }, { key: "client_secret", label: "OAuth Client Secret", secret: true }] },
  { provider: "google_calendar", name: "Google Calendar", description: "Book, reschedule and cancel appointments.", category: "Scheduling", type: "builtin", fields: [{ key: "client_id", label: "OAuth Client ID" }, { key: "client_secret", label: "OAuth Client Secret", secret: true }, { key: "calendar_id", label: "Calendar ID", placeholder: "primary" }] },
  { provider: "google_maps", name: "Google Maps", description: "Locations, directions and business hours.", category: "Data", type: "builtin", fields: [{ key: "api_key", label: "API Key", secret: true }] },
  { provider: "whatsapp", name: "WhatsApp", description: "Chat with customers on WhatsApp Business.", category: "Communication", type: "builtin", fields: [{ key: "phone_number_id", label: "Phone Number ID" }, { key: "access_token", label: "Access Token", secret: true }] },
  { provider: "slack", name: "Slack", description: "Notify teams and escalate to humans in Slack.", category: "Communication", type: "builtin", fields: [{ key: "bot_token", label: "Bot Token", secret: true }, { key: "default_channel", label: "Default Channel", placeholder: "#support" }] },
  { provider: "twilio", name: "Twilio", description: "SMS and voice calls for reminders and alerts.", category: "Communication", type: "builtin", fields: [{ key: "account_sid", label: "Account SID" }, { key: "auth_token", label: "Auth Token", secret: true }, { key: "from_number", label: "From Number", placeholder: "+1..." }] },
  { provider: "stripe", name: "Stripe", description: "Payments, invoices and subscription status.", category: "Payments", type: "builtin", fields: [{ key: "secret_key", label: "Secret Key", secret: true }] },
  { provider: "shopify", name: "Shopify", description: "Orders, products and inventory lookups.", category: "Commerce", type: "builtin", fields: [{ key: "shop_domain", label: "Shop Domain", placeholder: "my-store.myshopify.com" }, { key: "access_token", label: "Admin API Token", secret: true }] },
  { provider: "hubspot", name: "HubSpot", description: "CRM contacts, deals and pipelines.", category: "CRM", type: "builtin", fields: [{ key: "access_token", label: "Private App Token", secret: true }] },
  { provider: "salesforce", name: "Salesforce", description: "Enterprise CRM records and workflows.", category: "CRM", type: "builtin", fields: [{ key: "instance_url", label: "Instance URL" }, { key: "access_token", label: "Access Token", secret: true }] },
  { provider: "zapier", name: "Zapier", description: "Trigger thousands of Zapier automations.", category: "Automation", type: "webhook", fields: [{ key: "webhook_url", label: "Zap Webhook URL" }] },
  { provider: "n8n", name: "n8n", description: "Self-hosted workflow automation triggers.", category: "Automation", type: "webhook", fields: [{ key: "webhook_url", label: "Webhook URL" }, { key: "api_key", label: "API Key", secret: true }] },
  { provider: "custom_api", name: "Custom API", description: "Call any REST API with typed parameters.", category: "Developer", type: "api", fields: [{ key: "base_url", label: "Base URL", placeholder: "https://api.example.com" }, { key: "api_key", label: "API Key", secret: true }] },
  { provider: "webhook", name: "Webhook", description: "Send events to an arbitrary HTTP endpoint.", category: "Developer", type: "webhook", fields: [{ key: "url", label: "Endpoint URL" }, { key: "secret", label: "Signing Secret", secret: true }] },
  { provider: "database", name: "Database", description: "Query a SQL database for live business data.", category: "Developer", type: "api", fields: [{ key: "connection_string", label: "Connection String", secret: true }] },
];
