"""
Test Suite for API Refactor Verification - Iteration 32
Tests that all frontend components using api.js correctly integrate with backend APIs.

The refactor moved 31 frontend files from direct fetch/axios calls to centralized api.js service.
This test verifies no regressions in:
- Authentication (login/register via api.js authAPI)
- Books CRUD (via api.js booksAPI)
- Pro Studio gallery (via api.js proStudioAPI)
- Art Studio (via api.js artStudioAPI)
- User profile operations (via api.js userAPI)
- Chapter and page CRUD (via api.js pagesAPI)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://blank-screen-debug-3.preview.emergentagent.com')

# Test credentials
VIP_EMAIL = "jamesstephenbrooks@outlook.com"
VIP_PASSWORD = "test123"


class TestAuthAPI:
    """Test authentication endpoints used by AuthContext.js via api.js authAPI"""
    
    def test_login_success(self):
        """Test POST /api/auth/login - used by authAPI.login()"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": VIP_EMAIL,
            "password": VIP_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure matches what AuthContext expects
        assert "access_token" in data, "Missing access_token in login response"
        assert "user" in data, "Missing user object in login response"
        assert data["user"]["email"] == VIP_EMAIL
        print(f"✓ Login successful - token: {data['access_token'][:20]}...")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code in [401, 404], "Invalid login should return 401 or 404"
        print("✓ Invalid login correctly rejected")
    
    def test_auth_me(self, auth_token):
        """Test GET /api/auth/me - used by authAPI.me() to verify session"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Auth me failed: {response.text}"
        data = response.json()
        assert "email" in data
        assert data["email"] == VIP_EMAIL
        print(f"✓ Auth me successful - user: {data['email']}")


class TestBooksAPI:
    """Test book-related endpoints used by Library.js, BookEditor.js via api.js booksAPI"""
    
    def test_get_books_public(self):
        """Test GET /api/books - used by booksAPI.getAll() in Library.js"""
        response = requests.get(f"{BASE_URL}/api/books", params={
            "published_only": "true",
            "limit": "10"
        })
        
        assert response.status_code == 200, f"Get books failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Books should be a list"
        print(f"✓ Public books fetched - count: {len(data)}")
    
    def test_get_featured_books(self):
        """Test GET /api/books/featured - used in Library.js"""
        response = requests.get(f"{BASE_URL}/api/books/featured")
        
        assert response.status_code == 200, f"Get featured books failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Featured books fetched - count: {len(data)}")
    
    def test_get_genres(self):
        """Test GET /api/genres - used in Library.js filters"""
        response = requests.get(f"{BASE_URL}/api/genres")
        
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert isinstance(data["genres"], list)
        assert len(data["genres"]) > 0
        print(f"✓ Genres fetched - count: {len(data['genres'])}")
    
    def test_get_my_books(self, auth_token):
        """Test GET /api/books/my - used by booksAPI.getMy() in Dashboard"""
        response = requests.get(f"{BASE_URL}/api/books/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Get my books failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ User's books fetched - count: {len(data)}")
        return data
    
    def test_get_book_by_id(self, auth_token):
        """Test GET /api/books/{id} - used by booksAPI.getById() in BookEditor.js"""
        # First get user's books
        my_books = requests.get(f"{BASE_URL}/api/books/my", headers={
            "Authorization": f"Bearer {auth_token}"
        }).json()
        
        if len(my_books) > 0:
            book_id = my_books[0]["id"]
            response = requests.get(f"{BASE_URL}/api/books/{book_id}")
            
            assert response.status_code == 200, f"Get book by ID failed: {response.text}"
            data = response.json()
            assert "id" in data
            assert data["id"] == book_id
            print(f"✓ Book fetched by ID: {data.get('title', 'N/A')}")
        else:
            print("⚠ No books to test - skipping get by ID")


class TestChaptersAndPagesAPI:
    """Test chapter and page endpoints used by BookEditor.js via api.js pagesAPI"""
    
    def test_get_book_chapters(self, auth_token):
        """Test GET /api/books/{id}/chapters - used by booksAPI.getChapters()"""
        # Get a book first
        my_books = requests.get(f"{BASE_URL}/api/books/my", headers={
            "Authorization": f"Bearer {auth_token}"
        }).json()
        
        if len(my_books) > 0:
            book_id = my_books[0]["id"]
            response = requests.get(f"{BASE_URL}/api/books/{book_id}/chapters")
            
            assert response.status_code == 200, f"Get chapters failed: {response.text}"
            data = response.json()
            assert isinstance(data, list)
            print(f"✓ Chapters fetched for book - count: {len(data)}")
            return data, book_id
        else:
            print("⚠ No books to test chapters")
            return [], None
    
    def test_get_chapter_pages(self, auth_token):
        """Test GET /api/chapters/{id}/pages - used by pagesAPI.getByChapter()"""
        # Get chapters first
        my_books = requests.get(f"{BASE_URL}/api/books/my", headers={
            "Authorization": f"Bearer {auth_token}"
        }).json()
        
        if len(my_books) > 0:
            book_id = my_books[0]["id"]
            chapters = requests.get(f"{BASE_URL}/api/books/{book_id}/chapters").json()
            
            if len(chapters) > 0:
                chapter_id = chapters[0]["id"]
                response = requests.get(f"{BASE_URL}/api/chapters/{chapter_id}/pages")
                
                assert response.status_code == 200, f"Get pages failed: {response.text}"
                data = response.json()
                assert isinstance(data, list)
                print(f"✓ Pages fetched for chapter - count: {len(data)}")
            else:
                print("⚠ No chapters to test pages")
        else:
            print("⚠ No books to test pages")


class TestProStudioAPI:
    """Test Pro Studio endpoints used by ProStudio.js via api.js proStudioAPI"""
    
    def test_get_characters(self, auth_token):
        """Test GET /api/pro-studio/characters - used by proStudioAPI.getCharacters()"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Get characters failed: {response.text}"
        data = response.json()
        assert "characters" in data or isinstance(data, list)
        characters = data.get("characters", data)
        print(f"✓ Pro Studio characters fetched - count: {len(characters)}")
        return characters
    
    def test_get_gallery(self, auth_token):
        """Test GET /api/pro-studio/gallery - used by proStudioAPI.getGallery()"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/gallery", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Get gallery failed: {response.text}"
        data = response.json()
        print(f"✓ Pro Studio gallery fetched - items: {len(data.get('images', []))}")
    
    def test_get_gallery_unified(self, auth_token):
        """Test GET /api/pro-studio/gallery/unified - used by proStudioAPI.getGalleryUnified()"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/gallery/unified", headers={
            "Authorization": f"Bearer {auth_token}"
        }, params={"page": 1, "limit": 10})
        
        assert response.status_code == 200, f"Get unified gallery failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Unified gallery fetched - items: {len(data['items'])}, total: {data['total']}")
    
    def test_get_scenes(self, auth_token):
        """Test GET /api/pro-studio/scenes - used by proStudioAPI.getScenes()"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/scenes", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Get scenes failed: {response.text}"
        data = response.json()
        scenes = data.get("scenes", [])
        print(f"✓ Pro Studio scenes fetched - count: {len(scenes)}")
    
    def test_get_scene_options(self):
        """Test GET /api/pro-studio/scene-options - used by proStudioAPI.getSceneOptions()"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/scene-options")
        
        assert response.status_code == 200, f"Get scene options failed: {response.text}"
        data = response.json()
        # Should have location_types, lighting, moods
        print(f"✓ Scene options fetched - keys: {list(data.keys())}")
    
    def test_get_character_styles(self):
        """Test GET /api/pro-studio/character-styles - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-styles")
        
        assert response.status_code == 200
        data = response.json()
        assert "styles" in data
        print(f"✓ Character styles fetched - count: {len(data['styles'])}")
    
    def test_get_character_genres(self):
        """Test GET /api/pro-studio/character-genres - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/pro-studio/character-genres")
        
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        print(f"✓ Character genres fetched - count: {len(data['genres'])}")
    
    def test_get_character_gallery(self, auth_token):
        """Test GET /api/pro-studio/characters/{id}/gallery - used in BookEditor.js"""
        # First get characters
        chars_response = requests.get(f"{BASE_URL}/api/pro-studio/characters", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        chars = chars_response.json().get("characters", [])
        
        if len(chars) > 0:
            char_id = chars[0]["id"]
            response = requests.get(f"{BASE_URL}/api/pro-studio/characters/{char_id}/gallery", headers={
                "Authorization": f"Bearer {auth_token}"
            })
            
            assert response.status_code == 200, f"Get character gallery failed: {response.text}"
            data = response.json()
            print(f"✓ Character gallery fetched for {chars[0].get('name', 'N/A')} - images: {len(data.get('images', []))}")
        else:
            print("⚠ No characters to test gallery")


class TestArtStudioAPI:
    """Test Art Studio endpoints used by ArtStudio.js, BookEditor.js via api.js artStudioAPI"""
    
    def test_get_gallery(self, auth_token):
        """Test GET /api/art-studio/gallery - used by artStudioAPI.getGallery()"""
        response = requests.get(f"{BASE_URL}/api/art-studio/gallery", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Get art studio gallery failed: {response.text}"
        data = response.json()
        images = data.get("images", [])
        print(f"✓ Art Studio gallery fetched - images: {len(images)}")
    
    def test_get_book_gallery(self, auth_token):
        """Test GET /api/art-studio/gallery/book/{id} - used by artStudioAPI.getBookGallery()"""
        # Get a book first
        my_books = requests.get(f"{BASE_URL}/api/books/my", headers={
            "Authorization": f"Bearer {auth_token}"
        }).json()
        
        if len(my_books) > 0:
            book_id = my_books[0]["id"]
            response = requests.get(f"{BASE_URL}/api/art-studio/gallery/book/{book_id}", headers={
                "Authorization": f"Bearer {auth_token}"
            })
            
            assert response.status_code == 200, f"Get book gallery failed: {response.text}"
            data = response.json()
            print(f"✓ Book gallery fetched - images: {len(data.get('images', []))}")
        else:
            print("⚠ No books to test book gallery")


class TestUserAPI:
    """Test user-related endpoints used by UserProfile.js via api.js userAPI"""
    
    def test_get_user_profile(self, auth_token):
        """Test GET /api/users/{id} - used by userAPI.getProfile()"""
        # Get current user first
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        user = me_response.json()
        user_id = user.get("id")
        
        if user_id:
            response = requests.get(f"{BASE_URL}/api/users/{user_id}", headers={
                "Authorization": f"Bearer {auth_token}"
            })
            
            # Profile may or may not exist
            if response.status_code == 200:
                data = response.json()
                print(f"✓ User profile fetched - name: {data.get('name', data.get('email', 'N/A'))}")
            elif response.status_code == 404:
                print("⚠ User profile not found (may not be set up)")
            else:
                assert False, f"Unexpected status: {response.status_code}"
    
    def test_get_credits_balance(self, auth_token):
        """Test GET /api/credits/balance - used by creditsAPI.getBalance()"""
        response = requests.get(f"{BASE_URL}/api/credits/balance", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        
        assert response.status_code == 200, f"Get credits failed: {response.text}"
        data = response.json()
        assert "credits" in data
        print(f"✓ Credits balance fetched - credits: {data['credits']}")


class TestAdditionalEndpoints:
    """Test additional endpoints used across the app"""
    
    def test_get_voices(self):
        """Test GET /api/voices - used in BookEditor.js"""
        response = requests.get(f"{BASE_URL}/api/voices")
        
        assert response.status_code == 200, f"Get voices failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Voices fetched - count: {len(data)}")
    
    def test_get_starter_library(self):
        """Test GET /api/starter-library - used in BookEditor.js"""
        response = requests.get(f"{BASE_URL}/api/starter-library")
        
        assert response.status_code == 200, f"Get starter library failed: {response.text}"
        data = response.json()
        assert "images" in data
        print(f"✓ Starter library fetched - images: {len(data['images'])}")
    
    def test_get_fal_models(self):
        """Test GET /api/fal/models - used by falAPI.getModels()"""
        response = requests.get(f"{BASE_URL}/api/fal/models")
        
        assert response.status_code == 200, f"Get fal models failed: {response.text}"
        data = response.json()
        print(f"✓ Fal models info fetched - available: {data.get('available', 'N/A')}")


# Fixtures
@pytest.fixture
def auth_token():
    """Get authentication token for VIP user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": VIP_EMAIL,
        "password": VIP_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    pytest.skip("Could not authenticate - skipping authenticated tests")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
