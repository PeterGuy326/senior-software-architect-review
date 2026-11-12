CREATE TABLE IF NOT EXISTS coach.knowledge_releases (
 id text PRIMARY KEY, exam_id text NOT NULL, ready boolean NOT NULL DEFAULT false);
CREATE TABLE IF NOT EXISTS coach.knowledge_chunks (
 id text NOT NULL, release_id text REFERENCES coach.knowledge_releases(id), payload jsonb NOT NULL,
 PRIMARY KEY(release_id,id));
CREATE TABLE IF NOT EXISTS coach.chat_turns (
 goal_id varchar(64) REFERENCES coach.learning_goals(id), request_id text NOT NULL,
 user_message text NOT NULL, status text NOT NULL, lease text NOT NULL, lease_until timestamptz NOT NULL,
 response jsonb, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(goal_id,request_id));
CREATE INDEX IF NOT EXISTS chat_turns_goal_created ON coach.chat_turns(goal_id,created_at DESC);
ALTER TABLE coach.chat_turns ADD COLUMN IF NOT EXISTS attempts integer NOT NULL DEFAULT 0;
REVOKE ALL ON coach.knowledge_releases,coach.knowledge_chunks,coach.chat_turns FROM PUBLIC,anon,authenticated;

CREATE OR REPLACE FUNCTION public.coach_chat_rpc(p_action text,p_payload jsonb DEFAULT '{}',p_token text DEFAULT '')
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,coach AS $$
DECLARE owner_id text; g coach.learning_goals%ROWTYPE; t coach.chat_turns%ROWTYPE; result jsonb;
BEGIN
 IF p_action='knowledge' THEN
  IF NOT EXISTS(SELECT 1 FROM coach.knowledge_releases WHERE id=p_payload->>'release_id' AND ready) THEN
   RETURN '{"error":"not_found"}'; END IF;
  SELECT coalesce(jsonb_agg(payload),'[]') INTO result FROM coach.knowledge_chunks WHERE release_id=p_payload->>'release_id';
  RETURN jsonb_build_object('chunks',result);
 END IF;
 SELECT user_id INTO owner_id FROM coach.sessions WHERE token_hash=p_token AND expires_at>extract(epoch FROM now())::integer;
 IF owner_id IS NULL THEN RETURN '{"error":"unauthorized"}'; END IF;
 SELECT * INTO g FROM coach.learning_goals WHERE id=p_payload->>'goal_id' AND user_id=owner_id FOR UPDATE;
 IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;
 IF p_action IN ('history','begin') THEN
  SELECT coalesce(jsonb_agg(x.item ORDER BY x.created_at),'[]') INTO result FROM (
   SELECT jsonb_build_object('request_id',request_id,'user',user_message,'response',response) item,created_at
   FROM coach.chat_turns WHERE goal_id=g.id AND status='complete' ORDER BY created_at DESC LIMIT 10) x;
  IF p_action='history' THEN RETURN jsonb_build_object('items',result); END IF;
  IF length(p_payload->>'message') NOT BETWEEN 1 AND 2000 OR length(p_payload->>'request_id') NOT BETWEEN 8 AND 80 THEN
   RETURN '{"error":"invalid_answer"}'; END IF;
  SELECT * INTO t FROM coach.chat_turns WHERE goal_id=g.id AND request_id=p_payload->>'request_id';
  IF FOUND THEN
   IF t.user_message<>p_payload->>'message' THEN RETURN '{"error":"conflict"}'; END IF;
   IF t.status='complete' THEN RETURN jsonb_build_object('response',t.response); END IF;
   IF t.status='pending' AND t.lease_until>now() THEN RETURN '{"pending":true}'; END IF;
   IF t.attempts>=3 THEN RETURN '{"error":"rate_limit"}'; END IF;
  END IF;
  IF EXISTS(SELECT 1 FROM coach.chat_turns WHERE goal_id=g.id AND status='pending' AND lease_until>now()) THEN
   RETURN '{"error":"busy"}'; END IF;
  IF (SELECT count(*) FROM coach.chat_turns ct JOIN coach.learning_goals lg ON ct.goal_id=lg.id
      WHERE lg.user_id=owner_id AND ct.created_at>now()-interval '24 hours')>=50 AND t.request_id IS NULL THEN
   RETURN '{"error":"rate_limit"}'; END IF;
  INSERT INTO coach.chat_turns(goal_id,request_id,user_message,status,lease,lease_until,attempts)
   VALUES(g.id,p_payload->>'request_id',p_payload->>'message','pending',p_payload->>'lease',now()+interval '120 seconds',1)
   ON CONFLICT(goal_id,request_id) DO UPDATE SET status='pending',lease=excluded.lease,lease_until=excluded.lease_until,attempts=coach.chat_turns.attempts+1;
  RETURN jsonb_build_object('history',result);
 ELSIF p_action='result' THEN
  SELECT * INTO t FROM coach.chat_turns WHERE goal_id=g.id AND request_id=p_payload->>'request_id';
  IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;
  RETURN jsonb_build_object('status',CASE WHEN t.status='pending' AND t.lease_until<=now() THEN 'failed' ELSE t.status END,
                            'response',CASE WHEN t.status='complete' THEN t.response ELSE NULL END);
 ELSIF p_action='complete' THEN
  UPDATE coach.chat_turns SET status='complete',response=p_payload->'response'
   WHERE goal_id=g.id AND request_id=p_payload->>'request_id' AND lease=p_payload->>'lease' AND status='pending';
  IF NOT FOUND THEN RETURN '{"error":"conflict"}'; END IF;
  RETURN jsonb_build_object('response',p_payload->'response');
 ELSIF p_action='fail' THEN
  UPDATE coach.chat_turns SET status='failed',lease_until=now() WHERE goal_id=g.id AND request_id=p_payload->>'request_id'
   AND lease=p_payload->>'lease' AND status='pending';
  RETURN '{"ok":true}';
 END IF;
 RETURN '{"error":"unknown_action"}';
END; $$;
REVOKE ALL ON FUNCTION public.coach_chat_rpc(text,jsonb,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.coach_chat_rpc(text,jsonb,text) TO service_role;
NOTIFY pgrst,'reload schema';
