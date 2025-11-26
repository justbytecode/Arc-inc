@echo off
set GIT="C:\Program Files\Git\cmd\git.exe"

echo ----------------------------------------
echo  Deploying to GitHub...
echo ----------------------------------------

echo [1/6] Initializing repository...
%GIT% init

echo [2/6] Adding all files...
%GIT% add .

echo [3/6] Committing changes...
%GIT% commit -m "Initial commit: CSV Import App with modern UI"

echo [4/6] Renaming branch to 'main'...
%GIT% branch -M main

echo [5/6] Setting remote origin...
%GIT% remote remove origin 2>nul
%GIT% remote add origin https://github.com/justbytecode/Arc-inc.git

echo [6/6] Pushing to GitHub...
echo (A credential popup may appear - please sign in if requested)
%GIT% push -u origin main

echo ----------------------------------------
echo  Done!
echo ----------------------------------------
pause
