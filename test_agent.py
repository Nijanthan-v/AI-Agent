from agent import run_agent

def test_dynamic_agent_run():
    print("--- Testing Dynamic UI Payload for Alex Rivera ---")
    
    # Dynamic payload from UI team
    dynamic_payload = {
        "user_id": "usr_alex_01",
        "user_email": "alex@techcorp.io",
        "stripe_customer_id": "cus_stripe_alex123",
        "issue_description": "Paid for Pro Tier 2 hours ago ($29.00). Card charged. Account still locked on Free tier. Trace ID: tr_webhook_err_901."
    }
    
    result = run_agent(dynamic_payload)
    
    print(f"\nStatus: {result['status']}")
    print(f"Audit Passed: {result['audit_passed']}")
    print(f"Proposed Action: {result['proposed_action']}")
    print(f"Root Cause: {result['root_cause']}")
    print(f"\n💌 Dynamic Customer Response Message:")
    print(f"\"{result['customer_response_message']}\"")
    
    print("\nThought Process:")
    for t in result["thought_process"]:
        print(f"  {t}")

if __name__ == "__main__":
    test_dynamic_agent_run()
