CREATE TABLE IF NOT EXISTS coach.voice_jobs (
 goal_id varchar(64) REFERENCES coach.learning_goals(id),request_id text NOT NULL,
 audio_hash text NOT NULL,status text NOT NULL,lease text NOT NULL,lease_until timestamptz NOT NULL,
 transcript text,attempts integer NOT NULL DEFAULT 1,created_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL DEFAULT now()+interval '30 minutes',PRIMARY KEY(goal_id,request_id));
CREATE INDEX IF NOT EXISTS voice_jobs_goal_created ON coach.voice_jobs(goal_id,created_at DESC);
REVOKE ALL ON coach.voice_jobs FROM PUBLIC,anon,authenticated;
CREATE OR REPLACE FUNCTION public.coach_voice_rpc(p_action text,p_payload jsonb DEFAULT '{}',p_token text DEFAULT '')
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,coach AS $$
DECLARE owner_id text; g coach.learning_goals%ROWTYPE; j coach.voice_jobs%ROWTYPE;
BEGIN
 SELECT user_id INTO owner_id FROM coach.sessions WHERE token_hash=p_token AND expires_at>extract(epoch FROM now())::integer;
 IF owner_id IS NULL THEN RETURN '{"error":"unauthorized"}'; END IF;
 SELECT * INTO g FROM coach.learning_goals WHERE id=p_payload->>'goal_id' AND user_id=owner_id FOR UPDATE;
 IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;
 -- Intermediate drafts are unreadable after expiry; later traffic also clears old text.
 UPDATE coach.voice_jobs SET transcript=NULL,status='expired' WHERE expires_at<=now() AND status<>'expired';
 DELETE FROM coach.voice_jobs WHERE created_at<now()-interval '25 hours';
 SELECT * INTO j FROM coach.voice_jobs WHERE goal_id=g.id AND request_id=p_payload->>'request_id';
 IF p_action='begin' THEN
  IF FOUND THEN
   IF j.audio_hash<>p_payload->>'audio_hash' THEN RETURN '{"error":"conflict"}'; END IF;
   IF j.status='expired' THEN RETURN '{"status":"expired"}'; END IF;
   IF j.status='complete' THEN RETURN jsonb_build_object('status','complete','text',j.transcript); END IF;
   IF j.status='pending' AND j.lease_until>now() THEN RETURN '{"status":"pending"}'; END IF;
   IF j.attempts>=3 THEN RETURN '{"error":"rate_limit"}'; END IF;
  END IF;
  IF EXISTS(SELECT 1 FROM coach.voice_jobs WHERE goal_id=g.id AND status='pending' AND lease_until>now()) THEN RETURN '{"error":"busy"}'; END IF;
  IF j.request_id IS NULL AND (SELECT count(*) FROM coach.voice_jobs v JOIN coach.learning_goals lg ON lg.id=v.goal_id
      WHERE lg.user_id=owner_id AND v.created_at>now()-interval '24 hours')>=50 THEN RETURN '{"error":"rate_limit"}'; END IF;
  INSERT INTO coach.voice_jobs(goal_id,request_id,audio_hash,status,lease,lease_until)
   VALUES(g.id,p_payload->>'request_id',p_payload->>'audio_hash','pending',p_payload->>'lease',now()+interval '90 seconds')
   ON CONFLICT(goal_id,request_id) DO UPDATE SET status='pending',lease=excluded.lease,lease_until=excluded.lease_until,
      attempts=coach.voice_jobs.attempts+1;
  RETURN '{"generate":true,"status":"pending"}';
 ELSIF p_action='result' THEN
  IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;
  RETURN jsonb_build_object('status',CASE WHEN j.status='pending' AND j.lease_until<=now() THEN 'failed' ELSE j.status END,
      'text',CASE WHEN j.status='complete' THEN j.transcript ELSE NULL END);
 ELSIF p_action='complete' THEN
  UPDATE coach.voice_jobs SET status='complete',transcript=p_payload->>'text'
   WHERE goal_id=g.id AND request_id=p_payload->>'request_id' AND lease=p_payload->>'lease'
      AND status='pending' AND expires_at>now();
  IF NOT FOUND THEN RETURN '{"error":"conflict"}'; END IF;
  RETURN '{"ok":true}';
 ELSIF p_action='fail' THEN
  UPDATE coach.voice_jobs SET status='failed',lease_until=now() WHERE goal_id=g.id AND request_id=p_payload->>'request_id'
    AND lease=p_payload->>'lease' AND status='pending';
  RETURN '{"ok":true}';
 END IF;
 RETURN '{"error":"unknown_action"}';
END; $$;
REVOKE ALL ON FUNCTION public.coach_voice_rpc(text,jsonb,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.coach_voice_rpc(text,jsonb,text) TO service_role;
NOTIFY pgrst,'reload schema';
