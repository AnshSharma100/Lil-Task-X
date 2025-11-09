import { supabase } from "../lib/supabaseClient";

export type Author = "user" | "bot";

export type MessageRow = {
  id: number;
  product_id: number;
  author: Author;
  content: string;
  created_at: string;
  auth0_sub?: string | null;
};

export async function fetchMessages(productId: number) {
  return supabase
    .from("product_messages")
    .select("*")
    .eq("product_id", productId)
    .order("created_at", { ascending: true });
}

export async function insertMessage(productId: number, author: "user" | "bot", content: string, auth0_sub?: string | null) {
  return supabase
    .from("product_messages")
    .insert([{ product_id: productId, author, content }])
    .select("*")
    .single();
}
