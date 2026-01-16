"""
Compare the three celebrity lists and show statistics.
"""
import json
from collections import Counter

def analyze_list(filepath: str):
    """Analyze a celebrity list file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total = len(data)
    
    # Count by source if available
    sources = Counter(item.get("source", "unknown") for item in data)
    
    # Sample names
    sample = data[:10] if len(data) >= 10 else data
    
    return {
        "total": total,
        "sources": dict(sources),
        "sample": [item["name"] for item in sample]
    }

def main():
    lists = {
        "Curated (Original)": "data/celebrities_seed.json",
        "Generated (Wikipedia)": "data/celebrities_generated.json",
        "Combined (Merged)": "data/celebrities_combined.json"
    }
    
    print("="*70)
    print("CELEBRITY LISTS COMPARISON")
    print("="*70)
    
    for name, filepath in lists.items():
        try:
            stats = analyze_list(filepath)
            print(f"\n📋 {name}")
            print(f"   File: {filepath}")
            print(f"   Total: {stats['total']:,} celebrities")
            
            if stats['sources'] and stats['sources'] != {'unknown': stats['total']}:
                print(f"   Sources:")
                for source, count in stats['sources'].items():
                    print(f"     - {source}: {count:,}")
            
            print(f"   Sample (first 10):")
            for i, celeb_name in enumerate(stats['sample'], 1):
                print(f"     {i:2d}. {celeb_name}")
                
        except FileNotFoundError:
            print(f"\n📋 {name}")
            print(f"   File: {filepath}")
            print(f"   ❌ File not found - run the generator first!")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS:")
    print("="*70)
    print("""
🎯 For Testing (Quick):
   Use: data/celebrities_seed.json
   Why: Smaller, curated list of popular celebrities
   
🚀 For Production (Recommended):
   Use: data/celebrities_combined.json
   Why: Maximum coverage with 2,659 unique celebrities
   
📊 For Wikipedia-Only:
   Use: data/celebrities_generated.json
   Why: All celebrities have Wikipedia pages (higher image success rate)
""")
    print("="*70)

if __name__ == "__main__":
    main()

