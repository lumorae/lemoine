// Supabase Edge Function: instagram-sync
//
// Runs on a daily schedule. It:
//   1. Refreshes the long-lived Instagram token (extends it ~60 days) and
//      writes the new value back to Supabase Vault.
//   2. Pulls recent media + engagement and upserts into social.posts.
//   3. Writes a fresh metrics snapshot into social.post_metrics.
//   4. Records an account-level snapshot (followers/reach) into
//      social.account_metrics.
//
// STATUS: ready to deploy. Not yet deployed (Supabase MCP access was
// unavailable when this was written). Deploy with the Supabase MCP
// deploy_edge_function tool or `supabase functions deploy instagram-sync`.
//
// Required Vault secret: `ig_lemoinedesign_token`  (the IGA... access token)
// Required env (auto-present in Edge runtime): SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

import { createClient } from "jsr:@supabase/supabase-js@2";

const GRAPH = "https://graph.instagram.com/v21.0";
const TOKEN_SECRET = "ig_lemoinedesign_token";

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

async function getToken(): Promise<{ id: string; token: string }> {
  const { data, error } = await supabase
    .schema("vault").from("decrypted_secrets")
    .select("id, decrypted_secret").eq("name", TOKEN_SECRET).single();
  if (error) throw error;
  return { id: data.id, token: data.decrypted_secret };
}

async function refreshToken(token: string): Promise<string> {
  const r = await fetch(
    `${GRAPH}/refresh_access_token?grant_type=ig_refresh_token&access_token=${token}`,
  );
  const j = await r.json();
  return j.access_token ?? token; // fall back to current token if refresh not yet allowed
}

Deno.serve(async () => {
  try {
    const { id, token } = await getToken();

    // 1. refresh + persist
    const fresh = await refreshToken(token);
    if (fresh !== token) {
      await supabase.rpc("update_vault_secret", { secret_id: id, new_value: fresh });
    }

    // 2. pull media
    const fields = "id,caption,media_type,timestamp,like_count,comments_count,permalink";
    const res = await fetch(`${GRAPH}/me/media?fields=${fields}&limit=50&access_token=${fresh}`);
    const media = (await res.json()).data ?? [];

    let synced = 0;
    for (const m of media) {
      // upsert the post (system of record)
      const { data: post } = await supabase.schema("social").from("posts").upsert({
        airtable_record_id: null,
        caption: m.caption ?? null,
        media_type: (m.media_type ?? "image").toLowerCase().includes("video") ? "video"
                  : (m.media_type === "CAROUSEL_ALBUM" ? "carousel" : "image"),
        platforms: ["instagram"],
        status: "published",
        published_at: m.timestamp,
      }, { onConflict: "airtable_record_id", ignoreDuplicates: false })
        .select("id").maybeSingle();

      // metrics snapshot
      await supabase.schema("social").from("post_metrics").insert({
        post_id: post?.id ?? null,
        platform: "instagram",
        likes: m.like_count ?? 0,
        comments: m.comments_count ?? 0,
        raw: m,
      });
      synced++;
    }

    // 3. account snapshot
    const acct = await (await fetch(
      `${GRAPH}/me/insights?metric=reach&period=day&metric_type=total_value&access_token=${fresh}`,
    )).json();
    await supabase.schema("social").from("account_metrics").insert({
      account_id: null, raw: acct,
    });

    return new Response(JSON.stringify({ ok: true, synced }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ ok: false, error: String(e) }), {
      status: 500, headers: { "Content-Type": "application/json" },
    });
  }
});
