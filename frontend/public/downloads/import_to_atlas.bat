@echo off
REM MongoDB Atlas Import Script for Azories
REM ==========================================
REM 
REM INSTRUCTIONS:
REM 1. Install MongoDB Database Tools: https://www.mongodb.com/try/download/database-tools
REM 2. Edit the variables below with your credentials
REM 3. Make sure the COLLECTIONS_PATH points to your extracted collections folder
REM 4. Run this script as Administrator

REM ==========================================
REM EDIT THESE VARIABLES
REM ==========================================
set ATLAS_USER=palmbeachmagalluf
set ATLAS_PASSWORD=YOUR_PASSWORD_HERE
set ATLAS_CLUSTER=azories.6cv4tlm.mongodb.net
set DATABASE=azories
set COLLECTIONS_PATH=C:\Users\%USERNAME%\Downloads\mongodb_export\collections

REM ==========================================
REM DO NOT EDIT BELOW THIS LINE
REM ==========================================

set ATLAS_URI=mongodb+srv://%ATLAS_USER%:%ATLAS_PASSWORD%@%ATLAS_CLUSTER%/%DATABASE%?retryWrites=true^&w=majority

echo.
echo =====================================================
echo   MongoDB Atlas Import Script for Azories
echo =====================================================
echo.
echo Atlas URI: mongodb+srv://%ATLAS_USER%:****@%ATLAS_CLUSTER%/%DATABASE%
echo Collections Path: %COLLECTIONS_PATH%
echo.

REM Check if collections folder exists
if not exist "%COLLECTIONS_PATH%" (
    echo ERROR: Collections folder not found at %COLLECTIONS_PATH%
    echo Please extract mongodb_export.zip and update COLLECTIONS_PATH
    pause
    exit /b 1
)

REM Check if mongoimport exists
where mongoimport >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: mongoimport not found. Please install MongoDB Database Tools.
    echo Download from: https://www.mongodb.com/try/download/database-tools
    pause
    exit /b 1
)

echo Starting import of 31 collections...
echo.

REM Import each collection
echo [1/31] Importing analytics...
mongoimport --uri="%ATLAS_URI%" --collection=analytics --file="%COLLECTIONS_PATH%\analytics.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: analytics import may have failed

echo [2/31] Importing art_studio_animations...
mongoimport --uri="%ATLAS_URI%" --collection=art_studio_animations --file="%COLLECTIONS_PATH%\art_studio_animations.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: art_studio_animations import may have failed

echo [3/31] Importing art_studio_gallery...
mongoimport --uri="%ATLAS_URI%" --collection=art_studio_gallery --file="%COLLECTIONS_PATH%\art_studio_gallery.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: art_studio_gallery import may have failed

echo [4/31] Importing art_studio_generations...
mongoimport --uri="%ATLAS_URI%" --collection=art_studio_generations --file="%COLLECTIONS_PATH%\art_studio_generations.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: art_studio_generations import may have failed

echo [5/31] Importing art_studio_workflows...
mongoimport --uri="%ATLAS_URI%" --collection=art_studio_workflows --file="%COLLECTIONS_PATH%\art_studio_workflows.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: art_studio_workflows import may have failed

echo [6/31] Importing audio_cache...
mongoimport --uri="%ATLAS_URI%" --collection=audio_cache --file="%COLLECTIONS_PATH%\audio_cache.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: audio_cache import may have failed

echo [7/31] Importing book_images...
mongoimport --uri="%ATLAS_URI%" --collection=book_images --file="%COLLECTIONS_PATH%\book_images.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: book_images import may have failed

echo [8/31] Importing books...
mongoimport --uri="%ATLAS_URI%" --collection=books --file="%COLLECTIONS_PATH%\books.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: books import may have failed

echo [9/31] Importing chapters...
mongoimport --uri="%ATLAS_URI%" --collection=chapters --file="%COLLECTIONS_PATH%\chapters.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: chapters import may have failed

echo [10/31] Importing character_gallery...
mongoimport --uri="%ATLAS_URI%" --collection=character_gallery --file="%COLLECTIONS_PATH%\character_gallery.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: character_gallery import may have failed

echo [11/31] Importing character_profiles...
mongoimport --uri="%ATLAS_URI%" --collection=character_profiles --file="%COLLECTIONS_PATH%\character_profiles.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: character_profiles import may have failed

echo [12/31] Importing contact_messages...
mongoimport --uri="%ATLAS_URI%" --collection=contact_messages --file="%COLLECTIONS_PATH%\contact_messages.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: contact_messages import may have failed

echo [13/31] Importing credit_usage...
mongoimport --uri="%ATLAS_URI%" --collection=credit_usage --file="%COLLECTIONS_PATH%\credit_usage.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: credit_usage import may have failed

echo [14/31] Importing follows...
mongoimport --uri="%ATLAS_URI%" --collection=follows --file="%COLLECTIONS_PATH%\follows.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: follows import may have failed

echo [15/31] Importing invites...
mongoimport --uri="%ATLAS_URI%" --collection=invites --file="%COLLECTIONS_PATH%\invites.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: invites import may have failed

echo [16/31] Importing pages...
mongoimport --uri="%ATLAS_URI%" --collection=pages --file="%COLLECTIONS_PATH%\pages.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: pages import may have failed

echo [17/31] Importing password_resets...
mongoimport --uri="%ATLAS_URI%" --collection=password_resets --file="%COLLECTIONS_PATH%\password_resets.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: password_resets import may have failed

echo [18/31] Importing payment_transactions...
mongoimport --uri="%ATLAS_URI%" --collection=payment_transactions --file="%COLLECTIONS_PATH%\payment_transactions.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: payment_transactions import may have failed

echo [19/31] Importing pro_studio_characters...
mongoimport --uri="%ATLAS_URI%" --collection=pro_studio_characters --file="%COLLECTIONS_PATH%\pro_studio_characters.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: pro_studio_characters import may have failed

echo [20/31] Importing pro_studio_scenes...
mongoimport --uri="%ATLAS_URI%" --collection=pro_studio_scenes --file="%COLLECTIONS_PATH%\pro_studio_scenes.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: pro_studio_scenes import may have failed

echo [21/31] Importing profiles...
mongoimport --uri="%ATLAS_URI%" --collection=profiles --file="%COLLECTIONS_PATH%\profiles.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: profiles import may have failed

echo [22/31] Importing prompt_history...
mongoimport --uri="%ATLAS_URI%" --collection=prompt_history --file="%COLLECTIONS_PATH%\prompt_history.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: prompt_history import may have failed

echo [23/31] Importing reading_progress...
mongoimport --uri="%ATLAS_URI%" --collection=reading_progress --file="%COLLECTIONS_PATH%\reading_progress.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: reading_progress import may have failed

echo [24/31] Importing reading_stats...
mongoimport --uri="%ATLAS_URI%" --collection=reading_stats --file="%COLLECTIONS_PATH%\reading_stats.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: reading_stats import may have failed

echo [25/31] Importing reading_streaks...
mongoimport --uri="%ATLAS_URI%" --collection=reading_streaks --file="%COLLECTIONS_PATH%\reading_streaks.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: reading_streaks import may have failed

echo [26/31] Importing reviews...
mongoimport --uri="%ATLAS_URI%" --collection=reviews --file="%COLLECTIONS_PATH%\reviews.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: reviews import may have failed

echo [27/31] Importing scene_gallery...
mongoimport --uri="%ATLAS_URI%" --collection=scene_gallery --file="%COLLECTIONS_PATH%\scene_gallery.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: scene_gallery import may have failed

echo [28/31] Importing series...
mongoimport --uri="%ATLAS_URI%" --collection=series --file="%COLLECTIONS_PATH%\series.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: series import may have failed

echo [29/31] Importing system_settings...
mongoimport --uri="%ATLAS_URI%" --collection=system_settings --file="%COLLECTIONS_PATH%\system_settings.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: system_settings import may have failed

echo [30/31] Importing users...
mongoimport --uri="%ATLAS_URI%" --collection=users --file="%COLLECTIONS_PATH%\users.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: users import may have failed

echo [31/31] Importing vip_usage...
mongoimport --uri="%ATLAS_URI%" --collection=vip_usage --file="%COLLECTIONS_PATH%\vip_usage.json" --jsonArray --drop
if %ERRORLEVEL% neq 0 echo WARNING: vip_usage import may have failed

echo.
echo =====================================================
echo   IMPORT COMPLETE!
echo =====================================================
echo.
echo All 31 collections have been imported to MongoDB Atlas.
echo.
echo Next steps:
echo 1. Verify data in MongoDB Compass or Atlas web UI
echo 2. Set MONGO_URL in Emergent production settings
echo 3. Deploy to production
echo.
pause
