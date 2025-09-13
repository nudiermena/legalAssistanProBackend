-- Create friend testing invites table
-- Run this script in your Supabase SQL Editor

create table public.friend_testing_invites (
  id uuid not null default gen_random_uuid (),
  inviter_id uuid null,
  friend_email text not null,
  friend_name text null,
  invite_code text not null,
  daily_limit integer not null default 5,
  trial_days integer not null default 3,
  status text not null default 'pending'::text,
  accepted_at timestamp with time zone null,
  expires_at timestamp with time zone not null,
  created_at timestamp with time zone null default CURRENT_TIMESTAMP,
  updated_at timestamp with time zone null default CURRENT_TIMESTAMP,
  constraint friend_testing_invites_pkey primary key (id),
  constraint friend_testing_invites_friend_email_key unique (friend_email),
  constraint friend_testing_invites_invite_code_key unique (invite_code),
  constraint friend_testing_invites_inviter_id_fkey foreign KEY (inviter_id) references auth.users (id) on delete CASCADE,
  constraint friend_testing_invites_inviter_id_profiles_fkey foreign KEY (inviter_id) references profiles (id),
  constraint friend_testing_invites_status_check check (
    (
      status = any (
        array[
          'pending'::text,
          'accepted'::text,
          'expired'::text,
          'cancelled'::text
        ]
      )
    )
  )
) TABLESPACE pg_default;

create index IF not exists idx_friend_testing_invites_email on public.friend_testing_invites using btree (friend_email) TABLESPACE pg_default;

create index IF not exists idx_friend_testing_invites_code on public.friend_testing_invites using btree (invite_code) TABLESPACE pg_default;

-- Enable RLS (Row Level Security)
ALTER TABLE friend_testing_invites ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view invites they created" ON friend_testing_invites
    FOR SELECT USING (inviter_id = auth.uid());

CREATE POLICY "Users can create invites" ON friend_testing_invites
    FOR INSERT WITH CHECK (inviter_id = auth.uid());

CREATE POLICY "Users can update invites they created" ON friend_testing_invites
    FOR UPDATE USING (inviter_id = auth.uid());

-- Allow public access to validate invite codes (for the validation endpoint)
CREATE POLICY "Public can validate invite codes" ON friend_testing_invites
    FOR SELECT USING (status = 'pending' AND expires_at > NOW());

-- Create function to automatically expire invites
CREATE OR REPLACE FUNCTION expire_invites()
RETURNS void AS $$
BEGIN
    UPDATE friend_testing_invites 
    SET status = 'expired', updated_at = NOW()
    WHERE status = 'pending' AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_friend_testing_invites_updated_at
    BEFORE UPDATE ON friend_testing_invites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON friend_testing_invites TO anon, authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
