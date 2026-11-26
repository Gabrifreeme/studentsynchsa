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
grant select, insert on public.app_notifications to anon;
