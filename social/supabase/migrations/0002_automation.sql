-- Lemoine social — automation: secret storage, token refresh helper, daily sync
-- Apply AFTER 0001_social_schema.sql.
--
-- STATUS: not yet applied (Supabase MCP access was unavailable at authoring
-- time). Apply via apply_migration or `supabase db push`.

-- Extensions for scheduling + outbound HTTP from Postgres
create extension if not exists pg_cron;
create extension if not exists pg_net;
create extension if not exists supabase_vault;

-- Helper the edge function calls to rotate the token in Vault
create or replace function public.update_vault_secret(secret_id uuid, new_value text)
returns void language sql security definer as $$
  select vault.update_secret(secret_id, new_value);
$$;

-- One-time secret bootstrap (RUN MANUALLY with the real token — never commit it):
--   select vault.create_secret('<IGA... token>', 'ig_lemoinedesign_token',
--     'Instagram long-lived token for @lemoinedesign');

-- Register the connected account (external_id = IG user id from /me)
insert into social.accounts (platform, display_name, external_id, token_secret)
values ('instagram', '@lemoinedesign', '17841401720504053', 'ig_lemoinedesign_token')
on conflict (platform, external_id) do nothing;

-- Daily sync at 09:00 UTC. Replace <PROJECT_REF> and store the service-role key
-- in Vault as 'service_role_key' before enabling.
-- select cron.schedule(
--   'ig-daily-sync', '0 9 * * *',
--   $$ select net.http_post(
--        url := 'https://<PROJECT_REF>.functions.supabase.co/instagram-sync',
--        headers := jsonb_build_object(
--          'Authorization', 'Bearer ' || (select decrypted_secret from vault.decrypted_secrets where name='service_role_key'),
--          'Content-Type', 'application/json')
--   ) $$
-- );
