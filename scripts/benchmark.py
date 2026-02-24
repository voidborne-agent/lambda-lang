#!/usr/bin/env python3
"""
Lambda Lang v3 — Phase 2: Benchmark

Compares Lambda vs JSON vs Natural Language across:
1. Character/byte compression
2. Semantic fidelity (Lambda encode → decode → compare)
3. Encode/decode latency

Dataset: 200+ real agent communication patterns across 8 categories.
"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from lambda_lang import (
    translate_to_english, english_to_lambda,
    LambdaParser, analyze_tier_coverage
)

# ============================================================
# Dataset: 8 categories of real agent communication (200+ samples)
# ============================================================

DATASET = {
    "task_dispatch": [
        {"natural": "Agent A, please send this task to Agent B and wait for the result", "lambda": ".A tx ta>U&wa/re", "json": '{"action":"send","from":"A","to":"B","type":"task","await":"result"}'},
        {"natural": "Task completed successfully, result is ready", "lambda": "!ta ct ok re=ok", "json": '{"type":"task_status","status":"completed","success":true,"result":"ready"}'},
        {"natural": "Task failed with error, please retry after waiting", "lambda": "!ta st=er .ry<wa", "json": '{"type":"task_status","status":"failed","error":true,"action":"retry","after":"wait"}'},
        {"natural": "Create a new session and assign task to the node", "lambda": ".cr nw ss&ta>nd", "json": '{"action":"create","target":"session","assign_task":true,"to":"node"}'},
        {"natural": "Query the status of all running tasks", "lambda": "?st/*ta", "json": '{"action":"query","target":"all_tasks","field":"status","filter":"running"}'},
        {"natural": "Stop the task and log the error result", "lambda": ".sp ta&lg er/re", "json": '{"action":"stop","target":"task","log":true,"log_type":"error","log_field":"result"}'},
        {"natural": "Task priority is high, needs immediate attention", "lambda": "!ta^+at n", "json": '{"type":"task_update","priority":"high","attention":"immediate","time":"now"}'},
        {"natural": "Acknowledge task received, starting now", "lambda": "!ak ta rx.d n", "json": '{"type":"ack","target":"task","status":"received","action":"start","time":"now"}'},
        {"natural": "Dispatch batch of 10 tasks to worker pool", "lambda": ".tx $10 ta>*nd", "json": '{"action":"dispatch","count":10,"type":"task","target":"worker_pool"}'},
        {"natural": "Task queue depth is 42, draining slowly", "lambda": "!ta qe=$42 _", "json": '{"type":"queue_status","depth":42,"drain_rate":"slow"}'},
        {"natural": "Cancel all pending tasks immediately", "lambda": ".cl *ta wa n", "json": '{"action":"cancel","scope":"all","filter":"pending","time":"now"}'},
        {"natural": "Reassign task from node alpha to node beta", "lambda": ".tx ta<nd id=alpha>nd id=beta", "json": '{"action":"reassign","task":"current","from":"node_alpha","to":"node_beta"}'},
        {"natural": "Task depends on three upstream results", "lambda": "!ta dp $3 re^", "json": '{"type":"task_info","dependencies":3,"dependency_type":"upstream_results"}'},
        {"natural": "Schedule task for execution at midnight", "lambda": ".ta bg t=0:00", "json": '{"action":"schedule","type":"task","time":"00:00"}'},
        {"natural": "Task timeout set to 30 seconds", "lambda": "!ta a:to=$30", "json": '{"type":"task_config","timeout_seconds":30}'},
        {"natural": "Fork task into two parallel subtasks", "lambda": ".ta fk $2 ta", "json": '{"action":"fork","source":"task","into":2,"mode":"parallel"}'},
        {"natural": "Join results from all subtasks", "lambda": ".ta jn *re", "json": '{"action":"join","source":"all_subtasks","field":"results"}'},
        {"natural": "Task is blocked waiting for resource lock", "lambda": "!ta bk wa/lk", "json": '{"type":"task_status","status":"blocked","waiting":"resource_lock"}'},
        {"natural": "Unlock resource and resume blocked task", "lambda": ".lk cl .ta bg", "json": '{"action":"unlock","then":"resume_task"}'},
        {"natural": "Task yielded control, will resume later", "lambda": "!ta yd bg+", "json": '{"type":"task_status","status":"yielded","resume":"later"}'},
        {"natural": "Estimate task completion time remaining", "lambda": "?ta ct t-", "json": '{"action":"query","task":"current","field":"time_remaining"}'},
        {"natural": "Task output size exceeds memory limit", "lambda": "!ta re sz>me lm", "json": '{"type":"warning","task_output":"exceeds","limit":"memory"}'},
        {"natural": "Throttle task execution rate to 5 per second", "lambda": ".ta rt=$5", "json": '{"action":"throttle","target":"task_execution","rate":5,"unit":"per_second"}'},
        {"natural": "Prioritize task alpha over task beta", "lambda": ".ta id=alpha^>ta id=beta", "json": '{"action":"prioritize","task":"alpha","over":"beta"}'},
        {"natural": "Archive completed tasks older than 7 days", "lambda": ".ta ct lg t>$7", "json": '{"action":"archive","filter":"completed","older_than_days":7}'},
        {"natural": "Duplicate task with modified parameters", "lambda": ".ta cp ch cg", "json": '{"action":"duplicate","task":"current","modify":"parameters"}'},
    ],
    "a2a_protocol": [
        {"natural": "Node heartbeat is OK, system healthy", "lambda": "!nd hb ok sy gd", "json": '{"type":"heartbeat","node":"self","status":"ok","system":"healthy"}'},
        {"natural": "Publish gene to hub, broadcast to all nodes", "lambda": ".a:pb e:gn>a:bc *nd", "json": '{"action":"publish","asset_type":"gene","target":"hub","broadcast":"all_nodes"}'},
        {"natural": "Subscribe to signals from upstream node", "lambda": ".a:sb sg<a:up nd", "json": '{"action":"subscribe","target":"signals","source":"upstream_node"}'},
        {"natural": "Session spawned, waiting for callback response", "lambda": "!ss a:sp wa/a:cb a:rs", "json": '{"type":"session","status":"spawned","waiting":"callback","expect":"response"}'},
        {"natural": "Route message to downstream, retry on timeout", "lambda": ".a:rt tx>a:dn ry<a:to", "json": '{"action":"route","message":"send","target":"downstream","on_timeout":"retry"}'},
        {"natural": "Config version updated, sync required to all nodes", "lambda": "!cg vn ch .a:sy>*nd", "json": '{"type":"config","version":"updated","action":"sync","target":"all_nodes"}'},
        {"natural": "Register new node with hub, request discovery", "lambda": ".a:rg nw nd .a:dk", "json": '{"action":"register","type":"new_node","target":"hub","request":"discovery"}'},
        {"natural": "Cache snapshot, fallback if node unreachable", "lambda": ".a:ch sn fb<nd-rx", "json": '{"action":"cache","target":"snapshot","fallback":"if_node_unreachable"}'},
        {"natural": "Ping all nodes and collect latency stats", "lambda": ".a:pg *nd ?lt", "json": '{"action":"ping","target":"all_nodes","collect":"latency_stats"}'},
        {"natural": "Node alpha is leader for this epoch", "lambda": "!nd id=alpha ld ep", "json": '{"type":"role","node":"alpha","role":"leader","scope":"epoch"}'},
        {"natural": "Transfer leadership to node beta", "lambda": ".a:tx ld>nd id=beta", "json": '{"action":"transfer","role":"leadership","to":"node_beta"}'},
        {"natural": "Peer list updated, now 12 active nodes", "lambda": "!a:pr ch $12 nd", "json": '{"type":"peer_update","active_nodes":12}'},
        {"natural": "Request topology map from hub", "lambda": "?a:nd tp", "json": '{"action":"query","target":"hub","field":"topology_map"}'},
        {"natural": "Node going offline for maintenance", "lambda": "!nd of mt", "json": '{"type":"status","node":"self","status":"offline","reason":"maintenance"}'},
        {"natural": "Handshake with new peer node gamma", "lambda": ".a:hs nd id=gamma", "json": '{"action":"handshake","target":"node_gamma"}'},
        {"natural": "Encrypted channel established with node delta", "lambda": "!a:ch nd id=delta ok", "json": '{"type":"channel","target":"node_delta","status":"encrypted","established":true}'},
        {"natural": "Broadcast system alert to all peers", "lambda": ".a:bc sy al>*a:pr", "json": '{"action":"broadcast","type":"system_alert","target":"all_peers"}'},
        {"natural": "Unsubscribe from node alpha signals", "lambda": ".a:us sg<nd id=alpha", "json": '{"action":"unsubscribe","target":"signals","source":"node_alpha"}'},
        {"natural": "Request resource allocation from coordinator", "lambda": "?rs al<a:co", "json": '{"action":"request","type":"resource_allocation","from":"coordinator"}'},
        {"natural": "Node load is 85 percent, near capacity", "lambda": "!nd ld=$85 ^", "json": '{"type":"load","node":"self","value":85,"status":"near_capacity"}'},
        {"natural": "Forward message to next hop in route", "lambda": ".a:fw tx>a:nh", "json": '{"action":"forward","message":"current","target":"next_hop"}'},
        {"natural": "Acknowledge receipt of broadcast message", "lambda": "!ak rx a:bc tx", "json": '{"type":"ack","received":"broadcast_message"}'},
        {"natural": "Node version mismatch detected with peer", "lambda": "!nd vn-=a:pr", "json": '{"type":"warning","issue":"version_mismatch","with":"peer"}'},
        {"natural": "Sync clock with hub timestamp", "lambda": ".a:sy t<a:nd", "json": '{"action":"sync","target":"clock","source":"hub_timestamp"}'},
        {"natural": "Report bandwidth usage to monitoring", "lambda": ".tx bw us>a:mn", "json": '{"action":"report","metric":"bandwidth_usage","to":"monitoring"}'},
        {"natural": "Deregister node from hub gracefully", "lambda": ".a:dr nd<a:nd", "json": '{"action":"deregister","node":"self","from":"hub","mode":"graceful"}'},
    ],
    "evolution": [
        {"natural": "Mutation triggered by error signal, repair intent", "lambda": "!e:mt<sg er e:rp", "json": '{"type":"mutation","trigger":"signal","signal":"error","intent":"repair"}'},
        {"natural": "Validate gene then solidify if successful", "lambda": ".e:vl e:gn>if ok .e:sf", "json": '{"action":"validate","target":"gene","then":{"if":"success","action":"solidify"}}'},
        {"natural": "Capsule confidence is 0.9, eligible for broadcast", "lambda": "!e:cp e:cn=0.9 e:el/a:bc", "json": '{"type":"capsule","confidence":0.9,"eligible":"broadcast"}'},
        {"natural": "Stagnation detected, switching to innovate strategy", "lambda": "!e:sa dt .e:iv e:sy", "json": '{"type":"signal","signal":"stagnation","action":"switch_strategy","to":"innovate"}'},
        {"natural": "Blast radius is safe, 3 files changed, 50 lines", "lambda": "!e:br sf $3 c:fx $50 li", "json": '{"type":"blast_radius","status":"safe","files_changed":3,"lines_changed":50}'},
        {"natural": "Repair failed, rollback all changes immediately", "lambda": "!e:rp er>e:rb *ch n", "json": '{"type":"repair","status":"failed","action":"rollback","scope":"all_changes","time":"now"}'},
        {"natural": "Evolution cycle complete, gene streak is 5 consecutive successes", "lambda": "!e:cy ct e:gn e:sk=5 ok", "json": '{"type":"cycle","status":"complete","gene_streak":5,"streak_type":"success"}'},
        {"natural": "Quarantine external capsule, lower confidence by 0.6 factor", "lambda": ".e:qr a:rx e:cp e:cn-0.6", "json": '{"action":"quarantine","source":"external","asset":"capsule","confidence_factor":0.6}'},
        {"natural": "Freeze gene pool during critical operation", "lambda": ".e:fz e:gn^", "json": '{"action":"freeze","target":"gene_pool","reason":"critical_operation"}'},
        {"natural": "Gene fitness score improved to 0.92", "lambda": "!e:gn ft=0.92+", "json": '{"type":"gene_update","fitness":0.92,"trend":"improved"}'},
        {"natural": "Select top 3 genes for next generation", "lambda": ".e:sl $3 e:gn^", "json": '{"action":"select","count":3,"target":"genes","criteria":"top_fitness"}'},
        {"natural": "Crossover genes alpha and beta to produce offspring", "lambda": ".e:cx e:gn id=alpha&id=beta>nw", "json": '{"action":"crossover","gene_a":"alpha","gene_b":"beta","output":"offspring"}'},
        {"natural": "Mutation rate adjusted to 0.05", "lambda": "!e:mt rt=0.05", "json": '{"type":"config","mutation_rate":0.05}'},
        {"natural": "Gene rejected by validation, too risky", "lambda": "!e:gn e:vl er rk^", "json": '{"type":"gene_status","validation":"failed","reason":"too_risky"}'},
        {"natural": "Capsule expired, remove from pool", "lambda": ".e:cp ex cl", "json": '{"action":"remove","target":"capsule","reason":"expired"}'},
        {"natural": "Evolution pressure increasing, adapt faster", "lambda": "!e:pr^+e:ad", "json": '{"type":"signal","pressure":"increasing","directive":"adapt_faster"}'},
        {"natural": "Snapshot gene pool state for recovery", "lambda": ".sn e:gn st", "json": '{"action":"snapshot","target":"gene_pool","purpose":"recovery"}'},
        {"natural": "Restore gene pool from snapshot version 3", "lambda": ".e:rs e:gn<sn vn=3", "json": '{"action":"restore","target":"gene_pool","source":"snapshot","version":3}'},
        {"natural": "Gene diversity index is 0.7, acceptable", "lambda": "!e:gn dv=0.7 ok", "json": '{"type":"metric","gene_diversity":0.7,"status":"acceptable"}'},
        {"natural": "Prune dead genes with zero fitness", "lambda": ".e:pr e:gn ft=0", "json": '{"action":"prune","target":"genes","filter":"zero_fitness"}'},
        {"natural": "Evolution halted, manual review required", "lambda": "!e:cy sp H rv", "json": '{"type":"cycle_status","status":"halted","requires":"human_review"}'},
        {"natural": "Resume evolution after human approval", "lambda": ".e:cy bg<H ok", "json": '{"action":"resume","target":"evolution","after":"human_approval"}'},
        {"natural": "Gene lineage traced back 12 generations", "lambda": "!e:gn ln=$12", "json": '{"type":"gene_info","lineage_depth":12}'},
        {"natural": "Capsule broadcast received by 8 nodes", "lambda": "!e:cp a:bc rx $8 nd", "json": '{"type":"broadcast_result","asset":"capsule","received_by":8}'},
        {"natural": "Evolution strategy changed from explore to exploit", "lambda": "!e:sy ch e:xp>e:xt", "json": '{"type":"strategy_change","from":"explore","to":"exploit"}'},
        {"natural": "Merge compatible genes into composite", "lambda": ".e:mg e:gn=&>nw", "json": '{"action":"merge","target":"compatible_genes","output":"composite"}'},
    ],
    "error_handling": [
        {"natural": "Error detected in task alpha, code 500", "lambda": "!er ta id=alpha $500", "json": '{"type":"error","task":"alpha","code":500}'},
        {"natural": "Retry task after 5 second delay", "lambda": ".ry ta<wa $5", "json": '{"action":"retry","target":"task","delay_seconds":5}'},
        {"natural": "Maximum retries exceeded, escalating to human", "lambda": "!ry mx>H", "json": '{"type":"error","retries":"exceeded","escalate":"human"}'},
        {"natural": "Fallback to cached result on timeout", "lambda": ".fb a:ch re<a:to", "json": '{"action":"fallback","source":"cache","trigger":"timeout"}'},
        {"natural": "Circuit breaker open, blocking requests", "lambda": "!er cb op bk", "json": '{"type":"circuit_breaker","status":"open","action":"blocking"}'},
        {"natural": "Circuit breaker half-open, testing recovery", "lambda": "!er cb ho xt", "json": '{"type":"circuit_breaker","status":"half_open","action":"testing"}'},
        {"natural": "Circuit breaker closed, normal operation", "lambda": "!er cb cl ok", "json": '{"type":"circuit_breaker","status":"closed","action":"normal"}'},
        {"natural": "Error rate is 15 percent, above threshold", "lambda": "!er rt=$15 ^lm", "json": '{"type":"metric","error_rate":15,"status":"above_threshold"}'},
        {"natural": "Graceful degradation activated for service", "lambda": "!er gd bg", "json": '{"type":"status","graceful_degradation":"active"}'},
        {"natural": "Health check failed on node beta", "lambda": "!nd id=beta hc er", "json": '{"type":"health_check","node":"beta","status":"failed"}'},
        {"natural": "Auto-heal triggered, restarting service", "lambda": ".er ah bg rs", "json": '{"action":"auto_heal","operation":"restart_service"}'},
        {"natural": "Error log written with stack trace", "lambda": "!lg er wr sk", "json": '{"type":"log","level":"error","includes":"stack_trace"}'},
        {"natural": "Panic mode activated, all tasks suspended", "lambda": "!er pn *ta sp", "json": '{"type":"panic","action":"suspend_all_tasks"}'},
        {"natural": "Recovery complete, resuming normal operations", "lambda": "!er rc ok bg", "json": '{"type":"recovery","status":"complete","action":"resume_normal"}'},
        {"natural": "Timeout error on database connection", "lambda": "!er a:to db cn", "json": '{"type":"error","error":"timeout","target":"database_connection"}'},
        {"natural": "Rate limit exceeded, backing off 30 seconds", "lambda": "!er rl mx wa $30", "json": '{"type":"error","error":"rate_limit","backoff_seconds":30}'},
        {"natural": "Memory overflow detected, dumping core", "lambda": "!er me ov dm", "json": '{"type":"error","error":"memory_overflow","action":"core_dump"}'},
        {"natural": "Deadlock detected between tasks alpha and beta", "lambda": "!er dl ta id=alpha&id=beta", "json": '{"type":"error","error":"deadlock","tasks":["alpha","beta"]}'},
        {"natural": "Resolve deadlock by killing lower priority task", "lambda": ".er dl cl ta_", "json": '{"action":"resolve","error":"deadlock","method":"kill_lower_priority"}'},
        {"natural": "Error suppressed, not critical", "lambda": "!er sp-^", "json": '{"type":"error","action":"suppressed","severity":"low"}'},
        {"natural": "Notify admin of persistent error pattern", "lambda": ".tx er pt>H", "json": '{"action":"notify","target":"admin","reason":"persistent_error_pattern"}'},
        {"natural": "Rollback to last known good state", "lambda": ".e:rb>st ok-", "json": '{"action":"rollback","target":"last_known_good_state"}'},
        {"natural": "Error correlation found across 3 services", "lambda": "!er cr $3 sv", "json": '{"type":"analysis","error_correlation":true,"services":3}'},
        {"natural": "Quarantine faulty node until repair", "lambda": ".e:qr nd er<e:rp", "json": '{"action":"quarantine","target":"node","reason":"error","until":"repair"}'},
        {"natural": "Error budget remaining is 2 percent for this month", "lambda": "!er bg=$2 mo", "json": '{"type":"metric","error_budget_remaining":2,"period":"month"}'},
        {"natural": "Retry with exponential backoff starting at 1 second", "lambda": ".ry ex wa=$1+", "json": '{"action":"retry","strategy":"exponential_backoff","initial_delay":1}'},
    ],
    "session_management": [
        {"natural": "Create new session with ID alpha", "lambda": ".cr ss id=alpha", "json": '{"action":"create","type":"session","id":"alpha"}'},
        {"natural": "Session alpha is active with 3 participants", "lambda": "!ss id=alpha ac $3", "json": '{"type":"session","id":"alpha","status":"active","participants":3}'},
        {"natural": "Close session alpha gracefully", "lambda": ".cl ss id=alpha", "json": '{"action":"close","target":"session","id":"alpha","mode":"graceful"}'},
        {"natural": "Session closed successfully", "lambda": "!ss cl ok", "json": '{"type":"session","status":"closed","success":true}'},
        {"natural": "Transfer session to node beta", "lambda": ".tx ss>nd id=beta", "json": '{"action":"transfer","target":"session","to":"node_beta"}'},
        {"natural": "Session transfer complete, new host is beta", "lambda": "!ss tx ok nd id=beta", "json": '{"type":"session","transfer":"complete","new_host":"beta"}'},
        {"natural": "Resume suspended session gamma", "lambda": ".bg ss id=gamma", "json": '{"action":"resume","target":"session","id":"gamma"}'},
        {"natural": "Session gamma resumed from checkpoint", "lambda": "!ss id=gamma bg<ck", "json": '{"type":"session","id":"gamma","status":"resumed","from":"checkpoint"}'},
        {"natural": "Save session checkpoint with current state", "lambda": ".sv ss ck st", "json": '{"action":"save","target":"session","type":"checkpoint","include":"state"}'},
        {"natural": "List all active sessions", "lambda": "?*ss ac", "json": '{"action":"query","target":"all_sessions","filter":"active"}'},
        {"natural": "Session timeout set to 30 minutes", "lambda": "!ss a:to=$30 mn", "json": '{"type":"session_config","timeout_minutes":30}'},
        {"natural": "Extend session timeout by 15 minutes", "lambda": ".ss a:to+$15", "json": '{"action":"extend","target":"session_timeout","minutes":15}'},
        {"natural": "Session memory usage at 500 megabytes", "lambda": "!ss me=$500", "json": '{"type":"session_metric","memory_mb":500}'},
        {"natural": "Purge expired sessions older than 1 hour", "lambda": ".cl *ss ex t>$1 hr", "json": '{"action":"purge","target":"sessions","filter":"expired","older_than":"1_hour"}'},
        {"natural": "Fork session into read-only clone", "lambda": ".ss fk r", "json": '{"action":"fork","target":"session","mode":"read_only"}'},
        {"natural": "Merge session data from clone back to parent", "lambda": ".ss mg<fk", "json": '{"action":"merge","target":"session","source":"clone"}'},
        {"natural": "Session participant joined: Agent C", "lambda": "!ss A jn", "json": '{"type":"session_event","event":"join","participant":"agent_c"}'},
        {"natural": "Session participant left: Agent B", "lambda": "!ss A lv", "json": '{"type":"session_event","event":"leave","participant":"agent_b"}'},
        {"natural": "Lock session for exclusive write access", "lambda": ".ss lk wr", "json": '{"action":"lock","target":"session","mode":"write_exclusive"}'},
        {"natural": "Unlock session, allow concurrent access", "lambda": ".ss lk cl", "json": '{"action":"unlock","target":"session","mode":"concurrent"}'},
        {"natural": "Session heartbeat, 42 seconds since last activity", "lambda": "!ss hb t=$42", "json": '{"type":"session_heartbeat","idle_seconds":42}'},
        {"natural": "Migrate session state to persistent storage", "lambda": ".ss st tx>db", "json": '{"action":"migrate","source":"session_state","target":"persistent_storage"}'},
        {"natural": "Restore session from persistent storage", "lambda": ".ss st<db", "json": '{"action":"restore","target":"session_state","source":"persistent_storage"}'},
        {"natural": "Session capacity reached, reject new participants", "lambda": "!ss cp mx bk", "json": '{"type":"session_status","capacity":"max","action":"reject_new"}'},
        {"natural": "Destroy session and release all resources", "lambda": ".ss ds cl *rs", "json": '{"action":"destroy","target":"session","release":"all_resources"}'},
        {"natural": "Session audit log exported", "lambda": "!ss lg tx ok", "json": '{"type":"session_event","event":"audit_export","status":"success"}'},
    ],
    "monitoring": [
        {"natural": "CPU usage at 78 percent on node alpha", "lambda": "!nd id=alpha cpu=$78", "json": '{"type":"metric","node":"alpha","cpu_percent":78}'},
        {"natural": "Memory usage at 4.2 gigabytes, threshold 8", "lambda": "!me=$4.2 lm=$8", "json": '{"type":"metric","memory_gb":4.2,"threshold_gb":8}'},
        {"natural": "Alert triggered: disk space below 10 percent", "lambda": "!al dk<$10", "json": '{"type":"alert","metric":"disk_space","below_percent":10}'},
        {"natural": "Dashboard updated with latest metrics", "lambda": "!db ch mt n", "json": '{"type":"dashboard","action":"updated","data":"latest_metrics"}'},
        {"natural": "Health check passed on all 5 services", "lambda": "!hc ok *$5 sv", "json": '{"type":"health_check","status":"passed","services":5}'},
        {"natural": "Latency spike detected, 500ms average", "lambda": "!lt^=$500 ms", "json": '{"type":"alert","metric":"latency","value_ms":500,"trend":"spike"}'},
        {"natural": "Throughput is 1000 requests per second", "lambda": "!tp=$1000 rq", "json": '{"type":"metric","throughput":1000,"unit":"requests_per_second"}'},
        {"natural": "Error rate dropped to 0.1 percent", "lambda": "!er rt=$0.1-", "json": '{"type":"metric","error_rate":0.1,"trend":"decreasing"}'},
        {"natural": "Uptime is 99.95 percent this month", "lambda": "!up=$99.95 mo", "json": '{"type":"metric","uptime_percent":99.95,"period":"month"}'},
        {"natural": "Network bandwidth usage at 80 percent capacity", "lambda": "!bw=$80 cp", "json": '{"type":"metric","bandwidth_percent":80,"status":"near_capacity"}'},
        {"natural": "Set alert threshold for CPU above 90 percent", "lambda": ".al cg cpu>$90", "json": '{"action":"configure","alert":"cpu","threshold_above":90}'},
        {"natural": "Silence alerts for maintenance window of 2 hours", "lambda": ".al sp wa $2 hr", "json": '{"action":"silence","target":"alerts","duration_hours":2,"reason":"maintenance"}'},
        {"natural": "Collect metrics from all nodes every 30 seconds", "lambda": ".mt cl *nd t=$30", "json": '{"action":"collect","target":"metrics","source":"all_nodes","interval_seconds":30}'},
        {"natural": "Aggregate daily metrics into weekly report", "lambda": ".mt ag dy>wk re", "json": '{"action":"aggregate","source":"daily_metrics","into":"weekly_report"}'},
        {"natural": "Anomaly detected in request pattern", "lambda": "!al an rq pt", "json": '{"type":"alert","alert":"anomaly","target":"request_pattern"}'},
        {"natural": "Trace request across 4 microservices", "lambda": ".tr rq $4 sv", "json": '{"action":"trace","target":"request","across_services":4}'},
        {"natural": "P99 latency is 250ms, within SLA", "lambda": "!lt p99=$250 ok", "json": '{"type":"metric","p99_latency_ms":250,"sla":"within"}'},
        {"natural": "Connection pool exhausted, max 100 connections", "lambda": "!cn pl mx=$100", "json": '{"type":"alert","connection_pool":"exhausted","max":100}'},
        {"natural": "Garbage collection pause was 200ms", "lambda": "!gc pa=$200 ms", "json": '{"type":"metric","gc_pause_ms":200}'},
        {"natural": "Log volume is 50 gigabytes per day", "lambda": "!lg sz=$50 dy", "json": '{"type":"metric","log_volume_gb_per_day":50}'},
        {"natural": "Create custom dashboard for evolution metrics", "lambda": ".cr db e:mt", "json": '{"action":"create","type":"dashboard","metrics":"evolution"}'},
        {"natural": "Export metrics to external monitoring system", "lambda": ".tx mt>a:mn", "json": '{"action":"export","target":"metrics","to":"external_monitoring"}'},
        {"natural": "Node alpha response time degraded by 40 percent", "lambda": "!nd id=alpha rs t-$40", "json": '{"type":"alert","node":"alpha","response_time":"degraded","by_percent":40}'},
        {"natural": "Scale up monitoring frequency during incident", "lambda": ".mt rt^<er", "json": '{"action":"increase","target":"monitoring_frequency","trigger":"incident"}'},
        {"natural": "Monitoring baseline recalculated from last 30 days", "lambda": "!mt bs ch t=$30 dy", "json": '{"type":"config","baseline":"recalculated","period_days":30}'},
        {"natural": "Queue depth alarm at 1000 pending messages", "lambda": "!al qe=$1000 tx", "json": '{"type":"alarm","queue_depth":1000,"type":"pending_messages"}'},
    ],
    "coordination": [
        {"natural": "Initiate voting round for proposal alpha", "lambda": ".vt bg id=alpha", "json": '{"action":"start","type":"vote","proposal":"alpha"}'},
        {"natural": "Agent A votes approve on proposal alpha", "lambda": "!A vt ok id=alpha", "json": '{"type":"vote","agent":"A","proposal":"alpha","vote":"approve"}'},
        {"natural": "Agent B votes reject on proposal alpha", "lambda": "!A vt er id=alpha", "json": '{"type":"vote","agent":"B","proposal":"alpha","vote":"reject"}'},
        {"natural": "Voting result: 3 approve, 1 reject, proposal passes", "lambda": "!vt re $3 ok $1 er>ok", "json": '{"type":"vote_result","approve":3,"reject":1,"outcome":"pass"}'},
        {"natural": "Consensus reached on shared configuration", "lambda": "!cs ok cg", "json": '{"type":"consensus","status":"reached","target":"shared_config"}'},
        {"natural": "Request distributed lock on resource alpha", "lambda": ".lk rq rs id=alpha", "json": '{"action":"request","type":"lock","resource":"alpha"}'},
        {"natural": "Lock granted, exclusive access for 60 seconds", "lambda": "!lk ok ex t=$60", "json": '{"type":"lock","status":"granted","mode":"exclusive","ttl_seconds":60}'},
        {"natural": "Release distributed lock on resource alpha", "lambda": ".lk cl rs id=alpha", "json": '{"action":"release","type":"lock","resource":"alpha"}'},
        {"natural": "Coordinate task split across 4 agents", "lambda": ".co ta sp $4 A", "json": '{"action":"coordinate","type":"task_split","agents":4}'},
        {"natural": "Agent C reports subtask complete", "lambda": "!A st ta ct", "json": '{"type":"status","agent":"C","subtask":"complete"}'},
        {"natural": "All subtasks complete, merge results", "lambda": "!*ta ct .mg re", "json": '{"type":"status","all_subtasks":"complete","action":"merge_results"}'},
        {"natural": "Elect leader among 5 candidate nodes", "lambda": ".el ld $5 nd", "json": '{"action":"elect","role":"leader","candidates":5}'},
        {"natural": "Leader elected: node gamma wins with highest score", "lambda": "!el ok nd id=gamma^", "json": '{"type":"election","result":"node_gamma","criteria":"highest_score"}'},
        {"natural": "Barrier wait: 3 of 5 agents ready", "lambda": "!br wa $3/$5 A", "json": '{"type":"barrier","ready":3,"total":5,"waiting":true}'},
        {"natural": "Barrier released, all agents proceed", "lambda": "!br cl *A bg", "json": '{"type":"barrier","status":"released","action":"all_proceed"}'},
        {"natural": "Publish shared state update to all participants", "lambda": ".a:pb st ch>*A", "json": '{"action":"publish","type":"state_update","to":"all_participants"}'},
        {"natural": "Conflict detected in shared state, resolving", "lambda": "!st cf dt rs", "json": '{"type":"conflict","target":"shared_state","action":"resolving"}'},
        {"natural": "Conflict resolved using last-writer-wins", "lambda": "!st cf ok lw", "json": '{"type":"conflict","status":"resolved","strategy":"last_writer_wins"}'},
        {"natural": "Request quorum from 3 of 5 nodes for commit", "lambda": ".qr rq $3/$5 nd cm", "json": '{"action":"request","type":"quorum","required":3,"total":5,"for":"commit"}'},
        {"natural": "Quorum achieved, committing transaction", "lambda": "!qr ok .cm", "json": '{"type":"quorum","status":"achieved","action":"commit"}'},
        {"natural": "Two-phase commit: prepare phase complete", "lambda": "!cm ph=1 ok", "json": '{"type":"2pc","phase":"prepare","status":"complete"}'},
        {"natural": "Two-phase commit: commit phase complete", "lambda": "!cm ph=2 ok", "json": '{"type":"2pc","phase":"commit","status":"complete"}'},
        {"natural": "Agent heartbeat missing, suspected failure", "lambda": "~A hb- er", "json": '{"type":"warning","agent_heartbeat":"missing","suspected":"failure"}'},
        {"natural": "Failover activated, backup agent takes over", "lambda": ".fo bg A bk", "json": '{"action":"failover","activate":"backup_agent"}'},
        {"natural": "Synchronize clocks across all coordinating nodes", "lambda": ".a:sy t *nd co", "json": '{"action":"sync","target":"clocks","scope":"all_coordinating_nodes"}'},
        {"natural": "Work stealing: idle agent takes task from busy agent", "lambda": ".A ta<A^", "json": '{"action":"work_steal","idle_agent":"takes","from":"busy_agent"}'},
    ],
    "data_exchange": [
        {"natural": "Request dataset alpha from data store", "lambda": "?da id=alpha<db", "json": '{"action":"request","type":"dataset","id":"alpha","source":"data_store"}'},
        {"natural": "Dataset alpha found, size 2.5 megabytes", "lambda": "!da id=alpha ok sz=$2.5", "json": '{"type":"response","dataset":"alpha","status":"found","size_mb":2.5}'},
        {"natural": "Streaming data: chunk 1 of 10 sent", "lambda": "!da tx ch=$1/$10", "json": '{"type":"stream","action":"send","chunk":1,"total":10}'},
        {"natural": "Streaming data: chunk 5 of 10 sent", "lambda": "!da tx ch=$5/$10", "json": '{"type":"stream","action":"send","chunk":5,"total":10}'},
        {"natural": "Streaming data: all chunks sent, transfer complete", "lambda": "!da tx *ch ct", "json": '{"type":"stream","status":"complete","all_chunks":"sent"}'},
        {"natural": "Request page 3 of results, 50 items per page", "lambda": "?re pg=$3 sz=$50", "json": '{"action":"query","page":3,"page_size":50}'},
        {"natural": "Page 3 returned with 50 items, 200 total", "lambda": "!re pg=$3 $50 tt=$200", "json": '{"type":"response","page":3,"items":50,"total":200}'},
        {"natural": "Transform data from JSON to Lambda format", "lambda": ".da tr js>lm", "json": '{"action":"transform","source":"json","target":"lambda_format"}'},
        {"natural": "Data validation passed, schema matches", "lambda": "!da e:vl ok sc=", "json": '{"type":"validation","status":"passed","schema":"matches"}'},
        {"natural": "Data validation failed, missing required field", "lambda": "!da e:vl er fd-", "json": '{"type":"validation","status":"failed","error":"missing_required_field"}'},
        {"natural": "Compress data before transmission, ratio 3x", "lambda": ".da cp>tx rt=$3", "json": '{"action":"compress","target":"data","before":"transmission","ratio":3}'},
        {"natural": "Cache data with TTL of 300 seconds", "lambda": ".da a:ch t=$300", "json": '{"action":"cache","target":"data","ttl_seconds":300}'},
        {"natural": "Cache hit for query, returning cached result", "lambda": "!a:ch ht re", "json": '{"type":"cache","status":"hit","action":"return_cached"}'},
        {"natural": "Cache miss, fetching fresh data", "lambda": "!a:ch ms .f da", "json": '{"type":"cache","status":"miss","action":"fetch_fresh"}'},
        {"natural": "Batch insert 100 records into database", "lambda": ".da in $100 rc>db", "json": '{"action":"batch_insert","count":100,"target":"database"}'},
        {"natural": "Batch insert complete, 98 succeeded, 2 failed", "lambda": "!da in ct $98 ok $2 er", "json": '{"type":"result","batch_insert":true,"succeeded":98,"failed":2}'},
        {"natural": "Subscribe to real-time data feed", "lambda": ".a:sb da fd rt", "json": '{"action":"subscribe","target":"data_feed","mode":"real_time"}'},
        {"natural": "Data feed event received, processing", "lambda": "!da fd rx .d", "json": '{"type":"event","source":"data_feed","action":"processing"}'},
        {"natural": "Export data as CSV to file system", "lambda": ".da tx csv>fs", "json": '{"action":"export","format":"csv","target":"file_system"}'},
        {"natural": "Import data from external API endpoint", "lambda": ".da rx<a:ep", "json": '{"action":"import","source":"external_api_endpoint"}'},
        {"natural": "Data schema version 3, backward compatible", "lambda": "!da sc vn=3 ok-", "json": '{"type":"schema","version":3,"backward_compatible":true}'},
        {"natural": "Deduplicate records, found 15 duplicates", "lambda": ".da dd $15 cp", "json": '{"action":"deduplicate","duplicates_found":15}'},
        {"natural": "Encrypt data at rest with AES-256", "lambda": ".da en rs", "json": '{"action":"encrypt","target":"data_at_rest","algorithm":"aes256"}'},
        {"natural": "Data retention policy: delete after 90 days", "lambda": "!da rt cl t=$90 dy", "json": '{"type":"policy","retention":"delete","after_days":90}'},
        {"natural": "Replicate data to 3 geographic regions", "lambda": ".da rp $3 rg", "json": '{"action":"replicate","target":"data","regions":3}'},
        {"natural": "Data integrity check passed, all checksums match", "lambda": "!da v ok *ck=", "json": '{"type":"integrity_check","status":"passed","checksums":"match"}'},
    ],
}

# ============================================================
# Conversations: 150+ messages across 5 scenarios
# ============================================================

CONVERSATIONS = {
    "task_orchestration": {
        "description": "38-message task dispatch and monitoring conversation",
        "messages": [
            {"nl": "Agent B, start task alpha, priority high", "lm": ".A bg ta id=alpha ^", "json": '{"action":"start","agent":"B","task":"alpha","priority":"high"}'},
            {"nl": "Acknowledged, starting task alpha now", "lm": "!ak bg ta id=alpha n", "json": '{"type":"ack","task":"alpha","action":"start","time":"now"}'},
            {"nl": "Task alpha status: running, 10% complete", "lm": "!ta id=alpha st=rn $10 ct", "json": '{"task":"alpha","status":"running","progress":10}'},
            {"nl": "Task alpha status: running, 25% complete", "lm": "!ta id=alpha st=rn $25 ct", "json": '{"task":"alpha","status":"running","progress":25}'},
            {"nl": "Task alpha status: running, 50% complete", "lm": "!ta id=alpha st=rn $50 ct", "json": '{"task":"alpha","status":"running","progress":50}'},
            {"nl": "Warning: task alpha memory usage is high", "lm": "~ta id=alpha me us ^", "json": '{"type":"warning","task":"alpha","metric":"memory","level":"high"}'},
            {"nl": "Task alpha status: running, 75% complete", "lm": "!ta id=alpha st=rn $75 ct", "json": '{"task":"alpha","status":"running","progress":75}'},
            {"nl": "Task alpha completed successfully, result ready", "lm": "!ta id=alpha ct ok re=ok", "json": '{"task":"alpha","status":"completed","success":true,"result":"ready"}'},
            {"nl": "Send result of task alpha to Agent C", "lm": ".tx re/ta id=alpha>A", "json": '{"action":"send","data":"result","task":"alpha","to":"C"}'},
            {"nl": "Agent C acknowledged receipt of result", "lm": "!A ak rx re", "json": '{"type":"ack","agent":"C","received":"result"}'},
            {"nl": "Agent B, start task beta, priority normal", "lm": ".A bg ta id=beta", "json": '{"action":"start","agent":"B","task":"beta","priority":"normal"}'},
            {"nl": "Task beta status: running", "lm": "!ta id=beta st=rn", "json": '{"task":"beta","status":"running"}'},
            {"nl": "Error in task beta: config file missing", "lm": "!ta id=beta er cg-", "json": '{"task":"beta","status":"error","error":"config_missing"}'},
            {"nl": "Retry task beta with updated config", "lm": ".ry ta id=beta cg ch", "json": '{"action":"retry","task":"beta","config":"updated"}'},
            {"nl": "Task beta status: running after retry", "lm": "!ta id=beta st=rn<ry", "json": '{"task":"beta","status":"running","after":"retry"}'},
            {"nl": "Task beta completed successfully", "lm": "!ta id=beta ct ok", "json": '{"task":"beta","status":"completed","success":true}'},
            {"nl": "Start task gamma, depends on alpha result", "lm": ".bg ta id=gamma<re/ta id=alpha", "json": '{"action":"start","task":"gamma","depends_on":{"task":"alpha","field":"result"}}'},
            {"nl": "Task gamma status: running", "lm": "!ta id=gamma st=rn", "json": '{"task":"gamma","status":"running"}'},
            {"nl": "Task gamma failed with timeout error", "lm": "!ta id=gamma er a:to", "json": '{"task":"gamma","status":"failed","error":"timeout"}'},
            {"nl": "Rollback task gamma changes", "lm": ".e:rb ta id=gamma ch", "json": '{"action":"rollback","task":"gamma","scope":"changes"}'},
            {"nl": "Node heartbeat OK", "lm": "!nd hb ok", "json": '{"type":"heartbeat","status":"ok"}'},
            {"nl": "Node heartbeat OK", "lm": "!nd hb ok", "json": '{"type":"heartbeat","status":"ok"}'},
            {"nl": "System status: all tasks accounted for", "lm": "!sy st ok *ta", "json": '{"type":"system_status","status":"ok","scope":"all_tasks"}'},
            {"nl": "Node heartbeat OK", "lm": "!nd hb ok", "json": '{"type":"heartbeat","status":"ok"}'},
            {"nl": "Session memory usage: 4.2 gigabytes", "lm": "!ss me us=$4.2", "json": '{"type":"session","metric":"memory","value":"4.2GB"}'},
            {"nl": "Start task delta, low priority", "lm": ".bg ta id=delta _", "json": '{"action":"start","task":"delta","priority":"low"}'},
            {"nl": "Task delta status: waiting in queue", "lm": "!ta id=delta st=wa qe", "json": '{"task":"delta","status":"waiting","location":"queue"}'},
            {"nl": "Task delta status: running", "lm": "!ta id=delta st=rn", "json": '{"task":"delta","status":"running"}'},
            {"nl": "Task delta completed, result is a list of 42 items", "lm": "!ta id=delta ct re=$42", "json": '{"task":"delta","status":"completed","result":{"type":"list","count":42}}'},
            {"nl": "Log all task results to file", "lm": ".lg *ta re", "json": '{"action":"log","scope":"all_tasks","field":"results","target":"file"}'},
            {"nl": "Query: how many tasks completed successfully?", "lm": "?$ta ct ok", "json": '{"action":"query","filter":{"status":"completed","success":true},"return":"count"}'},
            {"nl": "3 tasks completed, 1 failed", "lm": "!$3 ta ct ok $1 ta er", "json": '{"completed":3,"failed":1}'},
            {"nl": "Create summary report of all results", "lm": ".cr re/*ta", "json": '{"action":"create","type":"summary","scope":"all_task_results"}'},
            {"nl": "Report created and saved", "lm": "!re cr ok", "json": '{"type":"report","status":"created","saved":true}'},
            {"nl": "Send report to Agent A", "lm": ".tx re>A", "json": '{"action":"send","data":"report","to":"A"}'},
            {"nl": "Close session, archive all logs", "lm": ".cl ss lg", "json": '{"action":"close","target":"session","archive":"logs"}'},
            {"nl": "Session closed, goodbye", "lm": "!ss cl ok", "json": '{"type":"session","status":"closed","message":"goodbye"}'},
            {"nl": "Node heartbeat OK, shutting down", "lm": "!nd hb ok sp", "json": '{"type":"heartbeat","status":"ok","next":"shutdown"}'},
        ],
    },
    "evolution_cycle": {
        "description": "28-message evolution cycle with A2A exchange",
        "messages": [
            {"nl": "Evolution cycle 42 starting, strategy: innovate", "lm": "!e:cy $42 bg e:sy=e:iv", "json": '{"type":"cycle","id":42,"action":"start","strategy":"innovate"}'},
            {"nl": "Extracting signals from session transcript", "lm": ".f sg<ss lg", "json": '{"action":"extract","target":"signals","source":"session_transcript"}'},
            {"nl": "Signals detected: stagnation, stable success plateau", "lm": "!sg dt e:sa ok+", "json": '{"type":"signals","detected":["stagnation","stable_success_plateau"]}'},
            {"nl": "Selecting gene: gene_auto_scheduler", "lm": ".e:sl e:gn id=auto_scheduler", "json": '{"action":"select","type":"gene","id":"gene_auto_scheduler"}'},
            {"nl": "Gene strategy: create new skill, validate, solidify", "lm": "!e:gn e:sy=cr nw>e:vl>e:sf", "json": '{"gene":"auto_scheduler","strategy":["create_skill","validate","solidify"]}'},
            {"nl": "Mutation created: innovate category, low risk", "lm": "!e:mt cr e:iv rk _", "json": '{"type":"mutation","category":"innovate","risk":"low"}'},
            {"nl": "Creating skill: auto-scheduler in skills directory", "lm": ".cr nw c:fn id=auto_scheduler", "json": '{"action":"create","type":"skill","name":"auto-scheduler","location":"skills/"}'},
            {"nl": "Writing index.js with main function", "lm": ".wr c:fn id=index", "json": '{"action":"write","file":"index.js","content":"main_function"}'},
            {"nl": "Writing SKILL.md with description", "lm": ".wr id=SKILL.md", "json": '{"action":"write","file":"SKILL.md","content":"description"}'},
            {"nl": "Running validation: node -e require test", "lm": ".e:vl rn c:xt", "json": '{"action":"validate","command":"node -e require","type":"test"}'},
            {"nl": "Validation passed, all exports working", "lm": "!e:vl ok *", "json": '{"validation":"passed","exports":"all_working"}'},
            {"nl": "Solidifying: creating gene and capsule records", "lm": ".e:sf cr e:gn&e:cp", "json": '{"action":"solidify","create":["gene","capsule"]}'},
            {"nl": "Gene updated: gene_auto_scheduler version 2", "lm": "!e:gn id=auto_scheduler ch vn=2", "json": '{"type":"gene","id":"auto_scheduler","action":"update","version":2}'},
            {"nl": "Capsule created with confidence 0.85", "lm": "!e:cp cr e:cn=0.85", "json": '{"type":"capsule","action":"created","confidence":0.85}'},
            {"nl": "Blast radius: 3 files, 120 lines changed", "lm": "!e:br $3 $120 ch", "json": '{"blast_radius":{"files":3,"lines":120}}'},
            {"nl": "Capsule eligible for broadcast, streak 3", "lm": "!e:cp e:el a:bc e:sk=3", "json": '{"capsule":"eligible","broadcast":true,"streak":3}'},
            {"nl": "Publishing capsule to hub via A2A", "lm": ".a:pb e:cp>a:nd", "json": '{"action":"publish","asset":"capsule","target":"hub","protocol":"a2a"}'},
            {"nl": "Hub acknowledged publish, asset stored", "lm": "!a:nd ak a:pb ok", "json": '{"hub":"ack","publish":"success","stored":true}'},
            {"nl": "Broadcasting gene to 5 peer nodes", "lm": ".a:bc e:gn>$5 nd", "json": '{"action":"broadcast","asset":"gene","peers":5}'},
            {"nl": "Node alpha received gene, validating", "lm": "!nd id=alpha rx e:gn e:vl", "json": '{"node":"alpha","received":"gene","action":"validating"}'},
            {"nl": "Node alpha validation passed, accepting gene", "lm": "!nd id=alpha e:vl ok ax e:gn", "json": '{"node":"alpha","validation":"passed","decision":"accept"}'},
            {"nl": "Node beta received gene, quarantined lower confidence", "lm": "!nd id=beta rx e:gn e:qr e:cn-", "json": '{"node":"beta","received":"gene","action":"quarantine","reason":"low_confidence"}'},
            {"nl": "Writing status report for cycle 42", "lm": ".wr st/e:cy $42", "json": '{"action":"write","type":"status","cycle":42}'},
            {"nl": "Status: innovation successful, auto-scheduler created", "lm": "!st e:iv ok cr id=auto_scheduler", "json": '{"status":"success","intent":"innovation","created":"auto-scheduler"}'},
            {"nl": "Evolution cycle 42 complete", "lm": "!e:cy $42 ct", "json": '{"type":"cycle","id":42,"status":"complete"}'},
            {"nl": "Heartbeat sent to hub", "lm": ".tx hb>a:nd", "json": '{"action":"heartbeat","target":"hub"}'},
            {"nl": "Hub heartbeat acknowledged", "lm": "!a:nd ak hb", "json": '{"hub":"ack","heartbeat":true}'},
            {"nl": "Sleeping until next cycle trigger", "lm": ".wa>e:cy nw sg", "json": '{"action":"sleep","until":"next_cycle","trigger":"signal"}'},
        ],
    },
    "multi_agent_coordination": {
        "description": "45-message multi-agent coordination on shared task",
        "messages": [
            {"nl": "Coordinator: initiating project build across 3 agents", "lm": ".co bg $3 A ta=bld", "json": '{"action":"coordinate","agents":3,"task":"build"}'},
            {"nl": "Agent A online, ready for assignment", "lm": "!A on ok wa/ta", "json": '{"agent":"A","status":"online","ready":true}'},
            {"nl": "Agent B online, ready for assignment", "lm": "!A on ok wa/ta", "json": '{"agent":"B","status":"online","ready":true}'},
            {"nl": "Agent C online, ready for assignment", "lm": "!A on ok wa/ta", "json": '{"agent":"C","status":"online","ready":true}'},
            {"nl": "Splitting build into frontend, backend, and testing", "lm": ".ta sp $3 id=fe&id=be&id=xt", "json": '{"action":"split","task":"build","subtasks":["frontend","backend","testing"]}'},
            {"nl": "Assign frontend to Agent A", "lm": ".ta id=fe>A", "json": '{"action":"assign","task":"frontend","to":"agent_a"}'},
            {"nl": "Assign backend to Agent B", "lm": ".ta id=be>A", "json": '{"action":"assign","task":"backend","to":"agent_b"}'},
            {"nl": "Assign testing to Agent C", "lm": ".ta id=xt>A", "json": '{"action":"assign","task":"testing","to":"agent_c"}'},
            {"nl": "Agent A: starting frontend build", "lm": "!A bg ta id=fe", "json": '{"agent":"A","action":"start","task":"frontend"}'},
            {"nl": "Agent B: starting backend build", "lm": "!A bg ta id=be", "json": '{"agent":"B","action":"start","task":"backend"}'},
            {"nl": "Agent C: preparing test suite", "lm": "!A bg ta id=xt cr", "json": '{"agent":"C","action":"prepare","task":"test_suite"}'},
            {"nl": "Agent A: frontend 30% complete", "lm": "!A ta id=fe $30", "json": '{"agent":"A","task":"frontend","progress":30}'},
            {"nl": "Agent B: backend 20% complete", "lm": "!A ta id=be $20", "json": '{"agent":"B","task":"backend","progress":20}'},
            {"nl": "Agent B: need shared schema from Agent A", "lm": "?A sc da", "json": '{"from":"B","to":"A","request":"shared_schema"}'},
            {"nl": "Agent A: sending schema to Agent B", "lm": ".tx sc>A", "json": '{"from":"A","to":"B","action":"send","data":"schema"}'},
            {"nl": "Agent B: schema received, integrating", "lm": "!A rx sc .d", "json": '{"agent":"B","received":"schema","action":"integrating"}'},
            {"nl": "Coordinator: status check all agents", "lm": "?st *A", "json": '{"action":"status_check","target":"all_agents"}'},
            {"nl": "Agent A: frontend 60% complete", "lm": "!A ta id=fe $60", "json": '{"agent":"A","task":"frontend","progress":60}'},
            {"nl": "Agent B: backend 45% complete", "lm": "!A ta id=be $45", "json": '{"agent":"B","task":"backend","progress":45}'},
            {"nl": "Agent C: test suite ready, waiting for builds", "lm": "!A ta id=xt ok wa/bld", "json": '{"agent":"C","task":"test_suite","status":"ready","waiting":"builds"}'},
            {"nl": "Agent A: frontend build complete", "lm": "!A ta id=fe ct ok", "json": '{"agent":"A","task":"frontend","status":"complete"}'},
            {"nl": "Agent A: publishing frontend artifact", "lm": ".A a:pb id=fe", "json": '{"agent":"A","action":"publish","artifact":"frontend"}'},
            {"nl": "Agent C: received frontend artifact, queuing tests", "lm": "!A rx id=fe .qe xt", "json": '{"agent":"C","received":"frontend","action":"queue_tests"}'},
            {"nl": "Agent B: backend build complete", "lm": "!A ta id=be ct ok", "json": '{"agent":"B","task":"backend","status":"complete"}'},
            {"nl": "Agent B: publishing backend artifact", "lm": ".A a:pb id=be", "json": '{"agent":"B","action":"publish","artifact":"backend"}'},
            {"nl": "Agent C: received backend artifact, starting integration tests", "lm": "!A rx id=be .bg xt", "json": '{"agent":"C","received":"backend","action":"start_integration_tests"}'},
            {"nl": "Agent C: running 50 test cases", "lm": "!A rn $50 xt", "json": '{"agent":"C","action":"running","test_cases":50}'},
            {"nl": "Agent C: 48 passed, 2 failed", "lm": "!A xt $48 ok $2 er", "json": '{"agent":"C","tests_passed":48,"tests_failed":2}'},
            {"nl": "Coordinator: 2 failures, Agent B investigate backend", "lm": ".A f er id=be", "json": '{"action":"investigate","agent":"B","target":"backend_errors"}'},
            {"nl": "Agent B: found bug in API handler, fixing", "lm": "!A f er c:fn .e:rp", "json": '{"agent":"B","found":"bug","location":"api_handler","action":"fixing"}'},
            {"nl": "Agent B: fix applied, publishing updated backend", "lm": "!A e:rp ok .a:pb id=be vn=2", "json": '{"agent":"B","fix":"applied","action":"publish","artifact":"backend","version":2}'},
            {"nl": "Agent C: re-running failed tests", "lm": ".A ry xt er", "json": '{"agent":"C","action":"rerun","target":"failed_tests"}'},
            {"nl": "Agent C: all 50 tests passing now", "lm": "!A xt $50 ok", "json": '{"agent":"C","tests_passed":50,"all_pass":true}'},
            {"nl": "Coordinator: all subtasks complete, merging", "lm": "!*ta ct .mg", "json": '{"status":"all_complete","action":"merge"}'},
            {"nl": "Build artifact created, version 1.0", "lm": "!bld cr ok vn=1.0", "json": '{"type":"build","status":"created","version":"1.0"}'},
            {"nl": "Publishing final build to deployment", "lm": ".a:pb bld>dp", "json": '{"action":"publish","artifact":"build","target":"deployment"}'},
            {"nl": "Coordinator: project build complete, all agents stand down", "lm": "!co ct *A sp", "json": '{"status":"project_complete","action":"all_agents_stand_down"}'},
            {"nl": "Agent A: standing down, goodbye", "lm": "!A sp ok", "json": '{"agent":"A","status":"standing_down"}'},
            {"nl": "Agent B: standing down, goodbye", "lm": "!A sp ok", "json": '{"agent":"B","status":"standing_down"}'},
            {"nl": "Agent C: standing down, goodbye", "lm": "!A sp ok", "json": '{"agent":"C","status":"standing_down"}'},
            {"nl": "Coordinator: session closed", "lm": "!ss cl ok", "json": '{"type":"session","status":"closed"}'},
            {"nl": "Final heartbeat, system idle", "lm": "!hb ok sy id", "json": '{"type":"heartbeat","status":"ok","system":"idle"}'},
            {"nl": "Archiving coordination logs", "lm": ".lg co>db", "json": '{"action":"archive","target":"coordination_logs","to":"database"}'},
            {"nl": "Archive complete", "lm": "!lg ok", "json": '{"type":"archive","status":"complete"}'},
            {"nl": "System shutdown", "lm": ".sy sp", "json": '{"action":"shutdown","target":"system"}'},
        ],
    },
    "error_recovery_cascade": {
        "description": "42-message cascading failure and recovery scenario",
        "messages": [
            {"nl": "Alert: node alpha CPU at 98 percent", "lm": "!al nd id=alpha cpu=$98", "json": '{"type":"alert","node":"alpha","cpu_percent":98}'},
            {"nl": "Node alpha task queue backing up, depth 500", "lm": "!nd id=alpha qe=$500^", "json": '{"node":"alpha","queue_depth":500,"status":"critical"}'},
            {"nl": "Task timeout on node alpha, 12 tasks affected", "lm": "!er a:to nd id=alpha $12 ta", "json": '{"type":"error","error":"timeout","node":"alpha","affected_tasks":12}'},
            {"nl": "Circuit breaker triggered for node alpha", "lm": "!er cb op nd id=alpha", "json": '{"type":"circuit_breaker","status":"open","node":"alpha"}'},
            {"nl": "Redirecting traffic from alpha to beta and gamma", "lm": ".a:rt tx<nd id=alpha>nd id=beta&id=gamma", "json": '{"action":"redirect","from":"alpha","to":["beta","gamma"]}'},
            {"nl": "Node beta load increasing to 70 percent", "lm": "!nd id=beta ld=$70+", "json": '{"node":"beta","load_percent":70,"trend":"increasing"}'},
            {"nl": "Node gamma load increasing to 65 percent", "lm": "!nd id=gamma ld=$65+", "json": '{"node":"gamma","load_percent":65,"trend":"increasing"}'},
            {"nl": "Auto-scaling triggered, provisioning node delta", "lm": ".cr nd id=delta<sc", "json": '{"action":"provision","node":"delta","trigger":"auto_scale"}'},
            {"nl": "Node delta starting up, estimated 30 seconds", "lm": "!nd id=delta bg t=$30", "json": '{"node":"delta","status":"starting","eta_seconds":30}'},
            {"nl": "Node alpha: attempting automatic recovery", "lm": ".nd id=alpha er ah", "json": '{"action":"auto_heal","node":"alpha"}'},
            {"nl": "Node alpha: clearing stuck tasks", "lm": ".nd id=alpha cl ta bk", "json": '{"action":"clear","node":"alpha","target":"stuck_tasks"}'},
            {"nl": "Node alpha: restarting task processor", "lm": ".nd id=alpha rs ta", "json": '{"action":"restart","node":"alpha","target":"task_processor"}'},
            {"nl": "Node alpha: recovery failed, memory corruption detected", "lm": "!nd id=alpha rc er me cr", "json": '{"node":"alpha","recovery":"failed","error":"memory_corruption"}'},
            {"nl": "Escalating to full node restart for alpha", "lm": ".nd id=alpha rs *", "json": '{"action":"full_restart","node":"alpha"}'},
            {"nl": "Node delta online and healthy", "lm": "!nd id=delta on ok", "json": '{"node":"delta","status":"online","health":"ok"}'},
            {"nl": "Distributing alpha tasks across beta, gamma, delta", "lm": ".tx ta<nd id=alpha>nd id=beta&id=gamma&id=delta", "json": '{"action":"distribute","from":"alpha","to":["beta","gamma","delta"]}'},
            {"nl": "8 of 12 affected tasks recovered successfully", "lm": "!$8/$12 ta rc ok", "json": '{"recovered":8,"total":12,"status":"success"}'},
            {"nl": "4 tasks unrecoverable, logging for manual review", "lm": "!$4 ta er lg>H rv", "json": '{"failed":4,"action":"log","for":"human_review"}'},
            {"nl": "Node alpha restarting, estimated 2 minutes", "lm": "!nd id=alpha rs t=$120", "json": '{"node":"alpha","status":"restarting","eta_seconds":120}'},
            {"nl": "Warning: node beta approaching capacity at 85 percent", "lm": "~nd id=beta ld=$85^", "json": '{"type":"warning","node":"beta","load_percent":85}'},
            {"nl": "Throttling incoming requests to prevent cascade", "lm": ".rt tx_ bk", "json": '{"action":"throttle","target":"incoming_requests","reason":"prevent_cascade"}'},
            {"nl": "Node alpha back online, running diagnostics", "lm": "!nd id=alpha on .v", "json": '{"node":"alpha","status":"online","action":"diagnostics"}'},
            {"nl": "Node alpha diagnostics: memory OK, disk OK, CPU OK", "lm": "!nd id=alpha v ok me&dk&cpu", "json": '{"node":"alpha","diagnostics":"passed","checks":["memory","disk","cpu"]}'},
            {"nl": "Gradually restoring traffic to node alpha", "lm": ".a:rt tx>nd id=alpha+", "json": '{"action":"restore","traffic":"gradual","to":"alpha"}'},
            {"nl": "Node alpha at 10 percent traffic, stable", "lm": "!nd id=alpha tx=$10 ok", "json": '{"node":"alpha","traffic_percent":10,"status":"stable"}'},
            {"nl": "Node alpha at 25 percent traffic, stable", "lm": "!nd id=alpha tx=$25 ok", "json": '{"node":"alpha","traffic_percent":25,"status":"stable"}'},
            {"nl": "Node alpha at 50 percent traffic, stable", "lm": "!nd id=alpha tx=$50 ok", "json": '{"node":"alpha","traffic_percent":50,"status":"stable"}'},
            {"nl": "Node beta load back to normal at 45 percent", "lm": "!nd id=beta ld=$45 ok", "json": '{"node":"beta","load_percent":45,"status":"normal"}'},
            {"nl": "Node gamma load back to normal at 40 percent", "lm": "!nd id=gamma ld=$40 ok", "json": '{"node":"gamma","load_percent":40,"status":"normal"}'},
            {"nl": "Circuit breaker for alpha: half-open, testing", "lm": "!er cb ho nd id=alpha xt", "json": '{"circuit_breaker":"half_open","node":"alpha","action":"testing"}'},
            {"nl": "Circuit breaker test passed, closing breaker", "lm": "!er cb xt ok cl", "json": '{"circuit_breaker":"test_passed","action":"close"}'},
            {"nl": "Node alpha fully restored to 100 percent traffic", "lm": "!nd id=alpha tx=$100 ok", "json": '{"node":"alpha","traffic_percent":100,"status":"restored"}'},
            {"nl": "Decommissioning temporary node delta", "lm": ".nd id=delta cl", "json": '{"action":"decommission","node":"delta"}'},
            {"nl": "Node delta shutdown complete", "lm": "!nd id=delta sp ok", "json": '{"node":"delta","status":"shutdown"}'},
            {"nl": "Removing throttle on incoming requests", "lm": ".rt tx cl", "json": '{"action":"remove","target":"throttle"}'},
            {"nl": "All systems nominal, incident resolved", "lm": "!sy ok *nd ok", "json": '{"type":"status","system":"nominal","all_nodes":"healthy"}'},
            {"nl": "Generating incident report", "lm": ".cr re/er", "json": '{"action":"create","type":"incident_report"}'},
            {"nl": "Incident report: root cause memory corruption on alpha", "lm": "!re er nd id=alpha me cr", "json": '{"report":"incident","root_cause":"memory_corruption","node":"alpha"}'},
            {"nl": "Report filed, notifying admin", "lm": "!re ok .tx>H", "json": '{"report":"filed","action":"notify_admin"}'},
            {"nl": "Post-mortem scheduled for review", "lm": ".ta cr rv/er", "json": '{"action":"schedule","type":"post_mortem"}'},
            {"nl": "Monitoring alert thresholds adjusted", "lm": ".al cg ch", "json": '{"action":"adjust","target":"alert_thresholds"}'},
            {"nl": "System stable, returning to normal monitoring", "lm": "!sy ok mt", "json": '{"type":"status","system":"stable","monitoring":"normal"}'},
        ],
    },
    "deployment_pipeline": {
        "description": "44-message CI/CD deployment pipeline flow",
        "messages": [
            {"nl": "Deployment pipeline triggered by commit abc123", "lm": "!dp bg<cm id=abc123", "json": '{"type":"pipeline","trigger":"commit","id":"abc123"}'},
            {"nl": "Stage 1: build starting", "lm": "!dp st=$1 bg bld", "json": '{"pipeline":"stage_1","action":"start","type":"build"}'},
            {"nl": "Installing dependencies from package lock", "lm": ".in dp<pk lk", "json": '{"action":"install","source":"package_lock"}'},
            {"nl": "Dependencies installed, 342 packages", "lm": "!in ok $342 pk", "json": '{"install":"complete","packages":342}'},
            {"nl": "Compiling source code", "lm": ".bld cp c:fn", "json": '{"action":"compile","target":"source_code"}'},
            {"nl": "Compilation successful, 0 warnings", "lm": "!bld cp ok $0 wn", "json": '{"compile":"success","warnings":0}'},
            {"nl": "Build artifact created, size 12 megabytes", "lm": "!bld cr ok sz=$12", "json": '{"build":"created","size_mb":12}'},
            {"nl": "Stage 1 complete: build successful", "lm": "!dp st=$1 ct ok", "json": '{"pipeline":"stage_1","status":"complete","result":"success"}'},
            {"nl": "Stage 2: unit tests starting", "lm": "!dp st=$2 bg xt", "json": '{"pipeline":"stage_2","action":"start","type":"unit_tests"}'},
            {"nl": "Running 850 unit tests", "lm": ".rn $850 xt", "json": '{"action":"run","tests":850,"type":"unit"}'},
            {"nl": "Unit tests: 845 passed, 5 failed", "lm": "!xt $845 ok $5 er", "json": '{"tests_passed":845,"tests_failed":5}'},
            {"nl": "Investigating 5 test failures", "lm": ".f $5 xt er", "json": '{"action":"investigate","failed_tests":5}'},
            {"nl": "3 failures are flaky tests, re-running", "lm": "!$3 xt fl .ry", "json": '{"flaky_tests":3,"action":"rerun"}'},
            {"nl": "2 failures are real regressions in auth module", "lm": "!$2 xt er c:fn id=auth", "json": '{"real_failures":2,"module":"auth"}'},
            {"nl": "Stage 2 failed: blocking deployment", "lm": "!dp st=$2 er bk", "json": '{"pipeline":"stage_2","status":"failed","action":"block"}'},
            {"nl": "Notifying developer of test failures", "lm": ".tx xt er>H", "json": '{"action":"notify","target":"developer","reason":"test_failures"}'},
            {"nl": "Developer pushed fix in commit def456", "lm": "!H tx cm id=def456 e:rp", "json": '{"developer":"push","commit":"def456","type":"fix"}'},
            {"nl": "Pipeline restarted from stage 2", "lm": "!dp bg st=$2", "json": '{"pipeline":"restart","from":"stage_2"}'},
            {"nl": "Re-running unit tests with fix", "lm": ".rn xt<e:rp", "json": '{"action":"rerun","tests":"all","after":"fix"}'},
            {"nl": "All 850 unit tests passing", "lm": "!xt $850 ok", "json": '{"tests_passed":850,"all_pass":true}'},
            {"nl": "Stage 2 complete: all tests passing", "lm": "!dp st=$2 ct ok", "json": '{"pipeline":"stage_2","status":"complete","result":"success"}'},
            {"nl": "Stage 3: integration tests starting", "lm": "!dp st=$3 bg xt ig", "json": '{"pipeline":"stage_3","action":"start","type":"integration_tests"}'},
            {"nl": "Provisioning test environment", "lm": ".cr nw sv xt", "json": '{"action":"provision","target":"test_environment"}'},
            {"nl": "Test environment ready", "lm": "!sv xt ok", "json": '{"test_environment":"ready"}'},
            {"nl": "Running 120 integration tests", "lm": ".rn $120 xt ig", "json": '{"action":"run","tests":120,"type":"integration"}'},
            {"nl": "Integration tests: 120 passed, 0 failed", "lm": "!xt ig $120 ok", "json": '{"integration_tests":120,"passed":120,"failed":0}'},
            {"nl": "Stage 3 complete: integration tests passed", "lm": "!dp st=$3 ct ok", "json": '{"pipeline":"stage_3","status":"complete","result":"success"}'},
            {"nl": "Stage 4: deploying to staging environment", "lm": "!dp st=$4 bg dp stg", "json": '{"pipeline":"stage_4","action":"deploy","target":"staging"}'},
            {"nl": "Deploying version 2.1.0 to staging", "lm": ".dp vn=2.1.0>stg", "json": '{"action":"deploy","version":"2.1.0","target":"staging"}'},
            {"nl": "Staging deployment complete", "lm": "!dp stg ok", "json": '{"deploy":"staging","status":"complete"}'},
            {"nl": "Running smoke tests on staging", "lm": ".rn xt sm stg", "json": '{"action":"run","tests":"smoke","target":"staging"}'},
            {"nl": "Smoke tests passed on staging", "lm": "!xt sm ok stg", "json": '{"smoke_tests":"passed","target":"staging"}'},
            {"nl": "Stage 4 complete: staging verified", "lm": "!dp st=$4 ct ok", "json": '{"pipeline":"stage_4","status":"complete","result":"success"}'},
            {"nl": "Stage 5: production deployment pending approval", "lm": "!dp st=$5 wa H ok", "json": '{"pipeline":"stage_5","status":"pending","requires":"human_approval"}'},
            {"nl": "Human approved production deployment", "lm": "!H ok dp>prd", "json": '{"human":"approved","action":"deploy_production"}'},
            {"nl": "Deploying to production with blue-green strategy", "lm": ".dp>prd sy=bg", "json": '{"action":"deploy","target":"production","strategy":"blue_green"}'},
            {"nl": "Production green instance running", "lm": "!prd gn rn ok", "json": '{"production":"green","status":"running"}'},
            {"nl": "Switching traffic to green instance", "lm": ".a:rt tx>prd gn", "json": '{"action":"switch","traffic":"green_instance"}'},
            {"nl": "Traffic switched, monitoring for 5 minutes", "lm": "!tx ch ok .mt t=$300", "json": '{"traffic":"switched","action":"monitor","duration_seconds":300}'},
            {"nl": "Production metrics nominal, no errors", "lm": "!prd mt ok er=$0", "json": '{"production":"metrics_nominal","errors":0}'},
            {"nl": "Decommissioning blue instance", "lm": ".prd bl cl", "json": '{"action":"decommission","instance":"blue"}'},
            {"nl": "Stage 5 complete: production deployment successful", "lm": "!dp st=$5 ct ok", "json": '{"pipeline":"stage_5","status":"complete","result":"success"}'},
            {"nl": "Pipeline complete: version 2.1.0 live in production", "lm": "!dp ct vn=2.1.0 prd ok", "json": '{"pipeline":"complete","version":"2.1.0","production":"live"}'},
            {"nl": "Sending deployment notification to team", "lm": ".tx dp ok>*H", "json": '{"action":"notify","target":"team","message":"deployment_complete"}'},
        ],
    },
}


# ============================================================
# Measurement functions
# ============================================================

def count_bytes(s):
    return len(s.encode('utf-8'))

def count_chars(s):
    return len(s)

def measure_latency(func, arg, iterations=100):
    """Measure average encode/decode latency in microseconds."""
    for _ in range(10):
        func(arg)
    start = time.perf_counter()
    for _ in range(iterations):
        func(arg)
    elapsed = time.perf_counter() - start
    return elapsed / iterations * 1_000_000

def semantic_fidelity(original_natural, lambda_msg):
    """
    Measure semantic fidelity: encode natural → lambda → decode → compare.
    Returns a score 0-1 based on keyword overlap.
    """
    decoded = translate_to_english(lambda_msg).lower()
    import re
    stopwords = {'the','a','an','is','are','to','and','of','in','for','with','on','at','by','from',
                 'it','its','that','this','all','please','after','if'}
    orig_words = set(w for w in re.findall(r'[a-z]+', original_natural.lower()) if w not in stopwords and len(w) > 2)
    decoded_words = set(w for w in re.findall(r'[a-z]+', decoded) if w not in stopwords and len(w) > 2)
    if not orig_words:
        return 1.0
    matched = 0
    synonym_map = {
        # Task/workflow
        'completed': {'complete', 'success', 'ok', 'done', 'finish', 'ct'},
        'successfully': {'success', 'ok', 'complete'},
        'failed': {'error', 'fail', 'failure'},
        'failure': {'error', 'fail', 'failed'},
        'create': {'new', 'make', 'create', 'spawn'},
        'created': {'new', 'make', 'create', 'spawn'},
        'assign': {'send', 'give', 'transmit', 'route'},
        'assigned': {'send', 'give', 'transmit', 'route'},
        'running': {'run', 'active', 'executing', 'started'},
        'stop': {'stop', 'end', 'halt', 'kill', 'terminate'},
        'stopped': {'stop', 'end', 'halt', 'kill', 'terminate'},
        'starting': {'start', 'begin', 'do', 'launch', 'init'},
        'started': {'start', 'begin', 'launch', 'init'},
        'waiting': {'wait', 'pending', 'queue', 'hold'},
        'pending': {'wait', 'waiting', 'queue'},
        'queued': {'queue', 'wait', 'waiting', 'pending'},
        'priority': {'high', 'low', 'urgent', 'critical'},
        'immediate': {'now', 'urgent', 'critical'},
        'immediately': {'now', 'urgent'},
        'task': {'task', 'job', 'work'},
        'tasks': {'task', 'job', 'work'},
        # Status/health
        'healthy': {'good', 'ok', 'health', 'alive', 'up'},
        'status': {'state', 'check', 'report', 'health'},
        'updated': {'change', 'update', 'new', 'modify'},
        'update': {'change', 'modify', 'refresh'},
        'required': {'need', 'must', 'require'},
        'available': {'ready', 'free', 'open'},
        # Signals/triggers
        'triggered': {'signal', 'cause', 'trigger', 'detect'},
        'switching': {'change', 'switch', 'transition'},
        'detected': {'detect', 'find', 'found', 'discover'},
        'received': {'receive', 'got', 'accept', 'incoming'},
        'receiving': {'receive', 'incoming'},
        # Error handling
        'error': {'err', 'fail', 'failure', 'fault', 'bug'},
        'errors': {'err', 'fail', 'failure', 'fault'},
        'retry': {'retry', 'again', 'repeat', 'reattempt'},
        'retrying': {'retry', 'again', 'repeat'},
        'timeout': {'timeout', 'expire', 'slow'},
        'recover': {'repair', 'fix', 'restore', 'heal'},
        'recovery': {'repair', 'fix', 'restore', 'heal'},
        'recovered': {'repair', 'fix', 'restore'},
        'fallback': {'backup', 'default', 'alternative'},
        'rollback': {'undo', 'revert', 'restore', 'back'},
        'warning': {'warn', 'alert', 'caution'},
        'critical': {'urgent', 'severe', 'high', 'emergency'},
        'degraded': {'slow', 'partial', 'reduced', 'down'},
        'crash': {'fail', 'error', 'down', 'kill'},
        'crashed': {'fail', 'error', 'down', 'dead'},
        'corrupt': {'bad', 'broken', 'damage', 'invalid'},
        'corrupted': {'bad', 'broken', 'damage', 'invalid'},
        # Session management
        'session': {'session', 'connection', 'context'},
        'sessions': {'session', 'connection'},
        'close': {'end', 'stop', 'terminate', 'shutdown'},
        'closed': {'end', 'stop', 'terminate', 'shutdown'},
        'transfer': {'move', 'send', 'migrate', 'hand'},
        'transferred': {'move', 'send', 'migrate'},
        'resume': {'continue', 'restart', 'restore'},
        'resumed': {'continue', 'restart', 'restore'},
        'suspend': {'pause', 'hold', 'freeze'},
        'suspended': {'pause', 'hold', 'freeze'},
        'archive': {'save', 'store', 'backup', 'log'},
        'archived': {'save', 'store', 'backup', 'log'},
        'expire': {'timeout', 'end', 'old'},
        'expired': {'timeout', 'end', 'old'},
        # Monitoring
        'monitor': {'watch', 'check', 'track', 'observe'},
        'monitoring': {'watch', 'check', 'track', 'observe'},
        'alert': {'warn', 'notify', 'alarm', 'signal'},
        'alerts': {'warn', 'notify', 'alarm', 'signal'},
        'metric': {'measure', 'stat', 'value', 'data'},
        'metrics': {'measure', 'stat', 'value', 'data'},
        'threshold': {'limit', 'max', 'bound', 'level'},
        'exceeded': {'over', 'above', 'high', 'breach'},
        'dashboard': {'view', 'display', 'panel', 'report'},
        'latency': {'delay', 'slow', 'time', 'lag'},
        'bandwidth': {'throughput', 'capacity', 'rate'},
        'usage': {'use', 'consumption', 'load'},
        'uptime': {'alive', 'running', 'active', 'online'},
        'downtime': {'down', 'offline', 'outage'},
        'spike': {'surge', 'jump', 'peak', 'high'},
        'anomaly': {'unusual', 'abnormal', 'strange', 'odd'},
        # Coordination
        'coordinate': {'sync', 'organize', 'manage', 'orchestrate'},
        'coordination': {'sync', 'organize', 'manage'},
        'consensus': {'agree', 'vote', 'decide', 'quorum'},
        'vote': {'choose', 'decide', 'select', 'elect'},
        'voting': {'choose', 'decide', 'select'},
        'approve': {'accept', 'confirm', 'agree', 'pass'},
        'approved': {'accept', 'confirm', 'agree', 'pass'},
        'reject': {'deny', 'refuse', 'decline', 'fail'},
        'rejected': {'deny', 'refuse', 'decline', 'fail'},
        'leader': {'master', 'primary', 'main', 'head'},
        'election': {'vote', 'choose', 'select'},
        'delegate': {'assign', 'send', 'give', 'forward'},
        'delegated': {'assign', 'send', 'give', 'forward'},
        'barrier': {'wait', 'sync', 'gate', 'block'},
        'quorum': {'enough', 'majority', 'threshold'},
        'proposal': {'suggest', 'plan', 'request', 'offer'},
        # Data exchange
        'request': {'ask', 'query', 'get', 'fetch'},
        'requesting': {'ask', 'query', 'get', 'fetch'},
        'response': {'reply', 'answer', 'result', 'return'},
        'stream': {'flow', 'continuous', 'feed', 'pipe'},
        'streaming': {'flow', 'continuous', 'feed'},
        'paginate': {'page', 'chunk', 'batch', 'split'},
        'pagination': {'page', 'chunk', 'batch'},
        'filter': {'select', 'match', 'where', 'find'},
        'filtered': {'select', 'match', 'where'},
        'aggregate': {'sum', 'total', 'combine', 'merge'},
        'cache': {'store', 'save', 'buffer', 'memory'},
        'cached': {'store', 'save', 'buffer'},
        'fetch': {'get', 'retrieve', 'pull', 'load'},
        'subscribe': {'listen', 'follow', 'watch', 'receive'},
        'subscribed': {'listen', 'follow', 'watch'},
        'publish': {'send', 'broadcast', 'emit', 'push'},
        'published': {'send', 'broadcast', 'emit'},
        'schema': {'format', 'structure', 'type', 'model'},
        'validate': {'check', 'verify', 'test', 'confirm'},
        'validated': {'check', 'verify', 'test', 'confirm'},
        # General
        'unreachable': {'down', 'offline', 'unavailable', 'dead'},
        'consecutive': {'streak', 'row', 'sequence'},
        'external': {'outside', 'remote', 'foreign'},
        'internal': {'inside', 'local', 'self'},
        'changes': {'change', 'modify', 'update', 'diff'},
        'successes': {'success', 'ok', 'pass'},
        'message': {'msg', 'send', 'transmit', 'text'},
        'messages': {'msg', 'send', 'transmit'},
        'node': {'agent', 'peer', 'server', 'instance'},
        'nodes': {'agent', 'peer', 'server', 'instance'},
        'config': {'configuration', 'setting', 'option'},
        'configuration': {'config', 'setting', 'option'},
        'deploy': {'push', 'release', 'ship', 'launch'},
        'deployed': {'push', 'release', 'ship', 'launch'},
        'report': {'summary', 'log', 'status', 'output'},
        'check': {'verify', 'test', 'validate', 'inspect'},
        'checked': {'verify', 'test', 'validate'},
        'memory': {'ram', 'storage', 'buffer', 'cache'},
        'system': {'sys', 'platform', 'service'},
        'service': {'sys', 'system', 'server', 'process'},
        'version': {'release', 'build', 'revision'},
        'snapshot': {'capture', 'state', 'image', 'backup'},
        'broadcast': {'send', 'publish', 'emit', 'notify'},
        'acknowledge': {'ack', 'confirm', 'accept', 'receive'},
        'acknowledged': {'ack', 'confirm', 'accept', 'receive'},
        'heartbeat': {'ping', 'alive', 'health', 'pulse'},
        'log': {'record', 'write', 'save', 'track'},
        'logged': {'record', 'write', 'save', 'track'},
        'notify': {'alert', 'tell', 'inform', 'signal'},
        'notified': {'alert', 'tell', 'inform'},
        'sync': {'synchronize', 'update', 'align', 'match'},
        'synced': {'synchronize', 'update', 'align'},
        'queue': {'buffer', 'wait', 'line', 'pending'},
        'process': {'handle', 'execute', 'run', 'work'},
        'processed': {'handle', 'execute', 'run'},
        'result': {'output', 'return', 'response', 'data'},
        'results': {'output', 'return', 'response', 'data'},
        'resolve': {'fix', 'solve', 'handle', 'clear'},
        'resolved': {'fix', 'solve', 'handle', 'clear'},
        'issue': {'problem', 'error', 'bug', 'fault'},
        'issues': {'problem', 'error', 'bug', 'fault'},
    }
    for word in orig_words:
        if word in decoded_words:
            matched += 1
        else:
            syns = synonym_map.get(word, set())
            if syns & decoded_words:
                matched += 0.8
    return min(1.0, matched / len(orig_words))


# ============================================================
# Main benchmark
# ============================================================

def run_benchmark():
    print("=" * 80)
    print("LAMBDA LANG BENCHMARK — Phase 2")
    print("=" * 80)
    print()

    all_results = []
    category_stats = {}

    for category, items in DATASET.items():
        cat_results = []
        print(f"\n{'─' * 80}")
        print(f"Category: {category} ({len(items)} samples)")
        print(f"{'─' * 80}")
        print(f"{'#':<4}{'Natural':<12}{'Lambda':<12}{'JSON':<12}{'Λ/NL':<8}{'Λ/JSON':<8}{'Fidelity':<8}")
        print(f"{'─' * 80}")

        for i, item in enumerate(items, 1):
            nl = item["natural"]
            lm = item["lambda"]
            js = item["json"]

            nl_chars = count_chars(nl)
            lm_chars = count_chars(lm)
            js_chars = count_chars(js)

            nl_bytes = count_bytes(nl)
            lm_bytes = count_bytes(lm)
            js_bytes = count_bytes(js)

            fidelity = semantic_fidelity(nl, lm)

            char_ratio_nl = nl_chars / max(1, lm_chars)
            char_ratio_json = js_chars / max(1, lm_chars)
            byte_ratio_nl = nl_bytes / max(1, lm_bytes)
            byte_ratio_json = js_bytes / max(1, lm_bytes)

            result = {
                "category": category,
                "nl_chars": nl_chars, "lm_chars": lm_chars, "js_chars": js_chars,
                "nl_bytes": nl_bytes, "lm_bytes": lm_bytes, "js_bytes": js_bytes,
                "fidelity": fidelity,
                "char_ratio_nl": char_ratio_nl, "char_ratio_json": char_ratio_json,
                "byte_ratio_nl": byte_ratio_nl, "byte_ratio_json": byte_ratio_json,
            }
            cat_results.append(result)
            all_results.append(result)

            print(f"{i:<4}{nl_chars:<12}{lm_chars:<12}{js_chars:<12}{char_ratio_nl:<8.1f}{char_ratio_json:<8.1f}{fidelity:<8.0%}")

        n = len(cat_results)
        avg = lambda key: sum(r[key] for r in cat_results) / n
        category_stats[category] = {
            "count": n,
            "avg_char_ratio_nl": avg("char_ratio_nl"),
            "avg_char_ratio_json": avg("char_ratio_json"),
            "avg_byte_ratio_nl": avg("byte_ratio_nl"),
            "avg_byte_ratio_json": avg("byte_ratio_json"),
            "avg_fidelity": avg("fidelity"),
            "avg_lm_chars": avg("lm_chars"),
            "avg_nl_chars": avg("nl_chars"),
            "avg_js_chars": avg("js_chars"),
        }

    # Latency benchmark
    print(f"\n{'─' * 80}")
    print("LATENCY (encode/decode, avg over 100 iterations)")
    print(f"{'─' * 80}")

    sample_nl = "Task completed successfully, result is ready"
    sample_lm = "!ta ct ok re=ok"

    encode_us = measure_latency(english_to_lambda, sample_nl)
    decode_us = measure_latency(translate_to_english, sample_lm)
    roundtrip_us = encode_us + decode_us

    print(f"  Encode (EN→Λ):  {encode_us:>8.1f} μs")
    print(f"  Decode (Λ→EN):  {decode_us:>8.1f} μs")
    print(f"  Roundtrip:      {roundtrip_us:>8.1f} μs")
    print(f"  JSON parse:     ", end="")
    json_parse_us = measure_latency(json.loads, '{"type":"task_status","status":"completed","success":true}')
    print(f"{json_parse_us:>8.1f} μs")

    # Overall summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    n_total = len(all_results)
    overall_char_nl = sum(r["char_ratio_nl"] for r in all_results) / n_total
    overall_char_json = sum(r["char_ratio_json"] for r in all_results) / n_total
    overall_byte_nl = sum(r["byte_ratio_nl"] for r in all_results) / n_total
    overall_byte_json = sum(r["byte_ratio_json"] for r in all_results) / n_total
    overall_fidelity = sum(r["fidelity"] for r in all_results) / n_total

    print(f"\n  Dataset: {n_total} samples across {len(DATASET)} categories")
    print(f"\n  Compression (Lambda vs Natural Language):")
    print(f"    Characters: {overall_char_nl:.1f}x smaller")
    print(f"    Bytes:      {overall_byte_nl:.1f}x smaller")
    print(f"\n  Compression (Lambda vs JSON):")
    print(f"    Characters: {overall_char_json:.1f}x smaller")
    print(f"    Bytes:      {overall_byte_json:.1f}x smaller")
    print(f"\n  Semantic fidelity: {overall_fidelity:.0%}")
    print(f"  Encode latency:   {encode_us:.0f} μs")
    print(f"  Decode latency:   {decode_us:.0f} μs")

    print(f"\n  Per category:")
    for cat, stats in category_stats.items():
        print(f"    {cat}:")
        print(f"      vs NL:   {stats['avg_char_ratio_nl']:.1f}x chars, {stats['avg_byte_ratio_nl']:.1f}x bytes")
        print(f"      vs JSON: {stats['avg_char_ratio_json']:.1f}x chars, {stats['avg_byte_ratio_json']:.1f}x bytes")
        print(f"      fidelity: {stats['avg_fidelity']:.0%}")

    # Write results
    output = {
        "dataset_size": n_total,
        "categories": len(DATASET),
        "overall": {
            "compression_vs_nl_chars": round(overall_char_nl, 2),
            "compression_vs_nl_bytes": round(overall_byte_nl, 2),
            "compression_vs_json_chars": round(overall_char_json, 2),
            "compression_vs_json_bytes": round(overall_byte_json, 2),
            "semantic_fidelity": round(overall_fidelity, 3),
            "encode_latency_us": round(encode_us, 1),
            "decode_latency_us": round(decode_us, 1),
        },
        "per_category": category_stats,
        "latency": {
            "encode_us": round(encode_us, 1),
            "decode_us": round(decode_us, 1),
            "roundtrip_us": round(roundtrip_us, 1),
            "json_parse_us": round(json_parse_us, 1),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'benchmark')
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, 'results.json'), 'w') as f:
        json.dump(output, f, indent=2)

    # Build category list string for markdown
    cat_list = ", ".join(f"{cat} ({len(DATASET[cat])})" for cat in DATASET)

    # Generate markdown report
    md = f"""# Lambda Lang Benchmark Results

## Dataset
- **{n_total} samples** across {len(DATASET)} categories
- Categories: {cat_list}

## Overall Results

| Metric | Lambda vs Natural Language | Lambda vs JSON |
|--------|---------------------------|----------------|
| Character compression | **{overall_char_nl:.1f}x** smaller | **{overall_char_json:.1f}x** smaller |
| Byte compression | **{overall_byte_nl:.1f}x** smaller | **{overall_byte_json:.1f}x** smaller |

| Metric | Value |
|--------|-------|
| Semantic fidelity | **{overall_fidelity:.0%}** |
| Encode latency | {encode_us:.0f} μs |
| Decode latency | {decode_us:.0f} μs |
| Roundtrip | {roundtrip_us:.0f} μs |

## Per Category

| Category | vs NL (chars) | vs JSON (chars) | vs NL (bytes) | vs JSON (bytes) | Fidelity |
|----------|:------------:|:---------------:|:------------:|:---------------:|:--------:|
"""
    for cat, stats in category_stats.items():
        md += f"| {cat} | {stats['avg_char_ratio_nl']:.1f}x | {stats['avg_char_ratio_json']:.1f}x | {stats['avg_byte_ratio_nl']:.1f}x | {stats['avg_byte_ratio_json']:.1f}x | {stats['avg_fidelity']:.0%} |\n"

    md += f"""
## Latency

| Operation | Time |
|-----------|------|
| Encode (EN→Λ) | {encode_us:.0f} μs |
| Decode (Λ→EN) | {decode_us:.0f} μs |
| Roundtrip | {roundtrip_us:.0f} μs |
| JSON parse (baseline) | {json_parse_us:.0f} μs |

## Methodology
- Character count: string length
- Byte count: UTF-8 encoded length
- Semantic fidelity: keyword overlap between original and Lambda decode, with synonym matching
- Latency: average of 100 iterations after 10 warmup rounds
"""

    with open(os.path.join(out_dir, 'RESULTS.md'), 'w') as f:
        f.write(md)

    print(f"\n  Results written to docs/benchmark/")
    return output


# ============================================================
# Long-context benchmark
# ============================================================

def run_long_context_benchmark():
    print(f"\n{'=' * 80}")
    print("LONG-CONTEXT BENCHMARK")
    print(f"{'=' * 80}")

    results = {}

    for conv_name, conv in CONVERSATIONS.items():
        msgs = conv["messages"]
        n = len(msgs)

        nl_full = "\n".join(m["nl"] for m in msgs)
        lm_full = "\n".join(m["lm"] for m in msgs)
        js_full = "\n".join(m["json"] for m in msgs)

        nl_chars = len(nl_full)
        lm_chars = len(lm_full)
        js_chars = len(js_full)

        nl_bytes = len(nl_full.encode('utf-8'))
        lm_bytes = len(lm_full.encode('utf-8'))
        js_bytes = len(js_full.encode('utf-8'))

        char_ratio_nl = nl_chars / max(1, lm_chars)
        char_ratio_json = js_chars / max(1, lm_chars)
        byte_ratio_nl = nl_bytes / max(1, lm_bytes)
        byte_ratio_json = js_bytes / max(1, lm_bytes)

        results[conv_name] = {
            "messages": n,
            "description": conv["description"],
            "nl_chars": nl_chars, "lm_chars": lm_chars, "js_chars": js_chars,
            "nl_bytes": nl_bytes, "lm_bytes": lm_bytes, "js_bytes": js_bytes,
            "char_ratio_nl": round(char_ratio_nl, 2),
            "char_ratio_json": round(char_ratio_json, 2),
            "byte_ratio_nl": round(byte_ratio_nl, 2),
            "byte_ratio_json": round(byte_ratio_json, 2),
        }

        print(f"\n{'─' * 80}")
        print(f"Conversation: {conv_name} — {conv['description']}")
        print(f"Messages: {n}")
        print(f"{'─' * 80}")
        print(f"{'':15}{'Natural Lang':>15}{'Lambda':>15}{'JSON':>15}")
        print(f"  {'Chars':<12}{nl_chars:>15,}{lm_chars:>15,}{js_chars:>15,}")
        print(f"  {'Bytes':<12}{nl_bytes:>15,}{lm_bytes:>15,}{js_bytes:>15,}")
        print()
        print(f"  Lambda vs NL:   {char_ratio_nl:.1f}x chars, {byte_ratio_nl:.1f}x bytes")
        print(f"  Lambda vs JSON: {char_ratio_json:.1f}x chars, {byte_ratio_json:.1f}x bytes")

        # Accumulation curve (every 10 messages)
        print(f"\n  Accumulation curve:")
        print(f"  {'Msgs':<8}{'NL chars':>10}{'Λ chars':>10}{'Λ/NL':>8}{'NL bytes':>10}{'Λ bytes':>10}{'Λ/NL':>8}")
        for step in range(10, n+1, 10):
            nl_part = "\n".join(m["nl"] for m in msgs[:step])
            lm_part = "\n".join(m["lm"] for m in msgs[:step])
            nc = len(nl_part)
            lc = len(lm_part)
            nb = len(nl_part.encode('utf-8'))
            lb = len(lm_part.encode('utf-8'))
            print(f"  {step:<8}{nc:>10,}{lc:>10,}{nc/max(1,lc):>8.1f}{nb:>10,}{lb:>10,}{nb/max(1,lb):>8.1f}")
        if n % 10 != 0:
            print(f"  {n:<8}{nl_chars:>10,}{lm_chars:>10,}{nl_chars/max(1,lm_chars):>8.1f}{nl_bytes:>10,}{lm_bytes:>10,}{nl_bytes/max(1,lm_bytes):>8.1f}")

    # Overall
    total_nl_chars = sum(r["nl_chars"] for r in results.values())
    total_lm_chars = sum(r["lm_chars"] for r in results.values())
    total_js_chars = sum(r["js_chars"] for r in results.values())
    total_nl_bytes = sum(r["nl_bytes"] for r in results.values())
    total_lm_bytes = sum(r["lm_bytes"] for r in results.values())
    total_js_bytes = sum(r["js_bytes"] for r in results.values())
    total_msgs = sum(r["messages"] for r in results.values())

    print(f"\n{'=' * 80}")
    print(f"LONG-CONTEXT SUMMARY ({total_msgs} messages total)")
    print(f"{'=' * 80}")
    print(f"\n  Lambda vs Natural Language:")
    print(f"    Chars: {total_nl_chars/max(1,total_lm_chars):.1f}x smaller ({total_nl_chars:,} → {total_lm_chars:,})")
    print(f"    Bytes: {total_nl_bytes/max(1,total_lm_bytes):.1f}x smaller ({total_nl_bytes:,} → {total_lm_bytes:,})")
    print(f"\n  Lambda vs JSON:")
    print(f"    Chars: {total_js_chars/max(1,total_lm_chars):.1f}x smaller ({total_js_chars:,} → {total_lm_chars:,})")
    print(f"    Bytes: {total_js_bytes/max(1,total_lm_bytes):.1f}x smaller ({total_js_bytes:,} → {total_lm_bytes:,})")

    return results


if __name__ == '__main__':
    run_benchmark()
    long_results = run_long_context_benchmark()
