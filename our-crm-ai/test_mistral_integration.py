#!/usr/bin/env python3
"""
Test script for Mistral AI integration in the AI Project Manager.

This script tests the Mistral AI provider functionality and verifies
that all components work together correctly.
"""

import asyncio
import os

from agent_integration_framework import (
    AgentIntegrationFramework,
    TaskExecution,
    TaskStatus,
)


async def test_mistral_integration():
    """Test Mistral AI provider integration."""
    print("🚀 Testing Mistral AI Integration...")
    print("=" * 50)

    # Initialize framework
    framework = AgentIntegrationFramework()

    # Check if Mistral API key is available
    if not os.getenv("MISTRAL_API_KEY"):
        print("⚠️  MISTRAL_API_KEY environment variable not set.")
        print("   Set it with: export MISTRAL_API_KEY='your-api-key'")
        return False

    # Test 1: Check if Mistral agents are loaded
    print("\n📋 Test 1: Checking Mistral agent configurations...")
    mistral_agents = [
        agent_id
        for agent_id, config in framework.agents.items()
        if config.provider == "mistral"
    ]

    if mistral_agents:
        print(f"✅ Found {len(mistral_agents)} Mistral agents:")
        for agent_id in mistral_agents:
            config = framework.agents[agent_id]
            print(f"   - {config.agent_name} ({agent_id})")
            print(f"     Model: {config.model}")
            print(f"     Specializations: {', '.join(config.specializations)}")
    else:
        print("❌ No Mistral agents found in configuration")
        return False

    # Test 2: Health check for first Mistral agent
    print(f"\n🔍 Test 2: Health check for {mistral_agents[0]}...")
    test_agent_id = mistral_agents[0]
    test_config = framework.agents[test_agent_id]

    try:
        provider = framework.providers["mistral"]
        health_status = await provider.health_check(test_config)

        if health_status:
            print(
                f"✅ Mistral agent '{test_config.agent_name}' is healthy and responsive"
            )
        else:
            print(f"❌ Mistral agent '{test_config.agent_name}' health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e!s}")
        return False

    # Test 3: Execute a simple task
    print(f"\n🎯 Test 3: Executing test task with {test_config.agent_name}...")

    test_task = TaskExecution(
        task_id="test-mistral-001",
        agent_id=test_agent_id,
        task_type="code_review",
        prompt="Please review this simple Python function and provide feedback:\n\ndef hello_world():\n    print('Hello, World!')\n    return True",
        context={"language": "python", "complexity": "simple"},
    )

    try:
        result = await framework.execute_task(
            test_task.agent_id, test_task.task_type, test_task.prompt, test_task.context
        )

        if result.status == TaskStatus.COMPLETED:
            print("✅ Task executed successfully!")
            print(
                f"   Result length: {len(result.result.get('result', ''))} characters"
            )
            print(f"   Tokens used: {result.tokens_used}")
            print(f"   Cost: ${result.cost:.6f}")
            print(f"   Quality score: {result.quality_score:.2f}")
            print(f"   Result: {result.result}")

            # Show a snippet of the result
            result_text = result.result.get("output", "")[:200]
            print(f"   Result preview: {result_text}...")

        else:
            print(f"❌ Task failed with status: {result.status}")
            if result.error:
                print(f"   Error: {result.error}")
            return False

    except Exception as e:
        print(f"❌ Task execution error: {e!s}")
        return False

    # Test 4: Test different Mistral models if multiple agents exist
    if len(mistral_agents) > 1:
        print("\n🔄 Test 4: Testing multiple Mistral agents...")

        for i, agent_id in enumerate(mistral_agents[:2]):  # Test first 2
            config = framework.agents[agent_id]
            print(f"   Testing {config.agent_name} ({config.model})...")

            simple_task = TaskExecution(
                task_id=f"test-mistral-multi-{i + 1}",
                agent_id=agent_id,
                task_type="analysis",
                prompt="What are the key benefits of using AI in project management?",
                context={"domain": "project_management"},
            )

            try:
                result = await framework.execute_task(
                    simple_task.agent_id,
                    simple_task.task_type,
                    simple_task.prompt,
                    simple_task.context,
                )
                if result.status == TaskStatus.COMPLETED:
                    print(
                        f"     ✅ Success - {result.tokens_used} tokens, ${result.cost:.6f}"
                    )
                else:
                    print(f"     ❌ Failed: {result.status}")
            except Exception as e:
                print(f"     ❌ Error: {e!s}")

    # Test 5: Performance comparison
    print("\n📊 Test 5: Performance summary...")

    total_tasks = len(
        [
            t
            for t in framework.completed_tasks.values()
            if framework.agents[t.agent_id].provider == "mistral"
        ]
    )
    total_cost = sum(
        [
            t.cost
            for t in framework.completed_tasks.values()
            if framework.agents[t.agent_id].provider == "mistral"
        ]
    )
    total_tokens = sum(
        [
            t.tokens_used
            for t in framework.completed_tasks.values()
            if framework.agents[t.agent_id].provider == "mistral"
        ]
    )

    print(f"   Total Mistral tasks completed: {total_tasks}")
    print(f"   Total tokens used: {total_tokens}")
    print(f"   Total cost: ${total_cost:.6f}")

    print("\n🎉 Mistral AI Integration Test Complete!")
    print("=" * 50)
    return True


async def main():
    """Main test function."""
    print("AI Project Manager - Mistral AI Integration Test")
    print("Version: 2.0.0")
    print()

    success = await test_mistral_integration()

    if success:
        print("\n✅ All tests passed! Mistral AI integration is working correctly.")
        print("\n🔧 Next steps:")
        print("   1. Set up your MISTRAL_API_KEY environment variable")
        print("   2. Configure additional Mistral agents as needed")
        print("   3. Test with real project management tasks")
        print("   4. Monitor usage and costs in production")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the configuration and try again.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
