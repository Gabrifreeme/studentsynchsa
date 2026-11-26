-- In-app notifications: email alerts pushed by ACEsi appear in the app.
-- Run this once in Supabase -> SQL Editor -> New query -> Run.

create table if not exists public.app_notifications (
  id bigint generated always as identity primary key,
  created_at timestamptz not null default now(),
  title text not null,
  body text not null,
  sender text
);

alter table public.app_notifications enable row level security;

drop policy if exists "anon read notifications" on public.app_notifications;
create policy "anon read notifications"
  on public.app_notifications for select to anon using (true);

drop policy if exists "anon insert notifications" on public.app_notifications;
create policy "anon insert notifications"
  on public.app_notifications for insert to anon with check (true);

grant usage on schema public to anon;
grant select, insert, delete on public.app_notifications to anon;

-- Allow the app's X button to delete an email notification.
drop policy if exists "anon delete notifications" on public.app_notifications;
create policy "anon delete notifications"
  on public.app_notifications for delete to anon using (true);

-- Web Push subscriptions (one row per device/browser).
create table if not exists public.push_subscriptions (
  id bigint generated always as identity primary key,
  endpoint text not null,
  p256dh text not null,
  auth text not null,
  created_at timestamptz not null default now()
);
alter table public.push_subscriptions enable row level security;
drop policy if exists "anon read push subscriptions" on public.push_subscriptions;
create policy "anon read push subscriptions"
  on public.push_subscriptions for select to anon using (true);
drop policy if exists "anon insert push subscriptions" on public.push_subscriptions;
create policy "anon insert push subscriptions"
  on public.push_subscriptions for insert to anon with check (true);
grant usage on schema public to anon;
grant select, insert on public.push_subscriptions to anon;
