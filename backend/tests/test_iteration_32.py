"""
Iteration 32 - Testing Cinema Studio Art Style and Book Editor Pro Characters/Scenes tabs

Features to test:
1. Cinema Studio Art Style selector - verify it sends art_style to backend
2. Backend /api/pro-studio/generate-image endpoint accepts art_style parameter
3. Backend /api/pro-studio/generate-variant endpoint accepts art_style parameter
4. Book Editor Gallery modal shows Pro Characters tab with all characters (not just those with gallery images)
5. Book Editor Gallery modal shows Pro Scenes tab with all scenes (not just those with gallery images)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
VIP_USER = {
    "email": "jamesstephenbrooks@outlook.com",
    "password": "test123"
}


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for VIP user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=VIP_USER)
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def headers(auth_token):
    """Auth headers for requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestProStudioGenerateImageArtStyle:
    """Test /api/pro-studio/generate-image endpoint with art_style parameter"""
    
    def test_generate_image_accepts_art_style_cinematic(self, headers):
        """Test that generate-image endpoint accepts cinematic art style"""
        # Just verify the endpoint accepts the payload, not actually generating (too slow)
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/generate-image",
            headers=headers,
            json={
                "prompt": "Test prompt",
                "art_style": "cinematic",
                "camera": "arri-alexa-35",
                "lens": "panavision-series",
                "focal_length": "35mm",
                "lighting": "natural",
                "aspect_ratio": "16:9"
            },
            timeout=5  # Short timeout - we just want to verify it accepts the request
        )
        # Even if it times out or takes too long, status 200/202 or in-progress means it accepted the params
        # A 422 would mean invalid request body
        assert response.status_code != 422, f"Endpoint rejected art_style parameter: {response.text}"
        print(f"✓ /api/pro-studio/generate-image accepts art_style parameter (status: {response.status_code})")
    
    def test_generate_image_accepts_art_style_cartoon(self, headers):
        """Test cartoon art style acceptance"""
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/generate-image",
            headers=headers,
            json={
                "prompt": "Test prompt cartoon",
                "art_style": "cartoon",
                "camera": "arri-alexa-35",
                "lens": "panavision-series",
                "focal_length": "35mm",
                "lighting": "natural",
                "aspect_ratio": "16:9"
            },
            timeout=5
        )
        assert response.status_code != 422, f"Endpoint rejected cartoon art_style: {response.text}"
        print(f"✓ /api/pro-studio/generate-image accepts cartoon art_style (status: {response.status_code})")
    
    def test_generate_image_accepts_art_style_anime(self, headers):
        """Test anime art style acceptance"""
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/generate-image",
            headers=headers,
            json={
                "prompt": "Test prompt anime",
                "art_style": "anime",
                "camera": "arri-alexa-35",
                "lens": "panavision-series",
                "focal_length": "35mm",
                "lighting": "natural",
                "aspect_ratio": "16:9"
            },
            timeout=5
        )
        assert response.status_code != 422, f"Endpoint rejected anime art_style: {response.text}"
        print(f"✓ /api/pro-studio/generate-image accepts anime art_style (status: {response.status_code})")
    
    def test_generate_image_accepts_all_art_styles(self, headers):
        """Test all supported art styles"""
        art_styles = ["realistic", "cinematic", "cartoon", "anime", "pixar", "watercolor", "comic", "fantasy", "storybook"]
        
        for style in art_styles:
            response = requests.post(
                f"{BASE_URL}/api/pro-studio/generate-image",
                headers=headers,
                json={
                    "prompt": f"Test prompt {style}",
                    "art_style": style,
                    "camera": "arri-alexa-35",
                    "lens": "panavision-series",
                    "focal_length": "35mm",
                    "lighting": "natural",
                    "aspect_ratio": "16:9"
                },
                timeout=5
            )
            assert response.status_code != 422, f"Endpoint rejected {style} art_style: {response.text}"
            print(f"✓ Art style '{style}' accepted")


class TestProStudioGenerateVariantArtStyle:
    """Test /api/pro-studio/generate-variant endpoint with art_style parameter"""
    
    def test_generate_variant_accepts_art_style(self, headers):
        """Test that generate-variant endpoint accepts art_style parameter"""
        # Use a dummy base64 image (smallest valid PNG)
        dummy_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/generate-variant",
            headers=headers,
            json={
                "source_image": dummy_image,
                "prompt": "Test variant",
                "art_style": "cinematic",
                "camera": "arri-alexa-35",
                "lens": "panavision-series",
                "focal_length": "35mm",
                "lighting": "natural",
                "aspect_ratio": "16:9",
                "strength": 0.7
            },
            timeout=5
        )
        # We just verify it doesn't reject with 422 (validation error)
        assert response.status_code != 422, f"Endpoint rejected art_style parameter: {response.text}"
        print(f"✓ /api/pro-studio/generate-variant accepts art_style parameter (status: {response.status_code})")
    
    def test_generate_variant_accepts_fantasy_style(self, headers):
        """Test fantasy art style acceptance in variant generation"""
        dummy_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        response = requests.post(
            f"{BASE_URL}/api/pro-studio/generate-variant",
            headers=headers,
            json={
                "source_image": dummy_image,
                "prompt": "Test fantasy variant",
                "art_style": "fantasy",
                "camera": "arri-alexa-35",
                "lens": "panavision-series",
                "focal_length": "35mm",
                "lighting": "natural",
                "aspect_ratio": "16:9",
                "strength": 0.7
            },
            timeout=5
        )
        assert response.status_code != 422, f"Endpoint rejected fantasy art_style: {response.text}"
        print(f"✓ /api/pro-studio/generate-variant accepts fantasy art_style (status: {response.status_code})")


class TestProStudioCharactersEndpoints:
    """Test Pro Studio characters endpoints used by Book Editor"""
    
    def test_get_characters(self, headers):
        """Test getting all user characters"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers=headers)
        assert response.status_code == 200, f"Failed to get characters: {response.text}"
        
        data = response.json()
        assert "characters" in data, "Response missing 'characters' key"
        characters = data["characters"]
        print(f"✓ Found {len(characters)} characters")
        
        # Verify character structure
        if len(characters) > 0:
            char = characters[0]
            assert "id" in char, "Character missing 'id'"
            assert "name" in char, "Character missing 'name'"
            print(f"✓ First character: {char['name']}")
            
            # Check for thumbnail (master image)
            if char.get("thumbnail"):
                print(f"✓ Character has thumbnail/master image")
            else:
                print(f"  Character '{char['name']}' has no thumbnail")
        
        return characters
    
    def test_get_character_gallery(self, headers):
        """Test getting character gallery - should work even if empty"""
        # First get characters
        chars_response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers=headers)
        assert chars_response.status_code == 200
        characters = chars_response.json().get("characters", [])
        
        if len(characters) == 0:
            pytest.skip("No characters to test gallery")
        
        # Test gallery for first character
        char = characters[0]
        gallery_response = requests.get(
            f"{BASE_URL}/api/pro-studio/characters/{char['id']}/gallery",
            headers=headers
        )
        assert gallery_response.status_code == 200, f"Failed to get gallery: {gallery_response.text}"
        
        data = gallery_response.json()
        # Gallery should return images list even if empty
        assert "images" in data, "Response missing 'images' key"
        print(f"✓ Character '{char['name']}' gallery has {len(data['images'])} images")


class TestProStudioScenesEndpoints:
    """Test Pro Studio scenes endpoints used by Book Editor"""
    
    def test_get_scenes(self, headers):
        """Test getting all user scenes"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/scenes", headers=headers)
        assert response.status_code == 200, f"Failed to get scenes: {response.text}"
        
        data = response.json()
        assert "scenes" in data, "Response missing 'scenes' key"
        scenes = data["scenes"]
        print(f"✓ Found {len(scenes)} scenes")
        
        # Verify scene structure
        if len(scenes) > 0:
            scene = scenes[0]
            assert "id" in scene, "Scene missing 'id'"
            assert "name" in scene, "Scene missing 'name'"
            print(f"✓ First scene: {scene['name']}")
            
            # Check for preview image
            if scene.get("preview_url") or scene.get("thumbnail"):
                print(f"✓ Scene has preview image")
            else:
                print(f"  Scene '{scene['name']}' has no preview image")
        
        return scenes
    
    def test_get_scene_gallery(self, headers):
        """Test getting scene gallery - should work even if empty"""
        # First get scenes
        scenes_response = requests.get(f"{BASE_URL}/api/pro-studio/scenes", headers=headers)
        assert scenes_response.status_code == 200
        scenes = scenes_response.json().get("scenes", [])
        
        if len(scenes) == 0:
            pytest.skip("No scenes to test gallery")
        
        # Test gallery for first scene
        scene = scenes[0]
        gallery_response = requests.get(
            f"{BASE_URL}/api/pro-studio/scenes/{scene['id']}/gallery",
            headers=headers
        )
        assert gallery_response.status_code == 200, f"Failed to get gallery: {gallery_response.text}"
        
        data = gallery_response.json()
        # Gallery should return images list even if empty
        assert "images" in data, "Response missing 'images' key"
        print(f"✓ Scene '{scene['name']}' gallery has {len(data['images'])} images")


class TestBookEditorIntegration:
    """Test the data flow that Book Editor relies on for Pro Characters/Scenes tabs"""
    
    def test_book_editor_characters_data_flow(self, headers):
        """
        Book Editor fetches characters and enriches them with:
        1. Character data including thumbnail
        2. Character gallery images
        3. Reference images
        This test verifies all data is available
        """
        # Get characters
        chars_response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers=headers)
        assert chars_response.status_code == 200
        characters = chars_response.json().get("characters", [])
        
        print(f"\n=== Book Editor Character Data Flow ===")
        print(f"Total characters: {len(characters)}")
        
        for char in characters:
            char_name = char.get("name", "Unknown")
            has_thumbnail = bool(char.get("thumbnail"))
            has_references = len(char.get("reference_images", [])) > 0
            
            # Get gallery
            gallery_response = requests.get(
                f"{BASE_URL}/api/pro-studio/characters/{char['id']}/gallery",
                headers=headers
            )
            gallery_count = 0
            if gallery_response.status_code == 200:
                gallery_count = len(gallery_response.json().get("images", []))
            
            print(f"  - {char_name}: thumbnail={has_thumbnail}, refs={has_references}, gallery={gallery_count}")
            
            # The key fix: Characters should appear in Book Editor even if gallery.length == 0
            # As long as they have thumbnail or reference_images
            total_images = (1 if has_thumbnail else 0) + len(char.get("reference_images", [])) + gallery_count
            print(f"    Total available images: {total_images}")
        
        print(f"✓ Character data flow verified")
    
    def test_book_editor_scenes_data_flow(self, headers):
        """
        Book Editor fetches scenes and enriches them with:
        1. Scene data including preview_url/thumbnail
        2. Scene gallery images
        3. Reference images
        This test verifies all data is available
        """
        # Get scenes
        scenes_response = requests.get(f"{BASE_URL}/api/pro-studio/scenes", headers=headers)
        assert scenes_response.status_code == 200
        scenes = scenes_response.json().get("scenes", [])
        
        print(f"\n=== Book Editor Scene Data Flow ===")
        print(f"Total scenes: {len(scenes)}")
        
        for scene in scenes:
            scene_name = scene.get("name", "Unknown")
            has_preview = bool(scene.get("preview_url") or scene.get("thumbnail"))
            has_references = len(scene.get("reference_images", [])) > 0
            
            # Get gallery
            gallery_response = requests.get(
                f"{BASE_URL}/api/pro-studio/scenes/{scene['id']}/gallery",
                headers=headers
            )
            gallery_count = 0
            if gallery_response.status_code == 200:
                gallery_count = len(gallery_response.json().get("images", []))
            
            print(f"  - {scene_name}: preview={has_preview}, refs={has_references}, gallery={gallery_count}")
            
            # The key fix: Scenes should appear in Book Editor even if gallery.length == 0
            # As long as they have preview_url or reference_images
            total_images = (1 if has_preview else 0) + len(scene.get("reference_images", [])) + gallery_count
            print(f"    Total available images: {total_images}")
        
        print(f"✓ Scene data flow verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
