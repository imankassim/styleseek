# tests/drift/
Runs the live `/search` endpoint against the frozen held-out judgment splits and fails if aggregate ndcg@10/recall@50 drop below a floor — architecture §15 "Offline evaluation".
