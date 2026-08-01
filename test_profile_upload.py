#!/usr/bin/env python3
"""
Test script to verify profile picture upload functionality.
Run this to diagnose any issues with the upload system.
"""

import os
import sys
import tempfile
from PIL import Image
from io import BytesIO

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

def test_folder_creation():
    """Test if profile_pictures folder can be created."""
    print("🧪 Test 1: Folder Creation")
    print("-" * 50)
    
    upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    profile_pics_folder = os.path.join(upload_folder, 'profile_pictures')
    
    print(f"Upload folder: {upload_folder}")
    print(f"Profile pics folder: {profile_pics_folder}")
    print(f"Upload folder exists: {os.path.exists(upload_folder)}")
    print(f"Profile pics folder exists: {os.path.exists(profile_pics_folder)}")
    
    try:
        os.makedirs(profile_pics_folder, exist_ok=True)
        print("✓ Successfully created profile_pictures folder")
        return True
    except Exception as e:
        print(f"✗ Error creating folder: {str(e)}")
        return False

def test_file_write():
    """Test if files can be written to the profile_pictures folder."""
    print("\n🧪 Test 2: File Write")
    print("-" * 50)
    
    upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    profile_pics_folder = os.path.join(upload_folder, 'profile_pictures')
    
    try:
        # Create a simple test image
        test_file_path = os.path.join(profile_pics_folder, 'test_upload.txt')
        with open(test_file_path, 'w') as f:
            f.write('Test file for profile picture upload\n')
        
        file_exists = os.path.exists(test_file_path)
        print(f"Test file path: {test_file_path}")
        print(f"Test file exists: {file_exists}")
        
        if file_exists:
            print("✓ Successfully wrote test file")
            os.remove(test_file_path)
            print("✓ Successfully deleted test file")
            return True
        else:
            print("✗ Test file was not created")
            return False
            
    except Exception as e:
        print(f"✗ Error writing file: {str(e)}")
        return False

def test_image_creation():
    """Test if PIL can create images."""
    print("\n🧪 Test 3: Image Creation with PIL")
    print("-" * 50)
    
    try:
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        
        upload_folder = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
        profile_pics_folder = os.path.join(upload_folder, 'profile_pictures')
        test_image_path = os.path.join(profile_pics_folder, 'test_image.png')
        
        img.save(test_image_path)
        
        if os.path.exists(test_image_path):
            file_size = os.path.getsize(test_image_path)
            print(f"✓ Successfully created test image")
            print(f"  Image path: {test_image_path}")
            print(f"  File size: {file_size} bytes")
            os.remove(test_image_path)
            return True
        else:
            print("✗ Test image was not created")
            return False
            
    except Exception as e:
        print(f"✗ Error creating image: {str(e)}")
        return False

def test_werkzeug_imports():
    """Test if required imports are available."""
    print("\n🧪 Test 4: Werkzeug Imports")
    print("-" * 50)
    
    try:
        from werkzeug.utils import secure_filename
        print("✓ Successfully imported secure_filename from werkzeug")
        
        # Test secure_filename
        test_names = [
            "profile_1_1234567890.jpg",
            "../../../etc/passwd.jpg",
            "file with spaces.jpg",
            "file-with-dashes.jpg"
        ]
        
        for name in test_names:
            secure = secure_filename(name)
            print(f"  secure_filename('{name}') = '{secure}'")
        
        return True
    except Exception as e:
        print(f"✗ Error importing werkzeug: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Profile Picture Upload - Diagnostic Tests")
    print("=" * 50)
    
    results = []
    
    results.append(("Folder Creation", test_folder_creation()))
    results.append(("File Write", test_file_write()))
    results.append(("Image Creation", test_image_creation()))
    results.append(("Werkzeug Imports", test_werkzeug_imports()))
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Profile picture upload should work.")
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check the errors above.")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
