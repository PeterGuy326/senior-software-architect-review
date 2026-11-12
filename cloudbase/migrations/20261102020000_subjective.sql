CREATE TABLE IF NOT EXISTS coach.subjective_issues (
 id varchar(64) PRIMARY KEY,goal_id varchar(64) NOT NULL REFERENCES coach.learning_goals(id),
 task_ref text NOT NULL,created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS subjective_issue_goal ON coach.subjective_issues(goal_id,created_at);
CREATE TABLE IF NOT EXISTS coach.subjective_reviews (
 goal_id varchar(64) REFERENCES coach.learning_goals(id),request_id text NOT NULL,
 kind text NOT NULL CHECK(kind IN ('case','essay')),issue_id varchar(64) REFERENCES coach.subjective_issues(id),
 input_hash text NOT NULL,input jsonb NOT NULL,status text NOT NULL,lease text NOT NULL,
 lease_until timestamptz NOT NULL,attempts integer NOT NULL DEFAULT 1,response jsonb,event jsonb,
 created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(goal_id,request_id));
CREATE UNIQUE INDEX IF NOT EXISTS subjective_case_once ON coach.subjective_reviews(issue_id) WHERE issue_id IS NOT NULL;
REVOKE ALL ON coach.subjective_issues,coach.subjective_reviews FROM PUBLIC,anon,authenticated;

CREATE OR REPLACE FUNCTION public.coach_subjective_rpc(p_action text,p_payload jsonb DEFAULT '{}',p_token text DEFAULT '')
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,coach AS $$
DECLARE owner_id text;g coach.learning_goals%ROWTYPE;i coach.subjective_issues%ROWTYPE;
 j coach.subjective_reviews%ROWTYPE;ref text;result jsonb;
BEGIN
 SELECT user_id INTO owner_id FROM coach.sessions WHERE token_hash=p_token AND expires_at>extract(epoch FROM now())::integer;
 IF owner_id IS NULL THEN RETURN '{"error":"unauthorized"}';END IF;
 SELECT * INTO g FROM coach.learning_goals WHERE id=p_payload->>'goal_id' AND user_id=owner_id FOR UPDATE;
 IF NOT FOUND THEN RETURN '{"error":"not_found"}';END IF;
 IF p_action='case_next' THEN
  SELECT * INTO i FROM coach.subjective_issues si WHERE si.goal_id=g.id AND NOT EXISTS(
   SELECT 1 FROM coach.subjective_reviews sr WHERE sr.issue_id=si.id AND sr.status IN ('complete','abandoned')) ORDER BY si.created_at LIMIT 1;
  IF NOT FOUND THEN
   SELECT value INTO ref FROM jsonb_array_elements_text(p_payload->'task_refs') ORDER BY
    (SELECT count(*) FROM coach.subjective_issues si WHERE si.goal_id=g.id AND si.task_ref=value),value LIMIT 1;
   IF ref IS NULL THEN RETURN '{"error":"not_found"}';END IF;
   INSERT INTO coach.subjective_issues(id,goal_id,task_ref) VALUES(p_payload->>'issue_id',g.id,ref) RETURNING * INTO i;
  END IF;
  RETURN to_jsonb(i);
 ELSIF p_action='case_message' THEN
  SELECT * INTO i FROM coach.subjective_issues WHERE id=p_payload->>'issue_id' AND goal_id=g.id;
  IF NOT FOUND THEN RETURN '{"error":"not_found"}';END IF;
  INSERT INTO coach.chat_turns(goal_id,request_id,user_message,status,lease,lease_until,response)
   VALUES(g.id,'case_'||i.id,'练一道案例','complete','',now(),p_payload->'response') ON CONFLICT DO NOTHING;
  RETURN '{"ok":true}';
 ELSIF p_action='issue' THEN
  SELECT * INTO i FROM coach.subjective_issues WHERE id=p_payload->>'issue_id' AND goal_id=g.id;
  IF NOT FOUND THEN RETURN '{"error":"not_found"}';END IF;
  RETURN to_jsonb(i);
 ELSIF p_action='summary' THEN
  SELECT jsonb_build_object('case_count',count(*) FILTER(WHERE kind='case'),'essay_count',count(*) FILTER(WHERE kind='essay'))
    INTO result FROM coach.subjective_reviews WHERE goal_id=g.id AND status='complete';
  RETURN result;
 ELSIF p_action='pending' THEN
  SELECT * INTO j FROM coach.subjective_reviews WHERE goal_id=g.id AND status IN ('pending','failed') ORDER BY created_at DESC LIMIT 1;
  IF NOT FOUND THEN RETURN '{"job":null}';END IF;
  RETURN jsonb_build_object('job',jsonb_build_object('request_id',j.request_id,'kind',j.kind,
    'status',CASE WHEN j.status='pending' AND j.lease_until<=now() THEN 'failed' ELSE j.status END));
 END IF;
 SELECT * INTO j FROM coach.subjective_reviews WHERE goal_id=g.id AND request_id=p_payload->>'request_id';
 IF p_action='begin' THEN
  IF FOUND THEN
   IF j.input_hash<>p_payload->>'input_hash' THEN RETURN '{"error":"conflict"}';END IF;
   IF j.status='abandoned' THEN RETURN '{"error":"conflict"}';END IF;
   IF j.status='complete' THEN RETURN jsonb_build_object('status','complete','response',j.response);END IF;
   IF j.status='pending' AND j.lease_until>now() THEN RETURN '{"status":"pending"}';END IF;
   IF j.attempts>=3 THEN RETURN '{"error":"rate_limit"}';END IF;
  END IF;
  IF EXISTS(SELECT 1 FROM coach.subjective_reviews WHERE goal_id=g.id AND status='pending' AND lease_until>now()) THEN RETURN '{"error":"busy"}';END IF;
  IF j.request_id IS NULL AND (SELECT count(*) FROM coach.subjective_reviews sr JOIN coach.learning_goals lg ON lg.id=sr.goal_id
    WHERE lg.user_id=owner_id AND sr.created_at>now()-interval '24 hours')>=15 THEN RETURN '{"error":"rate_limit"}';END IF;
  IF p_payload->>'kind'='case' THEN
   SELECT * INTO i FROM coach.subjective_issues WHERE id=p_payload->>'issue_id' AND goal_id=g.id;
   IF NOT FOUND OR i.task_ref<>p_payload->'input'->>'task_ref' THEN RETURN '{"error":"not_found"}';END IF;
   IF EXISTS(SELECT 1 FROM coach.subjective_reviews WHERE issue_id=i.id AND request_id<>p_payload->>'request_id') THEN RETURN '{"error":"conflict"}';END IF;
  END IF;
  IF length(p_payload->'input'->>'answer') NOT BETWEEN 1 AND 18000 THEN RETURN '{"error":"invalid_answer"}';END IF;
  INSERT INTO coach.subjective_reviews(goal_id,request_id,kind,issue_id,input_hash,input,status,lease,lease_until)
   VALUES(g.id,p_payload->>'request_id',p_payload->>'kind',p_payload->>'issue_id',p_payload->>'input_hash',p_payload->'input',
    'pending',p_payload->>'lease',now()+interval '180 seconds')
   ON CONFLICT(goal_id,request_id) DO UPDATE SET status='pending',lease=excluded.lease,lease_until=excluded.lease_until,
    attempts=coach.subjective_reviews.attempts+1;
  RETURN '{"status":"pending","generate":true}';
 ELSIF p_action IN ('result','input') THEN
  IF NOT FOUND THEN RETURN '{"error":"not_found"}';END IF;
  IF p_action='input' THEN RETURN jsonb_build_object('input',j.input,'input_hash',j.input_hash,'kind',j.kind,'issue_id',j.issue_id);END IF;
  RETURN jsonb_build_object('status',CASE WHEN j.status='pending' AND j.lease_until<=now() THEN 'failed' ELSE j.status END,
    'response',CASE WHEN j.status='complete' THEN j.response ELSE NULL END);
 ELSIF p_action='complete' THEN
  IF NOT FOUND OR j.lease<>p_payload->>'lease' THEN RETURN '{"error":"conflict"}';END IF;
  IF j.status='complete' THEN RETURN jsonb_build_object('response',j.response);END IF;
  IF g.state::jsonb<>p_payload->'expected_state' THEN RETURN '{"retry":true}';END IF;
  UPDATE coach.subjective_reviews SET status='complete',response=p_payload->'response',event=p_payload->'event'
   WHERE goal_id=g.id AND request_id=j.request_id AND lease=p_payload->>'lease' AND status='pending';
  IF NOT FOUND THEN RETURN '{"error":"conflict"}';END IF;
  UPDATE coach.learning_goals SET state=p_payload->'state' WHERE id=g.id;
  INSERT INTO coach.chat_turns(goal_id,request_id,user_message,status,lease,lease_until,response)
   VALUES(g.id,'review_'||j.request_id,p_payload->>'message','complete','',now(),p_payload->'response') ON CONFLICT DO NOTHING;
  RETURN jsonb_build_object('response',p_payload->'response');
 ELSIF p_action='dismiss' THEN
  IF NOT FOUND THEN RETURN '{"error":"not_found"}';END IF;
  IF j.status='complete' THEN RETURN jsonb_build_object('status','complete','response',j.response);END IF;
  IF j.status='pending' AND j.lease_until>now() THEN RETURN '{"error":"busy"}';END IF;
  UPDATE coach.subjective_reviews SET status='abandoned' WHERE goal_id=g.id AND request_id=j.request_id;
  IF j.issue_id IS NOT NULL THEN
   UPDATE coach.chat_turns SET response=jsonb_set(response,'{case,completed}','true') WHERE goal_id=g.id AND request_id='case_'||j.issue_id;
  END IF;
  RETURN '{"status":"abandoned"}';
 ELSIF p_action='fail' THEN
  UPDATE coach.subjective_reviews SET status='failed',lease_until=now() WHERE goal_id=g.id AND request_id=j.request_id
   AND lease=p_payload->>'lease' AND status='pending';RETURN '{"ok":true}';
 END IF;
 RETURN '{"error":"unknown_action"}';
END;$$;
REVOKE ALL ON FUNCTION public.coach_subjective_rpc(text,jsonb,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.coach_subjective_rpc(text,jsonb,text) TO service_role;
NOTIFY pgrst,'reload schema';
