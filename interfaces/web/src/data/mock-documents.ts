export interface MockDocument {
  document_type: string;
  raw_content: Record<string, unknown>;
  source_filename: string;
  _filename?: string;
}

export const MOCK_DOCUMENTS: MockDocument[] = [
  {
    document_type: "invoice",
    raw_content: {
      document_header: "FACTURE / INVOICE",
      invoice_number: "INV-2024-28289",
      date: "2024-05-08",
      shipper_name: "TransEurope Logistics GmbH",
      receiver_name: "Atlantic Shipping Ltd",
      origin: "Hamburg",
      destination: "Marseille",
      goods_description: "Composants électroniques haute densité",
      total_weight_kg: 82,
      transport_mode: "road",
      distance_km: 1450,
      departure_date: "2024-05-08",
      arrival_date: "2024-05-17",
      currency: "EUR",
    },
    source_filename: "invoice_001.json",
  },
  {
    document_type: "delivery_note",
    raw_content: {
      origin: "Stuttgart",
      destination: "Torino",
      total_weight_kg: 1200,
      transport_mode: "road",
      distance_km: 620,
      shipper_name: "Europarts Manufacturing GmbH",
      receiver_name: "Mediterranean Auto Components SRL",
    },
    source_filename: "delivery_note_001.json",
  },
];
