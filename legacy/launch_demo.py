#!/usr/bin/env python3
"""
Celebrity Face Match - Demo Launcher
Choose which version to run!
"""
import sys
import subprocess

def main():
    print("="*70)
    print("🎭 CELEBRITY FACE MATCH - DEMO LAUNCHER")
    print("="*70)
    print()
    print("Choose which demo to run:")
    print()
    print("  1. 📸 Static Upload Demo (app.py)")
    print("     - Upload photos or use webcam snapshot")
    print("     - Shows top 5 matches")
    print("     - Good for testing with existing photos")
    print()
    print("  2. 📹 LIVE Webcam Demo (app_live.py) ⭐ WOW FACTOR!")
    print("     - Real-time reactive face detection")
    print("     - Automatic matching as you move")
    print("     - Perfect for impressive customer demos!")
    print()
    print("  3. 🔧 Register Custom Face (register_face.py)")
    print("     - Add your friends/custom faces to database")
    print("     - Upload or webcam capture")
    print("     - Immediate registration to vector DB")
    print()
    print("  4. All demos (separate ports)")
    print()

    choice = input("Enter choice (1, 2, 3, or 4): ").strip()
    
    print()
    print("="*70)
    
    if choice == "1":
        print("🚀 Launching Static Upload Demo...")
        print("🌐 Opening on http://localhost:7860")
        print("="*70)
        subprocess.run([sys.executable, "app.py"])
    
    elif choice == "2":
        print("🚀 Launching LIVE Webcam Demo...")
        print("🌐 Opening on http://localhost:7860")
        print("="*70)
        subprocess.run([sys.executable, "app_live.py"])

    elif choice == "3":
        print("🚀 Launching Register Custom Face Admin UI...")
        print("🌐 Opening on http://localhost:7862")
        print("="*70)
        subprocess.run([sys.executable, "register_face.py"])

    elif choice == "4":
        print("🚀 Launching ALL demos...")
        print("📸 Static Demo: http://localhost:7860")
        print("📹 Live Demo: http://localhost:7861")
        print("🔧 Register Face: http://localhost:7862")
        print("="*70)

        import multiprocessing

        def run_static():
            subprocess.run([sys.executable, "app.py"])

        def run_live():
            # Modify port for second instance
            import app_live
            app_live.demo.launch(server_port=7861, share=False)

        def run_register():
            subprocess.run([sys.executable, "register_face.py"])

        p1 = multiprocessing.Process(target=run_static)
        p2 = multiprocessing.Process(target=run_live)
        p3 = multiprocessing.Process(target=run_register)

        p1.start()
        p2.start()
        p3.start()

        try:
            p1.join()
            p2.join()
            p3.join()
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down demos...")
            p1.terminate()
            p2.terminate()
            p3.terminate()

    else:
        print("❌ Invalid choice. Please run again and choose 1, 2, 3, or 4.")
        sys.exit(1)

if __name__ == "__main__":
    main()

