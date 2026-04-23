#!/usr/bin/env python3
"""
Implementation Status Checker
Verifies all required features are implemented
"""

import os
import sys
import importlib.util

def check_file_exists(filepath: str) -> bool:
    """Check if file exists"""
    return os.path.exists(filepath)

def check_function_in_file(filepath: str, function_name: str) -> bool:
    """Check if function exists in file"""
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            # For React client, check for both variable names and usage
            if filepath.startswith("simple-react-client"):
                if function_name == "conversationLog":
                    return "conversationLog" in content and "setConversationLog" in content
                elif function_name == "intentLog":
                    return "intentLog" in content and "setIntentLog" in content
                elif function_name in ["user_speech_text", "ai_speech_text", "ai_intent"]:
                    return f"'{function_name}'" in content or f'"{function_name}"' in content
            return function_name in content
    except:
        return False

def check_implementation_status():
    """Check implementation status of all features"""
    print("🔍 CHECKING IMPLEMENTATION STATUS")
    print("=" * 60)
    
    status = {}
    
    # 1. Check server files
    print("\n📁 SERVER FILES:")
    server_files = [
        "src/main.py",
        "src/tools/static_data_loader.py", 
        "src/tools/smart_action_executor.py",
        "src/tools/conversation_tracker.py",
        "src/pipecat_bot/conversation_handler.py",
        "src/pipecat_bot/bot_runner.py"
    ]
    
    for file in server_files:
        exists = check_file_exists(file)
        status[file] = exists
        print(f"  {'✅' if exists else '❌'} {file}")
    
    # 2. Check SSE endpoints
    print("\n📡 SSE ENDPOINTS:")
    sse_endpoints = [
        ("/navigation/stream", "navigation_stream"),
        ("/navigation/command", "receive_navigation_command"),
        ("/conversation/event", "receive_conversation_event"),
        ("/ai/data", "ai_data_ingress")
    ]
    
    main_py_content = ""
    if os.path.exists("src/main.py"):
        with open("src/main.py", 'r') as f:
            main_py_content = f.read()
    
    for endpoint, function in sse_endpoints:
        exists = function in main_py_content
        status[f"endpoint_{endpoint}"] = exists
        print(f"  {'✅' if exists else '❌'} {endpoint} ({function})")
    
    # 3. Check tool methods
    print("\n🛠️ TOOL METHODS:")
    tool_methods = [
        ("src/tools/static_data_loader.py", "send_static_data_via_sse"),
        ("src/tools/smart_action_executor.py", "generate_and_send_intent"),
        ("src/tools/smart_action_executor.py", "create_action_command"),
        ("src/tools/conversation_tracker.py", "process_user_speech"),
        ("src/tools/conversation_tracker.py", "process_ai_speech"),
        ("src/pipecat_bot/conversation_handler.py", "handle_transcription"),
        ("src/pipecat_bot/conversation_handler.py", "handle_tts_speak")
    ]
    
    for file, method in tool_methods:
        exists = check_function_in_file(file, method)
        status[f"method_{method}"] = exists
        print(f"  {'✅' if exists else '❌'} {method} in {file}")
    
    # 4. Check React client features
    print("\n⚛️ REACT CLIENT:")
    client_features = [
        ("simple-react-client/src/App.js", "conversationLog"),
        ("simple-react-client/src/App.js", "intentLog"),
        ("simple-react-client/src/App.js", "user_speech_text"),
        ("simple-react-client/src/App.js", "ai_speech_text"),
        ("simple-react-client/src/App.js", "ai_intent")
    ]
    
    for file, feature in client_features:
        exists = check_function_in_file(file, feature)
        status[f"client_{feature}"] = exists
        print(f"  {'✅' if exists else '❌'} {feature} in {file}")
    
    # 5. Check test files
    print("\n🧪 TEST FILES:")
    test_files = [
        "test/test_auth_complete.py",
        "test/test_sse_complete.py", 
        "test/run_all_tests.py",
        "test/quick_test.py"
    ]
    
    for file in test_files:
        exists = check_file_exists(file)
        status[f"test_{file}"] = exists
        print(f"  {'✅' if exists else '❌'} {file}")
    
    # 6. Check hash-based intent system
    print("\n🎯 HASH-BASED INTENT SYSTEM:")
    hash_features = [
        ("src/tools/smart_action_executor.py", "_get_element_hash"),
        ("src/tools/smart_action_executor.py", "Dashboard-GoToDashboard-1.0"),
        ("simple-react-client/src/App.js", "ai_intent")
    ]
    
    for file, feature in hash_features:
        exists = check_function_in_file(file, feature)
        status[f"hash_{feature}"] = exists
        print(f"  {'✅' if exists else '❌'} {feature} in {file}")
    
    # 7. Summary
    print("\n📊 SUMMARY:")
    total_checks = len(status)
    passed_checks = sum(status.values())
    
    print(f"  Total checks: {total_checks}")
    print(f"  Passed: {passed_checks}")
    print(f"  Failed: {total_checks - passed_checks}")
    print(f"  Success rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 ALL FEATURES IMPLEMENTED!")
        return True
    else:
        print(f"\n❌ {total_checks - passed_checks} FEATURES MISSING!")
        
        # Show failed checks
        print("\nFAILED CHECKS:")
        for check, passed in status.items():
            if not passed:
                print(f"  ❌ {check}")
        
        return False

if __name__ == "__main__":
    success = check_implementation_status()
    sys.exit(0 if success else 1)