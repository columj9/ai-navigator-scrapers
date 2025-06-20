"""
Fix Combined FutureTools File and Process All Tools
"""

import json
import sys
sys.path.append('/app')

def fix_combined_file():
    """Fix the combined JSONL file format"""
    
    print("🔧 Fixing combined FutureTools file format...")
    
    # Read the problematic file
    input_file = '/app/ai-navigator-scrapers/futuretools_combined_all.jsonl'
    output_file = '/app/ai-navigator-scrapers/futuretools_fixed_all.jsonl'
    
    tools = []
    seen_tools = set()
    
    try:
        with open(input_file, 'r') as f:
            content = f.read()
            
        # Split by }\n{ pattern to separate JSON objects
        json_strings = content.replace('}\n{', '}|||{').split('|||')
        
        for i, json_str in enumerate(json_strings):
            try:
                # Clean up the JSON string
                json_str = json_str.strip().rstrip('\n')
                
                # Parse JSON
                tool = json.loads(json_str)
                
                # Check for duplicates
                tool_key = f"{tool['tool_name_on_directory']}:{tool['external_website_url']}"
                if tool_key not in seen_tools:
                    seen_tools.add(tool_key)
                    tools.append(tool)
                    
            except json.JSONDecodeError as e:
                print(f"   ⚠️ Skipping invalid JSON on entry {i+1}: {str(e)}")
                continue
        
        # Write fixed file
        with open(output_file, 'w') as f:
            for tool in tools:
                f.write(json.dumps(tool) + '\n')
        
        print(f"✅ Fixed file created: {output_file}")
        print(f"📊 Total unique tools: {len(tools)}")
        
        return output_file, len(tools)
        
    except Exception as e:
        print(f"❌ Error fixing file: {str(e)}")
        return None, 0

def main():
    """Main execution"""
    
    print("🚀 FIXING AND PROCESSING ALL FUTURETOOLS")
    print("=" * 50)
    
    # Fix the combined file
    fixed_file, count = fix_combined_file()
    
    if fixed_file and count > 0:
        print(f"\n🎉 Successfully fixed file with {count} unique tools!")
        print(f"📁 Fixed file: {fixed_file}")
        
        # Show sample tools
        print(f"\n📋 Sample tools:")
        with open(fixed_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 5:  # Show first 5
                    break
                tool = json.loads(line.strip())
                print(f"   {i+1}. {tool['tool_name_on_directory']} -> {tool['external_website_url']}")
        
        # Now we can process them with our enhanced system
        print(f"\n🚀 Ready to process {count} tools with comprehensive enhancement!")
        print(f"   • Use this file: {fixed_file}")
        print(f"   • Maximum data extraction")
        print(f"   • Clean URL processing")
        print(f"   • 100% logo coverage")
        
        return fixed_file
    else:
        print("❌ Failed to fix combined file")
        return None

if __name__ == "__main__":
    main()