
import sys
import os

# Add the current directory to sys.path so we can import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.digest_service import generate_digest
import time

def test_digest():
    print("Starting digest generation test...")
    start_time = time.time()
    
    try:
        result = generate_digest()
        end_time = time.time()
        
        print("\n" + "="*50)
        print(f"Digest generated successfully in {end_time - start_time:.2f} seconds")
        print("="*50)
        print(f"Article Count: {result.get('article_count')}")
        print(f"Sources: {result.get('sources')}")
        print("\nDigest Content Preview:")
        print("-" * 20)
        print(result.get('digest', '')[:500] + "...")
        print("-" * 20)
        
    except Exception as e:
        print(f"\nERROR: Failed to generate digest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_digest()
