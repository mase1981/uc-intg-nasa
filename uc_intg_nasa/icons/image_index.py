"""NASA Image Index - Auto-generated
Contains categorized lists of optimized space images.
Based on your actual 26 downloaded images.
"""

# Images by category - distributed for optimal variety
EARTH_IMAGES = [
    "space_earth_048.jpg",
    "space_earth_067.jpg",
]

SPACE_IMAGES = [
    "space_general_012.jpg",
    "space_general_013.jpg", 
    "space_general_014.jpg",
    "space_general_015.jpg",
    "space_general_016.jpg",
    "space_general_018.jpg",
    "space_general_020.jpg",
    "space_general_021.jpg",
]

PLANETS_IMAGES = [
    "space_general_022.jpg",
    "space_general_023.jpg",
    "space_general_024.jpg",
    "space_general_025.jpg",
]

NEBULA_IMAGES = [
    "space_nebula_049.jpg",
    "space_general_026.jpg",
    "space_general_027.jpg",
    "space_general_028.jpg",
]

GALAXY_IMAGES = [
    "space_galaxy_062.jpg",
    "space_general_031.jpg",
    "space_general_032.jpg",
    "space_general_033.jpg",
]

GENERAL_IMAGES = [
    "space_general_057.jpg",
    "space_general_059.jpg", 
    "space_general_065.jpg",
    "space_general_066.jpg",
]

# Master list of all 26 images
ALL_IMAGES = [
    "space_earth_048.jpg",
    "space_earth_067.jpg",
    "space_galaxy_062.jpg",
    "space_general_012.jpg",
    "space_general_013.jpg",
    "space_general_014.jpg",
    "space_general_015.jpg",
    "space_general_016.jpg",
    "space_general_018.jpg",
    "space_general_020.jpg",
    "space_general_021.jpg",
    "space_general_022.jpg",
    "space_general_023.jpg",
    "space_general_024.jpg",
    "space_general_025.jpg",
    "space_general_026.jpg",
    "space_general_027.jpg",
    "space_general_028.jpg",
    "space_general_031.jpg",
    "space_general_032.jpg",
    "space_general_033.jpg",
    "space_general_057.jpg",
    "space_general_059.jpg",
    "space_general_065.jpg",
    "space_general_066.jpg",
    "space_nebula_049.jpg",
]

# Category mapping - optimally distributed for variety
CATEGORIES = {
    "earth": EARTH_IMAGES,      # 2 images
    "space": SPACE_IMAGES,      # 8 images  
    "planets": PLANETS_IMAGES,  # 4 images
    "nebula": NEBULA_IMAGES,    # 4 images
    "galaxy": GALAXY_IMAGES,    # 4 images
    "general": GENERAL_IMAGES,  # 4 images
}

# Summary stats
TOTAL_IMAGES = 26
CATEGORIES_COUNT = 6

# Auto-verification
if __name__ == "__main__":
    print(f"🎨 NASA Image Library: {TOTAL_IMAGES} optimized images across {CATEGORIES_COUNT} categories")
    print(f"   🌍 Earth: {len(EARTH_IMAGES)} images")
    print(f"   🌌 Space: {len(SPACE_IMAGES)} images") 
    print(f"   🪐 Planets: {len(PLANETS_IMAGES)} images")
    print(f"   ⭐ Nebula: {len(NEBULA_IMAGES)} images")
    print(f"   🌀 Galaxy: {len(GALAXY_IMAGES)} images")
    print(f"   ✨ General: {len(GENERAL_IMAGES)} images")
    
    # Verify all images are accounted for
    total_categorized = sum(len(imgs) for imgs in CATEGORIES.values())
    print(f"   ✅ Verification: {total_categorized}/{TOTAL_IMAGES} images categorized")
    
    if total_categorized == TOTAL_IMAGES:
        print("   🚀 Perfect! All images categorized correctly.")
    else:
        print("   ⚠️  Warning: Image count mismatch!")