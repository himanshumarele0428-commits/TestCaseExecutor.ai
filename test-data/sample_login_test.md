# Test Case: Login with valid credentials

Module: Authentication
Priority: High
Environment: QA
Browser: Chromium

## Steps

1. Open https://example.com/login
2. Enter "john@example.com" in the username field
3. Enter "Password123" in the password field
4. Click the Login button
5. Verify that the Dashboard page is displayed

# Test Case: Invalid Login

Module: Authentication
Priority: High

## Steps

1. Open https://example.com/login
2. Enter "wrong@test.com" in the username field
3. Enter "WrongPassword" in the password field
4. Click the Login button
5. Verify that an error message is displayed
