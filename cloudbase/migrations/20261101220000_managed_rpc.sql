-- Backend-only fixed RPC; coach tables remain outside the REST-exposed schema.
CREATE OR REPLACE FUNCTION public.coach_rpc(p_action text, p_payload jsonb DEFAULT '{}'::jsonb, p_token text DEFAULT '')
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, coach
AS $$
DECLARE
  owner_id text;
  g coach.learning_goals%ROWTYPE;
  i coach.question_issues%ROWTYPE;
  a coach.learning_attempts%ROWTYPE;
  q coach.questions%ROWTYPE;
  r coach.exam_releases%ROWTYPE;
  result jsonb;
BEGIN
  IF p_action='health' THEN
    RETURN jsonb_build_object('ready',EXISTS(SELECT 1 FROM coach.exam_releases WHERE id=p_payload->>'release_id' AND payload->>'publication_status'='ready'));
  ELSIF p_action='catalog' THEN
    SELECT COALESCE(jsonb_agg(jsonb_build_object('release_id',id) || (payload->'manifest')::jsonb),'[]') INTO result
      FROM coach.exam_releases WHERE id=p_payload->>'release_id' AND payload->>'publication_status'='ready';
    RETURN jsonb_build_object('items',result);
  ELSIF p_action='pack' THEN
    SELECT * INTO r FROM coach.exam_releases WHERE id=p_payload->>'release_id' AND payload->>'publication_status'='ready';
    IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;
    SELECT COALESCE(jsonb_agg(jsonb_build_object('key',key) || payload::jsonb),'[]') INTO result
      FROM coach.questions WHERE release_id=r.id;
    RETURN jsonb_build_object('release',r.payload,'questions',result);
  ELSIF p_action='login' THEN
    PERFORM pg_advisory_xact_lock(hashtextextended(p_payload->>'identity',0));
    SELECT id INTO owner_id FROM coach.users WHERE identity=p_payload->>'identity';
    IF owner_id IS NULL THEN
      owner_id := p_payload->>'user_id';
      INSERT INTO coach.users(id,identity) VALUES(owner_id,p_payload->>'identity');
    END IF;
    INSERT INTO coach.sessions(token_hash,user_id,expires_at)
      VALUES(p_payload->>'token_hash',owner_id,extract(epoch FROM now())::integer+604800);
    RETURN '{"ok":true}';
  END IF;

  SELECT user_id INTO owner_id FROM coach.sessions
    WHERE token_hash=p_token AND expires_at>extract(epoch FROM now())::integer;
  IF owner_id IS NULL THEN RETURN '{"error":"unauthorized"}'; END IF;

  IF p_action='goal' THEN
    PERFORM 1 FROM coach.users WHERE id=owner_id FOR UPDATE;
    SELECT * INTO r FROM coach.exam_releases WHERE id=p_payload->>'release_id'
      AND exam_id=p_payload->>'exam_id' AND payload->>'publication_status'='ready';
    IF NOT FOUND THEN RETURN '{"error":"invalid_exam"}'; END IF;
    SELECT * INTO g FROM coach.learning_goals WHERE user_id=owner_id AND release_id=r.id;
    IF NOT FOUND THEN
      INSERT INTO coach.learning_goals(id,user_id,release_id,profile,state)
        VALUES(p_payload->>'goal_id',owner_id,r.id,p_payload->'profile',p_payload->'state') RETURNING * INTO g;
    END IF;
    RETURN jsonb_build_object('goal_id',g.id,'release_id',g.release_id);
  END IF;

  IF p_action IN ('answer_snapshot','commit_answer') THEN
    SELECT * INTO i FROM coach.question_issues WHERE id=p_payload->>'issue_id';
    IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;
    SELECT * INTO g FROM coach.learning_goals WHERE id=i.goal_id AND user_id=owner_id FOR UPDATE;
  ELSE
    SELECT * INTO g FROM coach.learning_goals WHERE id=p_payload->>'goal_id' AND user_id=owner_id FOR UPDATE;
  END IF;
  IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;

  IF p_action='status' THEN
    SELECT count(*) INTO result FROM coach.learning_attempts WHERE goal_id=g.id;
    RETURN jsonb_build_object('goal',to_jsonb(g),'answered_count',result);
  ELSIF p_action='snapshot' THEN
    SELECT * INTO i FROM coach.question_issues issue WHERE issue.goal_id=g.id
      AND NOT EXISTS(SELECT 1 FROM coach.learning_attempts WHERE issue_id=issue.id) LIMIT 1;
    SELECT COALESCE(jsonb_object_agg(item_id,last_at),'{}') INTO result FROM (
      SELECT event->>'item_id' AS item_id,max(event->>'at') AS last_at
      FROM coach.learning_attempts WHERE goal_id=g.id GROUP BY event->>'item_id') times;
    RETURN jsonb_build_object('goal',to_jsonb(g),'pending',CASE WHEN i.id IS NULL THEN NULL ELSE to_jsonb(i) END,'last',result);
  ELSIF p_action='issue' THEN
    SELECT * INTO i FROM coach.question_issues issue WHERE issue.goal_id=g.id
      AND NOT EXISTS(SELECT 1 FROM coach.learning_attempts WHERE issue_id=issue.id) LIMIT 1;
    IF i.id IS NOT NULL THEN RETURN to_jsonb(i); END IF;
    IF g.state::jsonb <> p_payload->'expected_state' THEN RETURN '{"retry":true}'; END IF;
    SELECT * INTO q FROM coach.questions WHERE key=p_payload->>'question_key' AND release_id=g.release_id;
    IF NOT FOUND THEN RETURN '{"error":"not_found"}'; END IF;
    INSERT INTO coach.question_issues(id,goal_id,question_key,issued_at)
      VALUES(p_payload->>'issue_id',g.id,q.key,extract(epoch FROM now())::integer) RETURNING * INTO i;
    RETURN to_jsonb(i);
  ELSIF p_action IN ('answer_snapshot','commit_answer') THEN
    SELECT * INTO a FROM coach.learning_attempts WHERE issue_id=i.id;
    IF p_action='answer_snapshot' THEN
      RETURN jsonb_build_object('goal',to_jsonb(g),'issue',to_jsonb(i),
        'attempt',CASE WHEN a.id IS NULL THEN NULL ELSE to_jsonb(a) END);
    END IF;
    IF a.id IS NOT NULL THEN
      IF a.request::jsonb <> p_payload->'request' THEN RETURN '{"error":"conflict"}'; END IF;
      RETURN jsonb_build_object('report',a.report);
    END IF;
    IF g.state::jsonb <> p_payload->'expected_state' THEN RETURN '{"retry":true}'; END IF;
    -- Even the backend must bind a commit to the issued question and valid answer.
    SELECT * INTO q FROM coach.questions WHERE key=i.question_key;
    IF p_payload->'event'->>'item_id' <> q.item_id OR
       p_payload->'event'->>'attempt_id' IS NULL THEN RETURN '{"error":"invalid_answer"}'; END IF;
    IF (p_payload->'event'->>'score')::int <>
       (CASE WHEN (p_payload->'request'->>'selected')=(q.payload->'correct'->>0) THEN 1 ELSE 0 END)
       THEN RETURN '{"error":"invalid_answer"}'; END IF;
    INSERT INTO coach.learning_attempts(id,issue_id,goal_id,request,event,report)
      VALUES(p_payload->'event'->>'attempt_id',i.id,g.id,p_payload->'request',p_payload->'event',p_payload->'report');
    UPDATE coach.learning_goals SET state=p_payload->'state' WHERE id=g.id;
    RETURN jsonb_build_object('report',p_payload->'report');
  END IF;
  RETURN '{"error":"unknown_action"}';
END;
$$;
REVOKE ALL ON FUNCTION public.coach_rpc(text,jsonb,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.coach_rpc(text,jsonb,text) TO service_role;
NOTIFY pgrst, 'reload schema';
