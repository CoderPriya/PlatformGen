"""Quick test script to verify the full workflow pipeline."""

import httpx
import json
import time
import sys

BASE = "http://localhost:8000"


def main():
    print("=== Multi-Agent SDLC Platform — Workflow Test ===\n")

    # Health check
    r = httpx.get(f"{BASE}/health")
    print(f"Health: {r.json()}\n")

    # Create workflow
    wf = httpx.post(f"{BASE}/api/workflows", json={
        "title": "Customer Onboarding Service",
        "project_name": "onboarding-svc",
        "business_brief": (
            "Build a customer onboarding microservice that collects KYC data, "
            "validates identity via a third-party API (Onfido), "
            "and sends welcome emails via SendGrid. Must be GDPR-compliant."
        ),
        "description": "POC test workflow",
    }).json()
    wf_id = wf["id"]
    print(f"Created workflow: {wf_id}")
    print(f"Status: {wf['status']}\n")

    # Run workflow
    run = httpx.post(f"{BASE}/api/workflows/{wf_id}/run").json()
    print(f"Triggered: {run['message']}\n")

    # Poll for completion
    print("Waiting for pipeline to complete...")
    for i in range(20):
        time.sleep(2)
        status = httpx.get(f"{BASE}/api/workflows/{wf_id}").json()
        stage = status["current_stage"]
        wf_status = status["status"]
        outputs = len(status["agent_outputs"])
        print(f"  [{i*2}s] status={wf_status} stage={stage} outputs={outputs}")
        if wf_status in ("completed", "failed"):
            break

    print(f"\n=== Final Result ===")
    print(f"Status: {status['status']}")
    print(f"Stage: {status['current_stage']}")
    print(f"Agent outputs: {len(status['agent_outputs'])}")
    print(f"Approval gates: {len(status['approval_gates'])}")
    print(f"Artifact stages: {list(status['artifacts'].keys())}")

    if status["agent_outputs"]:
        print(f"\nAgent Output Summary:")
        for o in status["agent_outputs"]:
            print(f"  - {o['agent_type']:20s} | confidence={o['confidence']:.2f} | {o['confidence_band']}")

    # Events
    events = httpx.get(f"{BASE}/api/events?workflow_id={wf_id}").json()
    print(f"\nEvents: {len(events)}")
    for e in events[:10]:
        print(f"  - {e['topic']:40s} | {e['source_agent']}")

    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main()
