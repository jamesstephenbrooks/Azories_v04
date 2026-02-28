@echo off
REM MongoDB Atlas Import Script for Azories
REM ==========================================

REM Your MongoDB tools path
set MONGO_TOOLS=C:\Users\james\Downloads\mongodb-database-tools-windows-x86_64-100.14.1\mongodb-database-tools-windows-x86_64-100.14.1\bin

REM Atlas credentials
set ATLAS_URI=mongodb+srv://palmbeachmagalluf:5Woodgates179!@azories.6cv4tlm.mongodb.net/azories?retryWrites=true&w=majority

REM Path to your collections folder
set COLLECTIONS_PATH=C:\Users\james\Downloads\mongodb_export\collections

echo.
echo =====================================================
echo   MongoDB Atlas Import Script for Azories
echo =====================================================
echo.

REM Check if collections folder exists
if not exist "%COLLECTIONS_PATH%" (
    echo ERROR: Collections folder not found!
    echo Expected: %COLLECTIONS_PATH%
    echo.
    echo Please extract mongodb_export.zip to your Downloads folder
    pause
    exit /b 1
)

echo Starting import of 31 collections...
echo.

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=analytics --file="%COLLECTIONS_PATH%\analytics.json" --jsonArray --drop
echo [1/31] analytics done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=art_studio_animations --file="%COLLECTIONS_PATH%\art_studio_animations.json" --jsonArray --drop
echo [2/31] art_studio_animations done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=art_studio_gallery --file="%COLLECTIONS_PATH%\art_studio_gallery.json" --jsonArray --drop
echo [3/31] art_studio_gallery done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=art_studio_generations --file="%COLLECTIONS_PATH%\art_studio_generations.json" --jsonArray --drop
echo [4/31] art_studio_generations done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=art_studio_workflows --file="%COLLECTIONS_PATH%\art_studio_workflows.json" --jsonArray --drop
echo [5/31] art_studio_workflows done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=audio_cache --file="%COLLECTIONS_PATH%\audio_cache.json" --jsonArray --drop
echo [6/31] audio_cache done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=book_images --file="%COLLECTIONS_PATH%\book_images.json" --jsonArray --drop
echo [7/31] book_images done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=books --file="%COLLECTIONS_PATH%\books.json" --jsonArray --drop
echo [8/31] books done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=chapters --file="%COLLECTIONS_PATH%\chapters.json" --jsonArray --drop
echo [9/31] chapters done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=character_gallery --file="%COLLECTIONS_PATH%\character_gallery.json" --jsonArray --drop
echo [10/31] character_gallery done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=character_profiles --file="%COLLECTIONS_PATH%\character_profiles.json" --jsonArray --drop
echo [11/31] character_profiles done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=contact_messages --file="%COLLECTIONS_PATH%\contact_messages.json" --jsonArray --drop
echo [12/31] contact_messages done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=credit_usage --file="%COLLECTIONS_PATH%\credit_usage.json" --jsonArray --drop
echo [13/31] credit_usage done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=follows --file="%COLLECTIONS_PATH%\follows.json" --jsonArray --drop
echo [14/31] follows done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=invites --file="%COLLECTIONS_PATH%\invites.json" --jsonArray --drop
echo [15/31] invites done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=pages --file="%COLLECTIONS_PATH%\pages.json" --jsonArray --drop
echo [16/31] pages done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=password_resets --file="%COLLECTIONS_PATH%\password_resets.json" --jsonArray --drop
echo [17/31] password_resets done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=payment_transactions --file="%COLLECTIONS_PATH%\payment_transactions.json" --jsonArray --drop
echo [18/31] payment_transactions done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=pro_studio_characters --file="%COLLECTIONS_PATH%\pro_studio_characters.json" --jsonArray --drop
echo [19/31] pro_studio_characters done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=pro_studio_scenes --file="%COLLECTIONS_PATH%\pro_studio_scenes.json" --jsonArray --drop
echo [20/31] pro_studio_scenes done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=profiles --file="%COLLECTIONS_PATH%\profiles.json" --jsonArray --drop
echo [21/31] profiles done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=prompt_history --file="%COLLECTIONS_PATH%\prompt_history.json" --jsonArray --drop
echo [22/31] prompt_history done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=reading_progress --file="%COLLECTIONS_PATH%\reading_progress.json" --jsonArray --drop
echo [23/31] reading_progress done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=reading_stats --file="%COLLECTIONS_PATH%\reading_stats.json" --jsonArray --drop
echo [24/31] reading_stats done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=reading_streaks --file="%COLLECTIONS_PATH%\reading_streaks.json" --jsonArray --drop
echo [25/31] reading_streaks done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=reviews --file="%COLLECTIONS_PATH%\reviews.json" --jsonArray --drop
echo [26/31] reviews done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=scene_gallery --file="%COLLECTIONS_PATH%\scene_gallery.json" --jsonArray --drop
echo [27/31] scene_gallery done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=series --file="%COLLECTIONS_PATH%\series.json" --jsonArray --drop
echo [28/31] series done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=system_settings --file="%COLLECTIONS_PATH%\system_settings.json" --jsonArray --drop
echo [29/31] system_settings done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=users --file="%COLLECTIONS_PATH%\users.json" --jsonArray --drop
echo [30/31] users done

"%MONGO_TOOLS%\mongoimport.exe" --uri="%ATLAS_URI%" --collection=vip_usage --file="%COLLECTIONS_PATH%\vip_usage.json" --jsonArray --drop
echo [31/31] vip_usage done

echo.
echo =====================================================
echo   IMPORT COMPLETE!
echo =====================================================
echo.
echo All 31 collections imported to MongoDB Atlas.
echo.
pause
