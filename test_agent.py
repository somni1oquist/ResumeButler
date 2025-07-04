#!/usr/bin/env python3
"""
Test script for Resume Butler Agent functionality
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat import get_agent, user_profile
from agent import ResumeButlerAgent
from user_profile import UserProfile
from semantic_kernel.contents import ChatHistory

async def test_agent_functionality():
    """Test the agent functionality without Azure credentials"""
    print("🧪 Testing Resume Butler Agent...")
    
    # Test 1: Profile initialization
    print("\n1. Testing profile initialization...")
    profile = UserProfile()
    print(f"   ✓ Profile completion: {profile.get_completion_percentage():.1f}%")
    print(f"   ✓ Missing fields: {profile.get_missing_essential_fields()}")
    print(f"   ✓ Ready for generation: {profile.is_ready_for_generation()}")
    
    # Test 2: Agent initialization
    print("\n2. Testing agent initialization...")
    agent = get_agent()
    if agent:
        print("   ✓ Agent initialized successfully")
    else:
        print("   ✗ Agent not initialized (expected without Azure credentials)")
        return
    
    # Test 3: Information parsing
    print("\n3. Testing information parsing...")
    test_message = "Hi, my name is John Doe and my email is john.doe@example.com"
    parsed = agent.parse_user_information(test_message)
    print(f"   ✓ Parsed info: {parsed}")
    
    # Test 4: Profile updates
    print("\n4. Testing profile updates...")
    agent.update_profile_from_message(test_message)
    print(f"   ✓ Name: {agent.user_profile.name}")
    print(f"   ✓ Email: {agent.user_profile.email}")
    print(f"   ✓ Profile completion: {agent.user_profile.get_completion_percentage():.1f}%")
    
    # Test 5: Export functionality
    print("\n5. Testing export functionality...")
    try:
        from export import ResumeExporter
        exporter = ResumeExporter()
        
        sample_resume = """# John Doe
        
**Contact Information**
- Email: john.doe@example.com
- Phone: (555) 123-4567

## Professional Summary
Experienced software developer with 5+ years in web development.

## Experience
### Senior Developer | Tech Corp | 2020-Present
- Developed web applications using Python and JavaScript
- Led team of 3 developers

## Skills
- Python, JavaScript, React, Node.js
"""
        
        # Test Markdown export
        md_path, md_content = exporter.export_markdown(sample_resume)
        print(f"   ✓ Markdown export: {len(md_content)} characters")
        
        # Test HTML export
        html_path, html_content = exporter.export_html(sample_resume)
        print(f"   ✓ HTML export: {len(html_content)} characters")
        
        # Test DOCX export
        docx_result = exporter.export_docx(sample_resume)
        if docx_result:
            print(f"   ✓ DOCX export successful")
        else:
            print(f"   ⚠ DOCX export failed (dependencies missing)")
            
        exporter.cleanup()
        
    except Exception as e:
        print(f"   ✗ Export test failed: {e}")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_agent_functionality())